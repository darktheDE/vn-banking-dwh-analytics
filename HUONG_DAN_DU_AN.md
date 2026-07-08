# Hướng Dẫn Chi Tiết Toàn Bộ Dự Án: Kho Dữ Liệu & Nền Tảng Phân Tích Học Máy Hệ Thống Ngân Hàng Việt Nam

Tài liệu này cung cấp hướng dẫn cặn kẽ và chi tiết về toàn bộ dự án xây dựng Kho dữ liệu (Data Warehouse) trên Google BigQuery kết hợp với các mô hình học máy nâng cao nhằm phân tích và dự báo hoạt động của hệ thống ngân hàng Việt Nam. Hướng dẫn này được thiết kế để hỗ trợ việc tìm hiểu, vận hành và bảo vệ dự án trước các hội đồng học thuật.

---

## 1. Tổng Quan Dự Án và Bối Cảnh Nghiên Cứu

### 1.1 Bối Cảnh Thực Tế
Hệ thống ngân hàng và thị trường tài chính Việt Nam có vai trò cốt lõi trong nền kinh tế. Sự biến động của dòng tiền và chất lượng tài sản đòi hỏi các tổ chức tài chính và nhà đầu tư phải đưa ra quyết định dựa trên dữ liệu định lượng. Tuy nhiên, dữ liệu tài chính hiện nay thường bị phân mảnh giữa dữ liệu vi mô hàng ngày trên sàn giao dịch chứng khoán (như giá cổ phiếu, khối lượng mua bán của khối ngoại và tự doanh) và dữ liệu vĩ mô dài hạn từ báo cáo tài chính của các ngân hàng.

Để biết thêm thông tin chi tiết về bối cảnh nghiên cứu và các yêu cầu nghiệp vụ ban đầu, quý độc giả có thể tham khảo thêm tại [prd.md](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/docs/prd.md) hoặc [product-brief.md](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/docs/product-brief.md).

### 1.2 Mục Tiêu Dự Án
Dự án được thiết lập nhằm xây dựng một hệ thống tích hợp tự động hóa từ đầu đến cuối bao gồm:
- Thu thập và chuẩn hóa dữ liệu giao dịch hàng ngày của 4 cổ phiếu ngân hàng trọng điểm: BID, TCB, VCB, CTG.
- Thu thập và chuẩn hóa dữ liệu báo cáo tài chính theo chuẩn CAMELS của 45 ngân hàng thương mại Việt Nam trong giai đoạn 20 năm (2002–2022).
- Xây dựng Kho dữ liệu tài chính tập trung (Financial Data Warehouse) sử dụng cấu trúc Star Schema trên đám mây Google BigQuery.
- Triển khai 3 mô hình học máy chuyên sâu nhằm dự báo giá cổ phiếu ngắn hạn, phân cụm chiến lược ngân hàng và cảnh báo sớm rủi ro nợ xấu.
- Thiết lập hệ thống bảng điều khiển trực quan (Looker Studio Dashboard) kết nối trực tiếp với Kho dữ liệu.

### 1.3 Câu Hỏi Nghiên Cứu và Giả Thuyết Thực Nghiệm
Dự án tập trung giải quyết 4 câu hỏi nghiên cứu cốt lõi:
1. **Câu hỏi 1 (Q1):** Mô hình LSTM đa biến (kết hợp OHLCV và phần trăm biến động) có vượt trội hơn mô hình LSTM đơn biến và mô hình baseline ARIMA trong việc dự báo giá đóng cửa ngắn hạn của các cổ phiếu ngân hàng không?
   - **Giả thuyết:** Mô hình LSTM đa biến đạt sai số RMSE và MAE thấp hơn so với cả mô hình LSTM đơn biến và ARIMA, do khối lượng giao dịch và biến động biên độ cung cấp thông tin dự báo giá ngắn hạn tốt hơn.
2. **Câu hỏi 2 (Q2):** Xu hướng biến động giá đóng cửa ngắn hạn của 4 cổ phiếu ngân hàng (BID, TCB, VCB, CTG) là đồng pha hay phân hóa?
   - **Giả thuyết:** Có sự đồng pha mạnh mẽ trong ngắn hạn giữa các cổ phiếu thuộc nhóm quốc doanh (BID, VCB, CTG), trong khi nhóm cổ phần tư nhân (TCB) thể hiện sự phân hóa độc lập hơn.
3. **Câu hỏi 3 (Q3):** Những chỉ số tài chính nào quyết định việc một ngân hàng rơi vào nhóm có rủi ro nợ xấu cao?
   - **Giả thuyết:** Các ngân hàng có tỷ lệ trích lập dự phòng rủi ro thấp, hiệu quả hoạt động (ROA, ROE) kém và tỷ lệ chi phí trên thu nhập (CIR) cao sẽ có xác suất rơi vào nhóm rủi ro nợ xấu vượt mức 3% cao hơn.
4. **Câu hỏi 4 (Q4):** Có thể phân loại rõ rệt chiến lược hoạt động của các nhóm ngân hàng tại Việt Nam dựa trên dữ liệu tài chính hay không?
   - **Giả thuyết:** Phân tích dữ liệu sẽ phân tách hệ thống ngân hàng thành 3 cụm chính phản ánh đặc trưng sở hữu và hoạt động: nhóm quốc doanh tối ưu quy mô, nhóm cổ phần tối ưu lợi nhuận và nhóm ngân hàng liên doanh hoặc nước ngoài tối ưu an toàn vốn.

Chi tiết về kết quả kiểm chứng các câu hỏi nghiên cứu này được trình bày tại [RESULT.md](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/RESULT.md).

---

