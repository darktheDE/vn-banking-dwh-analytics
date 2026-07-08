# Nhật Ký Triển Khai Refactor Hệ Thống (refactor_log.md)
*Mục đích: Ghi nhận lịch sử thay đổi, kiểm thử và nghiệm thu hệ thống vn-banking-dwh-analytics qua từng giai đoạn refactor.*

---

## Ngày 08 tháng 07 năm 2026: Triển khai Giai đoạn 1 — Chuẩn hóa DWH và Star Schema

### 1. Mục tiêu và Nội dung thay đổi
*   **Mục tiêu**: Giải quyết triệt để phản hồi của giảng viên về việc phân tách làm nhiều bảng Fact thô giao dịch chứng khoán hàng ngày (`fact_price_history`, `fact_foreign_trading`, `fact_proprietary_trading`, và `fact_order_stats`). Đồng thời loại bỏ hoàn toàn dữ liệu giả lập (mock data) để bảo đảm tính chính xác, thực tế 100% của nghiên cứu khoa học.
*   **Hành động**:
    *   Hợp nhất các bảng Fact chứng khoán hàng ngày thành một bảng Fact duy nhất: **`fact_stock_daily_metrics`**.
    *   Bảng Fact hợp nhất này chỉ lưu trữ dữ liệu giá thực tế và khối lượng thực tế (**OHLCV**) cào từ API `vnstock` cho cả 4 ngân hàng mục tiêu (BID, TCB, VCB, CTG).
    *   Xóa bỏ hoàn toàn các cột thưa (cột chứa dữ liệu giả lập có phần lớn giá trị NULL như khối ngoại ròng, tự doanh ròng và các thống kê lệnh mẫu).
    *   Rút gọn cấu trúc Star Schema của kho dữ liệu từ 10 bảng xuống còn **7 bảng** chính thống (5 Dimension và 2 Fact).

### 2. Các tệp đã sửa đổi và tạo mới
*   **DDL Schema**: Sửa đổi [bigquery_schema.sql](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/sql/bigquery_schema.sql) để thay thế định nghĩa 4 bảng Fact cũ bằng bảng Fact hợp nhất `fact_stock_daily_metrics`.
*   **ETL Script**:
    *   Tạo mới [consolidate_stock_metrics.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/etl/consolidate_stock_metrics.py) để trích xuất dữ liệu giá sạch từ `fact_price_history_clean.csv`, định dạng lại kiểu dữ liệu, gán thông số audit và ghi nhận ra tệp `fact_stock_daily_metrics_clean.csv` (11.835 dòng, hoàn toàn không chứa NULL).
    *   Cập nhật [load_to_bigquery.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/etl/load_to_bigquery.py) để thay thế ánh xạ nạp dữ liệu cũ bằng bảng Fact mới.
    *   Cập nhật [recreate_tables.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/scripts/recreate_tables.py) để tự động hóa drop và khởi tạo lại DWH.
    *   Cập nhật [validate_integrity.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/etl/validate_integrity.py) để kiểm định khóa ngoại và chất lượng dữ liệu của bảng Fact mới.
*   **Tài liệu hệ thống**:
    *   Cập nhật [star-schema.md](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/docs/star-schema.md).
    *   Cập nhật [etl-spec.md](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/docs/etl-spec.md).
    *   Cập nhật [data-dictionary.md](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/docs/data-dictionary.md).
    *   Cập nhật tệp kế hoạch gốc [refactor-plan.md](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/refactor-plan.md) phản ánh định hướng loại bỏ dữ liệu giả lập.

### 3. Kết quả chạy kiểm định và nghiệm thu Giai đoạn 1

Chúng tôi đã khởi chạy tuần tự các lệnh để kiểm thử luồng DWH và thu được kết quả như sau:
1.  **Drop và Recreate Tables**: Chạy `scripts/recreate_tables.py` thành công. Toàn bộ 7 bảng của Star Schema mới đã được tạo lại rỗng trên Cloud BigQuery.
2.  **Consolidate CSV**: Chạy `src/etl/consolidate_stock_metrics.py` thành công.
    *   *Số lượng bản ghi tổng hợp*: **`11.835 dòng`**.
    *   *Địa chỉ lưu*: `data/processed/fact_stock_daily_metrics_clean.csv`.
3.  **BigQuery Load**: Chạy `src/etl/load_to_bigquery.py --full-reload` thành công.
    *   *Kết quả nạp*:
        *   `dim_date`: 9.131 dòng nạp thành công.
        *   `dim_stock`: 4 dòng nạp thành công.
        *   `dim_bank`: 45 dòng nạp thành công.
        *   `dim_trading_session`: 4 dòng nạp thành công.
        *   `fact_stock_daily_metrics`: 11.835 dòng nạp thành công.
        *   `fact_bank_performance`: 667 dòng nạp thành công.
