# Tài liệu Đặc tả Dữ liệu - Dự án Data Warehouse Tài chính Ngân hàng (BIDV, TCB, VCB, CTG)

Tài liệu này đặc tả chi tiết cấu trúc dữ liệu, lược đồ (schema), phạm vi và các tính chất dữ liệu của toàn bộ các tệp tin CSV đã được thu thập, chuẩn hóa và lưu trữ tại thư mục dữ liệu đã qua xử lý (`data/processed/`). Đây là cơ sở thông tin đồng nhất để phục vụ xây dựng Kho dữ liệu (Data Warehouse) và cung cấp đầu vào cho các mô hình học máy (Machine Learning).

---

## 1. Tổng quan Cấu trúc Thư mục Dữ liệu

Dữ liệu được tổ chức phân cấp rõ rệt để tách biệt giữa dữ liệu thô toàn ngành và dữ liệu chi tiết của từng ngân hàng:

```text
data/
├── raw/
│   └── VN banks dataset (updated August 2023).xlsx  # Dữ liệu Excel gốc 45 ngân hàng thương mại (2002-2022)
└── processed/
    ├── financial_items_mapping.csv                 # Từ điển chỉ tiêu tài chính Việt - Anh dùng chung (219 dòng)
    ├── bid/                                         # Thư mục dữ liệu processed của BIDV (BID)
    │   ├── bid_stock_history.csv
    │   ├── bid_balance_sheet_annual.csv / bid_balance_sheet_quarterly.csv
    │   ├── bid_income_statement_annual.csv / bid_income_statement_quarterly.csv
    │   ├── bid_cash_flow_annual.csv / bid_cash_flow_quarterly.csv
    │   └── bid_financial_ratios_annual.csv / bid_financial_ratios_quarterly.csv
    ├── tcb/                                         # Thư mục dữ liệu processed của Techcombank (TCB)
    │   ├── tcb_stock_history.csv
    │   └── ... (các file báo cáo tài chính tương tự)
    ├── vcb/                                         # Thư mục dữ liệu processed của Vietcombank (VCB)
    │   ├── vcb_stock_history.csv
    │   └── ... (các file báo cáo tài chính tương tự)
    └── ctg/                                         # Thư mục dữ liệu processed của VietinBank (CTG)
        ├── ctg_stock_history.csv
        └── ... (các file báo cáo tài chính tương tự)
```

---

## 2. Chi tiết Phạm vi & Thống kê Dữ liệu (Scope & Statistics)

Tất cả các tệp CSV báo cáo tài chính đều ở dạng **chuỗi thời gian dọc đã xoay trục (transposed time-series)**. Dưới đây là thống kê số dòng và mốc thời gian của từng ngân hàng:

### 2.1. Ngân hàng BIDV (BID)
*   **Giá cổ phiếu (`bid_stock_history.csv`)**: 3,096 dòng. Giai đoạn: `24/01/2014` (Ngày niêm yết) đến `26/06/2026`.
*   **Báo cáo tài chính Năm (Annual BS/IS/CF)**: 8 dòng. Giai đoạn: `2018` đến `2025`.
*   **Báo cáo tài chính Quý (Quarterly BS/IS/CF)**: 33 dòng. Giai đoạn: `Q1/2018` đến `Q1/2026`.
*   **Chỉ số tài chính tính sẵn (Financial Ratios)**: 8 dòng (Năm: `2018` - `2025`), 32 dòng (Quý: `Q1/2018` - `Q4/2025`).

### 2.2. Ngân hàng Techcombank (TCB)
*   **Giá cổ phiếu (`tcb_stock_history.csv`)**: 2,015 dòng. Giai đoạn: `04/06/2018` (Ngày niêm yết) đến `26/06/2026`.
*   **Báo cáo tài chính Năm (Annual BS/IS/CF)**: 8 dòng. Giai đoạn: `2018` đến `2025`.
*   **Báo cáo tài chính Quý (Quarterly BS/IS/CF)**: 33 dòng. Giai đoạn: `Q1/2018` đến `Q1/2026`.
*   **Chỉ số tài chính tính sẵn (Financial Ratios)**: 8 dòng (Năm: `2018` - `2025`), 31 dòng (Quý: `Q1/2018` - `Q3/2025`).

