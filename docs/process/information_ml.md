# Báo cáo Tiến độ và Nhiệm vụ của Phạm Minh Quân (Machine Learning)

## 1. Vai trò và Bản đồ Nhiệm vụ

Phạm Minh Quân chịu trách nhiệm chính về mảng **Machine Learning (Track C)**. Nhiệm vụ cốt lõi là từ dữ liệu đã được làm sạch trên BigQuery, tiến hành trích xuất đặc trưng (Feature Engineering) và xây dựng 3 hệ thống mô hình chính:
1. **Dự báo chuỗi thời gian (Time Series Forecasting)**: Dự đoán giá cổ phiếu BID (T+1 đến T+5) bằng mạng LSTM.
2. **Phân cụm (Clustering)**: Phân nhóm 46 ngân hàng dựa trên chỉ số tài chính CAMELS bằng PCA và K-Means.
3. **Phân loại (Classification)**: Dự đoán rủi ro nợ xấu (NPL $\ge$ 3%) bằng Random Forest.

---

## 2. Chi tiết Công việc Đã thực hiện


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

---

## 4. Quy trình Thực thi Local và Phân tích Dữ liệu (Local ML Data)

Để chạy thử nghiệm mô hình mà không cần kết nối trực tiếp với BigQuery, tôi đã xây dựng bộ mã nguồn chạy trên máy cá nhân (lưu tại `src/models/local`). Việc chạy offline giúp quá trình phát triển, kiểm thử diễn ra nhanh chóng và không tốn phí truy vấn cloud.

### 4.1. Thao tác tạo dữ liệu đầu vào (Input)
Trước khi train, tôi chạy lệnh `data_loader.py` để trích xuất và tiền xử lý dữ liệu từ kho lưu trữ thô:
```bash
python src/models/local/data_loader.py
```
Lệnh này tự động tạo ra thư mục `data/data_ml/input` chứa các file:

*   **`banks_camels_46.csv`**: File gộp bảng hiệu suất của 46 ngân hàng. 
    *   *Tại sao phải xử lý?* Thuật toán K-Means hoạt động dựa trên khoảng cách không gian (Euclidean distance). Nếu không được xử lý điền khuyết (median imputation) và chuẩn hóa (StandardScaler), thuật toán sẽ bị sai lệch vì biến quá lớn như `Tổng tài sản` sẽ lấn át tất cả.
*   **`bid_lstm_data.csv`**: Lịch sử giao dịch mã chứng khoán BID.
    *   *Tại sao phải xử lý?* Mạng LSTM không hiểu được dữ liệu dạng bảng tĩnh. Việc tính toán thêm biến phái sinh (`% thay đổi giá`) và chia thành các "cửa sổ trượt" (sliding windows) 5 ngày là bắt buộc để LSTM ép dữ liệu vào định dạng tensor 3D, giúp học được xu hướng thay vì giá trị tuyệt đối.
*   **`banks_4_financial_ratios.csv`**: Dữ liệu tài chính riêng biệt của 4 "ông lớn" ngân hàng (BID, CTG, TCB, VCB).
    *   *Tại sao phải xử lý?* Việc tách và nối (concat) dữ liệu của 4 ngân hàng trụ cột này thành một file riêng giúp làm giàu kho dữ liệu, tạo bộ tham chiếu chuẩn để phân tích chuyên sâu các chỉ số định giá (PE, PB, PS...) trên Dashboard, tách bạch khỏi nhóm dữ liệu huấn luyện ML chính.

### 4.2. Thao tác huấn luyện và Ý nghĩa Đầu ra (Output)
Sau khi có input, tôi tiến hành chạy tuần tự 3 thuật toán học máy:
```bash
python src/models/local/train_kmeans_local.py
python src/models/local/train_random_forest_local.py
python src/models/local/train_lstm_local.py
```
Kết quả được xuất ra thư mục `data/data_ml/output` nhằm trả lời trực tiếp các câu hỏi nghiệp vụ (Business Questions) của Ban lãnh đạo:

*   **`kmeans_clusters_local.csv`**: 
    *   *Câu hỏi:* "Ngân hàng nào đang có chung mô hình kinh doanh hoặc cấu trúc rủi ro?"
    *   *Ý nghĩa:* Chia các ngân hàng thành các Cụm (Cluster) để phân tích tương quan và so sánh chéo đối thủ cùng phân khúc.
*   **`rf_predictions_local.csv`**: 
    *   *Câu hỏi:* "Ngân hàng nào đang đối mặt với nguy cơ nợ xấu (NPL) vượt ngưỡng 3%?"
    *   *Ý nghĩa:* Bảng phân loại rủi ro (High Risk vs Healthy) này đóng vai trò như một hệ thống radar cảnh báo sớm rủi ro tín dụng.
*   **`rf_feature_importance_local.csv`**: 
    *   *Câu hỏi:* "Tại sao AI lại đánh giá ngân hàng này rủi ro? Nguyên nhân cốt lõi gây ra nợ xấu là gì?"
    *   *Ý nghĩa:* Bảng xếp hạng này (Explainable AI) chỉ ra chính xác chỉ số nào (tỷ lệ bao phủ nợ xấu, chi phí hoạt động...) đang gây áp lực lên ngân hàng.
*   **`lstm_predictions_local.csv`**: 
    *   *Câu hỏi:* "Xu hướng giá cổ phiếu BID trong 5 ngày tới ra sao?"
    *   *Ý nghĩa:* Bảng giá dự phóng T+1 đến T+5 này hỗ trợ đắc lực cho các quyết định đầu tư và trading ngắn hạn của phòng tự doanh.