## 2. Kiến Trúc Kho Dữ Liệu (Star Schema Data Warehouse)

Để tối ưu hóa hiệu năng truy vấn cho các công cụ Business Intelligence và chuẩn bị dữ liệu đầu vào cho các thuật toán học máy, dự án thiết kế Kho dữ liệu theo mô hình hình sao (Star Schema) lưu trữ trên Google BigQuery. Đặc tả chi tiết về các bảng và trường dữ liệu được tài liệu hóa tại [star-schema.md](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/docs/star-schema.md) và [data-dictionary.md](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/docs/data-dictionary.md).

### 2.1 Tại Sao Chọn Mô Hình Star Schema?
- **Hiệu năng truy vấn vượt trội:** Giảm thiểu số lượng liên kết bảng (JOIN) phức tạp khi thực hiện truy vấn phân tích.
- **Tính trực quan và dễ hiểu:** Cấu trúc phân tách rõ ràng giữa thực thể đo lường (Fact) và thực thể mô tả (Dimension), giúp người dùng doanh nghiệp dễ dàng thao tác trên Looker Studio.
- **Hỗ trợ tối ưu hóa chi phí đám mây:** Cấu trúc này cho phép áp dụng hiệu quả cơ chế phân vùng (partitioning) và phân cụm (clustering) trên BigQuery.

### 2.2 Các Bảng Chiều (Dimension Tables)
Hệ thống gồm 5 bảng chiều chính:
1. **dim_date:** Lưu trữ thông tin thời gian từ năm 2002 đến năm 2026.
   - *Khóa chính:* `date_key` (dạng số nguyên YYYYMMDD).
   - *Các trường thông tin:* `full_date`, `day`, `month`, `year`, `quarter`, `is_trading_day`.
2. **dim_stock:** Lưu trữ danh mục cổ phiếu ngân hàng được theo dõi.
   - *Khóa chính:* `stock_key` (mã số nguyên tự tăng).
   - *Các trường thông tin:* `ticker` (BID, TCB, VCB, CTG), `company_name`, `exchange` (HOSE), `industry`.
3. **dim_bank:** Lưu trữ danh sách 45 ngân hàng thương mại Việt Nam.
   - *Khóa chính:* `bank_key` (mã số nguyên tự tăng).
   - *Cơ chế SCD Type 2 (Slowly Changing Dimension):* Sử dụng các trường `valid_from`, `valid_to`, và `is_current` để theo dõi lịch sử thay đổi của ngân hàng (như thay đổi vốn điều lệ) theo thời gian mà không ghi đè dữ liệu cũ.
4. **dim_trading_session:** Phân chia các phiên giao dịch trong ngày trên sàn HOSE.
   - *Khóa chính:* `session_key` (mã số nguyên từ 1 đến 4).
   - *Các trường thông tin:* `session_name` (ATO, Sáng liên tục, Chiều liên tục, ATC), `start_time`, `end_time`.
5. **dim_audit:** Ghi nhận nhật ký chạy của hệ thống dữ liệu để phục vụ kiểm toán chất lượng.
   - *Khóa chính:* `audit_key` (mã số nguyên tạo bởi UUID hoặc mã chạy tự động).
   - *Các trường thông tin:* `run_id`, `run_timestamp`, `script_name`, `source_file`, `rows_processed`, `status`.

### 2.3 Các Bảng Thực Tế (Fact Tables)
Hệ thống gồm 2 bảng thực tế kết nối với các bảng chiều qua khóa ngoại:
1. **fact_stock_daily_metrics:** Lưu trữ lịch sử giao dịch và giá cổ phiếu hàng ngày.
   - *Khóa ngoại:* `date_key`, `stock_key`.
   - *Các trường đo lường:* `open_price`, `high_price`, `low_price`, `close_price`, `trading_volume`.
   - *Thiết kế vật lý:* Bảng được phân vùng (Partitioned) theo trường `date_key` và phân cụm (Clustered) theo trường `stock_key`. Điều này giúp BigQuery chỉ quét các vùng dữ liệu của ngày cụ thể và cổ phiếu cụ thể khi thực hiện truy vấn, giảm thiểu chi phí quét dữ liệu và tăng tốc độ xử lý.
2. **fact_bank_performance:** Lưu trữ 47 chỉ số tài chính CAMELS của 45 ngân hàng trong 20 năm.
   - *Khóa ngoại:* `date_key`, `bank_key`.
   - *Các trường đo lường:* Các chỉ số tài chính cốt lõi bao gồm tiền gửi (`deposits`), dư nợ (`loans`), tài sản (`tassets`), vốn chủ sở hữu (`equity`), dự phòng rủi ro tín dụng (`llp`), nợ xấu (`npl`), tỷ lệ nợ xấu (`npl_ratio`), hiệu số sinh lời (`roa`, `roe`), biên lãi ròng (`nim`), tỷ lệ chi phí trên thu nhập (`cir`), tỷ lệ dư nợ trên tiền gửi (`ltd`), vốn chủ sở hữu trên tổng tài sản (`eta`), và vốn chủ sở hữu trên tiền gửi khách hàng (`etd`).
   - *Trường bổ sung:* Trường `is_imputed` dùng để đánh dấu các hàng dữ liệu sử dụng phương pháp nội suy trung vị để làm sạch.

### 2.4 Các Bảng Đầu Ra Của Mô Hình Học Máy
Kết quả dự báo và phân cụm từ các mô hình học máy được ghi ngược trở lại BigQuery vào 3 bảng chuyên dụng để phục vụ trực quan hóa:
- **fact_model_predictions:** Lưu trữ dự báo giá đóng cửa ngắn hạn từ T+1 đến T+5 của mô hình LSTM.
- **bank_cluster_assignments:** Lưu trữ nhãn phân cụm chiến lược của các ngân hàng từ thuật toán K-Means.
- **bank_risk_predictions:** Lưu trữ kết quả phân loại rủi ro nợ xấu và xác suất tương ứng từ mô hình Random Forest.

