# Tài liệu Quy trình Kỹ thuật DWH Nâng cao (Auditing, SCD Type 2 & Incremental Loading)

Tài liệu này mô tả chi tiết thiết kế, triển khai và quy trình vận hành các kỹ thuật kho dữ liệu nâng cao được áp dụng trong dự án: Hệ thống Auditing động, theo dõi lịch sử thay đổi SCD Type 2, và cơ chế tải dữ liệu tăng trưởng (Incremental Loading) tự động tương thích với các tài khoản GCP Sandbox bị giới hạn Billing.

---

## 1. Hệ thống Auditing Động (`dim_audit`)

Để đảm bảo khả năng truy xuất nguồn gốc dữ liệu (data lineage) và phục vụ mục đích kiểm toán hệ thống, tất cả các bảng trong kho dữ liệu (bao gồm cả bảng Chiều - Dimension và bảng Sự kiện - Fact) đều được tích hợp các trường thông tin kiểm tra (audit metadata). Các trường này được gán động tại thời điểm chạy pipeline và liên kết đến bảng kiểm toán vật lý `dim_audit`.

### 1.1 Cấu trúc Bảng Audit (`dim_audit`)
Bảng `dim_audit` ghi nhận lịch sử thực thi của từng phiên chạy ingestion/load:
*   `audit_key` (INT64, Khóa chính): Được tạo động theo định dạng thời gian `YYYYMMDDHHMMSS` tại thời điểm chạy script (ví dụ: `20260630144049`).
*   `run_id` (STRING): Chuỗi định danh UUIDv4 duy nhất cho mỗi phiên chạy pipeline.
*   `run_timestamp` (TIMESTAMP): Thời gian chạy hệ thống theo chuẩn UTC.
*   `script_name` (STRING): Tên của script/module Python thực thi.
*   `source_file` (STRING): Tên tệp dữ liệu nguồn thô được xử lý.
*   `rows_processed` (INT64): Tổng số dòng dữ liệu đã tải thành công.
*   `status` (STRING): Trạng thái thực thi (`RUNNING`, `SUCCESS`, hoặc `FAILED`).

### 1.2 Các Trường Audit trên các Bảng Đích
Mỗi bảng fact và dimension trong hệ thống đều được tự động bổ sung 4 cột kiểm toán sau trong giai đoạn Transform:
1.  `audit_key` (INT64): Khóa ngoại tham chiếu đến cột `audit_key` trong bảng `dim_audit`.
2.  `_created_at` (TIMESTAMP): Thời điểm dòng dữ liệu được tải vào kho dữ liệu lần đầu tiên (theo giờ UTC).
3.  `_updated_at` (TIMESTAMP): Thời điểm dòng dữ liệu được cập nhật lần cuối (theo giờ UTC).
4.  `_source_file` (STRING): Tên tệp bảng tính nguồn thô (tệp Excel/CSV).

---

## 2. Theo dõi Lịch sử Thay đổi SCD Type 2 trên Bảng Chiều `dim_bank`

Để theo dõi lịch sử biến động các thuộc tính của ngân hàng (như vốn điều lệ, tên ngân hàng, phân loại ngân hàng) qua các năm, bảng `dim_bank` áp dụng kỹ thuật SCD (Slowly Changing Dimension) Type 2.

### 2.1 Cấu trúc Cột SCD
*   `bank_key` (INT64, Khóa chính): Khóa thay thế (surrogate key) được tạo tăng dần tự động.
*   `bank_code` (STRING): Khóa tự nhiên đại diện cho mã ngân hàng (ví dụ: `BID`, `TCB`, `VCB`).
*   `valid_from` (DATE): Ngày bắt đầu có hiệu lực của phiên bản dữ liệu.
*   `valid_to` (DATE): Ngày hết hiệu lực của phiên bản dữ liệu. Phiên bản hiện tại sẽ có giá trị mặc định là `9999-12-31`.
*   `is_current` (BOOLEAN): Cờ đánh dấu phiên bản đang có hiệu lực hiện tại.

### 2.2 Logic So sánh và Hợp nhất Phiên bản (Version-Merge)
Quy trình thực thi khi nạp thông tin ngân hàng:
1.  Script tải danh sách các bản ghi hiện tại đang có hiệu lực (`is_current = True`) từ BigQuery lên bộ nhớ để so sánh.
2.  Đối với mỗi bản ghi ngân hàng mới nạp, hệ thống so sánh các thuộc tính của nó (như `charter_capital`, `bank_type`, `bank_name`) với bản ghi hiện hành.
3.  Nếu không phát hiện thay đổi nào, bản ghi được bỏ qua.
4.  Nếu phát hiện có sự thay đổi:
    *   Bản ghi cũ sẽ bị hết hạn: đặt lại `valid_to` thành `ngày_hôm_nay - 1` và chuyển `is_current` thành `False`.
    *   Bản ghi mới với thuộc tính cập nhật sẽ được chèn vào: đặt `valid_from` thành `ngày_hôm_nay`, `valid_to` thành `9999-12-31`, và cờ `is_current` thành `True`.
5.  Nếu ngân hàng chưa từng xuất hiện trong hệ thống, bản ghi được khởi tạo mới với khoảng thời gian mặc định (`valid_from = '2002-01-01'`).

---

## 3. Cơ chế Incremental Load với Tự động Fallback cho Sandbox

