# Báo cáo Tiến độ và Nhiệm vụ của Trần Minh Khánh (Data Engineering / ETL)

Tài liệu này tổng hợp chi tiết vai trò, các công việc đã hoàn thành và các nhiệm vụ cần thực hiện tiếp theo của thành viên **Trần Minh Khánh** nhằm hoàn thiện hệ thống đường dẫn dữ liệu (ETL Pipeline) lên Google BigQuery cho dự án.

---

## 1. Vai trò và Bản đồ Nhiệm vụ trong [tasks.md](file:///d:/DWH/vn-banking-dwh-analytics/docs/tasks.md)

Trần Minh Khánh chịu trách nhiệm chính về mảng **Data Engineering / ETL (Track B)**, phối hợp cùng Nguyễn Đặng Quốc Anh và Đỗ Kiến Hưng để xây dựng và vận hành pipeline làm sạch dữ liệu, chuẩn hóa cấu trúc và tải dữ liệu lên Google BigQuery Star Schema.

### Bảng trạng thái chi tiết các nhiệm vụ được giao:

| Mã Nhiệm Vụ | Mô Tả Nhiệm Vụ | File Code Liên Quan | Trạng Thái Hiện Tại | Ghi Chú |
| :--- | :--- | :--- | :--- | :--- |
| **Track A** | Thiết lập môi trường và cấu hình dự án | `.env` | **Hoàn Thành** | Đã kích hoạt `venv`, cài đặt `requirements.txt` và cấu hình tệp tin `.env` chạy local. |
| **B-04** | Điền dữ liệu cho bảng chiều `dim_date` | [populate_dim_date.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/populate_dim_date.py) | **Hoàn Thành** | Đã sinh tự động chuỗi ngày từ 2002-2026 và xuất ra local CSV. |
| **B-05** | Điền dữ liệu cho bảng chiều `dim_stock` | [populate_dim_stock.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/populate_dim_stock.py) | **Hoàn Thành** | Đã ghi nhận thông tin 4 mã ngân hàng (BID, TCB, VCB, CTG) ra local CSV. |
| **B-06** | Điền dữ liệu cho bảng chiều `dim_bank` | [populate_dim_bank.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/populate_dim_bank.py) | **Hoàn Thành** | Đã trích xuất danh sách 46 ngân hàng thương mại ra local CSV. |
| **B-07** | Điền dữ liệu cho bảng chiều `dim_trading_session` | [populate_dim_trading_session.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/populate_dim_trading_session.py) | **Hoàn Thành** | Đã sinh dữ liệu 4 phiên giao dịch ra local CSV. |
| **B-08** | ETL dữ liệu lịch sử giá cổ phiếu BID | [load_price_history.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/load_price_history.py) | **Hoàn Thành** | Đã làm sạch và chuẩn hóa dữ liệu giá đóng cửa ra local CSV. |
| **B-09** | ETL dữ liệu giao dịch khối ngoại cổ phiếu BID | [load_foreign_trading.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/load_foreign_trading.py) | **Hoàn Thành** | Đã làm sạch và xử lý dòng tiền khối ngoại ra local CSV. |
| **B-10** | ETL dữ liệu giao dịch tự doanh cổ phiếu BID | [load_proprietary_trading.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/load_proprietary_trading.py) | **Hoàn Thành** | Đã làm sạch và xử lý giao dịch tự doanh ra local CSV. |
| **B-11** | ETL dữ liệu thống kê đặt lệnh cổ phiếu BID | [load_order_stats.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/load_order_stats.py) | **Hoàn Thành** | Đã làm sạch và xử lý thống kê đặt lệnh ra local CSV. |
| **B-12** | ETL dữ liệu khớp lệnh khớp tích tắc HPG | [load_intraday_matching.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/load_intraday_matching.py) | **Hoàn Thành** | Đã bãi bỏ/để trống bảng này do loại bỏ HPG ra khỏi phạm vi ngân hàng. |
| **B-13** | ETL dữ liệu báo cáo tài chính của 46 ngân hàng | [load_bank_performance.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/load_bank_performance.py) | **Hoàn Thành** | Đã làm sạch và impute dữ liệu CAMELS ngân hàng ra local CSV. |
| **B-14** | Chạy kiểm tra tính toàn vẹn tham chiếu | [validate_integrity.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/validate_integrity.py) | **Hoàn Thành** | Đã đối chiếu thành công khóa ngoại của 10 bảng dữ liệu dạng local CSV. |
| **B-15** | Kiểm tra chất lượng dữ liệu DQ-01 đến DQ-06 | [validate_integrity.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/validate_integrity.py) | **Hoàn Thành** | Đã chạy kiểm tra và đạt 0 lỗi chất lượng dữ liệu. |

