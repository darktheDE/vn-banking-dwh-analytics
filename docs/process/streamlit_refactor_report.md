# Báo Cáo Cải Tiến và Sửa Đổi Giao Diện Streamlit Dashboard
**Dự án**: Hệ thống Phân Tích Dữ Liệu Lịch Sử & Dự Báo ML Ngành Ngân Hàng Việt Nam
**Thời gian hoàn thành**: Ngày 08–09 tháng 07 năm 2026

---

## 1. Bối Cảnh Cải Tiến
Để đáp ứng các yêu cầu kiểm định định lượng khắt khe từ hội đồng chấm thi và tối ưu hóa hệ thống Star Schema thực tế trên BigQuery, giao diện Streamlit Dashboard (`src/dashboard/app.py`) đã được tái cấu trúc toàn diện. 

Cải tiến này tập trung vào 3 mục tiêu lớn:
1. **Khắc phục lỗi kết nối và tương thích DWH**: Sửa các truy vấn SQL đọc từ bảng thực thể hợp nhất thay thế cho các bảng cũ bị lược bỏ.
2. **Nâng cấp độ trực quan trực tiếp**: Chuyển đổi các báo cáo kiểm định văn bản thô (ADF, Granger, OLS Fixed Effects) và ma trận DTW tĩnh thành các cấu phần đồ họa, bảng biểu tương tác và bản đồ nhiệt.
3. **Thống nhất nội dung học thuật**: Đồng bộ hóa các câu hỏi nghiên cứu (Q1-Q4) và giả thuyết trong phần giới thiệu dự án khớp 100% với đề cương lý thuyết.

---

## 2. Các Nội Dung Cải Tiến Chi Tiết Theo Phân Hệ

### 2.1 Phân Hệ Dự Báo Giá Cổ Phiếu (LSTM)
Phân hệ được tái cấu trúc thành 3 Tab chuyên sâu:

*   **Tab 1: LSTM Đơn biến vs Đa biến**
    *   *Sửa lỗi 404 (Table Not Found)*: Chuyển đổi truy vấn giá lịch sử từ bảng cũ `fact_price_history` sang bảng thực tế `fact_stock_daily_metrics`.
    *   *Thay đổi hiển thị*: Thay thế việc so sánh LSTM vs ARIMA bằng so sánh song song giữa **Giá lịch sử thực tế vs Mô hình LSTM Đơn biến (Univariate) vs Mô hình LSTM Đa biến (Multivariate)** trên cùng biểu đồ Plotly trực quan.
    *   *Thông tin dự báo*: Hiển thị bảng chi tiết giá trị dự báo và biên độ biến động (%) trong 5 ngày tiếp theo ($T+1 \dots T+5$) của cả hai mô hình để kiểm chứng hiệu năng trực quan.

*   **Tab 2: Tương quan & Đồng pha (DTW & Pearson)**
    *   *Sửa lỗi giá trị rỗng (None)*: Cập nhật khóa tải dữ liệu tương thích với tệp tin JSON báo cáo mới (`dtw_distance_matrix` và `pearson_correlation_matrix` thay cho các khóa cũ).
    *   *Khắc phục lỗi hiển thị màu tối (Dark Mode)*: Loại bỏ hoàn toàn bảng HTML tĩnh vốn bị lỗi chữ trắng nền trắng. Thay thế bằng cấu hình `st.dataframe()` bản địa của Streamlit.
    *   *Giao diện bản đồ nhiệt (Heatmap)*: Sử dụng Pandas Styler tích hợp màu chuyển sắc (`cmap="YlOrRd_r"` cho khoảng cách DTW và `cmap="Blues"` cho tương quan Pearson) giúp trực quan hóa phân hóa/đồng pha trực diện và sắc nét.