4.  **Referential Integrity Check**: Chạy `src/etl/validate_integrity.py` thành công.
    *   *Kết quả*: **`0 lỗi (TOTAL ERRORS FOUND: 0)`**. Các khóa ngoại của bảng `fact_stock_daily_metrics` đối chiếu sang `dim_date` và `dim_stock` khớp 100%. Quy tắc DQ-03 kiểm định giá đóng cửa không null và không âm đạt kết quả tuyệt đối.
5.  **BigQuery Data Quality Query Check**: Chạy `scripts/check_data_quality.py` trực tiếp truy vấn vào DWH trên Cloud để kiểm soát.
    *   *Phân phối dòng theo mã cổ phiếu*:
        *   BID: 3.096 dòng (2014-01-24 đến 2026-06-26)
        *   CTG: 3.362 dòng (2013-01-02 đến 2026-06-26)
        *   TCB: 2.015 dòng (2018-06-04 đến 2026-06-26)
        *   VCB: 3.362 dòng (2013-01-02 đến 2026-06-26)
    *   *Tỷ lệ giá trị rỗng (NULL Ratio)*: **`0.0%`** (Tất cả 11.835 dòng đều đầy đủ dữ liệu giá và khối lượng thực tế).
    *   *Kết luận*: Giai đoạn 1 đã được nghiệm thu hoàn thành xuất sắc.

---

## Ngày 08 tháng 07 năm 2026: Triển khai Giai đoạn 2 — Nâng cấp mô hình Học máy & Kiểm định học thuật

### 1. Mục tiêu và Nội dung thay đổi
*   **Mục tiêu**: Thực hiện các yêu cầu kiểm định định lượng của hội đồng: Kiểm định nhân quả Granger cho cặp biến `llp_ratio` -> `npl_ratio` (Q3); So sánh chuỗi giá của 4 ngân hàng bằng thuật toán Dynamic Time Warping (DTW) và tương quan lăn (Q2); So sánh thực nghiệm hiệu năng giữa LSTM Đơn biến (giá đóng cửa) và LSTM Đa biến (giá + khối lượng + biến động) cho cả 4 ngân hàng (Q1 mới) sử dụng 100% dữ liệu thực tế sạch.
*   **Hành động**:
    *   Tạo script [causal_analysis_llp.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/models/causal_analysis_llp.py) để chạy ADF test, Granger Causality và hồi quy bảng trễ Fixed Effects.
    *   Tạo script [dtw_analysis.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/models/dtw_analysis.py) để tính khoảng cách DTW và ma trận tương quan Pearson/tương quan lăn.
    *   Cập nhật [train_lstm.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/models/train_lstm.py) huấn luyện song song hai cấu hình LSTM Univariate và Multivariate cho cả 4 ngân hàng, so sánh RMSE để chọn ra mô hình tối ưu nạp dự báo vào BigQuery.
    *   Cập nhật [train_kmeans.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/models/train_kmeans.py) bổ sung cột phân khúc chiến lược (`cluster_name`) và chạy nạp lại BigQuery.
    *   Cập nhật [train_random_forest.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/models/train_random_forest.py) nạp lại dự báo rủi ro tín dụng lên BigQuery.

### 2. Kết quả kiểm thử thực nghiệm và nghiệm thu Giai đoạn 2

#### A. Kiểm định nhân quả Granger và Hồi quy bảng trễ (Q3)
*   **Kiểm định tính dừng ADF**: Chuỗi mức của cả `llp_ratio` và `npl_ratio` đều không dừng. Sau khi lấy sai phân bậc 1, chuỗi `llp_ratio` dừng hoàn toàn ($p < 0.001$), chuỗi `npl_ratio` gần dừng ($p = 0.1601$). Do đó, Granger Causality được thực hiện trên chuỗi sai phân bậc 1.
*   **Granger Causality (llp_ratio -> npl_ratio)**: p-value ở độ trễ 1 năm là **`0.0914`** (có ý nghĩa thống kê ở mức 10%). Điều này cho thấy tỷ lệ dự phòng rủi ro tín dụng trễ 1 năm có xu hướng nhân quả giúp dự báo tỷ lệ nợ xấu tốt hơn.
*   **Hồi quy bảng trễ (LSDV Fixed Effects)**: 
    *   Mô hình đạt hệ số R-squared là **`53.03%`** (Adjusted R-squared: `48.95%`).
    *   Biến nợ xấu trễ 1 kỳ ($NPL_{t-1}$) có tác động tích cực cực kỳ ý nghĩa lên nợ xấu hiện tại ($\beta = 0.605, p < 0.001$).
    *   Biến dự phòng rủi ro trễ 1 kỳ ($LLP_{t-1}$) có tác động dương lên nợ xấu nhưng chưa có ý nghĩa thống kê ở mức 5% ($\beta = 0.030, p = 0.413$).

