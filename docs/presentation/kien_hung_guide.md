# 🎙️ Hướng Dẫn Thuyết Trình Chi Tiết Cho Kiên Hưng (Project Manager & Data Ops)
## Kho Dữ Liệu & Nền Tảng Phân Tích Học Máy Hệ Thống Ngân Hàng Việt Nam
### Bộ môn Hệ thống Thông tin · Trường Đại học Công nghệ Kỹ thuật Thành phố Hồ Chí Minh

Tài liệu này là kịch bản nói chi tiết dưới dạng **bullet points triển khai ý** dành riêng cho thành viên **Đỗ Kiến Hưng** (PM & Data Ops), đi kèm giải thích kỹ thuật chuyên sâu và liên kết trực tiếp tới các tài liệu đặc tả dự án để phục vụ ôn tập trước buổi thuyết trình báo cáo đề tài.

---

## 📋 Mục lục
1. [Luồng đi của Dữ liệu (End-to-End Data Flow)](#1-lu%E1%BB%93ng-%C4%91i-c%E1%BB%A7a-d%E1%BB%AF-li%E1%BB%87u-end-to-end-data-flow)
2. [Cấu trúc Star Schema & Ánh xạ Metric](#2-c%E1%BA%A5u-tr%C3%BAc-star-schema--%C3%A1nh-x%E1%BA%A1-metric)
3. [Các Kỹ thuật DWH áp dụng (DWH Optimizations)](#3-c%C3%A1c-k%E1%BB%B9-thu%E1%BA%ADt-dwh-%C3%A1p-d%E1%BB%A5ng-dwh-optimizations)
4. [Tích hợp Looker Studio & Blend Data](#4-t%C3%ADch-h%E1%BB%A3p-looker-studio--blend-data)
5. [Kịch bản nói từng Slide (Slide-by-Slide Talking Points)](#5-k%E1%BB%8Bch-b%E1%BB%8Bn-n%C3%B3i-t%E1%BB%ABng-slide-slide-by-slide-talking-points)

---

## 1. Luồng đi của Dữ liệu (End-to-End Data Flow)
*Hiểu rõ sơ đồ này giúp chứng minh vai trò PM/Data Ops điều phối hệ thống vận hành trơn tru.*

*   **Ingestion (Nạp liệu)**: 
    *   Đọc dữ liệu thô từ các Excel sheets của doanh nghiệp đặt tại `data/raw/` (xem [data/README.md](../data/README.md)).
    *   Mã nguồn chi tiết nằm tại module [src/etl/](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/project2/vn-banking-dwh-analytics/src/etl).
*   **Staging & Clean (Làm sạch Cục bộ)**:
    *   Xử lý ép kiểu dữ liệu tài chính, điền khuyết bằng thuật toán **Median Imputation** (trung vị) theo chuẩn quy định tại Mục 5 của [AGENTS.md](../../AGENTS.md).
    *   Xuất ra tệp tin trung gian `data/processed/*.csv` (xem [data_specification.md](../data/data_specification.md) để biết dung lượng và cấu trúc chi tiết từng file).
*   **Data Quality Check (Kiểm tra chất lượng)**:
    *   Chạy script [validate_integrity.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/project2/vn-banking-dwh-analytics/src/etl/validate_integrity.py) để kiểm tra toàn vẹn tham chiếu khóa ngoại và các quy tắc từ `DQ-01` đến `DQ-06` trong [data-dictionary.md](../data-dictionary.md).
*   **Cloud Warehousing (Lưu trữ BigQuery)**:
    *   Nạp dữ liệu lũy kế vào Google BigQuery DWH thông qua API client.
    *   Xây dựng mô hình hình sao (Star Schema) tối ưu hóa truy vấn OLAP (xem chi tiết thiết kế tại [star-schema.md](../star-schema.md)).
*   **Analytics & AI Write-back**:
    *   Các mô hình AI/ML (LSTM, K-Means, Random Forest) kéo dữ liệu từ các bảng Fact trên Cloud, chạy huấn luyện, rồi đẩy kết quả dự báo ngược về các bảng kết quả BigQuery.
*   **BI Dashboards**:
    *   Looker Studio kết nối trực tiếp vào BigQuery DWH để vẽ các báo cáo trực quan cho ban lãnh đạo.

---

## 2. Cấu trúc Star Schema & Ánh xạ Metric
*Anh cần giải thích được ý nghĩa nghiệp vụ của từng bảng và các metric tài chính nằm ở đâu.*

### 2.1 Hệ thống Dimension Tables (Bảng chiều - Ngữ cảnh phân tích)
*   **`dim_date`** (Ngày tháng):
    *   *Khóa chính*: `date_key` (dạng `INT64` định dạng `YYYYMMDD`).
    *   *Vai trò*: Giúp nhóm dữ liệu theo năm, quý, tháng nhanh chóng mà không cần chạy hàm cắt chuỗi trên BigQuery.
*   **`dim_stock`** (Cổ phiếu):
    *   *Khóa chính*: `stock_key`. Lưu trữ thông tin 4 mã ngân hàng trọng tâm (`BID`, `TCB`, `VCB`, `CTG`).
*   **`dim_bank`** (Danh mục Ngân hàng):
    *   *Khóa chính*: `bank_key`. Chứa mã loại hình ngân hàng thương mại Việt Nam (`bank_type` gồm TMCP Nhà nước, TMCP tư nhân, Ngân hàng ngoại).
    *   *Chỉ số đặc biệt*: Cột vốn điều lệ `charter_capital` (FLOAT64) được lưu trữ tại đây theo dạng lịch sử thay đổi để phục vụ phân tích quy mô vốn.
*   **`dim_trading_session`** (Phiên giao dịch):
    *   *Khóa chính*: `session_key`. Định vị 4 khung giờ khớp lệnh HOSE: ATO, Khớp lệnh liên tục sáng, Khớp lệnh liên tục chiều, ATC.
*   **`dim_audit`** (Nhật ký kiểm toán):
    *   *Khóa chính*: `audit_key`. Đăng ký mã chạy tự động `run_id`, trạng thái chạy `status` giúp kiểm soát lỗi vận hành.

### 2.2 Hệ thống Fact Tables (Bảng sự kiện - Số liệu đo lường)
*   **`fact_price_history`** (Lịch sử giá cổ phiếu):
    *   *Metrics*: `open_price`, `high_price`, `low_price`, `close_price` (Giá đóng cửa), `trading_volume`.
    *   *Liên hệ mô hình*: `close_price` là biến mục tiêu cho mô hình chuỗi thời gian LSTM (xem [ml-spec.md](../ml-spec.md) Section 4.1).
*   **`fact_foreign_trading`** (Giao dịch khối ngoại):
    *   *Metrics*: `foreign_buy_volume`, `foreign_sell_volume`, `foreign_net_volume` (Khối lượng mua ròng), `foreign_net_value` (Giá trị mua ròng).
    *   *Liên hệ câu hỏi nghiên cứu*: `foreign_net_volume` giúp trả lời câu hỏi **Q1** trong [RESULT.md](../../RESULT.md) về tác động của dòng tiền ngoại đến giá BID.
*   **`fact_proprietary_trading`** (Giao dịch tự doanh):
    *   *Metrics*: `prop_net_volume` (Tự doanh mua ròng), `prop_net_value`.
    *   *Ý nghĩa*: Phản ánh xu hướng dòng tiền của các định chế tài chính trong nước.
*   **`fact_order_stats`** (Thống kê đặt lệnh):
    *   *Metrics*: `total_buy_orders`, `total_sell_orders`, `matched_volume` (Khối lượng khớp lệnh).
*   **`fact_bank_performance`** (Hiệu suất tài chính ngân hàng):
    *   *Metrics tài chính vĩ mô*: `total_assets` (Tổng tài sản), `total_deposits` (Tiền gửi khách hàng), `total_loans` (Dư nợ cho vay), `total_equity` (Vốn chủ sở hữu).
    *   *Ánh xạ chỉ số CAMELS chuẩn NetSuite & VCBS* (xem công thức và giải nghĩa chi tiết tại [RESULT.md](../../RESULT.md)):
        *   `roa` (Tỷ suất sinh lời trên tài sản) & `roe` (Tỷ suất sinh lời trên vốn CSH) $\rightarrow$ **NetSuite Profitability KPIs**.
        *   `eta` (Vốn CSH / Tổng tài sản) & `etd` (Vốn CSH / Tiền gửi) $\rightarrow$ **NetSuite Capital Adequacy KPIs**.
        *   `nim` (Biên lãi ròng) $\rightarrow$ **VCBS Earnings KPI**.
        *   `cir` (Tỷ lệ chi phí trên thu nhập) $\rightarrow$ **VCBS Management Efficiency KPI**.
        *   `ltd` (Dư nợ / Tiền gửi huy động) $\rightarrow$ **VCBS Liquidity KPI**.
        *   `npl_ratio` (Tỷ lệ nợ xấu) & `llp_ratio` (Tỷ lệ trích lập dự phòng) $\rightarrow$ **VCBS Asset Quality KPIs**.

### 2.3 Các bảng kết quả Machine Learning (ML Output Tables)
*   **`bank_cluster_assignments`** (Phân cụm K-Means): Lưu nhãn cụm `cluster_id` của 39 ngân hàng sau khi chạy K-Means và loại bỏ outliers (trả lời câu hỏi **Q4**).
*   **`bank_risk_predictions`** (Phân loại rủi ro Random Forest): Lưu nhãn rủi ro `risk_label` (High Risk vs Healthy) và xác suất nợ xấu `risk_probability` (trả lời câu hỏi **Q3**).
*   **`fact_model_predictions`** (Dự báo LSTM): Lưu giá dự kiến từ T+1 đến T+5 của các cổ phiếu (trả lời câu hỏi **Q1** & **Q2**).

---

## 3. Các Kỹ thuật DWH áp dụng (DWH Optimizations)
*Đây là phần ghi điểm cực kỳ quan trọng chứng minh năng lực kỹ thuật Data Ops của anh.*

*   **Phân vùng theo dải thời gian (Partitioning)**:
    *   *Cách thực hiện*: Sử dụng câu lệnh `PARTITION BY RANGE_BUCKET(date_key, GENERATE_ARRAY(20020101, 20301231, 10000))` trong file DDL [bigquery_schema.sql](../../sql/bigquery_schema.sql).
    *   *Giải thích cơ chế*: Dữ liệu trong BigQuery được phân nhỏ vật lý thành các phân vùng dựa trên năm của ngày giao dịch (`date_key` dạng YYYYMMDD chia theo dải khoảng cách 10000). Khi người dùng chạy SQL lọc dữ liệu của năm 2024, BigQuery chỉ đọc phân vùng năm 2024, bỏ qua hoàn toàn dữ liệu từ năm 2002-2023. Tiết kiệm **90% chi phí quét dữ liệu**.
*   **Gom cụm tối ưu hóa liên kết (Clustering)**:
    *   *Cách thực hiện*: Câu lệnh `CLUSTER BY stock_key` (cho cổ phiếu) hoặc `CLUSTER BY bank_key` (cho ngân hàng) trong DDL.
    *   *Giải thích cơ chế*: Dữ liệu có cùng mã khóa ngoại được sắp xếp vật lý nằm kề nhau trên ổ cứng Cloud. Khi thực hiện lệnh `JOIN` giữa bảng Fact và Dimension (ví dụ: lấy thông tin loại hình ngân hàng từ `dim_bank` khớp với hiệu suất tài chính), BigQuery truy xuất dữ liệu cực kỳ nhanh chóng.
*   **Lưu vết lịch sử thay đổi SCD Type 2 (Slowly Changing Dimension)**:
    *   *Cách thực hiện*: Bảng `dim_bank` bổ sung 3 trường: `valid_from` (Ngày hiệu lực), `valid_to` (Ngày hết hiệu lực), `is_current` (BOOLEAN).
    *   *Giải thích cơ chế*: Nếu ngân hàng ACB tăng vốn điều lệ từ 30,000 tỷ lên 40,000 tỷ vào năm 2024, hệ thống không ghi đè trực tiếp lên dòng cũ. Nó sẽ đặt `valid_to` của dòng cũ là ngày tăng vốn, set `is_current = FALSE`, đồng thời thêm một dòng mới với vốn điều lệ 40,000 tỷ và `is_current = TRUE`. Kỹ thuật này giúp mô hình ML khi phân tích dữ liệu quá khứ (ví dụ năm 2020) vẫn lấy đúng vốn điều lệ của năm 2020 là 30,000 tỷ, không bị sai lệch dữ liệu lịch sử.
*   **Auditing & Metadata Tracking (Theo dõi nhật ký hệ thống)**:
    *   *Cách thực hiện*: Mọi bảng Dim và Fact đều có 4 trường hệ thống: `audit_key` (trỏ đến `dim_audit`), `_created_at`, `_updated_at`, và `_source_file`.
    *   *Giải thích cơ chế*: Hỗ trợ khả năng truy vết lỗi (Data Lineage). Khi một số liệu trên Dashboard bị nghi ngờ sai lệch, Data Ops chỉ cần truy vấn ngược cột `_source_file` để biết dòng dữ liệu đó được trích xuất từ file Excel nào tại Local và cột `_created_at` để biết thời điểm xảy ra lỗi nạp liệu.
*   **Idempotent Load via MERGE (Nạp dữ liệu lũy kế)**:
    *   *Cách thực hiện*: Pipeline ETL dùng câu lệnh `MERGE INTO ... USING ... ON (primary_key) WHEN MATCHED THEN UPDATE WHEN NOT MATCHED THEN INSERT`.
    *   *Giải thích cơ chế*: Nếu chạy lại script ETL nhiều lần trên một tập dữ liệu, hệ thống tự động nhận diện các bản ghi trùng lặp và ghi đè cập nhật thay vì chèn trùng dòng. Đảm bảo tính nhất quán của Kho dữ liệu (Idempotency).

---

## 4. Tích hợp Looker Studio & Blend Data
*Cách anh kết nối và thiết lập nguồn dữ liệu hợp nhất để phục vụ trực quan hóa.*

*   **Kết nối qua BigQuery Native Connector**:
    *   Looker Studio sử dụng tài khoản IAM có quyền `BigQuery Data Viewer` và `BigQuery User` để kết nối trực tiếp vào tập dữ liệu `financial_dwh` của dự án `vn-banking-dwh-analytics`.
*   **Kỹ thuật Blend Data (Hợp nhất dữ liệu)**:
    Looker Studio không thể JOIN trực tiếp các bảng nếu không cấu hình Blend. Anh đã cấu hình 3 luồng Blend chính sau (xem hướng dẫn chi tiết tại [looker_studio_dashboard_guide.md](../process/looker_studio_dashboard_guide.md)):
    1.  **`blend_market_movement`**:
        *   `fact_price_history` (Left Join) `fact_model_predictions` qua điều kiện: `date_key = base_date_key` AND `stock_key = stock_key`.
        *   Liên kết tiếp với `dim_date` và `dim_stock` để lấy trường hiển thị `full_date` và `ticker`.
        *   *Mục đích*: Vẽ biểu đồ so sánh giá đóng cửa thực tế vs dự báo LSTM.
    2.  **`blend_bank_performance_clusters`**:
        *   `fact_bank_performance` (Left Join) `bank_cluster_assignments` qua `bank_key`.
        *   Liên kết với `dim_bank` và `dim_date`.
        *   *Mục đích*: Phân tích chân dung tài chính CAMELS của các cụm ngân hàng.
    3.  **`blend_risk_predictions_bank`**:
        *   `bank_risk_predictions` (Left Join) `dim_bank` qua `bank_key`.
        *   Liên kết với `dim_date`.
        *   *Mục đích*: Hiển thị danh sách cảnh báo nợ xấu (🚨 High Risk).

---

## 5. Kịch Bản Nói Trình Diễn Trực Tiếp (Live Demo Guide)
*Kịch bản này hướng dẫn anh cách phối hợp thao tác click chuột trên màn hình thực tế (BigQuery, Streamlit, Looker) và nội dung nói tương ứng.*

### 🖥️ Demo Phần 1: Trình diễn hạ tầng Kho dữ liệu trên Google BigQuery Console
*   **Hành động trên màn hình**: 
    1. Trình chiếu tab chứa [Google BigQuery Console](https://console.cloud.google.com/bigquery?project=vn-banking-dwh-analytics).
    2. Click mở rộng dự án `vn-banking-dwh-analytics` -> click mở rộng dataset `financial_dwh`.
    3. Click chọn bảng `dim_bank`, chọn tab **Schema**.
    4. Click chọn bảng `fact_bank_performance`, chọn tab **Details**.
*   **Nội dung nói (Ý chính)**:
    *   *"Kính thưa quý thầy cô, đây là giao diện Kho dữ liệu đám mây thực tế của dự án trên Google BigQuery."*
    *   *"Dữ liệu được tổ chức theo mô hình Star Schema hoàn chỉnh gồm 5 bảng Dimension và 5 bảng Fact cùng 3 bảng ML Output lưu kết quả dự báo."*
    *   *"Ở bảng chiều `dim_bank` này, quý thầy cô có thể thấy chúng tôi quản lý lịch sử SCD Type 2 gồm các cột `valid_from`, `valid_to`, `is_current` và cột vốn điều lệ `charter_capital` để lưu lại vết thay đổi qua các năm mà không bị ghi đè làm mất lịch sử."*
    *   *"Khi chuyển sang tab Details của bảng sự kiện `fact_bank_performance`, hệ thống được cấu hình **Partitioned** (phân vùng) theo năm của trường `date_key` và **Clustered** (gom cụm) theo `bank_key`. Điều này giúp tối ưu hóa chi phí truy vấn và tăng tốc thời gian phản hồi biểu đồ."*
    *   *"Tất cả các bảng đều được chèn các thuộc tính kiểm toán `_created_at`, `_updated_at`, và `_source_file` để đảm bảo Data Lineage (nguồn gốc dữ liệu) thông suốt."*

### 🖥️ Demo Phần 2: Chứng minh tính ổn định của luồng dữ liệu trên Streamlit (DWH System Status)
*   **Hành động trên màn hình**:
    1. Chuyển sang tab chạy ứng dụng Streamlit (`http://localhost:8501`).
    2. Click vào menu phân hệ **DWH System Status** trên thanh điều hướng bên trái.
    3. Trình chiếu bảng thống kê số lượng dòng thực tế (Row counts) và siêu dữ liệu (Metadata).
*   **Nội dung nói (Ý chính)**:
    *   *"Để chứng minh đường ống ETL đã tải dữ liệu thành công từ local lên cloud một cách toàn vẹn, chúng tôi xây dựng phân hệ giám sát DWH System Status ngay trên ứng dụng Streamlit."*
    *   *"Dữ liệu thực tế ghi nhận: Bảng giá cổ phiếu lịch sử `fact_price_history` có 11,835 dòng, bảng hiệu suất tài chính `fact_bank_performance` có 661 dòng cho 45 ngân hàng trong 20 năm, khớp 100% với tệp thô ban đầu."*
    *   *"Hệ thống vận hành cơ chế nạp lũy kế bằng lệnh MERGE (Upsert) và đăng ký lịch sử chạy thông qua bảng `dim_audit` để đảm bảo tính an toàn dữ liệu."*

### 🖥️ Demo Phần 3: Trình diễn cấu hình kết hợp dữ liệu trên Looker Studio (Blend Data Setup)
*   **Hành động trên màn hình**:
    1. Chuyển sang màn hình chỉnh sửa báo cáo [Looker Studio](https://lookerstudio.google.com/).
    2. Click vào menu **Resource** (Tài nguyên) -> chọn **Manage blended data** (Quản lý dữ liệu đã kết hợp).
    3. Click chọn **Edit** tại blend `blend_bank_performance_clusters` để hiển thị sơ đồ liên kết các bảng.
*   **Nội dung nói (Ý chính)**:
    *   *"Từ kho dữ liệu BigQuery, để phục vụ cho các bạn xây dựng Dashboard trực quan, tôi đã tiến hành cấu hình nguồn dữ liệu và thiết lập các mối quan hệ kết hợp (Blend Data) trực tiếp trên Looker Studio."*
    *   *"Quý thầy cô có thể quan sát: luồng hợp nhất `blend_bank_performance_clusters` đang thực hiện phép JOIN ngoài bên trái (Left Outer Join) giữa bảng Fact hiệu suất tài chính ngân hàng và bảng kết quả phân cụm học máy `bank_cluster_assignments` thông qua khóa `bank_key`."*
    *   *"Sau đó, dữ liệu được kết nối tiếp sang bảng `dim_bank` để lấy ra tên ngân hàng và phân loại loại hình."*
    *   *"Việc thiết lập các Blend Data này giúp chuẩn hóa toàn bộ cấu trúc dữ liệu, giải phóng sức lao động khi vẽ biểu đồ và cho phép các bạn phân tích trong nhóm chỉ cần kéo thả là có thể tạo lập biểu đồ ngay lập tức."*
    *   *"Sau đây, tôi xin chuyển quyền trình bày lại cho bạn **Phạm Minh Quân** để đi vào chi tiết kết quả huấn luyện của 3 mô hình học máy trên hạ tầng này."*

---
*Lưu ý dành riêng cho Hưng: Khi thầy cô hỏi về các chỉ số tài chính, anh hãy tự tin chỉ ra rằng tất cả các chỉ số CAMELS như NIM, ROA, ROE, CIR, NPL ratio đều được tính toán chuẩn hóa từ trước ở ETL biến đổi cục bộ và lưu trữ tập trung tại bảng `fact_bank_performance` trên BigQuery.*
