# Hướng Dẫn Vận Hành Luồng ETL Local-First & Các Bước Tiếp Theo

Tài liệu này hướng dẫn thành viên **Trần Minh Khánh** (Data Engineering / ETL) cách tự chạy kiểm thử toàn bộ luồng ETL cục bộ và bàn giao kết quả cho ML Team.

---

## 1. Cách Chạy Luồng ETL Trên Máy Cục Bộ (Local)

Toàn bộ các file trống trong `src/etl/` đã được viết mã nguồn đầy đủ để hỗ trợ lưu trữ dữ liệu dạng CSV cục bộ trước khi đẩy lên BigQuery. Hãy thực hiện các lệnh sau theo thứ tự tại thư mục gốc của dự án:

### Bước 1: Kích hoạt môi trường ảo và cài đặt thư viện
```bash
# Kích hoạt venv (nếu chưa kích hoạt)
venv\Scripts\activate

# Cài đặt các thư viện bắt buộc
pip install -r requirements.txt
```

### Bước 2: Trích xuất dữ liệu thực tế (Crawl dữ liệu)
Tập lệnh trích xuất sẽ gọi API `vnstock` để tự động tải lịch sử giá thực tế của 4 mã ngân hàng (BID, TCB, VCB, CTG) và báo cáo tài chính BCTC về máy cục bộ:
```bash
python extract_data.py
```

### Bước 3: Chạy sinh các bảng chiều (Dimension Tables)
```bash
python -m src.etl.populate_dim_date
python -m src.etl.populate_dim_stock
python -m src.etl.populate_dim_bank
python -m src.etl.populate_dim_trading_session
```

### Bước 4: Chạy ETL cho các bảng sự kiện (Fact Tables) và Hợp nhất
```bash
# Xử lý giá lịch sử và dữ liệu CAMELS ngân hàng
python -m src.etl.load_price_history
python -m src.etl.load_bank_performance

# Hợp nhất dữ liệu giá và khối lượng chứng khoán
python -m src.etl.consolidate_stock_metrics
```

### Bước 5: Chạy kiểm tra tính toàn vẹn (Validation)
Tập lệnh này sẽ kiểm tra đối chiếu khóa ngoại giữa các file CSV Fact và Dimension vừa tạo trong `data/processed/`, kiểm tra trùng lặp khóa chính và định dạng dữ liệu (DQ-01 đến DQ-05):
```bash
python -m src.etl.validate_integrity
```
*   **Kết quả mong đợi**: Hệ thống báo cáo `=== VALIDATION COMPLETED. TOTAL ERRORS FOUND: 0 ===` và thoát thành công.

---

## 2. Kết Quả Đầu Ra Cần Kiểm Tra Trên Local

Sau khi chạy xong, hãy truy cập thư mục [data/processed/](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/data/processed/) để kiểm tra xem đã có đủ các file CSV sau chưa:

- `dim_date_clean.csv`
- `dim_stock_clean.csv`
- `dim_bank_clean.csv`
- `dim_trading_session_clean.csv`
- `fact_stock_daily_metrics_clean.csv`
- `fact_bank_performance_clean.csv`

---

## 3. Các Bước Công Việc Tiếp Theo Của Trần Minh Khánh

### 1. Bàn giao dữ liệu cục bộ cho ML Team
- Liên hệ với Phạm Minh Quân và Nguyễn Đặng Quốc Anh.
- Thông báo rằng dữ liệu mẫu toàn diện (Fact & Dim) đã được sinh và làm sạch sẵn dưới dạng CSV cục bộ trong thư mục `data/processed/`.
- ML Team có thể sửa cấu hình đọc dữ liệu của các mô hình từ BigQuery sang đọc các file CSV cục bộ này để huấn luyện và đánh giá mô hình nhanh chóng mà không phát sinh chi phí BigQuery.

### 2. Chuẩn bị cho tích hợp BigQuery (Giai đoạn cuối)
- Khi toàn bộ mô hình ML và cấu trúc dữ liệu đã ổn định trên local, anh sẽ thực hiện tích hợp hàm đẩy dữ liệu lên BigQuery (sử dụng thư viện `google-cloud-bigquery` và cấu hình LoadJobConfig quy định tại [AGENTS.md](file:///d:/DWH/vn-banking-dwh-analytics/AGENTS.md)).
- Thay đổi cấu hình tệp `.env` thành `LOCAL_ONLY=False` và điền khóa xác thực GCP để chạy luồng đẩy dữ liệu lên hệ thống thật.