---

## 3. Quy Trình Trích Xuất, Biến Đổi và Nạp Dữ Liệu (ETL Pipeline)

Quy trình ETL được triển khai hoàn toàn bằng mã nguồn Python, tuân thủ các quy định nghiệp vụ nghiêm ngặt về làm sạch và kiểm tra chất lượng dữ liệu được định nghĩa trong tài liệu đặc tả kỹ thuật dữ liệu [etl-spec.md](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/docs/etl-spec.md).

### 3.1 Cấu Trúc Các Tệp Tin ETL
Toàn bộ mã nguồn ETL nằm trong thư mục [src/etl](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/etl):
- [provision_schema.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/etl/provision_schema.py): Đọc tệp cấu trúc SQL `sql/bigquery_schema.sql` và khởi tạo toàn bộ cấu trúc bảng trống trên BigQuery.
- [populate_dim_date.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/etl/populate_dim_date.py): Tạo dữ liệu lịch ngày tự động từ năm 2002 đến năm 2026.
- [populate_dim_stock.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/etl/populate_dim_stock.py): Thiết lập các bản ghi tĩnh cho 4 mã cổ phiếu ngân hàng.
- [populate_dim_bank.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/etl/populate_dim_bank.py): Đọc danh sách ngân hàng từ tệp nguồn báo cáo tài chính, tạo khóa thay thế `bank_key`, xử lý trùng lặp và áp dụng cơ chế SCD Type 2 để lưu vết vốn điều lệ.
- [populate_dim_trading_session.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/etl/populate_dim_trading_session.py): Thiết lập thông tin về 4 phiên giao dịch chính trên sàn HOSE.
- [load_price_history.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/etl/load_price_history.py): Trích xuất và chuẩn hóa lịch sử giá giao dịch hàng ngày của 4 cổ phiếu.
- [load_foreign_trading.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/etl/load_foreign_trading.py): Xử lý dữ liệu giao dịch khối ngoại của cổ phiếu BID.
- [load_proprietary_trading.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/etl/load_proprietary_trading.py): Xử lý dữ liệu tự doanh của cổ phiếu BID.
- [load_order_stats.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/etl/load_order_stats.py): Xử lý thông tin đặt lệnh của cổ phiếu BID.
- [load_bank_performance.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/etl/load_bank_performance.py): Trích xuất dữ liệu tài chính 20 năm của các ngân hàng và thực hiện nội suy các giá trị khuyết thiếu.
- [load_to_bigquery.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/etl/load_to_bigquery.py): Tệp trung tâm điều phối việc tải các tệp dữ liệu đã làm sạch lên BigQuery.
- [validate_integrity.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/etl/validate_integrity.py): Chạy các truy vấn SQL kiểm định tính toàn vẹn khóa ngoại và các quy tắc chất lượng dữ liệu.

### 3.2 Quy Tắc Làm Sạch Dữ Liệu
Các bước biến đổi dữ liệu (Transform) áp dụng trong mã nguồn bao gồm:
- **Chuẩn hóa tên cột:** Loại bỏ các ký tự đặc biệt, đơn vị đo lường và khoảng trắng, chuyển toàn bộ tên cột thành dạng chữ thường phân tách bằng dấu gạch dưới (`snake_case`).
- **Ép kiểu dữ liệu:** Chuyển đổi các cột số tiền và tỷ lệ về dạng số thực (`float64`), các cột số lượng giao dịch và khóa ngoại về dạng số nguyên (`Int64`), xử lý các dấu phân tách phần nghìn trước khi ép kiểu.
- **Xử lý giá trị khuyết thiếu trong dữ liệu cổ phiếu:** Áp dụng phương pháp điền tiếp diễn (forward-fill) giá trị của ngày trước đó cho ngày tiếp theo nếu bị khuyết, giới hạn tối đa là 1 ngày và ghi log cảnh báo. Nếu giá đóng cửa (`close_price`) bị rỗng sau khi xử lý, dòng dữ liệu đó sẽ bị loại bỏ hoàn toàn.
- **Xử lý giá trị khuyết thiếu trong dữ liệu ngân hàng (2002–2005):** Giai đoạn này có nhiều chỉ số báo cáo tài chính bị khuyết do các quy định kế toán cũ. Hệ thống áp dụng phương pháp nội suy trung vị (median imputation) theo từng ngân hàng cụ thể. Nếu một ngân hàng không có đủ dữ liệu để tính trung vị, hệ thống sẽ sử dụng trung vị chung của toàn bộ hệ thống ngân hàng trong năm đó để điền vào, đồng thời thiết lập cột `is_imputed` thành `True` để phục vụ theo dõi.
- **Ràng buộc đặc biệt:** Tuyệt đối không áp dụng forward-fill cho biến tỷ lệ nợ xấu (`npl_ratio`) vì đây là biến mục tiêu dùng để phân loại rủi ro trong các mô hình học máy. Bất kỳ sự nội suy sai lệch nào trên biến này sẽ gây ra hiện tượng rò rỉ hoặc nhiễu dữ liệu nghiêm trọng. Biến này bắt buộc phải sử dụng nội suy trung vị theo năm để đảm bảo tính nhất quán.

