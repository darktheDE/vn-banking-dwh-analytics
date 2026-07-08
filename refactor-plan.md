# Kế Hoạch Triển Khai Chi Tiết Theo Giai Đoạn (Phiên bản v2 - Không sử dụng dữ liệu giả lập)

Kế hoạch này phân rã các tác vụ refactor hệ thống thành 4 giai đoạn rõ rệt, tập trung giải quyết trước các yêu cầu chỉnh sửa bắt buộc của giảng viên, loại bỏ hoàn toàn dữ liệu giả lập để bảo đảm tính trung thực của nghiên cứu khoa học, sau đó triển khai các hợp phần nâng cấp kiến trúc và hoàn thiện báo cáo.

Chúng ta sẽ đi qua từng tác vụ theo thứ tự và dừng lại tại mỗi giai đoạn để tiến hành review kết quả thực thi.

---

## Giai đoạn 1: Chuẩn hóa DWH và Star Schema (Đã hoàn thành)
*Mục tiêu: Giải quyết câu hỏi của giảng viên về bản chất của các bảng Fact chứng khoán thô bằng cách hợp nhất chúng thành một bảng Fact duy nhất sạch, hiệu năng cao và loại bỏ hoàn toàn dữ liệu giả lập.*

### Các tác vụ chi tiết:
*   **Tác vụ 1.1: Thiết kế bảng Fact hợp nhất `fact_stock_daily_metrics`**
    *   *Nội dung*: Gộp các bảng `fact_price_history`, `fact_foreign_trading`, `fact_proprietary_trading`, và `fact_order_stats` thành một bảng Fact duy nhất.
    *   *Điều chỉnh v2*: Loại bỏ hoàn toàn các cột dữ liệu giả lập (khối ngoại, tự doanh, thống kê lệnh mẫu). Bảng `fact_stock_daily_metrics` hiện tại chỉ chứa thông tin OHLCV chính thống cào từ API `vnstock` cho cả 4 ngân hàng (BID, TCB, VCB, CTG) với 11.835 dòng dữ liệu thực tế sạch, không có giá trị NULL.
    *   *Lý do*: Tối ưu hóa lưu trữ cột của BigQuery, tránh các phép JOIN tốn kém khi vẽ biểu đồ hay chạy mô hình, và tuân thủ mô hình Star Schema chuẩn Kimball mà không phụ thuộc vào dữ liệu giả lập.
*   **Tác vụ 1.2: Cập nhật tệp DDL DWH**
    *   *Nội dung*: Sửa đổi [bigquery_schema.sql](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/sql/bigquery_schema.sql) để phản ánh cấu trúc mới.
*   **Tác vụ 1.3: Chạy khởi tạo Schema trên BigQuery**
    *   *Nội dung*: Thực thi script [recreate_tables.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/scripts/recreate_tables.py) để cập nhật schema trên Cloud BigQuery.
*   **Tác vụ 1.4: Viết script tổng hợp dữ liệu**
    *   *Nội dung*: Thực thi [consolidate_stock_metrics.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/etl/consolidate_stock_metrics.py) để chuẩn bị tệp dữ liệu sạch `fact_stock_daily_metrics_clean.csv`.
*   **Tác vụ 1.5: Tải dữ liệu lên BigQuery và chạy kiểm tra toàn vẹn**
    *   *Nội dung*: Thực thi [load_to_bigquery.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/etl/load_to_bigquery.py) và [validate_integrity.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/etl/validate_integrity.py).

---
> [!IMPORTANT]
> **ĐIỂM DỪNG REVIEW 1**: Dừng lại để người dùng kiểm tra cấu trúc bảng Fact mới trên BigQuery console và chạy kiểm định chất lượng dữ liệu đạt 0 lỗi (Đã nghiệm thu đạt yêu cầu).
---

## Giai đoạn 2: Nâng cấp mô hình Học máy & Biện luận học thuật (Giai đoạn tiếp theo)
*Mục tiêu: Triển khai kiểm định nhân quả thực tế trên dữ liệu CAMELS, phương pháp so sánh toàn bộ chuỗi thời gian bằng DTW và so sánh thực nghiệm LSTM đơn biến vs đa biến.*

### Các tác vụ chi tiết:
*   **Tác vụ 2.1: Phân tích nhân quả Granger cho `llp_ratio` (Q3)**
    *   *Nội dung*: Viết script [causal_analysis_llp.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/models/causal_analysis_llp.py) thực thi kiểm định tính dừng ADF, kiểm định nhân quả Granger và hồi quy bảng có độ trễ để chứng minh mối quan hệ tác động nhân quả từ tỷ lệ dự phòng rủi ro tín dụng lên nợ xấu.
*   **Tác vụ 2.2: So sánh nguyên chuỗi bằng Dynamic Time Warping (Q2)**
    *   *Nội dung*: Tính toán chỉ số khoảng cách Dynamic Time Warping (DTW) giữa 4 chuỗi giá đóng cửa cổ phiếu ngân hàng (BID, TCB, VCB, CTG) trên tập kiểm thử (sau khi chuẩn hóa Z-score) để chứng minh tính đồng pha/phân hóa.
