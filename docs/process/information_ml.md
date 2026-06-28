# Báo cáo Tiến độ và Nhiệm vụ của Phạm Minh Quân (Machine Learning)

Tài liệu này tổng hợp chi tiết vai trò, các công việc đã hoàn thành và kết quả đạt được của thành viên **Phạm Minh Quân** trong việc xây dựng hệ thống mô hình học máy (Machine Learning Pipeline - Track C) cho dự án VN Banking DWH Analytics. Toàn bộ mã nguồn được lưu trữ tại `src/models/`.

---

## 1. Vai trò và Bản đồ Nhiệm vụ

Phạm Minh Quân chịu trách nhiệm chính về mảng **Machine Learning (Track C)**. Nhiệm vụ cốt lõi là từ dữ liệu đã được làm sạch trên BigQuery, tiến hành trích xuất đặc trưng (Feature Engineering) và xây dựng 3 hệ thống mô hình chính:
1. **Dự báo chuỗi thời gian (Time Series Forecasting)**: Dự đoán giá cổ phiếu BID (T+1 đến T+5) bằng mạng LSTM.
2. **Phân cụm (Clustering)**: Phân nhóm 46 ngân hàng dựa trên chỉ số tài chính CAMELS bằng PCA và K-Means.
3. **Phân loại (Classification)**: Dự đoán rủi ro nợ xấu (NPL $\ge$ 3%) bằng Random Forest.

---

## 2. Chi tiết Công việc Đã thực hiện

Tất cả các mô hình đã được lập trình hoàn thiện bằng Python, tuân thủ nghiêm ngặt chuẩn viết code chung (không dùng `print`, dùng `logger`, không hardcode thông tin kết nối).

### Bước 1: Xây dựng Tiện ích dùng chung (Utilities)
- Đã thiết lập `src/utils/logger.py` để định dạng log chuẩn cho toàn bộ quá trình train model.
- Đã thiết lập `src/utils/config.py` và `src/utils/bigquery_client.py` để tự động khởi tạo kết nối đến BigQuery một cách an toàn thông qua biến môi trường.

### Bước 2: Kỹ thuật Trích xuất Đặc trưng (Feature Engineering)
- **Cổ phiếu (BID)**: Tạo file `feature_engineering_stock.py`. Truy vấn và gộp dữ liệu từ 3 bảng Fact (`fact_price_history`, `fact_foreign_trading`, `fact_proprietary_trading`). Đã tính toán thêm các đặc trưng phái sinh: `% thay đổi giá`, `dòng tiền khối ngoại (trễ 1 ngày)`, `dòng tiền tự doanh (trễ 1 ngày)`.
- **Ngân hàng (CAMELS)**: Tạo file `feature_engineering_bank.py`. Lấy dữ liệu từ `fact_bank_performance`, loại bỏ nhiễu và sử dụng `StandardScaler` để đưa tất cả các tỷ số tài chính về cùng một thang đo chuẩn (mean=0, std=1) nhằm phục vụ tốt nhất cho thuật toán phân cụm dựa trên khoảng cách.

### Bước 3: Xây dựng Mô hình Baseline (Đường cơ sở)
- **ARIMA & MA**: Tại `baseline_arima.py`, đã xây dựng mô hình ARIMA(5,1,0) và Moving Average(5) để lấy điểm chuẩn RMSE cho chuỗi thời gian.
- **Logistic Regression**: Tại `baseline_logistic.py`, đã xây dựng mô hình Logistic với `class_weight='balanced'` để lấy điểm chuẩn AUC-ROC cho bài toán phân loại rủi ro tín dụng. Đã thực hiện chia tập dữ liệu theo mốc thời gian (Time-based split) để chống rò rỉ dữ liệu.

### Bước 4: Huấn luyện Mô hình Triển khai (Production Models)
- **Mô hình LSTM (`train_lstm.py`)**: 
  - Đã chuẩn hóa chuỗi dữ liệu (MinMaxScaler) và tạo cửa sổ trượt (Sliding Windows) 5 ngày.
  - Xây dựng kiến trúc LSTM kết hợp Dropout để chống overfitting.
  - Thiết lập EarlyStopping để tự động dừng khi validation loss không giảm.
  - Viết luồng kiểm định tự động: Chỉ cho qua (PASS) nếu RMSE của LSTM nhỏ hơn RMSE của ARIMA.