*   **Tab 3: So sánh Đơn biến vs Đa biến**
    *   *Sửa lỗi biên dịch (KeyError)*: Khắc phục lỗi trích xuất dữ liệu do thay đổi cấu trúc lưu trữ chỉ số. Bản đồ hóa các khóa phẳng trực tiếp từ JSON (`uni_rmse`, `uni_mae`, `multi_rmse`, `multi_mae`, `arima_rmse`, `arima_mae`).
    *   *Bảng đối chứng*: Hiển thị bảng so sánh RMSE và MAE của LSTM Univariate và Multivariate đối chứng với ARIMA Baseline trên tập Test thực tế của cả 4 ngân hàng (BID, TCB, VCB, CTG).

---

### 2.2 Phân Hệ Phân Loại Rủi Ro Tín Dụng (Random Forest)
Phân hệ được tổ chức thành 2 Tab rõ ràng:

*   **Tab 1: Phân loại rủi ro Random Forest**
    *   Hiển thị các chỉ số hiệu năng kiểm thử vượt trội của mô hình RF: **Recall đạt 91.67%** (vượt xa chỉ tiêu cam kết $\ge 85\%$), **AUC-ROC đạt 0.9752**.
    *   Vẽ biểu đồ hình tròn biểu diễn tỷ lệ phân phối trạng thái rủi ro của hệ thống (5.36% Nguy cơ cao, 94.64% An toàn).
    *   Trực quan hóa độ quan trọng tính năng (Feature Importance) với `llp_ratio` là chỉ số dẫn đường quan trọng nhất (> 20%).

*   **Tab 2: Kiểm định nhân quả Granger (LLP -> NPL)**
    *   *Trực quan hóa bảng biểu*: Thay thế cho ô văn bản thô dài dòng trước đây, các kết quả kiểm định toán học định lượng đã được bóc tách ra các cấu phần giao diện riêng biệt:
        1.  **Bảng Kiểm định tính dừng ADF**: Hiển thị rõ giá trị kiểm định ADF, p-value và kết luận chuỗi dừng ở mức/sai phân bậc 1.
        2.  **Bảng Kiểm định nhân quả Granger**: Đối chiếu giá trị p-value kiểm định theo các độ trễ 1-3 năm kèm cột kết luận ý nghĩa thống kê rõ ràng.
        3.  **Hồi quy Bảng trễ (Entity Fixed Effects)**: Thiết kế các ô Metric lớn hiển thị các tham số chất lượng của mô hình bảng (`R-squared: 53.03%`, `Adj. R-squared: 48.95%`, `Obs: 577`). 
        4.  **Bảng Hệ số hồi quy (Coefficients)**: Liệt kê chi tiết hệ số tác động trễ của nợ xấu kỳ trước (`npl_ratio_lag1` đạt 0.6050, có ý nghĩa thống kê cực kỳ mạnh mẽ) và tỷ lệ trích lập dự phòng trễ (`llp_ratio_lag1`), có cảnh báo màu đỏ trực quan cho các hệ số thực sự có ý nghĩa.
    *   *Hộp thoại ẩn*: Thu gọn toàn bộ báo cáo văn bản gốc của mô hình vào trong `st.expander` để hội đồng chấm thi có thể tự do mở ra tra cứu các thông số phụ khi cần thiết.

---

### 2.3 Đồng Bộ Tài Liệu Kiến Trúc & Nhật Ký
*   **Tổng quan dự án**: Khôi phục lại đúng câu hỏi nghiên cứu **Q1** và **Giả thuyết 1** ban đầu của đề tài liên quan đến dòng tiền khối ngoại và tự doanh nhằm đảm bảo tính thống nhất trong đề cương lý thuyết.
*   **Tương thích**: Viết bổ sung các hàm Python an toàn để đọc báo cáo cục bộ trên đĩa (`load_dtw_report`, `load_causal_report`, `load_lstm_comparison`).
*   **Mã nguồn**: Đã kiểm định không phát sinh lỗi cú pháp (`python -m py_compile`) và thực hiện đẩy (push) toàn bộ nhánh sửa đổi lên repository GitHub.