---

## 2. Chi tiết Công việc Đã thực hiện (Nhiệm vụ B-13)

Nhiệm vụ **B-13** liên quan đến việc xử lý dữ liệu CAMELS của 46 ngân hàng thương mại Việt Nam. Khung xử lý chính đã được viết hoàn chỉnh trong file [load_bank_performance.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/load_bank_performance.py) với các tính năng:

- **Trích xuất (Extract)**: Tự động đọc dữ liệu từ trang tính `Data` và `Banks List` của file Excel mẫu [VN banks dataset (updated August 2023).xlsx](file:///d:/DWH/vn-banking-dwh-analytics/docs/ref/VN%20banks%20dataset%20(updated%20August%202023).xlsx).
- **Biến đổi (Transform)**:
  - Chuẩn hóa tên cột sang định dạng `snake_case` và loại bỏ các ký tự đặc biệt theo đúng [etl-spec.md](file:///d:/DWH/vn-banking-dwh-analytics/docs/etl-spec.md).
  - Ép kiểu dữ liệu (FLOAT sang `float64`, INTEGER sang `Int64` nullable).
  - Thực hiện điền khuyết dữ liệu tài chính giai đoạn 2002–2005 bằng thuật toán Median Imputation (tính trung vị theo từng ngân hàng hoặc trung vị toàn cục nếu không có dữ liệu lịch sử) và gán cờ cảnh báo `is_imputed` tương ứng.
  - Sinh khóa thay thế `bank_key` dựa trên bảng đối chiếu 46 ngân hàng.
  - Loại bỏ các dòng trùng lặp dựa trên cặp khóa chính `(date_key, bank_key)` giữ lại bản ghi đầu tiên.
- **Lưu trữ trung gian**: Ghi dữ liệu đã làm sạch ra các file CSV trung gian tại thư mục `data/processed/` bao gồm:
  - `dim_bank_clean.csv`
  - `fact_bank_performance_clean.csv`
  - `fact_bank_performance_eda_summary.csv`
- **Công việc còn thiếu ở B-13**: Tích hợp module kết nối BigQuery và đẩy trực tiếp DataFrame sau biến đổi vào bảng `fact_bank_performance` trên GCP.

---

## 3. Kế hoạch công việc cần triển khai tiếp theo (To-Do List)

Để hoàn tất các nhiệm vụ được giao, Trần Minh Khánh cần tập trung thực hiện các công việc sau theo thứ tự ưu tiên:

### Bước 1: Hoàn thành thiết lập môi trường cá nhân (Track A)
- Cấu hình tệp cấu hình môi trường cục bộ `.env` từ `.env.example` và đặt biến môi trường xác thực `GOOGLE_APPLICATION_CREDENTIALS` trỏ tới tệp khóa JSON nhận từ quản trị viên.

### Bước 2: Bổ sung logic tải dữ liệu lên BigQuery cho [load_bank_performance.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/load_bank_performance.py) (Hoàn thành 100% B-13)
- Sử dụng BigQuery client được khai báo tại [bigquery_client.py](file:///d:/DWH/vn-banking-dwh-analytics/src/utils/bigquery_client.py) để tải dữ liệu đã làm sạch lên bảng `fact_bank_performance` trong BigQuery.
- Áp dụng cấu hình ghi đè/chèn tiếp (`WRITE_APPEND` hoặc `WRITE_TRUNCATE` phù hợp) và ghi log số dòng đã tải thành công.

### Bước 3: Triển khai các scripts điền dữ liệu bảng chiều (Dimension Population - B-04 đến B-07)
- [populate_dim_date.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/populate_dim_date.py): Viết mã sinh tự động danh sách ngày từ `2002-01-01` đến `2026-12-31` kèm theo các trường thông tin năm, quý, tháng, ngày giao dịch và ghi lên BigQuery.
- [populate_dim_stock.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/populate_dim_stock.py): Ghi danh mục 4 mã ngân hàng (`BID`, `TCB`, `VCB`, `CTG` từ key 1-4) lên bảng chiều cổ phiếu.
- [populate_dim_bank.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/populate_dim_bank.py): Đọc danh sách 46 ngân hàng từ file Excel và ghi vào bảng chiều ngân hàng.
- [populate_dim_trading_session.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/populate_dim_trading_session.py): Ghi thông tin 4 phiên giao dịch sàn HOSE (ATO, Khớp lệnh liên tục sáng, Khớp lệnh liên tục chiều, ATC) theo đặc tả [AGENTS.md](file:///d:/DWH/vn-banking-dwh-analytics/AGENTS.md) Mục 3.2.

### Bước 4: Triển khai ETL cho dữ liệu giao dịch cổ phiếu (B-08 đến B-12)
- Xây dựng các scripts xử lý và tải dữ liệu cổ phiếu cho các bảng fact:
  - [load_price_history.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/load_price_history.py): Đọc dữ liệu giá cổ phiếu, loại bỏ dòng nếu `close_price` trống, không dùng forward-fill.
  - [load_foreign_trading.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/load_foreign_trading.py): Đọc và tính toán dòng tiền khối ngoại, áp dụng forward-fill tối đa 1 ngày nếu thiếu dữ liệu.
  - [load_proprietary_trading.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/load_proprietary_trading.py): Đọc dữ liệu tự doanh, áp dụng forward-fill tối đa 1 ngày.
  - [load_order_stats.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/load_order_stats.py): Xử lý thống kê lệnh mua bán, reject dòng nếu thiếu dữ liệu.
  - [load_intraday_matching.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/load_intraday_matching.py): Bãi bỏ do loại bỏ HPG, nạp bảng trống lên BigQuery.

### Bước 5: Triển khai kiểm tra chất lượng dữ liệu (Validation - B-14 & B-15)
- Viết mã cho [validate_integrity.py](file:///d:/DWH/vn-banking-dwh-analytics/src/etl/validate_integrity.py) thực hiện các truy vấn so khớp khóa ngoại giữa các bảng Fact và các bảng Dimension để đảm bảo không xảy ra lỗi toàn vẹn tham chiếu.
- Thực hiện kiểm tra chất lượng dữ liệu DQ-01 đến DQ-06 quy định tại Section 5 của [data-dictionary.md](file:///d:/DWH/vn-banking-dwh-analytics/docs/data-dictionary.md).

---

## 4. Các quy chuẩn phát triển bắt buộc tuân thủ (Trích từ [AGENTS.md](file:///d:/DWH/vn-banking-dwh-analytics/AGENTS.md))

- **Không sử dụng hàm `print()`**: Tất cả các thông báo tiến trình, cảnh báo và thông tin số dòng được nạp phải ghi nhận qua hệ thống log dùng chung bằng thư viện:
  ```python
  from src.utils.logger import get_logger
  logger = get_logger(__name__)
  ```
- **Không hardcode thông tin kết nối**: Tuyệt đối không viết cứng mã dự án GCP, Dataset ID hay thông tin Service Account vào mã nguồn. Luôn sử dụng lớp cấu hình tập trung từ [config.py](file:///d:/DWH/vn-banking-dwh-analytics/src/utils/config.py) hoặc `os.getenv()`.
- **Cấu hình Job tải BigQuery**: Khi đẩy dữ liệu từ DataFrame lên BigQuery, bắt buộc sử dụng cấu hình phân vùng (Partitioning) theo cột ngày `date_key` và gom cụm (Clustering) theo cột khóa ngoại tương ứng để tối ưu chi phí truy vấn:
  ```python
  job_config = bigquery.LoadJobConfig(
      write_disposition="WRITE_APPEND", # Hoặc WRITE_TRUNCATE tùy trường hợp đầy đủ
      time_partitioning=bigquery.TimePartitioning(
          type_=bigquery.TimePartitioningType.DAY,
          field="date_key",
      ),
      clustering_fields=["bank_key"], # Hoặc ["stock_key"] cho bảng cổ phiếu
  )
  ```