### 3.3 Cơ Chế Tải Dữ Liệu Tăng Dần (Incremental Load) và Tính Bất Biến
Để đảm bảo tính bất biến (idempotency) và tránh trùng lặp dữ liệu khi chạy lại các tiến trình tải, [load_to_bigquery.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/etl/load_to_bigquery.py) triển khai cơ chế tải tăng dần bằng câu lệnh `MERGE` SQL.

Dữ liệu mới trước tiên được đẩy vào một bảng tạm (staging table). Sau đó, câu lệnh `MERGE` so khớp các bản ghi giữa bảng thực tế chính thức và bảng tạm dựa trên tập hợp khóa chính (ví dụ như kết hợp `date_key` và `stock_key`). Nếu bản ghi đã tồn tại, hệ thống tiến hành cập nhật (UPDATE) các trường thông tin thay đổi và cập nhật trường kiểm toán hệ thống `_updated_at`. Nếu bản ghi chưa tồn tại, hệ thống tiến hành chèn mới (INSERT) toàn bộ dòng dữ liệu cùng với các trường kiểm toán hệ thống.

Trong trường hợp tài khoản Google Cloud Platform bị chặn tính năng thanh toán (khiến cho DML/MERGE bị khóa), mã nguồn có cơ chế dự phòng (fallback path) tự động chuyển sang tải lô (batch load) sử dụng cấu hình `WRITE_APPEND` hoặc `WRITE_TRUNCATE` của thư viện Google Cloud BigQuery API để đảm bảo tiến trình không bị gián đoạn.

### 3.4 Kiểm Toán Hệ Thống (System Auditing)
Mọi dòng dữ liệu khi đi qua quy trình biến đổi đều được tự động bổ sung 4 trường thông tin hệ thống:
- `audit_key`: Khóa liên kết với bảng nhật ký `dim_audit`, giúp truy vết dòng dữ liệu này được nạp vào kho ở phiên chạy nào.
- `_created_at`: Thời điểm dòng dữ liệu được tạo ra trong kho dữ liệu (kiểu TIMESTAMP).
- `_updated_at`: Thời điểm dòng dữ liệu được cập nhật lần cuối trong kho dữ liệu (kiểu TIMESTAMP).
- `_source_file`: Tên tệp Excel nguồn chứa dữ liệu gốc, giúp dễ dàng kiểm tra chéo khi xảy ra sai sót dữ liệu.

---

## 4. Chi Tiết Các Mô Hình Học Máy (Machine Learning Platform)

Nền tảng học máy tích hợp sử dụng dữ liệu trực tiếp truy vấn từ Kho dữ liệu BigQuery, thực hiện huấn luyện các mô hình và ghi nhận kết quả. Đặc tả chi tiết của các mô hình học máy được mô tả tại [ml-spec.md](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/docs/ml-spec.md).

### 4.1 Mô Hình Dự Báo Chuỗi Thời Gian Giá Cổ Phiếu (LSTM)
Mô hình LSTM (Long Short-Term Memory) được triển khai trong tệp [train_lstm.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/models/train_lstm.py) nhằm dự báo giá đóng cửa của cổ phiếu trong 5 ngày giao dịch tiếp theo ($T+1$ đến $T+5$).

- **Kỹ thuật Đặc trưng (Feature Engineering):**
  - Đối với cổ phiếu BID (có đầy đủ dữ liệu phụ trợ): Đầu vào bao gồm giá đóng cửa (`close_price`), giá mở cửa, giá cao nhất, giá thấp nhất, khối lượng giao dịch, khối lượng mua ròng khối ngoại (`foreign_net_volume`), giá trị mua ròng khối ngoại, khối lượng mua ròng tự doanh (`prop_net_volume`), giá trị mua ròng tự doanh, tỷ lệ thay đổi giá hàng ngày (`price_change_pct`), và các đặc trưng trễ 1 ngày của dòng tiền ngoại và tự doanh (`foreign_net_lag_1`, `prop_net_lag_1`). Các đặc trưng này được xây dựng trong [feature_engineering_stock.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/models/feature_engineering_stock.py).
  - Đối với các cổ phiếu khác (TCB, VCB, CTG): Sử dụng các chỉ số giá cơ bản kết hợp tỷ lệ thay đổi giá và tỷ lệ thay đổi khối lượng giao dịch (`volume_change_pct`).
- **Chuẩn hóa dữ liệu:** Sử dụng `MinMaxScaler` để đưa các đặc trưng về khoảng $[0, 1]$. Việc chuẩn hóa được thực hiện trên từng cửa sổ trượt (sliding window sequences) để tránh hiện tượng rò rỉ thông tin từ tương lai.
- **Ràng buộc huấn luyện:** Mô hình chỉ huấn luyện trên các ngày giao dịch thực tế của sàn HOSE, không tạo thêm dữ liệu giả cho ngày nghỉ hay cuối tuần. Để tránh hiện tượng trượt giá lịch sử quá xa đối với các ngân hàng có dữ liệu dài hạn, mô hình giới hạn huấn luyện trong 750 phiên giao dịch gần nhất (khoảng 3 năm hoạt động gần đây).
- **Cấu trúc mạng LSTM:**
  - Đối với các bộ dữ liệu nhỏ (dưới 200 mẫu): Sử dụng cấu trúc mạng đơn giản gồm 1 lớp LSTM (64 units), 1 lớp ẩn Dense (32 units) và lớp đầu ra để tránh quá khớp (overfitting).
  - Đối với các bộ dữ liệu lớn (VCB, CTG, TCB): Sử dụng cấu trúc xếp chồng (stacked LSTM) gồm 2 lớp LSTM (128 units và 64 units), xen kẽ các lớp Dropout (tỷ lệ 0.2) để điều hòa trọng số, nối tiếp bởi lớp Dense ẩn và lớp Dense đầu ra có kích thước bằng 5 (tương ứng dự báo từ T+1 đến T+5).