### 2.3. Ngân hàng Vietcombank (VCB)
*   **Giá cổ phiếu (`vcb_stock_history.csv`)**: 3,362 dòng. Giai đoạn: `02/01/2013` (Mốc dữ liệu đồng bộ) đến `26/06/2026`.
*   **Báo cáo tài chính Năm (Annual BS/IS/CF)**: 8 dòng. Giai đoạn: `2018` đến `2025`.
*   **Báo cáo tài chính Quý (Quarterly BS/IS/CF)**: 33 dòng. Giai đoạn: `Q1/2018` đến `Q1/2026`.
*   **Chỉ số tài chính tính sẵn (Financial Ratios)**: 8 dòng (Năm: `2018` - `2025`), 32 dòng (Quý: `Q1/2018` - `Q4/2025`).

### 2.4. Ngân hàng VietinBank (CTG)
*   **Giá cổ phiếu (`ctg_stock_history.csv`)**: 3,362 dòng. Giai đoạn: `02/01/2013` (Mốc dữ liệu đồng bộ) đến `26/06/2026`.
*   **Báo cáo tài chính Năm (Annual BS/IS/CF)**: 8 dòng. Giai đoạn: `2018` đến `2025`.
*   **Báo cáo tài chính Quý (Quarterly BS/IS/CF)**: 33 dòng. Giai đoạn: `Q1/2018` đến `Q1/2026`.
*   **Chỉ số tài chính tính sẵn (Financial Ratios)**: 8 dòng (Năm: `2018` - `2025`), 32 dòng (Quý: `Q1/2018` - `Q4/2025`).

---

## 3. Đặc tả Lược đồ Dữ liệu (Data Schemas)

### 3.1. Lược đồ Giá Chứng khoán hàng ngày (`*_stock_history.csv`)
Tệp tin chứa lịch sử giá cổ phiếu dạng chuỗi thời gian liên tục từ các phiên giao dịch chính thức của sàn HOSE.
*   `time` (Date): Ngày giao dịch (Định dạng chuẩn ISO: `YYYY-MM-DD`).
*   `open` (Float64): Giá mở cửa (đơn vị: nghìn VND, ví dụ: 36.05 tức là 36,050 VND).
*   `high` (Float64): Giá cao nhất trong ngày giao dịch (đơn vị: nghìn VND).
*   `low` (Float64): Giá thấp nhất trong ngày giao dịch (đơn vị: nghìn VND).
*   `close` (Float64): Giá đóng cửa phiên (đơn vị: nghìn VND). **Đây là biến mục tiêu cho mô hình chuỗi thời gian LSTM.**
*   `volume` (Int64): Tổng khối lượng cổ phiếu khớp lệnh thành công trong phiên.

### 3.2. Báo cáo Tài chính dạng xoay trục dọc (`*_balance_sheet_*.csv`, `*_income_statement_*.csv`, `*_cash_flow_*.csv`)
Các báo cáo này đã được transpose để phù hợp với định dạng nạp BigQuery.
*   **Hàng (Rows)**: Định vị bằng cột khóa `period` (chu kỳ báo cáo).
    *   Đối với báo cáo Năm: `YYYY` (ví dụ: `2024`).
    *   Đối với báo cáo Quý: `YYYY-QX` (ví dụ: `2024-Q1`).
*   **Cột (Columns)**: Mỗi cột tương ứng với một chỉ tiêu tài chính cụ thể bằng tiếng Việt (khớp chính xác với cột `item_vi` trong từ điển mapping).
*   **Giá trị**: Số thực đại diện cho giá trị bằng Đồng Việt Nam (VND). Các số liệu có quy mô lớn (hàng nghìn tỷ) được ghi nhận đầy đủ chữ số (không viết tắt).

### 3.3. Chỉ số Tài chính tính sẵn (`*_financial_ratios_*.csv`)
Lược đồ chứa các hệ số định giá, hiệu quả sinh lời và đo lường an toàn tài chính.
*   `period` (String): Chu kỳ báo cáo (`YYYY` hoặc `YYYY-QX`).
*   `pe` (Float64): Hệ số giá trên thu nhập mỗi cổ phần (Price-to-Earnings).
*   `pb` (Float64): Hệ số giá trên giá trị sổ sách (Price-to-Book).
*   `roe` (Float64): Tỷ suất sinh lời trên vốn chủ sở hữu (Return on Equity).
*   `roa` (Float64): Tỷ suất sinh lời trên tổng tài sản (Return on Assets).
*   `dividendYield` (Float64): Tỷ suất cổ tức.
*   `marketCap` (Float64): Vốn hóa thị trường của ngân hàng (VND).
*   `netProfitMargin` (Float64): Biên lợi nhuận ròng.
*   `nim` (Float64): Biên lãi ròng (Net Interest Margin) - biên lợi nhuận cốt lõi của hoạt động tín dụng.
*   `casaRate` (Float64): Tỷ lệ tiền gửi không kỳ hạn (CASA).

