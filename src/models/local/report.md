# Báo Cáo Chạy Mô Hình Machine Learning (Local CSV)

Tài liệu này ghi lại quá trình tạo và xử lý dữ liệu cho các mô hình Machine Learning chạy hoàn toàn ở môi trường local, sử dụng trực tiếp các file dữ liệu tĩnh thay vì kết nối với Google BigQuery.

## 1. Dòng Chảy Dữ Liệu (Data Flow)

Để đáp ứng yêu cầu tiền xử lý dữ liệu và xuất kết quả ra thư mục `data/ML_data`, chúng ta đã tạo một file luồng dữ liệu trung tâm: `data_loader.py`.

### 1.1 `data_loader.py`
- **Quá trình quét và đọc**: File này sẽ tìm kiếm trong thư mục `data/processed/` lấy dữ liệu của 4 ngân hàng (BID, CTG, TCB, VCB). Nó ưu tiên đọc các file báo cáo tài chính hàng năm (`*_balance_sheet_annual.csv`, `*_income_statement_annual.csv`, `*_financial_ratios_annual.csv`).
- **Ghép nối (Merge & Concat)**: Các file của cùng một ngân hàng sẽ được ghép với nhau (Merge outer) theo cột `period` (Năm). Cuối cùng, dữ liệu của cả 4 ngân hàng được nối (Concat) thành một tệp tổng hợp chứa tất cả các biến số CAMELS.
- **Xử lý NPL Ratio**: Cột `npl` được ánh xạ thành `npl_ratio` để chuẩn bị cho nhãn phân loại rủi ro tín dụng. Nếu có giá trị trống (NaN), nó sẽ được điền bằng trung vị (median) theo chuẩn tài liệu `AGENTS.md`.
- **Cổ phiếu BID**: Dữ liệu lịch sử giá cổ phiếu (`bid_stock_history.csv`) được đọc riêng, đổi tên cột theo đúng chuẩn yêu cầu của LSTM (date_key, close_price, open_price, v.v.), và tính toán phần trăm thay đổi giá.
- **Kết quả xuất ra**: 
  - `data/ML_data/banks_camels_data.csv`: Chứa dữ liệu tài chính của 4 ngân hàng.
  - `data/ML_data/bid_lstm_data.csv`: Chứa chuỗi thời gian giá cổ phiếu BID.

## 2. Các Mô Hình Thực Thi

Toàn bộ các thuật toán dưới đây đều đọc data từ `data/ML_data/` và xuất kết quả CSV vào cùng thư mục. Không dùng API kết nối BigQuery.

### 2.1 LSTM (Dự báo cổ phiếu) - `train_lstm_local.py`
- Lấy `bid_lstm_data.csv`.
- Dùng MinMaxScaler và biến chuỗi thời gian thành các cửa sổ 5 ngày.
- Mô hình LSTM sẽ học và xuất ra 5 bước thời gian tiếp theo (T+1 đến T+5).
- Output: `lstm_predictions_local.csv`.

### 2.2 K-Means (Phân cụm) - `train_kmeans_local.py`
- Lấy `banks_camels_data.csv` (chỉ xét kỳ báo cáo mới nhất của 4 ngân hàng).
- Tiền xử lý: Điền các giá trị thiếu (NaN) bằng 0 (hoặc median) cho các feature. Dùng `StandardScaler` và `PCA` giữ lại 80% phương sai.
- Chạy K-Means với k=2 (vì chúng ta chỉ có 4 mẫu dữ liệu cục bộ).
- Output: `kmeans_clusters_local.csv`.

### 2.3 Random Forest (Phân loại nợ xấu) - `train_random_forest_local.py`
- Đọc `banks_camels_data.csv`, tạo label: `1` nếu `npl_ratio >= 0.03`, ngược lại `0`.
- Chạy phân tách Train/Test dựa vào thời gian (period).
- Train RF Classifier với class weight cân bằng (balanced).
- Xuất độ quan trọng của đặc trưng để biết biến CAMELS nào có sức ảnh hưởng mạnh nhất tới nợ xấu.
- Output: `rf_predictions_local.csv` và `rf_feature_importance_local.csv`.

## 3. Cách Sử Dụng
Tại thư mục gốc của dự án, chạy lần lượt các lệnh:
1. `python3 src/models/local/data_loader.py` (Để sinh data vào `data/ML_data/`)
2. `python3 src/models/local/train_lstm_local.py`
3. `python3 src/models/local/train_kmeans_local.py`
4. `python3 src/models/local/train_random_forest_local.py`

Tất cả các file mô hình đều đã hoạt động trơn tru trong môi trường cục bộ và đã được test thành công. Môi trường đã sẵn sàng để tích hợp BigQuery sau khi bên pipeline xử lý xong.
