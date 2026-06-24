# Tài liệu Đặc tả Dữ liệu - Dự án Data Warehouse Ngân hàng BIDV (2014 - 2026)

Tài liệu này đặc tả chi tiết toàn bộ cấu trúc dữ liệu, lược đồ (schema) và các tệp tin CSV đã được thu thập và số hóa phục vụ xây dựng Kho dữ liệu (Data Warehouse) cho nghiên cứu tài chính doanh nghiệp ngân hàng BIDV (BID).

---

## 1. Danh sách các tệp dữ liệu đầu ra

Tất cả các tệp dữ liệu được lưu trữ dưới định dạng phẳng CSV (mã hóa UTF-8) tại thư mục `c:\StudyZone\DAAN\project2\data\`:

| Tên tệp tin | Số dòng | Giai đoạn dữ liệu | Mô tả chi tiết |
| :--- | :--- | :--- | :--- |
| **`bid_stock_history.csv`** | 3.091 | 24/01/2014 - 19/06/2026 | Dữ liệu giao dịch giá cổ phiếu BID theo ngày trên sàn HOSE |
| **`bid_balance_sheet_annual.csv`** | 8 | 2018 - 2025 | Bảng cân đối kế toán hợp nhất theo Năm |
| **`bid_balance_sheet_quarterly.csv`** | 33 | Q1/2018 - Q1/2026 | Bảng cân đối kế toán hợp nhất theo Quý |
| **`bid_income_statement_annual.csv`** | 8 | 2018 - 2025 | Báo cáo kết quả hoạt động kinh doanh hợp nhất theo Năm |
| **`bid_income_statement_quarterly.csv`** | 33 | Q1/2018 - Q1/2026 | Báo cáo kết quả hoạt động kinh doanh hợp nhất theo Quý |
| **`bid_cash_flow_annual.csv`** | 8 | 2018 - 2025 | Báo cáo lưu chuyển tiền tệ hợp nhất theo Năm |
| **`bid_cash_flow_quarterly.csv`** | 33 | Q1/2018 - Q1/2026 | Báo cáo lưu chuyển tiền tệ hợp nhất theo Quý |
| **`bid_financial_ratios_annual.csv`** | 8 | 2018 - 2025 | Các chỉ số tài chính tính sẵn theo Năm |
| **`bid_financial_ratios_quarterly.csv`** | 32 | Q1/2018 - Q4/2025 | Các chỉ số tài chính tính sẵn theo Quý |
| **`financial_items_mapping.csv`** | 219 | - | Từ điển dữ liệu đối chiếu mã chỉ tiêu Việt - Anh |

---

## 2. Đặc tả Lược đồ Dữ liệu (Data Schemas)

### 2.1. Dữ liệu Giá Chứng khoán hàng ngày (`bid_stock_history.csv`)
Tệp tin chứa lịch sử giá cổ phiếu dạng chuỗi thời gian liên tục từ ngày niêm yết đầu tiên.

*   **Lược đồ bảng (Schema):**
    *   `time` (Date): Ngày giao dịch (Định dạng: `YYYY-MM-DD`).
    *   `open` (Float): Giá mở cửa (đơn vị: nghìn VND).
    *   `high` (Float): Giá cao nhất trong phiên (đơn vị: nghìn VND).
    *   `low` (Float): Giá thấp nhất trong phiên (đơn vị: nghìn VND).
    *   `close` (Float): Giá đóng cửa (đơn vị: nghìn VND) - dùng làm giá tính toán.
    *   `volume` (Integer): Khối lượng khớp lệnh (số lượng cổ phiếu).

---

### 2.2. Báo cáo Tài chính hợp nhất xoay dọc (`bid_balance_sheet_*.csv` & `bid_income_statement_*.csv` & `bid_cash_flow_*.csv`)
Các báo cáo này đã được **xoay trục (transpose)**. 
*   **Hàng (Rows):** Đại diện cho chu kỳ báo cáo `period` (Năm dạng `YYYY` hoặc Quý dạng `YYYY-QX`).
*   **Cột (Columns):** Mỗi cột tương ứng với một chỉ tiêu tài chính bằng tiếng Việt.
*   **Giá trị:** Đơn vị tiền tệ (Đồng - VND).

#### A. Các chỉ tiêu tiêu biểu trong Bảng cân đối kế toán (Balance Sheet):
*   `Tiền mặt, vàng bạc, đá quý` (Cash & gold equivalents)
*   `Tiền gửi tại Ngân hàng nhà nước Việt Nam` (Balances with SBV)
*   `Cho vay khách hàng` (Loans to customers)
*   `Tiền gửi của khách hàng` (Customer deposits)
*   `TỔNG TÀI SẢN` (Total Assets)
*   `TỔNG NỢ PHẢI TRẢ` (Total Liabilities)
*   `VỐN CHỦ SỞ HỮU` (Shareholder's Equity)

#### B. Các chỉ tiêu tiêu biểu trong Báo cáo kết quả kinh doanh (Income Statement):
*   `Thu nhập lãi và các khoản thu nhập tương tự` (Interest income)
*   `Chi phí lãi và các chi phí tương tự` (Interest expenses)
*   `Thu nhập lãi thuần` (Net interest income)
*   `Lãi/lỗ thuần từ hoạt động dịch vụ` (Net fee & commission income)
*   `Chi phí hoạt động` (Operating expenses)
*   `Chi phí dự phòng rủi ro tín dụng` (Credit loss provision)
*   `Tổng lợi nhuận trước thuế` (Profit before tax)
*   `Lợi nhuận sau thuế của cổ đông của Ngân hàng mẹ` (Net profit)

---

### 2.3. Chỉ số Tài chính tính sẵn (`bid_financial_ratios_*.csv`)
Lược đồ chứa các chỉ số hiệu quả tài chính và định giá.
*   `period` (String): Chu kỳ báo cáo (`YYYY` hoặc `YYYY-QX`).
*   `pe` (Float): Hệ số giá trên thu nhập (Price-to-Earnings).
*   `pb` (Float): Hệ số giá trên giá trị sổ sách (Price-to-Book).
*   `ps` (Float): Hệ số giá trên doanh thu (Price-to-Sales).
*   `roe` (Float): Tỷ suất lợi nhuận trên vốn chủ sở hữu (Return on Equity).
*   `roa` (Float): Tỷ suất sinh lợi trên tổng tài sản (Return on Assets).
*   `dividendYield` (Float): Tỷ suất cổ tức.
*   `marketCap` (Float): Vốn hóa thị trường (đơn vị: VND).
*   `netProfitMargin` (Float): Biên lợi nhuận ròng.
*   `nim` (Float): Biên lãi ròng (Net Interest Margin) - chỉ số đặc thù của Ngân hàng.
*   `casaRate` (Float): Tỷ lệ tiền gửi không kỳ hạn (CASA).

---

### 2.4. Từ điển Ánh xạ Chỉ tiêu Tài chính (`financial_items_mapping.csv`)
Tệp tin đối chiếu giúp liên kết các trường dữ liệu tiếng Việt với mã ID tiếng Anh phục vụ cho lập trình hoặc phân tích tự động.
*   `report_type` (String): Phân loại báo cáo (`balance_sheet`, `income_statement`, `cash_flow`, `ratios`).
*   `item_id` (String): Mã ID chuẩn hóa tiếng Anh (ví dụ: `net_interest_income`).
*   `item_vi` (String): Tên chỉ tiêu tiếng Việt đầy đủ (khớp với tiêu đề cột của các bảng báo cáo).
*   `item_en` (String): Tên chỉ tiêu tiếng Anh tương ứng.

---

## 3. Hướng dẫn tích hợp dữ liệu toàn ngành (Data Integration Guide)

Để xây dựng Kho dữ liệu hoàn chỉnh, bạn có thể thực hiện liên kết (JOIN) các tệp tin CSV vừa tải với tệp Excel dữ liệu toàn ngành [VN banks dataset (updated August 2023).xlsx](file:///c:/StudyZone/DAAN/project2/data/VN%20banks%20dataset%20(updated%20August%202023).xlsx) theo các nguyên tắc sau:

1.  **Mã Ngân hàng (Bank Code/Ticker):**
    *   Trong tệp Excel toàn ngành, mã ngân hàng BIDV được ký hiệu là **`BIDV`** (trong sheet `Data`).
    *   Trong dữ liệu chứng khoán và báo cáo tài chính trích xuất mới, mã cổ phiếu là **`BID`**.
    *   *Nguyên tắc:* Khi viết câu lệnh SQL hoặc Pandas, hãy ánh xạ `BID` và `BIDV` về cùng một khóa trước khi JOIN.

2.  **Khớp dữ liệu theo Năm (Annual Merge):**
    *   Sheet `Data` trong Excel toàn ngành đã chứa 49 chỉ tiêu của **`BIDV`** từ năm **2002 đến năm 2022**.
    *   Tệp `bid_balance_sheet_annual.csv` và `bid_income_statement_annual.csv` chứa dữ liệu chi tiết của BIDV từ năm **2018 đến 2025**.
    *   *Nguyên tắc:* Bạn có thể sử dụng dữ liệu Excel toàn ngành cho giai đoạn lịch sử cũ (2014 - 2017) và nối tiếp (Append) dữ liệu trích xuất mới cho giai đoạn (2023 - 2025) để có một chuỗi thời gian liên tục 12 năm hoàn chỉnh từ 2014 đến nay.

3.  **Công thức tính toán chỉ số (Metrics Calculation):**
    *   Dựa trên hướng dẫn của VCBS, các chỉ số cốt lõi đối với ngân hàng như:
        *   $$\text{NIM} = \frac{\text{Thu nhập lãi thuần}}{\text{Tài sản có sinh lãi bình quân}}$$
        *   $$\text{Tỷ lệ nợ xấu (NPL)} = \frac{\text{Nợ nhóm 3 + Nhóm 4 + Nhóm 5}}{\text{Tổng dư nợ cho vay}}$$
        *   $$\text{Hệ số LDR (Cho vay / Huy động)} = \frac{\text{Cho vay khách hàng}}{\text{Tiền gửi của khách hàng}}$$
    *   Các chỉ tiêu đầu vào này đều có mặt đầy đủ trong các tệp CSV báo cáo tài chính vừa được trích xuất.