### 3.4. Từ điển Ánh xạ Chỉ tiêu Tài chính (`financial_items_mapping.csv`)
Tệp tin đối chiếu dùng chung cho cả 4 ngân hàng giúp ánh xạ các trường tiếng Việt sang mã ID chuẩn tiếng Anh.
*   `report_type` (String): Loại báo cáo (`balance_sheet`, `income_statement`, `cash_flow`, `ratios`).
*   `item_id` (String): Mã ID định danh chuẩn hóa tiếng Anh (ví dụ: `net_interest_income`).
*   `item_vi` (String): Tên cột chỉ tiêu tiếng Việt đầy đủ (khớp với tiêu đề cột của các bảng báo cáo dọc).
*   `item_en` (String): Tên dịch nghĩa tiếng Anh tương ứng.

---

## 4. Tính chất Dữ liệu & Quy tắc Tích hợp (Data Integration Rules)

Để xây dựng bảng Fact hoàn chỉnh phục vụ phân tích vĩ mô toàn ngành và vi mô từng ngân hàng, cần áp dụng các nguyên tắc sau:

### 4.1. Ánh xạ Mã Ngân hàng (Entity Mapping)
*   Trong tệp Excel toàn ngành (`data/raw/`): Mã ngân hàng BIDV được ký hiệu là **`BIDV`**, Vietcombank là **`VCB`**, Techcombank là **`TCB`**, VietinBank là **`CTG`**.
*   Trong dữ liệu chứng khoán và BCTC mới trích xuất: Mã cổ phiếu tương ứng là **`BID`**, **`VCB`**, **`TCB`**, **`CTG`**.
*   *Nguyên tắc:* Cần sử dụng bảng ánh xạ khóa ngoại (`dim_bank`) để liên kết chính xác `BID` <-> `BIDV` trước khi thực hiện câu lệnh JOIN hoặc APPEND.

### 4.2. Khớp nối Dữ liệu Lịch sử & Dữ liệu Cập nhật (Time-series Appending)
*   Dữ liệu lịch sử toàn ngành trong file Excel đã có sẵn số liệu đến năm **2022**.
*   Dữ liệu mới trích xuất chi tiết theo Năm từ API có giai đoạn **2018 - 2025**.
*   *Nguyên tắc:* 
    *   Đối với phân tích lịch sử dài hạn (Năm): Sử dụng dữ liệu Excel toàn ngành từ 2002 đến 2022 làm gốc, sau đó lấy dữ liệu từ `data/processed/<bank>/` cho giai đoạn **2023 - 2025** để nối tiếp (Append) tạo thành chuỗi thời gian liên tục dài 23 năm.
    *   Đối với phân tích ngắn hạn chi tiết (Quý): Sử dụng trực tiếp chuỗi dữ liệu Quý từ 2018 đến Q1/2026 trong thư mục `processed`.

### 4.3. Quy tắc đồng bộ tỷ lệ và Đơn vị tính
*   **Đơn vị tiền tệ**: Toàn bộ dữ liệu tiền tệ trong file báo cáo tài chính processed được lưu ở đơn vị **VND tuyệt đối**. Khi JOIN với dữ liệu toàn ngành trong Excel (đơn vị: tỷ VND), bắt buộc phải chia dữ liệu processed cho `1,000,000,000` (1 tỷ) để đồng bộ quy mô.
*   **Định dạng tỷ lệ**: Các chỉ số tỷ lệ như `npl_ratio`, `roa`, `roe`, `nim` từ chỉ số tính sẵn cần được quy đổi về dạng số thực số thập phân trong phạm vi `[0.0 - 1.0]` (ví dụ: Tỷ lệ nợ xấu 3.5% trong báo cáo phải được lưu là `0.035` trong cơ sở dữ liệu).