- **Mô hình K-Means (`train_kmeans.py`)**:
  - Tích hợp giải thuật PCA để giảm chiều dữ liệu, tự động giữ lại tập hợp các thành phần giải thích $\ge$ 80% phương sai.
  - Tự động dò tìm số cụm tối ưu ($k$) bằng phương pháp Elbow và phân tích điểm Silhouette. 
- **Mô hình Random Forest (`train_random_forest.py`)**:
  - Giải quyết bài toán mất cân bằng nhãn (class imbalance) với `class_weight='balanced'`.
  - Thiết lập luồng kiểm tra khắt khe: Bắt buộc `AUC-ROC > 0.80` và `Recall (Nhóm rủi ro cao) >= 85%`.
  - Đã viết logic để vẽ và lưu biểu đồ Độ Quan Trọng Của Đặc Trưng (Feature Importance).

### Bước 5: Viết kết quả ngược về Data Warehouse
- Toàn bộ các script huấn luyện mô hình chính (`train_lstm`, `train_kmeans`, `train_random_forest`) đều đã được tích hợp đoạn code khởi tạo `bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")` để tự động lưu kết quả dự đoán và gán nhãn về lại các bảng lưu trữ trên BigQuery, sẵn sàng cho team làm Dashboard (Track D) sử dụng.

---

## 3. Kết quả mong đợi khi chạy ML tại Local

Khi hệ thống Data Engineering (Track B) nạp dữ liệu xong vào BigQuery, các file ML có thể được chạy trực tiếp tại máy cá nhân (Local) thông qua Terminal:

```bash
python -m src.models.train_lstm
python -m src.models.train_kmeans
python -m src.models.train_random_forest
```

**Kết quả kỳ vọng (Local Execution Results):**

1. **Hiển thị Log rõ ràng (Terminal)**: Sẽ không có bất kỳ dòng chữ lộn xộn nào, mọi thông báo đều có tiền tố thời gian và cấp độ (INFO, WARNING).
2. **Kiểm tra Mốc Tiêu Chuẩn (Acceptance Tests)**:
   - Trong quá trình chạy LSTM, Terminal sẽ hiển thị dòng chữ so sánh RMSE với ARIMA và trả về `[INFO] ACCEPTANCE PASSED: LSTM RMSE is lower than ARIMA RMSE.`.
   - Trong quá trình chạy Random Forest, Terminal sẽ hiển thị 2 mốc kiểm tra và trả về `ACCEPTANCE PASSED` cho ngưỡng AUC-ROC > 0.80 và ngưỡng Recall >= 0.85.
3. **Sinh ra các File Artifact**: Trong thư mục `reports/figures/` (nếu chưa có sẽ tự động được tạo ra), hệ thống sẽ lưu lại 4 biểu đồ sắc nét để chứng minh cho chất lượng mô hình:
   - `pca_explained_variance.png`: Biểu đồ tích lũy phương sai của PCA.
   - `kmeans_elbow_silhouette.png`: Biểu đồ chọn K tối ưu.
   - `kmeans_cluster_scatter.png`: Biểu đồ phân tán các cụm ngân hàng.
   - `rf_feature_importance.png`: Biểu đồ cột ngang phân tích mức độ quan trọng của các biến đầu vào (CAMELS).
   - `rf_roc_curve.png`: Biểu đồ đường cong ROC cho mô hình cảnh báo rủi ro.
4. **Lưu Model File**: Các mô hình huấn luyện xong sẽ được nén và xuất ra file `lstm_bid_price.h5` và `random_forest_credit_risk.pkl` trong `reports/models/` để có thể tái sử dụng mà không cần huấn luyện lại.
5. **Ghi lên BigQuery thành công**: Hệ thống sẽ thông báo: `[INFO] Successfully wrote X predictions to...` cho cả 3 mô hình, khẳng định chu trình khép kín từ kho dữ liệu, qua AI, và quay trở về kho dữ liệu đã diễn ra thông suốt.
