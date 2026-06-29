# Bảng Tra Cứu Dữ Liệu Học Máy (Local ML Data Overview)

Thư mục `data_ml` (và thư mục con `figures`) chứa toàn bộ các tập dữ liệu đầu vào (Input) và kết quả đầu ra (Output) trong quá trình huấn luyện 3 mô hình học máy: **K-Means**, **Random Forest**, và **LSTM** tại môi trường Local.

Dưới đây là tài liệu giải thích chi tiết ý nghĩa của từng file.

---

## 1. Dữ Liệu Đầu Vào (Input Data)
Thư mục `input/` chứa các file CSV được trích xuất và tiền xử lý bởi script `data_loader.py`. 

**Tại sao phải tạo ra các file input này?**
Thay vì kết nối trực tiếp vào Data Warehouse (BigQuery) vốn đòi hỏi cấu hình mạng phức tạp và tốn thời gian truy vấn, việc tạo ra các file CSV tĩnh ở Local giúp quá trình phát triển, kiểm thử, và tinh chỉnh mô hình Machine Learning diễn ra cực kỳ nhanh chóng, an toàn và hoàn toàn ngoại tuyến (offline). Môi trường `local` này mô phỏng lại chính xác luồng dữ liệu thật trên Cloud.

**Chi tiết quá trình tạo và nội dung từng file:**

*   **`banks_camels_46.csv`**:
    *   *Được tạo như thế nào?* File được tổng hợp bằng cách gộp (merge) bảng hiệu suất `fact_bank_performance_clean` và thông tin `dim_bank_clean` của 46 ngân hàng. Script tự động xử lý các giá trị bị khuyết (ví dụ: `npl_ratio` bị thiếu) bằng phương pháp điền trung vị (median imputation) theo chuẩn kiến trúc hệ thống để đảm bảo không bị lỗi dữ liệu đầu vào.
    *   *Nội dung:* Chứa các chỉ số sức khỏe tài chính cốt lõi (CAMELS) như `npl_ratio` (nợ xấu), `roa`, `roe`, `cir`. Đây là nguyên liệu chính yếu để thuật toán K-Means gom nhóm và Random Forest phân tích cảnh báo.

*   **`bid_lstm_data.csv`**:
    *   *Được tạo như thế nào?* Trích xuất từ lịch sử giao dịch gốc của mã chứng khoán BID. Script `data_loader.py` đã chủ động tính toán thêm các biến phái sinh vô cùng quan trọng như `% thay đổi giá` (price_change_pct) và `% thay đổi khối lượng` (volume_change_pct).
    *   *Nội dung:* Gồm các cột OHLCV cùng các biến phái sinh. Việc tính biến phái sinh là vì mạng LSTM nhạy cảm với sự thay đổi (xu hướng) hơn là giá trị tuyệt đối. File này đã được chuẩn bị sẵn sàng để đưa vào hàm cắt "cửa sổ trượt" (sliding windows) 5 ngày ở bước train mô hình.

*   **`banks_4_financial_ratios.csv`**:
    *   *Được tạo như thế nào?* Đọc và nối (concat) dữ liệu các chỉ số tài chính riêng lẻ từ 4 ông lớn ngân hàng (BID, CTG, TCB, VCB).
    *   *Nội dung:* Chứa các chỉ số định giá (PE, PB, PS...). Dùng làm dữ liệu tham chiếu bổ sung để làm giàu cho các báo cáo phân tích sâu (nếu cần thiết).

---

## 2. Kết Quả Dự Đoán (Output Data)
Thư mục `output/` chứa các file CSV được sinh tự động sau khi các thuật toán AI chạy xong. Đây chính là giá trị cốt lõi của dự án, nhằm **trực tiếp trả lời các câu hỏi nghiệp vụ (Business Questions)** của Ban lãnh đạo.

*   **`kmeans_clusters_local.csv`**: 
    *   *Câu hỏi giải quyết:* "Trong 46 ngân hàng hiện nay, những ngân hàng nào đang có chung một mô hình kinh doanh hoặc cấu trúc rủi ro?"
    *   *Nội dung:* Kết quả chia các ngân hàng thành các Cụm (Cluster). Nhờ đó, người quản lý có thể phân tích tương quan và so sánh một ngân hàng với các đối thủ cùng phân khúc.
*   **`rf_predictions_local.csv`**: 
    *   *Câu hỏi giải quyết:* "Ngân hàng nào đang đối mặt với nguy cơ nợ xấu (NPL) vượt ngưỡng báo động 3%?"
    *   *Nội dung:* Bảng phân loại rủi ro (High Risk vs Healthy). Nó đóng vai trò như một hệ thống radar cảnh báo sớm rủi ro tín dụng của toàn ngành.
*   **`rf_feature_importance_local.csv`**: 
    *   *Câu hỏi giải quyết:* "Tại sao AI lại đánh giá ngân hàng này là rủi ro? Đâu là nguyên nhân gốc rễ?"
    *   *Nội dung:* Bảng xếp hạng mức độ đóng góp của từng chỉ số vào kết quả dự đoán (Explainable AI). Qua đó ta sẽ biết liệu nợ xấu cao là do "tỷ lệ bao phủ nợ xấu (llp_ratio) thấp" hay do "chi phí hoạt động (cir) kém hiệu quả".
*   **`lstm_predictions_local.csv`**: 
    *   *Câu hỏi giải quyết:* "Xu hướng giá cổ phiếu đóng cửa của BID trong 5 ngày giao dịch tiếp theo sẽ như thế nào?"
    *   *Nội dung:* Bảng kết quả giá dự phóng (T+1 đến T+5). Hỗ trợ nhà đầu tư hoặc phòng ban tự doanh ra quyết định mua/bán (trading) trong ngắn hạn.

---

## 3. Thư mục Biểu Đồ (`figures/`)
Các biểu đồ được lưu tự động bằng `matplotlib` nhằm chứng minh trực quan chất lượng của các mô hình AI.

*   **`pca_explained_variance.png`**: Biểu đồ đường của thuật toán PCA. Nó chứng minh xem ta cần giữ lại bao nhiêu thành phần (components) thì mới đủ giải thích $\ge$ 80% phương sai của bộ dữ liệu 46 ngân hàng.
*   **`kmeans_elbow_silhouette.png`**: Hai biểu đồ (Elbow và Silhouette) kết hợp để biện luận lý do chọn số lượng cụm (K) tối ưu nhất (thường là điểm uốn của chỏm khuỷu tay hoặc đỉnh cao nhất của điểm Silhouette).
*   **`kmeans_cluster_scatter.png`**: Đồ thị phân tán (Scatter Plot) hiển thị vị trí các ngân hàng trong không gian 2 chiều (sau khi giảm chiều) để xem các cụm có tách bạch rõ ràng hay không.
*   **`rf_roc_curve.png`**: Biểu đồ đường cong ROC của Random Forest. Diện tích dưới đường cong (AUC) là tham số dùng để kiểm định chất lượng thuật toán (Yêu cầu hệ thống: AUC > 0.80).
*   **`rf_feature_importance.png`**: Đồ thị cột nằm ngang, phiên bản trực quan của file `rf_feature_importance_local.csv`, giúp sếp/người xem dễ dàng nhận biết chỉ số nào đang đóng vai trò sống còn trong việc hình thành nợ xấu.