Để hỗ trợ cập nhật dữ liệu liên tục và ngăn ngừa hiện tượng trùng lặp dữ liệu khi nạp lại nhiều lần, pipeline triển khai cơ chế load tăng trưởng sử dụng câu lệnh SQL `MERGE`.

### 3.1 Cơ chế Nạp dữ liệu qua Bảng Staging (`MERGE`)
1.  Dữ liệu từ tệp CSV đã làm sạch được tải lên một bảng tạm (ví dụ: `staging_fact_stock_daily_metrics`) sử dụng chế độ ghi đè `WRITE_TRUNCATE`.
2.  Một lệnh SQL `MERGE` được thực thi để kết hợp bảng tạm và bảng đích dựa trên các cột khóa chính (ví dụ: `date_key` và `stock_key`).
3.  `WHEN MATCHED`: Cập nhật các cột dữ liệu thay đổi trong bảng đích dựa trên dữ liệu mới (loại trừ cột khóa chính và cột thời gian khởi tạo `_created_at`).
4.  `WHEN NOT MATCHED`: Chèn mới toàn bộ bản ghi.
5.  Xóa bảng tạm sau khi hoàn tất.

### 3.2 Tự động Fallback khi Billing bị Vô hiệu hóa (GCP Free-Tier Sandbox)
Do tài khoản Google Cloud Free-Tier không cho phép chạy các lệnh DML (như SQL `MERGE`, `UPDATE`, `DELETE`) cũng như dịch vụ Streaming Insert, pipeline áp dụng cơ chế tự động chuyển hướng thông minh:
1.  **Ghi nhật ký Audit**: Thay vì sử dụng lệnh DML `MERGE` trên bảng `dim_audit` để cập nhật trạng thái, hệ thống ghi nhận lịch sử chạy thông qua các tác vụ tải dữ liệu lô chuẩn (`WRITE_APPEND`). Tác vụ này hoàn toàn miễn phí và được hỗ trợ đầy đủ trong gói Free Tier.
2.  **Tải bảng đích**: Nếu câu lệnh `MERGE` lỗi với mã lỗi `403 billingNotEnabled`, hệ thống sẽ tự động bắt ngoại lệ và kích hoạt chế độ tải trực tiếp bằng API Load Job (`WRITE_APPEND` hoặc `WRITE_TRUNCATE` tùy thuộc vào cài đặt chạy pipeline), đảm bảo quá trình tải dữ liệu không bị gián đoạn.

---

## 4. Loại bỏ Hoàn toàn Dữ liệu Mã HPG

Theo yêu cầu từ ban dự án, toàn bộ lịch sử giao dịch mã HPG và bảng `fact_intraday_matching` đã được loại bỏ triệt để khỏi hệ thống:
*   Đã xóa tệp `load_intraday_matching.py`.
*   Loại bỏ mọi khai báo liên quan đến HPG và `fact_intraday_matching` trong tệp cấu hình DDL, tài liệu đặc tả schema và kiểm thử.
*   Bảng chiều cổ phiếu `dim_stock` hiện tại chỉ lưu trữ đúng 4 mã ngân hàng trọng tâm (BID, TCB, VCB, CTG).

---

## 5. Hướng dẫn Lệnh Vận hành Pipeline (ETL Commands)

Thực thi các lệnh dưới đây bên trong môi trường ảo (`venv`) để vận hành và kiểm tra hệ thống:

### 5.1 Khởi tạo lại Schema Cơ sở dữ liệu
Xóa sạch các bảng cũ và tạo mới toàn bộ cấu trúc bảng kèm theo hệ thống auditing và trường SCD2:
```powershell
.\venv\Scripts\python.exe -m src.etl.provision_schema
```

### 5.2 Xử lý và làm sạch dữ liệu cục bộ
Chạy quy trình ETL cục bộ trên các bảng chiều và bảng fact để tạo ra các tệp CSV sạch đi kèm cột `audit_key` động:
```powershell
.\venv\Scripts\python.exe -m src.etl.populate_dim_date
.\venv\Scripts\python.exe -m src.etl.populate_dim_stock
.\venv\Scripts\python.exe -m src.etl.populate_dim_bank
.\venv\Scripts\python.exe -m src.etl.populate_dim_trading_session
.\venv\Scripts\python.exe -m src.etl.load_price_history
.\venv\Scripts\python.exe -m src.etl.load_bank_performance
```

### 5.3 Xác thực tính Toàn vẹn dữ liệu
Chạy kiểm tra ràng buộc khóa ngoại, tính duy nhất khóa chính và các điều kiện chất lượng dữ liệu (DQ-01 tới DQ-06) trên các tệp CSV cục bộ trước khi tải lên Cloud:
```powershell
.\venv\Scripts\python.exe -m src.etl.validate_integrity
```

### 5.4 Tải dữ liệu vào BigQuery
Nạp dữ liệu vào BigQuery. Lệnh mặc định sẽ nạp tăng trưởng qua câu lệnh `MERGE` (và tự động chuyển về chế độ batch append nếu tài khoản GCP không kích hoạt billing):
```powershell
.\venv\Scripts\python.exe -m src.etl.load_to_bigquery
```

Để thực hiện xóa sạch và nạp lại toàn bộ dữ liệu (Full Reload):
```powershell
.\venv\Scripts\python.exe -m src.etl.load_to_bigquery --full-reload
```
