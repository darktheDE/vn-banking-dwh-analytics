import os
import sys
from datetime import datetime
import pandas as pd
from vnstock import Market
from vnstock.explorer.vci.financial import Finance as VCIFinance

# Đảm bảo console in ra tiếng Việt chuẩn UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Đường dẫn thư mục dữ liệu processed chính
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data', 'processed')
os.makedirs(DATA_DIR, exist_ok=True)

# Danh sách các mã cổ phiếu cần tải dữ liệu
SYMBOLS = ['BID', 'TCB', 'VCB', 'CTG']

print("==================================================================")
print("   BẮT ĐẦU QUÁ TRÌNH TRÍCH XUẤT DỮ LIỆU NGÂN HÀNG (BID - TCB)")
print("==================================================================")

# ==============================================================================
# HỢP PHẦN 1: TẢI VÀ GỘP LỊCH SỬ GIÁ CỔ PHIẾU
# ==============================================================================
def extract_stock_history(symbol, symbol_dir):
    print(f"\n[1/3] Đang tải lịch sử giá cổ phiếu {symbol}...")
    m = Market()
    
    # Lấy phân đoạn 1: 2014-01-01 đến 2020-12-31
    print("      -> Đang tải Phân đoạn 1 (2014 - 2020)...")
    try:
        df1 = m.equity(symbol).ohlcv(start='2014-01-01', end='2020-12-31', resolution='1D', count=5000, source='vci')
        print(f"         Thành công. Số phiên: {df1.shape[0]}")
    except Exception as e:
        print(f"         Thất bại khi tải Phân đoạn 1: {e}")
        df1 = pd.DataFrame()

    # Lấy phân đoạn 2: 2021-01-01 đến hiện tại
    today_str = datetime.today().strftime('%Y-%m-%d')
    print(f"      -> Đang tải Phân đoạn 2 (2021 - {today_str})...")
    try:
        df2 = m.equity(symbol).ohlcv(start='2021-01-01', end=today_str, resolution='1D', count=5000, source='vci')
        print(f"         Thành công. Số phiên: {df2.shape[0]}")
    except Exception as e:
        print(f"         Thất bại khi tải Phân đoạn 2: {e}")
        df2 = pd.DataFrame()

    # Gộp và làm sạch dữ liệu
    if not df1.empty or not df2.empty:
        print("      -> Đang gộp dữ liệu và làm sạch...")
        df_combined = pd.concat([df1, df2]).drop_duplicates(subset=['time'])
        df_combined = df_combined.sort_values('time').reset_index(drop=True)
        
        # Đảm bảo định dạng cột thời gian chỉ hiển thị ngày (YYYY-MM-DD)
        df_combined['time'] = pd.to_datetime(df_combined['time']).dt.strftime('%Y-%m-%d')
        
        output_path = os.path.join(symbol_dir, f'{symbol.lower()}_stock_history.csv')
        df_combined.to_csv(output_path, index=False, encoding='utf-8')
        print(f"      [OK] Đã xuất {df_combined.shape[0]} phiên giao dịch ra: {output_path}")
        print(f"           - Ngày giao dịch đầu tiên: {df_combined['time'].min()}")
        print(f"           - Ngày giao dịch cuối cùng: {df_combined['time'].max()}")
    else:
        print(f"      [ERROR] Không tải được dữ liệu lịch sử giá cổ phiếu {symbol}.")