- **So sánh Baseline:** Mô hình được đối chiếu trực tiếp với mô hình baseline truyền thống là **ARIMA** trong [baseline_arima.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/models/baseline_arima.py). Ràng buộc nghiệm thu bắt buộc là sai số bình phương trung bình chân phương (RMSE) của mô hình LSTM trên tập kiểm thử phải thấp hơn mô hình ARIMA.
- **Kết quả thực tế:** Mô hình LSTM đạt hiệu năng vượt trội so với ARIMA trên tất cả các mã cổ phiếu. Ví dụ, đối với BID, LSTM đạt RMSE là **0.9167** so với ARIMA là **1.1696**; đối với TCB, LSTM đạt RMSE là **1.3725** so với ARIMA là **9.4864**.

### 4.2 Mô Hình Gom Cụm Chiến Lược Hoạt Động Ngân Hàng (K-Means & PCA)
Thuật toán học máy không giám sát được triển khai trong tệp [train_kmeans.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/models/train_kmeans.py) nhằm nhóm các ngân hàng thương mại tại Việt Nam dựa trên tương đồng về các chỉ số tài chính CAMELS.

- **Tiền xử lý dữ liệu:** Chuẩn hóa toàn bộ 47 chỉ số tài chính bằng `StandardScaler` để đưa phân phối về trung bình bằng 0 và độ lệch chuẩn bằng 1 bằng cách sử dụng các hàm trong [feature_engineering_bank.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/models/feature_engineering_bank.py).
- **Giảm chiều dữ liệu bằng PCA (Principal Component Analysis):** Do dữ liệu tài chính có số lượng biến rất lớn (47 cột) và có hiện tượng đa cộng tuyến cao giữa các chỉ số hiệu suất, thuật toán PCA được áp dụng để giảm chiều không gian đặc trưng. Dự án lựa chọn số lượng thành phần chính sao cho tổng phương sai giải thích tích lũy (cumulative explained variance) đạt tối thiểu **80%**. Kết quả thực tế giữ lại **3 thành phần chính** (giải thích **85.92%** lượng thông tin gốc).
- **Lựa chọn số cụm K tối ưu:**
  - *Phương pháp cùi chỏ (Elbow Method):* Vẽ biểu đồ tổng bình phương khoảng cách trong cụm (WCSS) theo số cụm K và tìm điểm uốn.
  - *Phân tích hệ số Silhouette:* Đánh giá độ tương đồng của một điểm với cụm của nó so với các cụm khác. Điểm số Silhouette lớn nhất tại $K=3$ xác định số lượng phân cụm tối ưu.
- **Đánh giá mô hình:** Phân cụm chính thức tại $K=3$ đạt điểm Silhouette Score là **0.3222** và chỉ số Davies-Bouldin đạt **0.9746**, xác nhận các cụm được phân tách rõ ràng trên không gian giảm chiều.
- **Diễn giải nghiệp vụ của 3 cụm:**
  - **Cụm 0 (13 ngân hàng - TMCP quy mô nhỏ và vừa):** Có biên lãi ròng NIM tương đối tốt nhưng tỷ lệ chi phí trên thu nhập CIR cao do chưa tối ưu được hiệu quả vận hành theo quy mô.
  - **Cụm 1 (24 ngân hàng - Trụ cột hệ thống):** Gồm các ngân hàng lớn nhất hệ thống như VCB, BID, CTG, TCB, ACB, MBB. Nhóm này có quy mô tài sản và tiền gửi lớn vượt trội, tỷ lệ sinh lời ROA/ROE ổn định và duy trì biên lãi ròng NIM bền vững.
  - **Cụm 2 (2 ngân hàng - Ngân hàng nước ngoài/Liên doanh đặc thù):** Có đặc trưng quy mô tín dụng nhỏ nhưng tỷ lệ an toàn vốn cực kỳ cao và tỷ lệ nợ xấu gần như bằng không.
  - *Lưu ý:* Quá trình phân cụm loại bỏ 6 ngân hàng ngoại lai đặc thù do có cấu trúc tài sản dị biệt bao gồm CB, VBSP, DAB, GPB, WEB, MDB.

### 4.3 Mô Hình Phân Loại Cảnh Báo Sớm Rủi Ro Nợ Xấu (Random Forest)
Mô hình phân loại có giám sát được triển khai trong tệp [train_random_forest.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/models/train_random_forest.py) để phân loại khả năng một ngân hàng rơi vào nhóm rủi ro tài chính cao.

- **Nhãn mục tiêu (Target Variable):** Tạo biến nhị phân `risk_label` nhận giá trị **1** nếu tỷ lệ nợ xấu (`npl_ratio`) của ngân hàng tại năm đó lớn hơn hoặc bằng **3%** (ngưỡng cảnh báo đỏ theo quy định của Ngân hàng Nhà nước), và nhận giá trị **0** nếu nhỏ hơn 3%.
- **Phân tách tập dữ liệu (Train/Test Split):** Không sử dụng phương pháp chia ngẫu nhiên thông thường để tránh rò rỉ dữ liệu chuỗi thời gian (data leakage). Dự án sử dụng phương pháp phân tách theo mốc thời gian: Huấn luyện trên toàn bộ dữ liệu từ năm 2021 trở về trước, và kiểm thử trên toàn bộ dữ liệu của năm 2022.
- **Ràng buộc chấp nhận nghiêm ngặt:** Do mục tiêu là phát hiện sớm rủi ro tín dụng để ngăn chặn tổn thất tài chính, mô hình bắt buộc phải đạt:
  - Chỉ số AUC-ROC lớn hơn **0.80**.
  - Độ nhạy (Recall) đối với lớp Rủi ro cao (`risk_label = 1`) lớn hơn hoặc bằng **85%**. Điều này đảm bảo hệ thống không bỏ sót các trường hợp ngân hàng thực tế có nợ xấu cao nhưng lại dự báo là an toàn.
