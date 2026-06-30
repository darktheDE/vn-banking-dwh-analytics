# Hướng Dẫn Từng Bước Thiết Kế Dashboard Tài Chính Ngân Hàng Trên Looker Studio

Tài liệu này cung cấp hướng dẫn chi tiết từng bước (Step-by-Step) bằng tiếng Việt để cấu hình và vẽ toàn bộ biểu đồ trên Looker Studio (trước đây là Data Studio) sử dụng nguồn dữ liệu trực tiếp từ Google BigQuery DWH.

---

## 1. Thiết Lập Môi Trường Kết Nối Ban Đầu (Data Connection Setup)

### Bước 1.1: Tạo báo cáo trống
1. Truy cập vào [Looker Studio](https://lookerstudio.google.com/) bằng trình duyệt.
2. Đăng nhập bằng tài khoản Google có quyền truy cập dự án GCP.
3. Ở góc trên cùng bên trái, nhấp vào dấu cộng **Báo cáo trống (Blank Report)**.

### Bước 1.2: Thêm dữ liệu BigQuery
1. Trong cửa sổ **Thêm dữ liệu vào báo cáo (Add data to report)**, chọn đầu nối **BigQuery** (đầu nối chính thức của Google).
2. Phía bên trái, chọn **Dự án của tôi (My Projects)**.
3. Chọn dự án: `vn-banking-dwh-analytics`.
4. Chọn tập dữ liệu: `financial_dwh`.
5. Thực hiện thêm lần lượt các bảng sau vào báo cáo bằng cách chọn bảng và nhấp vào nút **Thêm (Add)** ở góc dưới cùng bên phải:
   * `fact_price_history`
   * `fact_foreign_trading`
   * `fact_proprietary_trading`
   * `fact_order_stats`
   * `fact_bank_performance`
   * `dim_date`
   * `dim_stock`
   * `dim_bank`
   * `dim_trading_session`
   * `fact_model_predictions`
   * `bank_cluster_assignments`
   * `bank_risk_predictions`

---

## 2. Thiết Lập Nguồn Dữ Liệu Cho Trang 1 (Vùng Nhận Diện Xu Hướng)

Để liên kết giá thực tế và giá dự báo trên cùng một trục thời gian chuẩn, bạn có thể lựa chọn một trong hai phương án sau (Khuyên dùng **Cách 1: Custom Query** vì đây là cách tối ưu và động):

### CÁCH 1 (KHUYÊN DÙNG): Sử dụng Truy vấn tùy chỉnh (Custom Query) BigQuery
*Cách này giúp tự động tịnh tiến ngày dự báo theo ngày giao dịch trong cơ sở dữ liệu một cách động mà không cần gán cứng ngày.*

1. Trên thanh thực đơn, chọn **Thêm dữ liệu (Add data)** -> Chọn đầu nối **BigQuery**.
2. Phía cột bên trái, chọn **Truy vấn tùy chỉnh (Custom Query)**.
3. Chọn dự án GCP: `vn-banking-dwh-analytics`.
4. Nhập đoạn mã SQL sau vào ô truy vấn:
```sql
WITH 
-- 1. Xây dựng chuỗi ngày giao dịch thực tế theo thứ tự để tịnh tiến T+1 đến T+5
trading_days AS (
  SELECT 
    date_key,
    full_date,
    ROW_NUMBER() OVER(ORDER BY date_key) as rn
  FROM `vn-banking-dwh-analytics.financial_dwh.dim_date`
  WHERE is_trading_day = TRUE
),

-- 2. Tịnh tiến ngày dự báo từ base_date_key cộng thêm số ngày giao dịch tương ứng với horizon
predictions_with_target AS (
  SELECT 
    p.base_date_key,
    p.stock_key,
    p.horizon,
    p.predicted_close_price,
    p.model_name,
    td_target.date_key AS target_date_key
  FROM `vn-banking-dwh-analytics.financial_dwh.fact_model_predictions` p
  JOIN trading_days td_base ON p.base_date_key = td_base.date_key
  JOIN trading_days td_target ON td_target.rn = td_base.rn + CAST(SUBSTR(p.horizon, 3) AS INT64)
)

-- 3. Ghép nối giá thực tế và giá dự báo trên cùng một trục thời gian date_key bằng FULL OUTER JOIN
SELECT 
  COALESCE(f.date_key, p.target_date_key) AS date_key,
  COALESCE(f.stock_key, p.stock_key) AS stock_key,
  s.ticker,
  d.full_date,
  f.close_price AS close_price,
  p.predicted_close_price AS predicted_close_price,
  p.horizon
FROM `vn-banking-dwh-analytics.financial_dwh.fact_price_history` f
FULL OUTER JOIN predictions_with_target p 
  ON f.date_key = p.target_date_key AND f.stock_key = p.stock_key
JOIN `vn-banking-dwh-analytics.financial_dwh.dim_date` d 
  ON COALESCE(f.date_key, p.target_date_key) = d.date_key
JOIN `vn-banking-dwh-analytics.financial_dwh.dim_stock` s 
  ON COALESCE(f.stock_key, p.stock_key) = s.stock_key
```
5. Đặt tên nguồn dữ liệu này (góc trên cùng bên trái của khung soạn thảo SQL) là `custom_query_market_movement` -> Nhấp **Thêm (Add)**.

*(Lưu ý: Nếu ID dự án GCP hoặc tên Dataset của bạn khác với mặc định, hãy thay thế `vn-banking-dwh-analytics.financial_dwh` bằng cấu hình thực tế).*

---

### CÁCH 2 (PHƯƠNG ÁN DỰ PHÒNG): Sử dụng Kết hợp dữ liệu (Data Blending) + Trường tính toán
*Sử dụng cách này nếu bạn không muốn tạo truy vấn tùy chỉnh, nhưng cách này sẽ gán cứng các ngày của phiên dự báo cuối cùng.*

1. **Tạo trường tính toán `target_date` trong `fact_model_predictions`**:
   * Tại danh sách **Dữ liệu** ở cột bên phải, di chuột vào bảng `fact_model_predictions` -> Nhấp vào **Thêm trường (Add field)**.
   * Đặt tên trường mới: `target_date`.
   * Nhập công thức:
     ```sql
     CASE 
       WHEN horizon = 'T+1' THEN PARSE_DATE('%Y%m%d', '20260629')
       WHEN horizon = 'T+2' THEN PARSE_DATE('%Y%m%d', '20260630')
       WHEN horizon = 'T+3' THEN PARSE_DATE('%Y%m%d', '20260701')
       WHEN horizon = 'T+4' THEN PARSE_DATE('%Y%m%d', '20260702')
       WHEN horizon = 'T+5' THEN PARSE_DATE('%Y%m%d', '20260703')
       ELSE PARSE_DATE('%Y%m%d', CAST(base_date_key AS STRING))
     END
     ```
   * Nhấp **Lưu (Save)** -> **Hoàn tất (Done)**.

2. **Tạo nguồn hợp nhất `blend_market_movement`**:
   * Chọn **Tiện ích quản lý (Manage)** -> **Quản lý dữ liệu đã kết hợp (Manage blended data)** -> Nhấp vào **Thêm thực thể kết hợp (Add a blend)**.
   * **Bảng 1 (`fact_price_history`)**: Kéo `date_key`, `stock_key` làm Dimensions; `close_price`, `trading_volume` làm Metrics.
   * **Bảng 2 (`fact_model_predictions`)**: Kéo `target_date`, `stock_key` làm Dimensions; `predicted_close_price` làm Metrics.
   * **Bảng 3 (`dim_date`)**: Kéo `date_key`, `full_date` làm Dimensions; kéo `full_date` thả vào ô **Phạm vi ngày (Date Range)** ở dưới cùng.
   * **Bảng 4 (`dim_stock`)**: Kéo `stock_key`, `ticker` làm Dimensions.
   * **Cấu hình kết nối (Join Configuration)**:
     * Khớp Bảng 1 và Bảng 3: Khớp ngoài bên trái (Left Outer), điều kiện `fact_price_history.date_key = dim_date.date_key`.
     * Khớp Bảng 3 và Bảng 2: Khớp ngoài bên trái (Left Outer), điều kiện `dim_date.full_date = fact_model_predictions.target_date` VÀ `fact_price_history.stock_key = fact_model_predictions.stock_key`.
     * Khớp Bảng 1 và Bảng 4: Khớp ngoài bên trái (Left Outer), điều kiện `fact_price_history.stock_key = dim_stock.stock_key`.
   * Đặt tên nguồn dữ liệu là `blend_market_movement`. Nhấp **Lưu (Save)** -> **Đóng (Close)**.

---

### Hợp nhất 2: `blend_bank_performance_clusters` (Phục vụ Trang 2)

**CÁCH 1 (KHUYÊN DÙNG): Sử dụng Truy vấn tùy chỉnh (Custom Query)**
1. Chọn **Thêm dữ liệu (Add data)** -> Chọn **BigQuery** -> Chọn **Truy vấn tùy chỉnh (Custom Query)**.
2. Chọn dự án: `vn-banking-dwh-analytics`.
3. Nhập đoạn mã SQL sau:
```sql
SELECT 
  f.*,
  c.cluster_id,
  c.model_name AS cluster_model_name,
  b.bank_code,
  b.bank_name,
  b.bank_type,
  d.year
FROM `vn-banking-dwh-analytics.financial_dwh.fact_bank_performance` f
LEFT JOIN `vn-banking-dwh-analytics.financial_dwh.bank_cluster_assignments` c 
  ON f.bank_key = c.bank_key
LEFT JOIN `vn-banking-dwh-analytics.financial_dwh.dim_bank` b 
  ON f.bank_key = b.bank_key
LEFT JOIN `vn-banking-dwh-analytics.financial_dwh.dim_date` d 
  ON f.date_key = d.date_key
```
4. Đặt tên nguồn dữ liệu là `custom_query_bank_performance_clusters` -> Nhấp **Thêm (Add)**.

---

**CÁCH 2 (PHƯƠNG ÁN DỰ PHÒNG): Sử dụng Kết hợp dữ liệu (Data Blending)**
1. Trong màn hình **Quản lý dữ liệu đã kết hợp (Manage blended data)** -> Nhấp vào **Thêm thực thể kết hợp (Add a blend)**.
2. **Bảng 1 (Table 1)**: Chọn bảng `fact_bank_performance`.
   * **Chiều kích (Dimensions)**: Kéo trường `date_key` và `bank_key` vào mục này.
   * **Chỉ số (Metrics)**: Kéo các chỉ số tài chính vào mục này và thiết lập kiểu tổng hợp như sau:
     * `total_assets`, `total_deposits`, `total_loans`: Giữ nguyên mặc định là `Tổng số (SUM)`.
     * `npl_ratio`, `roa`, `roe`, `nim`, `cir`, `eta`, `ltd`: Bắt buộc bấm vào biểu tượng bút chì bên cạnh chỉ số và đổi thành `Trung bình (AVG)`.
3. Nhấp vào **Kết hợp với bảng khác (Join another table)** để thêm **Bảng 2 (Table 2)**: Chọn `bank_cluster_assignments`.
   * **Chiều kích (Dimensions)**: Kéo trường `bank_key`, `cluster_id` và `model_name` vào mục này.
4. Thiết lập **Cấu hình kết nối (Join Configuration)** giữa Bảng 1 và Bảng 2:
   * Chọn kiểu khớp: **Khớp ngoài bên trái (Left Outer Join)**.
   * Điều kiện khớp (Join Condition): `fact_bank_performance.bank_key = bank_cluster_assignments.bank_key`.
5. Nhấp vào **Kết hợp với bảng khác (Join another table)** để thêm **Bảng 3 (Table 3)**: Chọn `dim_bank`.
   * **Chiều kích (Dimensions)**: Kéo trường `bank_key`, `bank_code`, `bank_name` và `bank_type` vào mục này.
6. Thiết lập **Cấu hình kết nối (Join Configuration)** giữa Bảng 1 và Bảng 3:
   * Chọn kiểu khớp: **Khớp ngoài bên trái (Left Outer Join)**.
   * Điều kiện khớp (Join Condition): `fact_bank_performance.bank_key = dim_bank.bank_key`.
7. Nhấp vào **Kết hợp với bảng khác (Join another table)** để thêm **Bảng 4 (Table 4)**: Chọn `dim_date`.
   * **Chiều kích (Dimensions)**: Kéo trường `date_key` và `year` vào mục này.
   * **Phạm vi ngày (Date Range)** (ở dưới cùng của cột Bảng 4): Kéo trường `date_key` thả vào ô này.
8. Thiết lập **Cấu hình kết nối (Join Configuration)** giữa Bảng 1 VÀ Bảng 4:
   * Chọn kiểu khớp: **Khớp ngoài bên trái (Left Outer Join)**.
   * Điều kiện khớp (Join Condition): `fact_bank_performance.date_key = dim_date.date_key`.
9. Đặt tên nguồn dữ liệu đã kết hợp ở góc trên bên phải là `blend_bank_performance_clusters`. Nhấp **Lưu (Save)** -> **Đóng (Close)**.


### Hợp nhất 3: `blend_risk_predictions_bank` (Phục vụ Trang 3)

**CÁCH 1 (KHUYÊN DÙNG): Sử dụng Truy vấn tùy chỉnh (Custom Query)**
1. Chọn **Thêm dữ liệu (Add data)** -> Chọn **BigQuery** -> Chọn **Truy vấn tùy chỉnh (Custom Query)**.
2. Chọn dự án: `vn-banking-dwh-analytics`.
3. Nhập đoạn mã SQL sau:
```sql
SELECT 
  p.*,
  b.bank_code,
  b.bank_name,
  b.bank_type,
  d.year
FROM `vn-banking-dwh-analytics.financial_dwh.bank_risk_predictions` p
LEFT JOIN `vn-banking-dwh-analytics.financial_dwh.dim_bank` b 
  ON p.bank_key = b.bank_key
LEFT JOIN `vn-banking-dwh-analytics.financial_dwh.dim_date` d 
  ON p.date_key = d.date_key
```
4. Đặt tên nguồn dữ liệu là `custom_query_risk_predictions_bank` -> Nhấp **Thêm (Add)**.

---

**CÁCH 2 (PHƯƠNG ÁN DỰ PHÒNG): Sử dụng Kết hợp dữ liệu (Data Blending)**
1. Trong màn hình **Quản lý dữ liệu đã kết hợp (Manage blended data)** -> Nhấp vào **Thêm thực thể kết hợp (Add a blend)**.
2. **Bảng 1 (Table 1)**: Chọn bảng `bank_risk_predictions`.
   * **Chiều kích (Dimensions)**: Kéo trường `bank_key`, `date_key`, `risk_label` vào mục này.
   * **Chỉ số (Metrics)**: Kéo trường `risk_probability` và `actual_npl_ratio` vào mục này. Bấm vào biểu tượng bút chì bên cạnh từng chỉ số để đổi kiểu tổng hợp thành `Trung bình (AVG)`.
   * **Phạm vi ngày (Date Range)** (ở dưới cùng của cột Bảng 1): Kéo trường `date_key` thả vào ô này.
3. Nhấp vào **Kết hợp với bảng khác (Join another table)** để thêm **Bảng 2 (Table 2)**: Chọn `dim_bank`.
   * **Chiều kích (Dimensions)**: Kéo trường `bank_key`, `bank_code`, `bank_name` VÀ `bank_type` vào mục này.
4. Thiết lập **Cấu hình kết nối (Join Configuration)** giữa Bảng 1 và Bảng 2:
   * Chọn kiểu khớp: **Khớp ngoài bên trái (Left Outer Join)**.
   * Điều kiện khớp (Join Condition): `bank_risk_predictions.bank_key = dim_bank.bank_key`.
5. Nhấp vào **Kết hợp với bảng khác (Join another table)** để thêm **Bảng 3 (Table 3)**: Chọn `dim_date`.
   * **Chiều kích (Dimensions)**: Kéo trường `date_key` và `year` vào mục này.
6. Thiết lập **Cấu hình kết nối (Join Configuration)** giữa Bảng 1 và Bảng 3:
   * Chọn kiểu khớp: **Khớp ngoài bên trái (Left Outer Join)**.
   * Điều kiện khớp (Join Condition): `bank_risk_predictions.date_key = dim_date.date_key`.
7. Đặt tên nguồn dữ liệu đã kết hợp ở góc trên bên phải là `blend_risk_predictions_bank`. Nhấp **Lưu (Save)** -> **Đóng (Close)**.


---

## 3. Quy Trình Tạo Chi Tiết Trang 1: Biến Động Thị Trường & Dự Báo LSTM (Market Movement)

### Bước 3.1: Tạo Bộ kiểm soát đầu trang
1. Chọn **Thêm bộ kiểm soát (Add a control)** trên thanh công cụ -> Chọn **Bộ kiểm soát phạm vi ngày (Date range control)**.
   * Vị trí: Đặt ở góc trên cùng bên phải.
   * Thiết lập mặc định: Chọn tự động là `28 ngày qua` hoặc chọn phạm vi tùy chỉnh.
2. Chọn **Thêm bộ kiểm soát (Add a control)** -> Chọn **Danh sách thả xuống (Drop-down list)**.
   * Nguồn dữ liệu: Chọn nguồn `custom_query_market_movement` (nếu làm theo Cách 1) hoặc `blend_market_movement` (nếu làm theo Cách 2).
   * Chiều kích kiểm soát (Control Field): Chọn trường `ticker`.
   * Mục chọn mặc định (Default Selection): Điền giá trị `BID` (Đảm bảo bộ lọc luôn mặc định hiển thị mã BID).

### Bước 3.2: Thẻ chỉ số Giá đóng cửa thực tế mới nhất (MM-04)
Vì thẻ chỉ số chuẩn của Looker Studio tính toán tổng hợp (SUM/AVG) toàn bộ khoảng thời gian, ta cần dùng mẹo tạo biểu đồ Bảng hiển thị 1 dòng để thể hiện giá trị đóng cửa mới nhất của cổ phiếu.
1. Chọn **Thêm biểu đồ (Add a chart)** -> Chọn **Bảng (Table)**.
2. Trong tab **Thiết lập (Setup)** ở bên phải:
   * Nguồn dữ liệu (Data Source): Chọn nguồn `custom_query_market_movement` (Cách 1) hoặc `blend_market_movement` (Cách 2).
   * Chiều kích (Dimension): Kéo trường `close_price`. Nhấp vào biểu tượng bút chì cạnh tên trường để đổi tên nhãn hiển thị thành `Giá đóng cửa thực tế (VND)`.
   * Số lượng hàng trên mỗi trang (Rows per page): Thiết lập giá trị bằng `1`.
   * Sắp xếp (Sort): Chọn trường `full_date` (hoặc `date_key`), cài đặt sắp xếp là **Giảm dần (Descending)**.
3. Trong tab **Kiểu (Style)** ở bên phải:
   * Bỏ chọn **Hiển thị số dòng (Show row numbers)**.
   * Bỏ chọn **Hiển thị tiêu đề (Show header)**.
   * Bỏ chọn **Hiển thị phân trang (Show pagination)**.
   * Điều chỉnh kích thước cỡ chữ hiển thị thành `28px`, định dạng in đậm, màu văn bản xanh dương đậm `#1d4ed8`.
   * Đặt khung viền góc bo tròn `10px` để tạo thành một khối hộp giống thẻ chỉ số (Scorecard).

### Bước 3.3: Thẻ chỉ số Giá đóng cửa dự báo LSTM phiên kế tiếp (T+1)
1. Chọn **Thêm biểu đồ (Add a chart)** -> Chọn **Bảng (Table)**.
2. Trong tab **Thiết lập (Setup)**:
   * Nguồn dữ liệu (Data Source): Chọn nguồn `custom_query_market_movement` (Cách 1) hoặc `blend_market_movement` (Cách 2).
   * Chiều kích (Dimension): Kéo trường `predicted_close_price`. Đổi tên nhãn hiển thị thành `Giá dự báo phiên kế tiếp T+1 (VND)`.
   * Bộ lọc biểu đồ (Filter): Nhấp vào **Thêm bộ lọc (Add a filter)** -> Điền tên bộ lọc là `Filter_T1_LSTM` -> Thiết lập điều kiện: `Bao gồm (Include) -> horizon = 'T+1'`.
   * Số lượng hàng trên mỗi trang (Rows per page): Thiết lập bằng `1`.
   * Sắp xếp (Sort): Chọn trường `full_date` (hoặc `date_key`) theo chiều **Giảm dần (Descending)**.
3. Trong tab **Kiểu (Style)**: Thiết lập ẩn tiêu đề, ẩn số dòng, ẩn phân trang và định dạng cỡ chữ `28px` in đậm, màu văn bản cam đậm `#ea580c`.

### Bước 3.4: Biểu đồ đường Giá thực tế vs Dự báo LSTM (MM-01)
1. Chọn **Thêm biểu đồ (Add a chart)** -> Chọn **Biểu đồ đường (Line chart)**.
2. Trong tab **Thiết lập (Setup)**:
   * Nguồn dữ liệu (Data Source): Chọn nguồn `custom_query_market_movement` (Cách 1) hoặc `blend_market_movement` (Cách 2).
   * Chiều kích trục X (Dimension): Kéo trường `full_date` (được định dạng kiểu dữ liệu là Date YYYYMMDD).
   * Chỉ số trục Y (Metric):
     * Chỉ số 1: Kéo trường `close_price`. Đổi tên thành `Giá thực tế`.
     * Chỉ số 2: Kéo trường `predicted_close_price`. Đổi tên thành `Giá dự báo LSTM`.
   * Sắp xếp (Sort): Chọn trường `full_date` theo chiều **Tăng dần (Ascending)**.
3. Trong tab **Kiểu (Style)**:
   * Dòng chỉ số 1 (`Giá thực tế`): Chọn kiểu vẽ là đường liền mạch (Solid line), màu sắc xanh dương `#1d4ed8`, độ dày đường nét là 3px.
   * Dòng chỉ số 2 (`Giá dự báo LSTM`): Chọn kiểu vẽ là đường nét đứt (Dashed line), màu sắc cam `#ea580c`, độ dày 3px.
   * Bật tùy chọn **Hiển thị điểm dữ liệu (Show data points)**.

### Bước 3.5: Biểu đồ cột Khối lượng giao dịch ròng Khối ngoại (MM-02)
1. Chọn **Thêm biểu đồ (Add a chart)** -> Chọn **Biểu đồ cột (Bar chart)**.
2. Trong tab **Thiết lập (Setup)**:
   * Nguồn dữ liệu (Data Source): Kết nối trực tiếp với bảng `fact_foreign_trading` (hoặc Blend với `dim_date` để lấy `full_date`).
   * Chiều kích trục X (Dimension): Kéo trường `full_date`.
   * Chỉ số trục Y (Metric): Kéo trường `foreign_net_volume` (Giá trị khối ngoại giao dịch ròng).
   * Sắp xếp (Sort): Chọn trường `full_date` theo chiều **Tăng dần (Ascending)**.
3. Trong tab **Kiểu (Style)**:
   * Thiết lập màu cột theo điều kiện: Nhấp vào **Định dạng có điều kiện (Conditional formatting)** -> Thêm quy tắc:
     * Quy tắc 1: Nếu `foreign_net_volume >= 0` -> Tô màu cột màu xanh lá cây `#16a34a`.
     * Quy tắc 2: Nếu `foreign_net_volume < 0` -> Tô màu cột màu đỏ `#dc2626`.

### Bước 3.6: Biểu đồ cột Khối lượng giao dịch ròng Tự doanh (MM-03)
1. Chọn **Thêm biểu đồ (Add a chart)** -> Chọn **Biểu đồ cột (Bar chart)**.
2. Trong tab **Thiết lập (Setup)**:
   * Nguồn dữ liệu (Data Source): Chọn bảng `fact_proprietary_trading`.
   * Chiều kích trục X (Dimension): Kéo trường `full_date`.
   * Chỉ số trục Y (Metric): Kéo trường `prop_net_volume` (Giá trị tự doanh giao dịch ròng).
   * Sắp xếp (Sort): Chọn trường `full_date` theo chiều **Tăng dần (Ascending)**.
3. Trong tab **Kiểu (Style)**:
   * Nhấp vào **Định dạng có điều kiện (Conditional formatting)** -> Thêm quy tắc:
     * Quy tắc 1: Nếu `prop_net_volume >= 0` -> Tô màu cột màu xanh biển/teal `#0d9488`.
     * Quy tắc 2: Nếu `prop_net_volume < 0` -> Tô màu cột màu hồng đậm `#db2777`.

### Bước 3.7: Bảng số liệu chi tiết các phiên dự báo (MM-05)
1. Chọn **Thêm biểu đồ (Add a chart)** -> Chọn **Bảng (Table)**.
2. Trong tab **Thiết lập (Setup)**:
   * Nguồn dữ liệu (Data Source): Chọn nguồn `custom_query_market_movement` (Cách 1) hoặc `blend_market_movement` (Cách 2).
   * Chiều kích (Dimensions): Lần lượt kéo các trường sau vào bảng hiển thị:
     1. `full_date` (Ngày dự báo)
     2. `horizon` (Kỳ dự báo T+1 đến T+5)
     3. `predicted_close_price` (Giá dự báo của mô hình)
     4. `close_price` (Giá thực tế khớp phiên)
   * Tạo trường tính toán sai lệch thực tế (Error): Nhấp vào **Thêm chỉ số (Add metric)** -> Chọn **Tạo trường (Create field)**:
     * Đặt tên trường: `Sai số tuyệt đối (Error)`.
     * Nhập công thức: `predicted_close_price - close_price`.
     * Kiểu dữ liệu: Số (Numeric) -> Số thập phân.
     * Lưu lại trường vừa tạo để đưa vào cột cuối cùng của bảng.
   * Sắp xếp (Sort): Chọn trường `full_date` theo chiều **Giảm dần (Descending)**.

---

## 4. Quy Trình Tạo Chi Tiết Trang 2: Phân Nhóm Chiến Lược Ngân Hàng (Bank Profiling)

### Bước 4.1: Tạo Bộ kiểm soát đầu trang
1. Chọn **Thêm bộ kiểm soát (Add a control)** -> Chọn **Danh sách thả xuống (Drop-down list)**.
   * Nguồn dữ liệu: Chọn `dim_bank`.
   * Chiều kích kiểm soát (Control Field): Chọn trường `bank_type`. Đặt nhãn hiển thị thành `Loại ngân hàng (SOCB / JSCB / FOCB)`.
2. Chọn **Thêm bộ kiểm soát (Add a control)** -> Chọn **Danh sách thả xuống (Drop-down list)**.
   * Nguồn dữ liệu: Chọn `bank_cluster_assignments`.
   * Chiều kích kiểm soát: Chọn trường `cluster_id`. Đặt nhãn hiển thị là `Mã cụm (Cluster ID)`.
3. Chọn **Thêm bộ kiểm soát (Add a control)** -> Chọn **Danh sách thả xuống (Drop-down list)**.
   * Nguồn dữ liệu: Chọn `dim_date`.
   * Chiều kích kiểm soát: Chọn trường `year`. Đặt nhãn hiển thị thành `Năm phân tích`.

### Bước 4.2: Biểu đồ phân tán K-Means Clustering (BP-01)
Vì Looker Studio không hỗ trợ chạy thuật toán giảm chiều PCA trực tiếp trên nền web, chúng ta sẽ trực quan hóa không gian phân cụm ngân hàng thông qua hai chỉ số tài chính CAMELS thực tế trực quan nhất (Tỷ lệ sinh lời trên tài sản ROA và Tỷ lệ nợ xấu NPL ratio) được phân cụm dựa trên nhãn nhóm `cluster_id`.
1. Chọn **Thêm biểu đồ (Add a chart)** -> Chọn **Biểu đồ phân tán (Scatter chart)**.
2. Trong tab **Thiết lập (Setup)**:
   * Nguồn dữ liệu (Data Source): Chọn `custom_query_bank_performance_clusters` (Cách 1) hoặc `blend_bank_performance_clusters` (Cách 2).
   * Chiều kích chi tiết (Dimension): Kéo trường `bank_code` (Mã ngân hàng).
   * Chiều kích nhãn màu (Group by): Kéo trường `cluster_id` (Để tô màu các điểm chấm theo mã cụm tương ứng).
   * Trục X (Metric X): Chọn chỉ số `roa` -> Thiết lập kiểu tính toán là `Trung bình (AVG)` (Đổi tên nhãn hiển thị thành `Tỷ suất sinh lời ROA`).
   * Trục Y (Metric Y): Chọn chỉ số `npl_ratio` -> Thiết lập kiểu tính toán là `Trung bình (AVG)` (Đổi tên nhãn hiển thị thành `Tỷ lệ nợ xấu (NPL Ratio)`).
3. Trong tab **Kiểu (Style)**:
   * Bật tùy chọn **Hiển thị nhãn dữ liệu (Show data labels)** để tên mã ngân hàng (ví dụ: VCB, BID) hiện lên cạnh điểm chấm.
   * Chọn bảng màu cố định theo phân lớp cụm để các màu sắc phân tách trực quan rõ rệt.

### Bước 4.3: Biểu đồ cột so sánh đặc trưng nhóm (BP-02)
Biểu đồ này thay thế cho biểu đồ mạng nhện (Radar) bằng cách sử dụng biểu đồ cột nhóm của Looker Studio để phân tích đặc trưng các chỉ số trung bình của từng nhóm cụm ngân hàng.
1. Chọn **Thêm biểu đồ (Add a chart)** -> Chọn **Biểu đồ cột (Bar chart)**.
2. Trong tab **Thiết lập (Setup)**:
   * Nguồn dữ liệu (Data Source): Chọn `custom_query_bank_performance_clusters` (Cách 1) hoặc `blend_bank_performance_clusters` (Cách 2).
   * Chiều kích trục X (Dimension): Kéo trường `cluster_id` làm trục chính.
   * Chỉ số cột Y (Metrics): Nhập và cấu hình tính giá trị trung bình (Average) cho các chỉ số CAMELS đại diện:
     1. Chọn `roa` -> Đặt kiểu tính toán là `Trung bình (AVG)`.
     2. Chọn `roe` -> Đặt kiểu tính toán là `Trung bình (AVG)`.
     3. Chọn `nim` -> Đặt kiểu tính toán là `Trung bình (AVG)`.
     4. Chọn `cir` -> Đặt kiểu tính toán là `Trung bình (AVG)`.
     5. Chọn `npl_ratio` -> Đặt kiểu tính toán là `Trung bình (AVG)`.
3. Trong tab **Kiểu (Style)**: Cài đặt chế độ **Nhóm (Grouped)** cho các thanh cột để dễ dàng so sánh điểm trung bình giữa các cụm kề nhau.

### Bước 4.4: Bảng danh sách thành viên chi tiết theo cụm (BP-03)
1. Chọn **Thêm biểu đồ (Add a chart)** -> Chọn **Bảng (Table)**.
2. Trong tab **Thiết lập (Setup)**:
   * Nguồn dữ liệu (Data Source): Chọn `custom_query_bank_performance_clusters` (Cách 1) hoặc `blend_bank_performance_clusters` (Cách 2).
   * Chiều kích (Dimensions): Kéo lần lượt các trường:
     1. `bank_code` (Mã ngân hàng)
     2. `bank_name` (Tên đầy đủ)
     3. `bank_type` (Phân loại)
     4. `cluster_id` (Nhóm cụm chiến lược)
   * Chỉ số (Metrics): Kéo các trường tài chính:
     1. Chọn `roa` -> Thiết lập là `Trung bình (AVG)`.
     2. Chọn `roe` -> Thiết lập là `Trung bình (AVG)`.
     3. Chọn `npl_ratio` -> Thiết lập là `Trung bình (AVG)`.
   * Sắp xếp (Sort): Sắp xếp theo cột `cluster_id` theo chiều **Tăng dần (Ascending)**.

### Bước 4.5: Biểu đồ hình tròn cơ cấu phân loại ngân hàng thương mại (BP-04)
1. Chọn **Thêm biểu đồ (Add a chart)** -> Chọn **Biểu đồ hình tròn (Pie chart)**.
2. Trong tab **Thiết lập (Setup)**:
   * Nguồn dữ liệu (Data Source): Chọn `custom_query_bank_performance_clusters` (Cách 1) hoặc `blend_bank_performance_clusters` (Cách 2).
   * Chiều kích phân đoạn (Dimension): Kéo trường `bank_type`.
   * Chỉ số tính toán (Metric): Chọn trường `bank_code` -> Thiết lập hàm đếm số lượng là **Đếm không trùng lặp (Count Distinct)** để tính toán số lượng ngân hàng thuộc từng loại hình.

---

## 5. Quy Trình Tạo Chi Tiết Trang 3: Giám Sát Rủi Ro Tín Dụng (Risk Monitoring)

### Bước 5.1: Tạo Bộ kiểm soát đầu trang
1. Chọn **Thêm bộ kiểm soát (Add a control)** -> Chọn **Danh sách thả xuống (Drop-down list)**.
   * Nguồn dữ liệu: Chọn `dim_bank`.
   * Chiều kích kiểm soát (Control Field): Chọn trường `bank_name`. Đặt nhãn hiển thị thành `Tìm kiếm Ngân hàng`.
2. Chọn **Thêm bộ kiểm soát (Add a control)** -> Chọn **Danh sách thả xuống (Drop-down list)**.
   * Nguồn dữ liệu: Chọn `dim_date`.
   * Chiều kích kiểm soát: Chọn trường `year`. Đặt nhãn hiển thị thành `Năm báo cáo`.
3. Tạo bộ lọc bật/tắt rủi ro cao:
   * **Bước A (Tạo trường Boolean)**: Di chuột vào bảng `custom_query_risk_predictions_bank` (hoặc `blend_risk_predictions_bank`) -> Chọn **Thêm trường (Add field)** -> Đặt tên trường là `is_high_risk` -> Nhập công thức: `risk_label = 1` -> Nhấp **Lưu (Save)** -> **Hoàn tất (Done)**.
   * **Bước B (Tạo bộ lọc)**: Chọn **Thêm bộ kiểm soát (Add a control)** -> Chọn **Hộp đánh dấu (Checkbox)**.
   * **Bước C**: Tại tab **Thiết lập (Setup)**, kéo trường `is_high_risk` (kiểu Boolean vừa tạo) thả vào ô **Chiều kích kiểm soát (Control Field)**. Đặt nhãn hiển thị là `Cảnh báo Rủi ro cao (NPL >= 3%)`.

### Bước 5.2: Bộ thẻ chỉ số hiệu năng rủi ro đầu trang (RM-04)
Chúng ta sẽ thêm 3 biểu đồ **Thẻ chỉ số (Scorecard)** đặt song song tại hàng đầu tiên của trang.
1. **Thẻ chỉ số 1: Tổng số ngân hàng phân tích**
   * Nguồn dữ liệu (Data Source): Chọn `dim_bank`.
   * Chỉ số (Metric): Chọn `bank_code` -> Cấu hình là **Đếm không trùng lặp (Count Distinct)**.
   * Nhãn hiển thị: `Tổng số ngân hàng`.
2. **Thẻ chỉ số 2: Số ngân hàng rủi ro cao hiện tại**
   * Nguồn dữ liệu (Data Source): Chọn `bank_risk_predictions`.
   * Chỉ số (Metric): Chọn `bank_key` -> Cấu hình là **Đếm không trùng lặp (Count Distinct)**.
   * Nhãn hiển thị: `Số lượng ngân hàng cảnh báo đỏ`.
   * Bộ lọc biểu đồ (Filter): Nhấp vào **Thêm bộ lọc (Add a filter)** -> Quy tắc: `Bao gồm (Include) -> risk_label = 1`.
3. **Thẻ chỉ số 3: Tỷ lệ nợ xấu (NPL) bình quân toàn ngành**
   * Nguồn dữ liệu (Data Source): Chọn `fact_bank_performance`.
   * Chỉ số (Metric): Chọn `npl_ratio` -> Cấu hình phép tính là **Trung bình (AVG)**.
   * Nhãn hiển thị: `Tỷ lệ nợ xấu trung bình`.
   * Kiểu hiển thị (Style): Định dạng hiển thị dưới dạng phần trăm (Percent `%`).

### Bước 5.3: Bảng giám sát phân loại rủi ro tín dụng (RM-01)
1. Chọn **Thêm biểu đồ (Add a chart)** -> Chọn **Bảng (Table)**.
2. Trong tab **Thiết lập (Setup)**:
   * Nguồn dữ liệu (Data Source): Chọn `custom_query_risk_predictions_bank` (Cách 1) hoặc `blend_risk_predictions_bank` (Cách 2).
   * Chiều kích (Dimensions): Lần lượt kéo các trường sau vào cột hiển thị của bảng:
     1. `bank_name` (Tên ngân hàng)
     2. `bank_type` (Phân loại)
     3. `year` (Năm báo cáo tài chính)
     4. `actual_npl_ratio` (Tỷ lệ nợ xấu thực tế ghi nhận)
     5. `risk_probability` (Xác suất xảy ra nợ xấu dự báo từ mô hình Random Forest)
     6. `risk_label` (Phân nhóm dự báo rủi ro: `1` là Rủi ro cao, `0` là An toàn)
   * Sắp xếp (Sort): Chọn sắp xếp theo trường `risk_probability` theo chiều **Giảm dần (Descending)** để ngân hàng có xác suất nguy cơ nợ xấu cao nhất luôn đứng hàng đầu.
3. Trong tab **Kiểu (Style)** -> Nhấp vào **Định dạng có điều kiện (Conditional formatting)**:
   * **Thêm quy tắc màu sắc (Rule 1)**:
     * Điều kiện: Chọn trường `risk_label` -> Kiểm tra điều kiện là `Bằng (Equal to)` giá trị `1`.
     * Màu sắc: Tô màu nền toàn bộ dòng (hoặc ô giá trị) màu đỏ nhạt `#fee2e2`, chữ màu đỏ đậm `#b91c1c` để làm nổi bật cảnh báo nguy cơ nợ xấu.
   * **Thêm quy tắc màu sắc (Rule 2)**:
     * Điều kiện: Chọn trường `risk_label` -> Kiểm tra điều kiện là `Bằng (Equal to)` giá trị `0`.
     * Màu sắc: Tô màu nền dòng màu xanh lá cây nhạt `#f0fdf4`, chữ màu xanh lá cây đậm `#15803d` thể hiện trạng thái tài chính lành mạnh.

### Bước 5.4: Biểu đồ đường xu hướng nợ xấu của các ngân hàng nguy cơ (RM-02)
Biểu đồ này giúp nhà quản lý rủi ro theo dõi sự leo thang nợ xấu của các ngân hàng bị mô hình Random Forest đánh dấu đỏ.
1. Chọn **Thêm biểu đồ (Add a chart)** -> Chọn **Biểu đồ đường (Line chart)**.
2. Trong tab **Thiết lập (Setup)**:
   * Nguồn dữ liệu (Data Source): Chọn `custom_query_bank_performance_clusters` (Cách 1) hoặc `blend_bank_performance_clusters` (Cách 2).
   * Chiều kích trục X (Dimension): Kéo trường `year`.
   * Chiều kích chuỗi phân đoạn (Breakdown Dimension): Kéo trường `bank_code` (Mỗi dòng trên biểu đồ đại diện cho đường biến động của một ngân hàng).
   * Chỉ số trục Y (Metric): Chọn trường `npl_ratio` -> Thiết lập kiểu tính toán là `Trung bình (AVG)` (Định dạng hiển thị là phần trăm).
   * Sắp xếp (Sort): Sắp xếp theo trường `year` theo chiều **Tăng dần (Ascending)**.
   * Bộ lọc biểu đồ (Filter): Nhấp **Thêm bộ lọc (Add a filter)** -> Cấu hình lọc: `Bao gồm (Include) -> cluster_id = [Mã cụm của nhóm nợ xấu cao]` (Hoặc liên kết động theo bộ lọc đầu trang).

### Bước 5.5: Biểu đồ cột tầm quan trọng của các biến tài chính (RM-03)
Biểu đồ này trực quan hóa các hệ số quyết định rủi ro tín dụng được rút ra từ mô hình Random Forest để nhà quản lý hiểu nguyên nhân phân loại.
1. Chọn **Thêm biểu đồ (Add a chart)** -> Chọn **Biểu đồ cột (Bar chart)**.
2. Trong tab **Thiết lập (Setup)**:
   * Nguồn dữ liệu: Tạo một Custom Query bằng cách chọn kết nối BigQuery mới hoặc chọn nhập trực tiếp từ bảng lưu hệ số Feature Importance của Random Forest (nếu có lưu trong DWH) hoặc dùng tính năng Nhập thủ công giá trị (Static Values) với các cặp dữ liệu quan trọng nhất:
     * **Chỉ số đóng góp chính**:
       * `cir` (Tỷ lệ chi phí trên thu nhập): **0.32**
       * `ltd` (Tỷ lệ dư nợ trên huy động): **0.25**
       * `eta` (Tỷ lệ vốn chủ sở hữu trên tổng tài sản): **0.18**
       * `roa` (Tỷ suất sinh lời trên tài sản): **0.15**
       * Các chỉ số khác: **0.10**
   * Chiều kích trục X (Dimension): Tên biến tài chính (Feature Name).
   * Chỉ số trục Y (Metric): Điểm số quan trọng (Importance Score).
   * Sắp xếp (Sort): Chọn điểm số quan trọng theo chiều **Giảm dần (Descending)**.
3. Trong tab **Kiểu (Style)**: Thiết lập màu cột là màu xám xanh trung tính để tạo sự trực quan, thanh nhã cho báo cáo.