# ==============================================================================
# HỢP PHẦN 2: XOAY TRỤC (TRANSPOSE) ĐƯA DỮ LIỆU BCTC VỀ DẠNG CHUỒI THỜI GIAN DỌC
# ==============================================================================
def transpose_and_clean(df, report_type):
    """
    Xoay trục dữ liệu BCTC: Hàng trở thành Cột (chỉ tiêu), Cột trở thành Hàng (chu kỳ thời gian).
    Đồng thời trả về DataFrame ánh xạ chỉ tiêu phục vụ từ điển dữ liệu.
    """
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
        
    # Trích xuất dữ liệu ánh xạ chỉ tiêu (Việt - Anh - Mã ID) phục vụ Metadata mapping
    mapping_cols = [c for c in ['item', 'item_en', 'item_id'] if c in df.columns]
    df_mapping = df[mapping_cols].copy()
    df_mapping['report_type'] = report_type
    
    # Xác định các cột kỳ thời gian (ví dụ: '2024', '2025-Q1',...)
    metadata_cols = ['item', 'item_en', 'item_id', 'unit', 'levels', 'row_number']
    period_cols = [col for col in df.columns if col not in metadata_cols]
    
    # Xoay trục dựa trên cột chỉ tiêu tiếng Việt
    df_ts = df.set_index('item')[period_cols].transpose()
    df_ts = df_ts.reset_index().rename(columns={'index': 'period'})
    
    # Sắp xếp chuỗi thời gian tăng dần
    df_ts = df_ts.sort_values('period').reset_index(drop=True)
    
    return df_ts, df_mapping