- **So sánh Baseline:** Mô hình Random Forest được đối chiếu với baseline là mô hình Hồi quy Logistic (Logistic Regression) trong [baseline_logistic.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/models/baseline_logistic.py).
- **Kết quả huấn luyện thực tế:**
  - Mô hình Random Forest đạt điểm **AUC-ROC là 0.9370** (vượt xa yêu cầu 0.80).
  - Bằng cách điều chỉnh ngưỡng quyết định (decision threshold) tối ưu về mức **0.2822**, mô hình đạt chỉ số **Recall cho lớp Rủi ro cao là 85.71%**, hoàn thành chỉ tiêu nghiệp vụ đề ra.
- **Xác định tầm quan trọng đặc trưng (Feature Importance):**
  1. `llp_ratio` (Độ quan trọng **21.05%**): Tỷ lệ trích lập dự phòng rủi ro tín dụng là biến số quan trọng nhất, phản ánh trực tiếp chất lượng danh mục cho vay.
  2. `roe` (Độ quan trọng **11.49%**) và `roa` (Độ quan trọng **9.85%**): Sự sụt giảm trong hiệu quả sinh lời là dấu hiệu tiền đề của suy yếu tài chính.
  3. `cir` (Độ quan trọng **11.03%**): Tỷ lệ chi phí trên thu nhập cao thể hiện năng lực quản lý yếu kém, làm giảm khả năng tự phòng thủ của ngân hàng trước các cú sốc nợ xấu.

---

## 5. Trực Quan Hóa Dữ Liệu và Hệ Thống Báo Cáo (Business Intelligence)

Hệ thống báo cáo được phát triển qua hai giai đoạn để đảm bảo tính chính xác về mặt nghiệp vụ trước khi triển khai trực tuyến. Đặc tả chi tiết về hệ thống báo cáo được ghi nhận tại [dashboard-spec.md](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/docs/dashboard-spec.md).

### 5.1 Kiểm Định Cục Bộ (Local Prototyping)
Trước khi kết nối trực tuyến với đám mây, các đồ thị phân tích được thiết kế và kiểm tra cục bộ bằng thư viện Python Seaborn và Matplotlib thông qua tệp [local/generate_dashboard_plots.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/models/local/generate_dashboard_plots.py). Các đồ thị này bao gồm phân phối biến thế, ma trận tương quan CAMELS, biểu đồ gom cụm PCA và biểu đồ tầm quan trọng đặc trưng. Kết quả được lưu tại thư mục hình ảnh để phục vụ báo cáo khoa học.

### 5.2 Bảng Điều Khiển Trực Tuyến Looker Studio
Sau khi kiểm định dữ liệu trên BigQuery, hệ thống được kết nối trực tiếp với Looker Studio thông qua cổng kết nối gốc (Native BigQuery Connector), phân chia thành 3 trang báo cáo tương ứng với các mục tiêu nghiên cứu:

1. **Trang 1: Biến động Thị trường (Market Movement Dashboard)**
   - *Mục tiêu:* Hỗ trợ phân tích biến động giá cổ phiếu ngắn hạn và theo dõi dòng tiền lớn.
   - *Biểu đồ chính:* Đồ thị đường so sánh giá đóng cửa thực tế (`close_price`) và giá dự báo từ mô hình LSTM trong 5 ngày kế tiếp. Biểu đồ cột thể hiện giá trị giao dịch ròng của khối ngoại (`foreign_net_value`) và tự doanh (`prop_net_value`) theo thời gian.
   - *Bộ lọc tương tác:* Lọc theo mã cổ phiếu (`ticker`), khoảng thời gian giao dịch.
2. **Trang 2: Hồ sơ Hệ thống Ngân hàng (Bank Profiling Dashboard)**
   - *Mục tiêu:* Nhận diện cấu trúc tài chính và định vị chiến lược của từng ngân hàng.
   - *Biểu đồ chính:* Đồ thị phân tán (Scatter Plot) biểu diễn các ngân hàng trên không gian 2 chiều của các thành phần chính PCA, tô màu theo nhãn cụm K-Means. Đồ thị mạng nhện (Radar Chart) biểu diễn giá trị trung bình của các chỉ số CAMELS cốt lõi (NIM, CIR, ROE, LTA, ETA) của từng cụm để làm nổi bật đặc trưng hoạt động.
   - *Bộ lọc tương tác:* Lọc theo cụm (`cluster_id`), loại hình ngân hàng (SOCB, JSCB, FOCB), và tên ngân hàng.
3. **Trang 3: Giám sát Rủi ro Tín dụng (Risk Monitoring Dashboard)**
   - *Mục tiêu:* Đưa ra các cảnh báo sớm về chất lượng tài sản và sức khỏe vốn.
   - *Biểu đồ chính:* Bảng danh sách ngân hàng được sắp xếp theo mức độ rủi ro, tô màu đỏ cảnh báo đối với các đơn vị được mô hình Random Forest phân loại thuộc nhóm Rủi ro cao hoặc có xác suất dự báo nợ xấu vượt ngưỡng quyết định. Biểu đồ đường xu hướng tỷ lệ nợ xấu (`npl_ratio`) qua các năm của từng ngân hàng để nhận diện tốc độ suy thoái tài sản.
   - *Bộ lọc tương tác:* Lọc theo phân loại rủi ro (An toàn / Rủi ro cao), tên ngân hàng, và năm báo cáo.

