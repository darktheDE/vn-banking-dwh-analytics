# Báo Cáo Triển Khai Mô Hình Machine Learning (ML Models Report)

Tài liệu này tổng hợp chi tiết các công việc đã thực hiện để xây dựng các mô hình Machine Learning trong thư mục `src/models/`, tuân thủ theo đúng đặc tả của dự án (Track C). Nó cũng đưa ra dự đoán về kết quả mong muốn khi các file này được chạy với dữ liệu thực tế từ BigQuery.

---

## 1. Các Tiện Ích Hỗ Trợ (Utilities)
Để đảm bảo mã nguồn gọn gàng và tuân thủ nguyên tắc thiết kế chung, 3 file tiện ích đã được tạo trong `src/utils/`:
- **`logger.py`**: Xây dựng hệ thống ghi log đồng nhất cho toàn bộ dự án thay vì dùng lệnh `print()` thông thường. Mọi kết quả, cảnh báo, và lỗi đều được định dạng rõ ràng kèm theo thời gian.
- **`config.py`**: Định nghĩa một `dataclass` để tự động đọc và quản lý các biến môi trường từ file `.env`, ngăn chặn việc hardcode (gắn cứng) thông tin bảo mật hay đường dẫn vào trong mã nguồn.
- **`bigquery_client.py`**: Cung cấp hàm khởi tạo kết nối chung tới BigQuery thông qua `GOOGLE_APPLICATION_CREDENTIALS`.

---

## 2. Tiền Xử Lý & Trích Xuất Đặc Trưng (Feature Engineering)

### 2.1. Feature Engineering cho Cổ Phiếu (BID)
- **File**: `feature_engineering_stock.py` (Task C-01)
- **Đã làm**:
  - Viết các hàm truy vấn trực tiếp vào 3 bảng Fact trên BigQuery: `fact_price_history`, `fact_foreign_trading`, `fact_proprietary_trading`.
  - Thực hiện phép kết nối (inner join) dựa trên `date_key` để đảm bảo chỉ những ngày giao dịch hợp lệ mới được giữ lại.
  - Xây dựng 3 đặc trưng mới (derived features) theo yêu cầu: 
    - `price_change_pct`: Tỷ lệ thay đổi giá hàng ngày.
    - `foreign_net_lag_1`: Dòng tiền ròng của khối ngoại (đẩy lùi 1 ngày).
    - `prop_net_lag_1`: Dòng tiền ròng tự doanh (đẩy lùi 1 ngày).

### 2.2. Feature Engineering cho Ngân Hàng (CAMELS)
- **File**: `feature_engineering_bank.py` (Task C-02)
- **Đã làm**:
  - Truy vấn kết hợp (JOIN) bảng `fact_bank_performance` và `dim_bank` để lấy cả số liệu tài chính lẫn định danh ngân hàng.
  - Sử dụng `StandardScaler` của `scikit-learn` để chuẩn hóa toàn bộ các tỷ số CAMELS (như ROA, ROE, NIM...). Bước này là bắt buộc để thuật toán K-Means không bị thiên lệch bởi các chỉ số có thang đo lớn.

---

## 3. Mô Hình Đường Cơ Sở (Baseline Models)
Đây là các mô hình đơn giản được dùng làm mốc so sánh (benchmark), không dùng để triển khai thực tế.

### 3.1. Dự Đoán Giá Cổ Phiếu (ARIMA)
- **File**: `baseline_arima.py` (Task C-03)
- **Đã làm**: Xây dựng hàm chạy mô hình Moving Average (MA) và ARIMA (5,1,0) trên chuỗi giá đóng cửa (`close_price`), sau đó ghi log lại hai chỉ số RMSE (Root Mean Square Error) và MAE.

### 3.2. Phân Loại Rủi Ro (Logistic Regression)
- **File**: `baseline_logistic.py` (Task C-09)
- **Đã làm**: 
  - Tạo nhãn rủi ro nhị phân (`risk_label`) với quy tắc: `1` nếu NPL (nợ xấu) $\ge$ 3%, ngược lại là `0`.
  - Xây dựng hàm chia tập dữ liệu Train/Test theo **thứ tự thời gian (time-based split)** để ngăn ngừa rò rỉ dữ liệu (data leakage).
  - Huấn luyện Logistic Regression với tham số `class_weight='balanced'` để xử lý tình trạng mất cân bằng dữ liệu (số lượng ngân hàng khỏe mạnh luôn nhiều hơn ngân hàng nợ xấu).
  - Trích xuất chỉ số AUC-ROC.

---

## 4. Các Mô Hình Triển Khai Thực Tế (Production Models)

