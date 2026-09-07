# SPEC-01: DWH Idempotency and Zero-Duplicate Data Ingestion Specification

## 1. Mục đích & Bối cảnh
Data Warehouse (DWH) `financial_dwh` trên Google BigQuery phục vụ làm Single Source of Truth cho các mô hình học máy (LSTM, K-Means, Random Forest) và báo cáo trực quan Looker Studio.
Đặc tả này quy định các tiêu chuẩn kỹ thuật bắt buộc nhằm đảm bảo mọi quá trình trích xuất, nạp dữ liệu (ETL/ELT) đều đạt tính chất **Idempotent (tính bất biến theo số lần thực thi)**: chạy lại pipeline $N$ lần vẫn cho ra cùng một trạng thái dữ liệu chính xác, không sinh ra bản ghi trùng lặp (duplicate rows).

## 2. Tiêu chuẩn Data Ingestion trên BigQuery

### 2.1. Quản lý Môi trường: Production vs Sandbox/Free Tier
- **Production (Có Billing Account):**
  - Tải dữ liệu vào bảng tạm (Staging table: `_staging_<table_name>_<uuid>`).
  - Thực thi lệnh `MERGE` SQL để Upsert (Update bản ghi đã tồn tại theo khóa chính, Insert bản ghi mới).
  - Khóa chính định danh cho từng bảng:
    - `dim_date`: `date_key`
    - `dim_stock`: `stock_key`
    - `dim_bank`: `bank_key` (và `valid_from` trong cấu hình SCD Type 2)
    - `dim_trading_session`: `session_key`
    - `fact_stock_daily_metrics`: `(date_key, stock_key)`
    - `fact_bank_performance`: `(date_key, bank_key)`
- **Sandbox / Free Tier (Không bật Billing hoặc bị lỗi `billingNotEnabled`):**
  - Theo tài liệu chính thức của Google Cloud, BigQuery Sandbox **không cho phép chạy DML** (`MERGE`, `UPDATE`, `DELETE`).
  - **Quy tắc bắt buộc:** Khi xảy ra lỗi `billingNotEnabled` hoặc khi người dùng truyền cờ `--full-reload`, pipeline **tuyệt đối không dùng `WRITE_APPEND`**, mà bắt buộc phải dùng:
    ```python
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )
    ```
  - `WRITE_TRUNCATE` là thao tác LoadJob hợp lệ trong Sandbox, đảm bảo làm sạch bảng cũ trước khi ghi dữ liệu mới, ngăn ngừa triệt để duplicate.

### 2.2. Tiêu chí nghiệm thu (Acceptance Criteria)
1. **Zero-Duplicate Rule:** Khi chạy liên tiếp `python -m src.etl.load_to_bigquery` 2 lần:
   - `COUNT(*)` của `dim_bank` trên BigQuery = 45.
   - `COUNT(*)` của `fact_bank_performance` trên BigQuery = 667.
   - `COUNT(*)` của `dim_date` trên BigQuery = 9.131.
2. Script kiểm tra `scripts/check_duplicates.py` phải trả về mã thoát `0` (PASS).