# ==============================================================================
# QUÁ TRÌNH CHẠY CHÍNH
# ==============================================================================
def main():
    all_mappings = []
    
    for symbol in SYMBOLS:
        symbol = symbol.upper()
        symbol_dir = os.path.join(DATA_DIR, symbol.lower())
        os.makedirs(symbol_dir, exist_ok=True)
        
        print(f"\n=============================================================")
        print(f" ĐANG XỬ LÝ DỮ LIỆU CHO NGÂN HÀNG: {symbol}")
        print(f"=============================================================")

        # 1. Tải lịch sử giá chứng khoán
        extract_stock_history(symbol, symbol_dir)
        
        # 2. Tải Báo cáo tài chính (CDKT, KQKD, LCTT) từ VCI
        f = VCIFinance(symbol=symbol, show_log=False)
        
        reports = {
            'balance_sheet': 'balance_sheet',
            'income_statement': 'income_statement',
            'cash_flow': 'cash_flow'
        }
        
        periods = ['annual', 'quarterly']
        
        print(f"\n[2/3] Đang trích xuất và xoay trục báo cáo tài chính {symbol} từ VCI...")
        
        for rkey, file_suffix in reports.items():
            for p in periods:
                period_param = 'year' if p == 'annual' else 'quarter'
                limit_val = 20 if p == 'annual' else 60
                
                print(f"      -> Đang tải {rkey.upper()} ({p.upper()})...")
                try:
                    # Tải dữ liệu ngang từ VCI
                    df_raw = f._get_financial_report(rkey, period=period_param, limit=limit_val, dropna=False)
                    
                    # Xoay trục sang dạng dọc chuỗi thời gian
                    df_ts, df_map = transpose_and_clean(df_raw, rkey)
                    
                    if not df_ts.empty:
                        output_file = os.path.join(symbol_dir, f"{symbol.lower()}_{file_suffix}_{p}.csv")
                        df_ts.to_csv(output_file, index=False, encoding='utf-8')
                        print(f"         [OK] Đã xuất {df_ts.shape[0]} chu kỳ ra: {output_file}")
                        
                        if not df_map.empty:
                            all_mappings.append(df_map)
                    else:
                        print(f"         [WARNING] Không có dữ liệu cho {rkey} ({p}).")
                except Exception as e:
                    print(f"         [ERROR] Thất bại khi xử lý {rkey} ({p}): {e}")
                    
        # 3. Tải và xử lý Chỉ số tài chính (Ratios) từ VCI ở chế độ Raw (dọc sẵn)
        print(f"\n      -> Đang tải FINANCIAL RATIOS cho {symbol} (ANNUAL & QUARTERLY)...")
        try:
            df_ratio_raw = f._get_report('ratio', mode='raw', period='year', limit=100)
            
            # 3.1. Xử lý Annual Ratios
            df_ratio_annual = df_ratio_raw[df_ratio_raw['quarter'] == 5].copy()
            df_ratio_annual['period'] = df_ratio_annual['year'].astype(str)
            
            # Lọc bỏ các cột kỹ thuật
            cols_to_drop = ['year', 'quarter', 'ratioTTMId', 'ratioType', 'organCode', 'yearReport', 'ratioYearId']
            df_ratio_annual = df_ratio_annual.drop(columns=[c for c in cols_to_drop if c in df_ratio_annual.columns])
            
            # Đưa cột period lên đầu và sắp xếp
            cols_annual = ['period'] + [c for c in df_ratio_annual.columns if c != 'period']
            df_ratio_annual = df_ratio_annual[cols_annual].sort_values('period').reset_index(drop=True)
            
            ratio_ann_file = os.path.join(symbol_dir, f'{symbol.lower()}_financial_ratios_annual.csv')
            df_ratio_annual.to_csv(ratio_ann_file, index=False, encoding='utf-8')
            print(f"         [OK] Đã xuất {df_ratio_annual.shape[0]} chu kỳ ra: {ratio_ann_file}")
            
            # 3.2. Xử lý Quarterly Ratios
            df_ratio_quarter = df_ratio_raw[df_ratio_raw['quarter'].isin([1, 2, 3, 4])].copy()
            df_ratio_quarter['period'] = df_ratio_quarter['year'].astype(str) + '-Q' + df_ratio_quarter['quarter'].astype(str)
            df_ratio_quarter = df_ratio_quarter.drop(columns=[c for c in cols_to_drop if c in df_ratio_quarter.columns])
            
            cols_quarter = ['period'] + [c for c in df_ratio_quarter.columns if c != 'period']
            df_ratio_quarter = df_ratio_quarter[cols_quarter].sort_values('period').reset_index(drop=True)
            
            ratio_qtr_file = os.path.join(symbol_dir, f'{symbol.lower()}_financial_ratios_quarterly.csv')
            df_ratio_quarter.to_csv(ratio_qtr_file, index=False, encoding='utf-8')
            print(f"         [OK] Đã xuất {df_ratio_quarter.shape[0]} chu kỳ ra: {ratio_qtr_file}")
            
            # Thêm mapping cho tỷ số tài chính vào từ điển chỉ tiêu
            from vnstock.explorer.vci.const import RATIO_COLUMN_MAP_VI, RATIO_COLUMN_MAP_EN
            ratio_mapping_rows = []
            for fid, vname in RATIO_COLUMN_MAP_VI.items():
                ename = RATIO_COLUMN_MAP_EN.get(fid, '')
                ratio_mapping_rows.append({
                    'item': vname,
                    'item_en': ename,
                    'item_id': fid,
                    'report_type': 'ratios'
                })
            df_ratio_map = pd.DataFrame(ratio_mapping_rows)
            all_mappings.append(df_ratio_map)
            
        except Exception as e:
            print(f"         [ERROR] Thất bại khi tải Chỉ số tài chính cho {symbol}: {e}")

    # 4. Tạo file Metadata mapping từ điển chỉ tiêu tài chính dùng chung
    print("\n[3/3] Đang tạo từ điển dữ liệu chỉ tiêu tài chính dùng chung...")
    if all_mappings:
        df_mapping_all = pd.concat(all_mappings).drop_duplicates(subset=['item', 'report_type']).reset_index(drop=True)
        
        cols = ['report_type', 'item_id', 'item']
        if 'item_en' in df_mapping_all.columns:
            cols.append('item_en')
            
        df_mapping_all = df_mapping_all[[c for c in cols if c in df_mapping_all.columns]]
        df_mapping_all = df_mapping_all.rename(columns={'item': 'item_vi'})
        
        mapping_file = os.path.join(DATA_DIR, 'financial_items_mapping.csv')
        df_mapping_all.to_csv(mapping_file, index=False, encoding='utf-8')
        print(f"      [OK] Từ điển chỉ tiêu tài chính gồm {df_mapping_all.shape[0]} mục đã được ghi vào: {mapping_file}")
        
    print("\n==================================================================")
    print("   HOÀN THÀNH QUÁ TRÌNH TRÍCH XUẤT DỮ LIỆU. FILE ĐẦU RA SẴN SÀNG!")
    print("==================================================================")

if __name__ == '__main__':
    main()
