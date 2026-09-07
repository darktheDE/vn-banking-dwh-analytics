import os
import sys
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from vnstock import Market
from vnstock.explorer.vci.financial import Finance as VCIFinance

from src.utils.config import load_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Đảm bảo console in ra tiếng Việt chuẩn UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Đường dẫn thư mục dữ liệu processed chính — đọc từ .env thông qua Config.
# B-10 fix: trước đây hardcode DATA_DIR = os.path.join(os.path.dirname(__file__), 'data', 'processed'),
# gây sai path khi move file. Giờ đọc PROCESSED_DATA_PATH env var (default './data/processed/').
load_dotenv()
config = load_config()
DATA_DIR = os.path.join(config.processed_data_path, "raw_extractions")
os.makedirs(DATA_DIR, exist_ok=True)

# Danh sách các mã cổ phiếu cần tải dữ liệu
SYMBOLS = ['BID', 'TCB', 'VCB', 'CTG']

logger.info("==================================================================")
logger.info("   BẮT ĐẦU QUÁ TRÌNH TRÍCH XUẤT DỮ LIỆU NGÂN HÀNG (BID - TCB)")
logger.info("==================================================================")

# ==============================================================================
# HỢP PHẦN 1: TẢI VÀ GỘP LỊCH SỬ GIÁ CỔ PHIẾU
# ==============================================================================
def extract_stock_history(symbol, symbol_dir):
    logger.info("[1/3] Dang tai lich su gia co phieu %s ...", symbol)
    m = Market()

    # Lấy phân đoạn 1: 2014-01-01 đến 2020-12-31
    logger.info("      -> Dang tai Phan doan 1 (2014 - 2020)...")
    try:
        df1 = m.equity(symbol).ohlcv(start='2014-01-01', end='2020-12-31', resolution='1D', count=5000, source='vci')
        logger.info("         Thanh cong. So phien: %d", df1.shape[0])
    except Exception as e:
        logger.error("         That bai khi tai Phan doan 1: %s", e)
        df1 = pd.DataFrame()

    # Lấy phân đoạn 2: 2021-01-01 đến hiện tại
    today_str = datetime.today().strftime('%Y-%m-%d')
    logger.info("      -> Dang tai Phan doan 2 (2021 - %s)...", today_str)
    try:
        df2 = m.equity(symbol).ohlcv(start='2021-01-01', end=today_str, resolution='1D', count=5000, source='vci')
        logger.info("         Thanh cong. So phien: %d", df2.shape[0])
    except Exception as e:
        logger.error("         That bai khi tai Phan doan 2: %s", e)
        df2 = pd.DataFrame()

    # Gộp và làm sạch dữ liệu
    if not df1.empty or not df2.empty:
        logger.info("      -> Dang gop du lieu va lam sach...")
        df_combined = pd.concat([df1, df2]).drop_duplicates(subset=['time'])
        df_combined = df_combined.sort_values('time').reset_index(drop=True)

        # Đảm bảo định dạng cột thời gian chỉ hiển thị ngày (YYYY-MM-DD)
        df_combined['time'] = pd.to_datetime(df_combined['time']).dt.strftime('%Y-%m-%d')

        output_path = os.path.join(symbol_dir, f'{symbol.lower()}_stock_history.csv')
        df_combined.to_csv(output_path, index=False, encoding='utf-8')
        logger.info("      [OK] Da xuat %d phien giao dich ra: %s", df_combined.shape[0], output_path)
        logger.info("           - Ngay giao dich dau tien: %s", df_combined['time'].min())
        logger.info("           - Ngay giao dich cuoi cung: %s", df_combined['time'].max())
    else:
        logger.error("      [ERROR] Khong tai duoc du lieu lich su gia co phieu %s.", symbol)

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

        logger.info("=============================================================")
        logger.info(" DANG XU LY DU LIEU CHO NGAN HANG: %s", symbol)
        logger.info("=============================================================")

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

        logger.info("[2/3] Dang trich xuat va xoay truc bao cao tai chinh %s tu VCI...", symbol)

        for rkey, file_suffix in reports.items():
            for p in periods:
                period_param = 'year' if p == 'annual' else 'quarter'
                limit_val = 20 if p == 'annual' else 60

                logger.info("      -> Dang tai %s (%s)...", rkey.upper(), p.upper())
                try:
                    # Tải dữ liệu ngang từ VCI
                    df_raw = f._get_financial_report(rkey, period=period_param, limit=limit_val, dropna=False)

                    # Xoay trục sang dạng dọc chuỗi thời gian
                    df_ts, df_map = transpose_and_clean(df_raw, rkey)

                    if not df_ts.empty:
                        output_file = os.path.join(symbol_dir, f"{symbol.lower()}_{file_suffix}_{p}.csv")
                        df_ts.to_csv(output_file, index=False, encoding='utf-8')
                        logger.info("         [OK] Da xuat %d chu ky ra: %s", df_ts.shape[0], output_file)

                        if not df_map.empty:
                            all_mappings.append(df_map)
                    else:
                        logger.warning("         [WARNING] Khong co du lieu cho %s (%s).", rkey, p)
                except Exception as e:
                    logger.error("         [ERROR] That bai khi xu ly %s (%s): %s", rkey, p, e)

        # 3. Tải và xử lý Chỉ số tài chính (Ratios) từ VCI ở chế độ Raw (dọc sẵn)
        logger.info("      -> Dang tai FINANCIAL RATIOS cho %s (ANNUAL & QUARTERLY)...", symbol)
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
            logger.info("         [OK] Da xuat %d chu ky ra: %s", df_ratio_annual.shape[0], ratio_ann_file)

            # 3.2. Xử lý Quarterly Ratios
            df_ratio_quarter = df_ratio_raw[df_ratio_raw['quarter'].isin([1, 2, 3, 4])].copy()
            df_ratio_quarter['period'] = df_ratio_quarter['year'].astype(str) + '-Q' + df_ratio_quarter['quarter'].astype(str)
            df_ratio_quarter = df_ratio_quarter.drop(columns=[c for c in cols_to_drop if c in df_ratio_quarter.columns])

            cols_quarter = ['period'] + [c for c in df_ratio_quarter.columns if c != 'period']
            df_ratio_quarter = df_ratio_quarter[cols_quarter].sort_values('period').reset_index(drop=True)

            ratio_qtr_file = os.path.join(symbol_dir, f'{symbol.lower()}_financial_ratios_quarterly.csv')
            df_ratio_quarter.to_csv(ratio_qtr_file, index=False, encoding='utf-8')
            logger.info("         [OK] Da xuat %d chu ky ra: %s", df_ratio_quarter.shape[0], ratio_qtr_file)

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
            logger.error("         [ERROR] That bai khi tai Chi so tai chinh cho %s: %s", symbol, e)

    # 4. Tạo file Metadata mapping từ điển chỉ tiêu tài chính dùng chung
    logger.info("[3/3] Dang tao tu dien du lieu chi tieu tai chinh dung chung...")
    if all_mappings:
        df_mapping_all = pd.concat(all_mappings).drop_duplicates(subset=['item', 'report_type']).reset_index(drop=True)

        cols = ['report_type', 'item_id', 'item']
        if 'item_en' in df_mapping_all.columns:
            cols.append('item_en')

        df_mapping_all = df_mapping_all[[c for c in cols if c in df_mapping_all.columns]]
        df_mapping_all = df_mapping_all.rename(columns={'item': 'item_vi'})

        mapping_file = os.path.join(DATA_DIR, 'financial_items_mapping.csv')
        df_mapping_all.to_csv(mapping_file, index=False, encoding='utf-8')
        logger.info("      [OK] Tu dien chi tieu tai chinh gom %d muc da duoc ghi vao: %s", df_mapping_all.shape[0], mapping_file)

    logger.info("==================================================================")
    logger.info("   HOAN THANH QUA TRINH TRICH XUAT DU LIEU. FILE DAU RA SAN SANG!")
    logger.info("==================================================================")

if __name__ == '__main__':
    main()