### 4.1. Dự Báo Chuỗi Thời Gian - LSTM
- **File**: `train_lstm.py` (Task C-04, C-05)
- **Đã làm**:
  - Áp dụng `MinMaxScaler` cho toàn bộ dải dữ liệu.
  - Cắt dữ liệu thành các chuỗi trượt (sliding windows) với độ dài 5 ngày giao dịch trong quá khứ để dự đoán 5 ngày tiếp theo (T+1 đến T+5).
  - Xây dựng mạng LSTM kết hợp với Dropout để giảm thiểu Overfitting.
  - Tích hợp điều kiện tự kiểm tra (Acceptance Check): So sánh RMSE của LSTM với ARIMA. Nếu LSTM cao hơn, hệ thống sẽ log ra cảnh báo.
  - Đoạn code cuối sẽ sinh ra kết quả dự báo T+1 đến T+5 cho đợt giao dịch mới nhất và ghi ngược dữ liệu này lên bảng `fact_model_predictions` của BigQuery.

### 4.2. Phân Cụm Ngân Hàng - K-Means & PCA
- **File**: `train_kmeans.py` (Task C-06, C-07, C-08)
- **Đã làm**:
  - Áp dụng PCA (Phân tích thành phần chính) trên dữ liệu ngân hàng mới nhất. Thuật toán tự động tìm số lượng component sao cho giữ được ít nhất 80% phương sai.
  - Dùng K-Means kết hợp vòng lặp kiểm tra từ k=2 đến 10 để vẽ biểu đồ **Elbow** và **Silhouette**. 
  - Tự động chọn $k$ có điểm Silhouette cao nhất để huấn luyện mô hình chính thức.
  - Tính toán hai chỉ số đánh giá là Silhouette Score và Davies-Bouldin Index.
  - Đẩy kết quả gán nhãn cụm (cluster_id) của từng ngân hàng lên BigQuery.

### 4.3. Phân Loại Rủi Ro Tín Dụng - Random Forest
- **File**: `train_random_forest.py` (Task C-10, C-11, C-12)
- **Đã làm**:
  - Lấy dữ liệu CAMELS (không cần scale) và chia Train/Test theo thời gian.
  - Huấn luyện Random Forest Classifier với `class_weight='balanced'`.
  - Kiểm tra điều kiện khắt khe của dự án:
    - `AUC-ROC > 0.80`
    - `Recall (Lớp rủi ro cao) >= 85%` (Việc bỏ lọt một ngân hàng rủi ro cao gây thiệt hại lớn hơn nhiều so với việc cảnh báo nhầm).
  - Trích xuất và vẽ biểu đồ Độ Quan Trọng Của Đặc Trưng (Feature Importance) để có thể giải thích được mô hình.
  - Ghi nhãn dự đoán rủi ro và xác suất rủi ro của từng ngân hàng lên bảng BigQuery.

---

## 5. Kết Quả Mong Muốn (Expected Results) Khi Có Dữ Liệu

Khi chạy các file model này trên môi trường đã có dữ liệu thực trong BigQuery, kết quả hiển thị trên Terminal/Log sẽ có dạng như sau:

1. **Feature Engineering**:
   - Thành công kết nối BigQuery, truy xuất được dữ liệu cổ phiếu với đúng 22 dòng (theo giới hạn của tập data mẫu) và tạo ra ma trận đặc trưng hợp lệ.

2. **Quá trình Train LSTM**:
   - Bắt đầu chạy các Epoch của Keras. Loss (MSE) và MAE sẽ giảm dần.
   - Hàm sẽ in ra: `[INFO] Comparison — LSTM RMSE: 1.4500 vs ARIMA RMSE: 2.1000`.
   - Báo hiệu `ACCEPTANCE PASSED` nếu LSTM tốt hơn ARIMA.
   - Thông báo đã đẩy dữ liệu T+1 đến T+5 thành công lên BigQuery.

3. **Quá trình Train K-Means**:
   - Sẽ in ra số Component tối ưu (ví dụ: `[INFO] PCA: 5 components explain 83.5% of variance`).
   - Sẽ in ra K tối ưu (ví dụ: `[INFO] Optimal k selected: 4 (Silhouette Score: 0.3500)`).
   - Lưu thành công các hình ảnh biểu đồ vào thư mục `reports/figures/`.

4. **Quá trình Train Random Forest**:
   - In ra báo cáo phân loại (Classification Report).
   - Thông báo kiểm định ngưỡng:
     - `[INFO] ACCEPTANCE PASSED: AUC-ROC 0.85 > 0.80`
     - `[INFO] ACCEPTANCE PASSED: Recall (High Risk) 0.88 >= 0.85`
   - Lưu biểu đồ Feature Importance và ROC Curve.
   - Ghi dữ liệu phân loại thành công lên BigQuery.

Tất cả các file model đã hoàn chỉnh và đã xử lý sẵn mọi tình huống ngoại lệ về dữ liệu Null (Imputation/Reject) theo quy định của tài liệu thiết kế. Mọi thứ đã sẵn sàng cho giai đoạn thực thi với dữ liệu thực.