Ngoài ra, dự án còn đi kèm một giao diện ứng dụng web Streamlit cục bộ được xây dựng trong [app.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/dashboard/app.py) để người dùng có thể chạy trực quan hóa và kiểm tra kết quả ngay trên máy tính cá nhân.

---

## 6. Hướng Dẫn Thiết Lập và Chạy Hệ Thống

Để vận hành toàn bộ hệ thống từ bước khởi tạo cơ sở dữ liệu đến chạy huấn luyện các mô hình học máy, người dùng thực hiện theo các bước chi tiết dưới đây. Các cấu hình liên quan đến môi trường được hướng dẫn chi tiết tại [env-config.md](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/docs/env-config.md).

### 6.1 Môi Trường và Các Thư Viện Phụ Thuộc
Dự án yêu cầu cài đặt phiên bản Python từ 3.9 trở lên (khuyến nghị sử dụng Python 3.9 hoặc 3.10 để đảm bảo tính tương thích tốt nhất với thư viện TensorFlow).

Các thư viện cốt lõi được định nghĩa trong [requirements.txt](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/requirements.txt) bao gồm:
- `pandas` và `openpyxl`: Phục vụ trích xuất và biến đổi dữ liệu bảng tính.
- `google-cloud-bigquery` và `pandas-gbq`: Kết nối và nạp dữ liệu lên Google Cloud BigQuery.
- `scikit-learn`: Triển khai các mô hình học máy cổ điển (K-Means, PCA, Random Forest, Logistic Regression).
- `tensorflow`: Huấn luyện mạng neural tuần hoàn LSTM.
- `python-dotenv`: Quản lý các biến môi trường và thông tin cấu hình bảo mật.

### 6.2 Thiết Lập Biến Môi Trường (.env)
Người dùng cần tạo một tệp `.env` tại thư mục gốc của dự án dựa trên tệp mẫu `.env.example`. Nội dung tệp `.env` cấu hình các thông số sau:

```bash
# Đường dẫn tuyệt đối đến tệp JSON chứa khóa bảo mật của tài khoản dịch vụ GCP
GOOGLE_APPLICATION_CREDENTIALS="D:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/vn-banking-dwh-analytics-67f213ad7317.json"

# Mã dự án Google Cloud Platform
GCP_PROJECT_ID="vn-banking-dwh-analytics"

# Tên Dataset lưu trữ trên BigQuery (mặc định: financial_dwh)
BQ_DATASET_ID="financial_dwh"

# Tên bảng lưu trữ kết quả đầu ra của các mô hình học máy
BQ_PREDICTIONS_TABLE="fact_model_predictions"

# Đường dẫn lưu trữ dữ liệu nguồn và kết quả trung gian
RAW_DATA_PATH="data/raw"
PROCESSED_DATA_PATH="data/processed"
MODEL_ARTIFACT_PATH="reports/models"
```

*Lưu ý an toàn:* Tuyệt đối không đưa tệp `.env` hoặc tệp khóa JSON bảo mật (`*.json`) lên các kho lưu trữ mã nguồn công cộng như GitHub để tránh rò rỉ thông tin tài khoản đám mây. Các tệp này đã được cấu hình trong tệp `.gitignore` để hệ thống tự động bỏ qua khi commit.

### 6.3 Hướng Dẫn Cấp Quyền Tài Khoản Dịch Vụ Trên Google Cloud
Để mã nguồn Python có thể tương tác với Google BigQuery, người quản trị đám mây cần thực hiện:
1. Truy cập vào Google Cloud Console, điều hướng đến phần **IAM & Admin** -> **Service Accounts**.
2. Tạo một tài khoản dịch vụ mới (ví dụ: `bq-loader-service-account`).
3. Gán hai vai trò (Roles) bắt buộc cho tài khoản này:
   - **BigQuery Data Editor:** Cho phép thực hiện các thao tác ghi dữ liệu, tạo bảng và chỉnh sửa cấu trúc bảng.
   - **BigQuery Job User:** Cho phép khởi chạy các tiến trình truy vấn và nạp dữ liệu.
4. Tạo khóa bảo mật mới cho tài khoản dịch vụ này dưới định dạng **JSON** và tải về máy tính cá nhân. Lưu tệp này vào thư mục dự án và khai báo đường dẫn đầy đủ trong trường `GOOGLE_APPLICATION_CREDENTIALS` của tệp `.env`.

### 6.4 Thứ Tự Chạy Các Script Khởi Tạo và Nạp Dữ Liệu
Chạy lần lượt các lệnh sau trong môi trường terminal của Python (đã kích hoạt ảo hóa `venv`):

1. **Khởi tạo cấu trúc Kho dữ liệu trống:**
   ```bash
   python -m src.etl.provision_schema
   ```
   *Chức năng:* Lệnh này sẽ kết nối với BigQuery và tạo ra toàn bộ 10 bảng (5 bảng Dim và 5 bảng Fact) với cấu trúc phân vùng và phân cụm chuẩn hóa.

2. **Nạp dữ liệu cho các bảng chiều:**
   ```bash
   python -m src.etl.populate_dim_date
   python -m src.etl.populate_dim_stock
   python -m src.etl.populate_dim_bank
   python -m src.etl.populate_dim_trading_session
   ```
   *Chức năng:* Các lệnh này sẽ chuẩn hóa và nạp dữ liệu nền tảng cho các bảng chiều tương ứng. Tệp `populate_dim_bank.py` sẽ tự động xử lý logic SCD Type 2 cho các ngân hàng.