#### B. Phân tích tương đồng chuỗi thời gian DTW và tương quan lăn (Q2)
*   **Kết quả khoảng cách DTW** (Z-score normalized close price):
    *   `BID` & `VCB`: Khoảng cách DTW rất nhỏ (**`201.25`**, Pearson $r = 0.958$) -> Cho thấy sự đồng pha mạnh mẽ nhất giữa hai ngân hàng thương mại nhà nước lớn nhất.
    *   `TCB` & `CTG`: Khoảng cách DTW nhỏ (**`162.87`**, Pearson $r = 0.941$) -> Tương thích và đồng pha cao.
    *   `TCB` & `VCB`: Khoảng cách DTW lớn (**`457.03`**, Pearson $r = 0.713$) -> Xuất hiện sự phân hóa rõ nét giữa ngân hàng tư nhân lớn và ngân hàng nhà nước.

#### C. Kết quả huấn luyện LSTM so sánh Đơn biến vs Đa biến (Q1 mới)
*   Đối với cả 4 ngân hàng, cấu hình **LSTM Multivariate (Đa biến)** đều có hiệu năng vượt trội hơn cấu hình LSTM Univariate (Đơn biến) và vượt xa đường cơ sở ARIMA trên tập kiểm thử (test set):
    *   **BID**: LSTM Multi RMSE = **`0.9634`** vs LSTM Uni RMSE = `1.0366` (ARIMA: `1.1696`) -> Đạt yêu cầu nghiệm thu (PASSED).
    *   **TCB**: LSTM Multi RMSE = **`1.2589`** vs LSTM Uni RMSE = `1.3411` (ARIMA: `9.4864`) -> Đạt yêu cầu nghiệm thu (PASSED).
    *   **VCB**: LSTM Multi RMSE = **`2.8278`** vs LSTM Uni RMSE = `2.9125` (ARIMA: `4.4900`) -> Đạt yêu cầu nghiệm thu (PASSED).
    *   **CTG**: LSTM Multi RMSE = **`1.3733`** vs LSTM Uni RMSE = `1.6568` (ARIMA: `11.3624`) -> Đạt yêu cầu nghiệm thu (PASSED).
*   Đã nạp thành công 20 dòng dự báo tương lai (T+1 đến T+5) của mô hình LSTM tốt nhất cho cả 4 mã lên BigQuery table `fact_model_predictions`.

#### D. Nghiệm thu nạp dữ liệu K-Means và Random Forest
*   **K-Means**: Phân cụm 39 ngân hàng ra 3 nhóm và nạp đầy đủ thuộc tính phân khúc `cluster_name` (`TMCP Nhỏ`, `Trụ Cột Lớn`, `Ngân Hàng Ngoại`) lên BigQuery table `bank_cluster_assignments` (39 dòng).
    *   *Silhouette Score*: **`0.3222`**
    *   *Davies-Bouldin Index*: **`0.9746`**
*   **Random Forest**: Huấn luyện phân loại rủi ro nợ xấu thành công và nạp kết quả dự báo lên BigQuery table `bank_risk_predictions` (661 dòng).
    *   *AUC-ROC*: **`0.9370`** (Ngưỡng yêu cầu: > 0.80) -> Đạt yêu cầu nghiệm thu (PASSED).
    *   *Recall (High Risk)*: **`0.8571`** (Ngưỡng yêu cầu: >= 0.85) -> Đạt yêu cầu nghiệm thu (PASSED).

---

## Kế hoạch cho Giai đoạn tiếp theo (Giai đoạn 3)
1.  **Cập nhật Streamlit Dashboard**: Tích hợp các biểu đồ trực quan hóa kết quả phân tích thống kê và học máy mới: Biểu đồ biến động giá và DTW, ma trận tương quan Pearson, tương quan lăn 60 phiên, so sánh LSTM vs ARIMA/Univariate, kết quả kiểm định Granger và Hồi quy.
2.  **Cập nhật tài liệu thiết kế Dashboard** trong `dashboard-spec.md`.

