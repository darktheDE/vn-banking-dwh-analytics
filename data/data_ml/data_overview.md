# Bảng Tra Cứu Dữ Liệu Học Máy (Local ML Data Overview)

Thư mục `data_ml` (và thư mục con `figures`) chứa toàn bộ các tập dữ liệu đầu vào (Input) và kết quả đầu ra (Output) trong quá trình huấn luyện 3 mô hình học máy: **K-Means**, **Random Forest**, và **LSTM** tại môi trường Local.

Dưới đây là tài liệu giải thích chi tiết ý nghĩa của từng file.

---

## 1. Dữ Liệu Đầu Vào (Input Data)
Đây là các file được sinh ra từ script `data_loader.py`, dùng để nạp vào huấn luyện thuật toán.

*   **`banks_camels_46.csv`**: Bộ dữ liệu tài chính chuẩn xác của 45-46 ngân hàng thương mại Việt Nam (~667 dòng). Chứa các chỉ số CAMELS (như `npl_ratio`, `roa`, `roe`, `cir`...). Đây là **nguồn dữ liệu sống còn** để chạy mô hình K-Means (phân cụm ngân hàng) và Random Forest (dự đoán nợ xấu).
*   **`bid_lstm_data.csv`**: Dữ liệu lịch sử giao dịch của mã cổ phiếu BID (hơn 3000 dòng). Đã được tích hợp các tính toán phái sinh (phần trăm thay đổi giá, khối lượng) để nạp vào mạng Neural Network LSTM dự báo chuỗi thời gian.
*   **`banks_4_financial_ratios.csv`**: Dữ liệu bổ sung các chỉ số định giá tài chính (PE, PB, PS...) của 4 ngân hàng lớn nhất (BID, CTG, TCB, VCB) dùng để đối chiếu hoặc mở rộng cho việc phân tích chuyên sâu.

---

## 2. Kết Quả Dự Đoán (Output Data)
Đây là các file CSV được các mô hình tự động sinh ra sau khi huấn luyện xong. Chúng là **kết quả** để đem lên làm Dashboard báo cáo.

*   **`kmeans_clusters_local.csv`**: Chứa danh sách các ngân hàng kèm theo **nhãn Cụm (Cluster)** mà mô hình K-Means vừa chia ra. Giúp ta biết ngân hàng nào đang nằm chung nhóm với ngân hàng nào dựa trên sức khỏe tài chính.
*   **`rf_predictions_local.csv`**: Chứa kết quả dự đoán của Random Forest cho tập Test. Gồm nhãn thực tế (`Actual`) và nhãn mô hình dự đoán (`Predicted`) về việc ngân hàng có nguy cơ nợ xấu cao (High Risk) hay không.
*   **`rf_feature_importance_local.csv`**: Bảng xếp hạng mức độ quan trọng của các chỉ số tài chính (Ví dụ: `llp_ratio`, `roe`...) ảnh hưởng đến nợ xấu ngân hàng.
*   **`lstm_predictions_local.csv`**: Bảng dự báo giá đóng cửa của cổ phiếu BID trong 5 ngày tương lai tiếp theo (T+1 đến T+5).

---

## 3. Thư mục Biểu Đồ (`figures/`)
Các biểu đồ được lưu tự động bằng `matplotlib` nhằm chứng minh trực quan chất lượng của các mô hình AI.

*   **`pca_explained_variance.png`**: Biểu đồ đường của thuật toán PCA. Nó chứng minh xem ta cần giữ lại bao nhiêu thành phần (components) thì mới đủ giải thích $\ge$ 80% phương sai của bộ dữ liệu 46 ngân hàng.
*   **`kmeans_elbow_silhouette.png`**: Hai biểu đồ (Elbow và Silhouette) kết hợp để biện luận lý do chọn số lượng cụm (K) tối ưu nhất (thường là điểm uốn của chỏm khuỷu tay hoặc đỉnh cao nhất của điểm Silhouette).
*   **`kmeans_cluster_scatter.png`**: Đồ thị phân tán (Scatter Plot) hiển thị vị trí các ngân hàng trong không gian 2 chiều (sau khi giảm chiều) để xem các cụm có tách bạch rõ ràng hay không.
*   **`rf_roc_curve.png`**: Biểu đồ đường cong ROC của Random Forest. Diện tích dưới đường cong (AUC) là tham số dùng để kiểm định chất lượng thuật toán (Yêu cầu hệ thống: AUC > 0.80).
*   **`rf_feature_importance.png`**: Đồ thị cột nằm ngang, phiên bản trực quan của file `rf_feature_importance_local.csv`, giúp sếp/người xem dễ dàng nhận biết chỉ số nào đang đóng vai trò sống còn trong việc hình thành nợ xấu.