*   **Tác vụ 2.3: Huấn luyện lại và so sánh mô hình LSTM (Q1 mới)**
    *   *Nội dung*: Cập nhật [train_lstm.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/models/train_lstm.py) để huấn luyện hai cấu hình:
        - **LSTM Univariate (Baseline)**: Chỉ dự báo dựa trên chuỗi giá đóng cửa lịch sử.
        - **LSTM Multivariate (Enriched)**: Dự báo dựa trên OHLCV, biến động giá trễ (`price_change_pct`) và biến động khối lượng trễ (`volume_change_pct`).
        - *Mục tiêu*: So sánh RMSE để kiểm chứng việc đưa thêm các đặc trưng khối lượng giao dịch và chỉ báo biến động trễ có giúp cải thiện độ chính xác dự báo cho cả 4 ngân hàng hay không.
*   **Tác vụ 2.4: Phân cụm K-Means & Cơ sở đặt tên (Q4)**
    *   *Nội dung*: Cập nhật [train_kmeans.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/models/train_kmeans.py) để làm rõ cơ sở lý thuyết đặt tên cho các cụm (Trụ Cột Lớn, TMCP Nhỏ, Ngân Hàng Ngoại) và tính toán Silhouette Score, Davies-Bouldin Index.

---
> [!IMPORTANT]
> **ĐIỂM DỪNG REVIEW 2**: Dừng lại để xem xét kết quả p-value của kiểm định Granger, ma trận khoảng cách DTW và bảng so sánh RMSE của hai cấu hình LSTM cho cả 4 ngân hàng.
---

## Giai đoạn 3: Nâng cấp Streamlit Dashboard (UI & Trực quan hóa)
*Mục tiêu: Đưa các kết quả phân tích trực quan mới lên giao diện người dùng.*

### Các tác vụ chi tiết:
*   **Tác vụ 3.1: Cập nhật Streamlit Dashboard**
    *   *Nội dung*: Cập nhật [app.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/src/dashboard/app.py) để hiển thị biểu đồ so sánh chuỗi DTW, kết quả kiểm định nhân quả Granger, và biểu đồ so sánh hiệu năng hai cấu hình LSTM.
*   **Tác vụ 3.2: Cập nhật tài liệu thiết kế Dashboard**
    *   *Nội dung*: Sửa đổi [dashboard-spec.md](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/docs/dashboard-spec.md).

---
> [!IMPORTANT]
> **ĐIỂM DỪNG REVIEW 3**: Dừng lại để người dùng kiểm thử toàn diện Dashboard hoạt động và nghiệm thu biểu đồ hiển thị.
---

## Giai đoạn 4: Hoàn thiện Báo cáo & Tài liệu kiến trúc
*Mục tiêu: Cập nhật hệ thống tài liệu kiến trúc chính thống, giải thích việc lược bỏ tích hợp Supabase OLTP và viết báo cáo đối chiếu.*

### Các tác vụ chi tiết:
*   **Tác vụ 4.1: Cập nhật tài liệu thiết kế hệ thống**
    *   *Nội dung*: Sửa đổi [system-arch.md](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/docs/system-arch.md) và [project-overview.md](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/docs/project-overview.md) giải thích rõ ràng việc trì hoãn tích hợp Supabase OLTP và cấu trúc bảng Fact tối giản sạch sẽ.
*   **Tác vụ 4.2: Viết tài liệu đối chiếu v1 vs v2**
    *   *Nội dung*: Cập nhật [RESULT.md](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/RESULT.md) bổ sung báo cáo so sánh chi tiết các cải tiến khoa học của v2 so với v1 (loại bỏ mock data, Granger Causality, DTW, LSTM Đa biến).
*   **Tác vụ 4.3: Viết Nhật ký Triển khai (Implementation Logs)**:
    *   *Nội dung*: Viết tệp [refactor_log.md](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/final/project2/vn-banking-dwh-analytics/docs/process/refactor_log.md) để ghi nhận chi tiết nhật ký thực thi refactor.

---
> [!IMPORTANT]
> **ĐIỂM DỪNG REVIEW 4**: Dừng lại để người dùng kiểm thử toàn diện hệ thống tài liệu và nghiệm thu hoàn thành dự án.
---

## Ghi chú về luồng dữ liệu OLTP-OLAP
Hội đồng đã được làm rõ: Do thời gian thực hiện dự án gấp rút và hạn chế của API lịch sử dòng tiền, nhóm quyết định hoãn việc tích hợp Supabase OLTP và tập trung làm sạch, chuẩn hóa Star Schema trên BigQuery OLAP bằng 100% dữ liệu cào thực tế ohlcv của 4 ngân hàng thương mại Việt Nam. Quyết định kiến trúc này giúp kho dữ liệu đạt độ tin cậy tuyệt đối và không chứa dữ liệu giả lập.