3. **Chạy biến đổi dữ liệu thực tế (Fact):**
   ```bash
   python -m src.etl.load_price_history
   python -m src.etl.load_foreign_trading
   python -m src.etl.load_proprietary_trading
   python -m src.etl.load_order_stats
   python -m src.etl.load_bank_performance
   ```
   *Chức năng:* Các tệp này sẽ đọc dữ liệu thô từ thư mục `data/raw/`, thực hiện các bước làm sạch, ép kiểu và nội suy các giá trị thiếu theo quy tắc nghiệp vụ, sau đó ghi các tệp kết quả sạch dạng CSV vào thư mục `data/processed/`.

4. **Nạp dữ liệu thực tế lên BigQuery:**
   ```bash
   python -m src.etl.load_to_bigquery
   ```
   *Chức năng:* Đọc toàn bộ các tệp CSV sạch trong `data/processed/` và thực hiện câu lệnh `MERGE` SQL để cập nhật hoặc chèn mới dữ liệu vào các bảng thực tế tương ứng trên BigQuery một cách an toàn.

5. **Kiểm tra tính toàn vẹn và chất lượng dữ liệu:**
   ```bash
   python -m src.etl.validate_integrity
   ```
   *Chức năng:* Thực hiện kiểm tra chéo toàn bộ khóa ngoại giữa các bảng Fact và Dim (đảm bảo mọi `date_key` trong bảng Fact đều tồn tại trong `dim_date`), đồng thời kiểm định các quy tắc nghiệp vụ dữ liệu tài chính. Nếu có bất kỳ lỗi vi phạm toàn vẹn nào, chương trình sẽ báo lỗi và dừng tiến trình.

### 6.5 Thứ Tự Chạy Huấn Luyện Các Mô Hình Học Máy
Sau khi dữ liệu đã được nạp và kiểm định thành công trên Kho dữ liệu BigQuery, chạy các lệnh sau để bắt đầu quy trình phân tích nâng cao:

1. **Huấn luyện mô hình chuỗi thời gian LSTM:**
   ```bash
   python -m src.models.train_lstm
   ```
   *Chức năng:* Lấy dữ liệu giá và dòng tiền từ BigQuery, xây dựng đặc trưng trễ, huấn luyện mô hình mạng LSTM cho từng cổ phiếu (BID, TCB, VCB, CTG), lưu tệp trọng số mô hình `.keras` và bộ chuẩn hóa `.pkl` vào thư mục lưu trữ, so sánh sai số với baseline ARIMA, sau đó xuất kết quả dự báo T+1 đến T+5 vào bảng `fact_model_predictions` trên BigQuery.

2. **Huấn luyện mô hình gom cụm K-Means & PCA:**
   ```bash
   python -m src.models.train_kmeans
   ```
   *Chức năng:* Lấy dữ liệu chỉ số tài chính CAMELS của các ngân hàng từ BigQuery, áp dụng chuẩn hóa, thực hiện giảm chiều PCA, chạy thuật toán phân cụm K-Means, lưu các biểu đồ phân tích cùi chỏ và Silhouette vào thư mục báo cáo, và ghi nhãn phân cụm vào bảng `bank_cluster_assignments` trên BigQuery.

3. **Huấn luyện mô hình phân loại rủi ro Random Forest:**
   ```bash
   python -m src.models.train_random_forest
   ```
   *Chức năng:* Lấy dữ liệu CAMELS từ BigQuery, gán nhãn rủi ro dựa trên ngưỡng tỷ lệ nợ xấu 3%, chia tập huấn luyện theo mốc thời gian, huấn luyện mô hình Random Forest, tính toán và tối ưu hóa ngưỡng quyết định để đạt chỉ số Recall tối thiểu 85%, lưu biểu đồ tầm quan trọng đặc trưng, và ghi nhận kết quả phân loại rủi ro vào bảng `bank_risk_predictions` trên BigQuery.

---

## 7. Quy Chuẩn Lập Trình và Bảo Mật Hệ Thống

Để dự án hoạt động ổn định và dễ bảo trì trong môi trường sản xuất thực tế, toàn bộ mã nguồn phải tuân thủ nghiêm ngặt các quy chuẩn kỹ thuật được định nghĩa tại [DEVELOPMENT.md](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/DEVELOPMENT.md):

- **Ghi nhật ký hệ thống (Logging):** Tuyệt đối không sử dụng hàm `print()` thông thường trong các tệp tin sản xuất thuộc thư mục `src/etl/` và `src/models/`. Hệ thống bắt buộc phải sử dụng thư viện logging chuẩn hóa được cấu hình trong [logger.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/utils/logger.py). Điều này giúp phân loại thông tin log theo các cấp độ `INFO`, `WARNING`, `ERROR`, hỗ trợ giám sát và gỡ lỗi từ xa một cách khoa học.
- **Bảo mật thông tin cấu hình:** Không được nhúng cứng (hardcode) các thông tin nhạy cảm như ID dự án GCP, tên Dataset, hoặc nội dung của tệp khóa bảo mật JSON vào trong mã nguồn. Mọi cấu hình phải được nạp động từ biến môi trường thông qua tệp cấu hình trung tâm [config.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/utils/config.py).
- **Tính bất biến của dữ liệu chuỗi thời gian:** Trong quá trình chuẩn bị dữ liệu đầu vào cho mô hình LSTM, tuyệt đối không sử dụng phương pháp nội suy tiếp diễn (forward-fill) để tạo ra các dòng dữ liệu nhân tạo cho các ngày nghỉ hoặc ngày lễ giao dịch. Dữ liệu huấn luyện mô hình bắt buộc phải phản ánh chính xác các phiên giao dịch thực tế của sàn HOSE để tránh làm sai lệch mô hình dự báo chuỗi thời gian.
