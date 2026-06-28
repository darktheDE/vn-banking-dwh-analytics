# Kết Quả Chạy Mô Hình ML (Local) — result.md

> Ngày chạy: 2026-06-28
> Người thực hiện: Phạm Minh Quân (Track C — Machine Learning)

---

## 1. Tổng Quan Pipeline

Toàn bộ 3 mô hình ML đã được chạy thành công trên dữ liệu local (không cần BigQuery).
Dữ liệu đầu vào từ `data/processed/`, sau khi xử lý được xuất ra `data/ML_data/`.

| Bước | File Script | Trạng thái |
|------|-------------|------------|
| Chuẩn bị dữ liệu | `data_loader.py` | ✅ Thành công |
| LSTM (Dự báo giá BID) | `train_lstm_local.py` | ✅ Thành công |
| K-Means (Phân cụm ngân hàng) | `train_kmeans_local.py` | ✅ Thành công |
| Random Forest (Phân loại rủi ro) | `train_random_forest_local.py` | ✅ Thành công |

---

## 2. Dữ Liệu Đã Xử Lý (data/ML_data/)

### 2.1 Dữ liệu đầu vào cho ML

| File | Mô tả | Kích thước |
|------|--------|------------|
| `banks_camels_46.csv` | Dữ liệu CAMELS 45 ngân hàng (2002-2022) từ `fact_bank_performance_clean.csv` ghép với `dim_bank_clean.csv` | 667 dòng x 36 cột |
| `bid_lstm_data.csv` | Lịch sử giá cổ phiếu BID (2014-2026) từ `bid/bid_stock_history.csv` | 3096 dòng x 8 cột |
| `banks_4_financial_ratios.csv` | Tỷ số tài chính chi tiết của 4 ngân hàng BID/CTG/TCB/VCB (bổ sung) | 32 dòng x 55 cột |

### 2.2 Kết quả xuất ra

| File | Mô tả |
|------|--------|
| `lstm_predictions_local.csv` | Dự báo giá BID từ T+1 đến T+5 |
| `kmeans_clusters_local.csv` | Phân cụm 45 ngân hàng |
| `rf_predictions_local.csv` | Kết quả phân loại rủi ro nợ xấu |
| `rf_feature_importance_local.csv` | Độ quan trọng của các đặc trưng |
| `figures/` | Các biểu đồ PCA, Elbow, Silhouette, Feature Importance, ROC |

---

## 3. Kết Quả Chi Tiết Từng Mô Hình

### 3.1 LSTM — Dự báo giá cổ phiếu BID

**Dữ liệu**: 3096 ngày giao dịch (24/01/2014 – 26/06/2026)
**Features**: close_price, open_price, high_price, low_price, trading_volume, price_change_pct, volume_change_pct
**Kiến trúc**: LSTM(64) → Dropout(0.2) → Dense(32, relu) → Dense(5)
**Training**: 50 epochs (EarlyStopping dừng tại epoch 22), batch_size=16

| Horizon | RMSE | MAE | MAPE |
|---------|------|-----|------|
| T+1 | 1.1329 | 0.7717 | 1.87% |
| T+2 | 1.4381 | 0.9873 | 2.40% |
| T+3 | 1.6716 | 1.1412 | 2.77% |
| T+4 | 1.8076 | 1.2191 | 2.96% |
| T+5 | 2.0691 | 1.4424 | 3.50% |
| **Overall** | **1.6549** | **1.1123** | — |

**Dự báo T+1 đến T+5 (từ ngày 26/06/2026):**

| Horizon | Giá dự báo (nghìn VND) |
|---------|------------------------|
| T+1 | 41.16 |
| T+2 | 41.03 |
| T+3 | 40.93 |
| T+4 | 40.94 |
| T+5 | 40.59 |

**Nhận xét**: MAPE T+1 chỉ 1.87%, mô hình LSTM dự báo khá chính xác cho horizons ngắn. Sai số tăng dần khi dự báo xa hơn, điều này phù hợp với đặc tính của chuỗi thời gian tài chính. *(Chưa so sánh với ARIMA baseline vì baseline chạy riêng trên BigQuery.)*

---

### 3.2 K-Means + PCA — Phân cụm 45 ngân hàng

**Dữ liệu**: 45 ngân hàng (snapshot năm mới nhất mỗi ngân hàng)
**Features**: 11 chỉ số CAMELS (npl_ratio, llp_ratio, roa, roe, nim, cir, eta, etd, lta, ltd, gta)
**Tiền xử lý**: StandardScaler → PCA

| Chỉ số | Giá trị |
|--------|---------|
| Số thành phần PCA | 4 (giải thích 82.67% phương sai) |
| Số cụm tối ưu (k) | 2 |
| **Silhouette Score** | **0.7098** (tốt — gần 1 nghĩa là cụm rõ ràng) |
| **Davies-Bouldin Index** | **0.1914** (rất tốt — càng thấp càng tốt) |

**Phân bổ cụm:**

| Cluster | Số ngân hàng | Đặc điểm |
|---------|-------------|----------|
| 0 | 44 | Nhóm chính: BID, CTG, VCB, TCB, ACB, MB, VPB... (các ngân hàng hoạt động bình thường) |
| 1 | 1 | DAB — ngân hàng có chỉ số tài chính ngoại lai (outlier) |

**Nhận xét**: Silhouette Score 0.71 là rất tốt, cho thấy cụm được phân tách rõ ràng. Tuy nhiên k=2 với chỉ 1 ngân hàng ở cluster 1 cho thấy DAB là một outlier rõ rệt. Khi chạy với 46 ngân hàng đầy đủ trên BigQuery, kỳ vọng sẽ có 3-4 cụm phân biệt (quốc doanh, cổ phần, ngoại) theo giả thuyết Q4.

---

### 3.3 Random Forest — Phân loại rủi ro tín dụng (NPL >= 3%)

**Dữ liệu**: 661 quan sát (sau khi loại null), 45 ngân hàng, chia 80/20 theo thời gian
**Target**: risk_label = 1 nếu npl_ratio >= 3%, ngược lại = 0
**Phân bổ nhãn**: 588 Healthy (0) / 79 High Risk (1)

| Chỉ số | Giá trị | Ngưỡng chấp nhận | Trạng thái |
|--------|---------|-------------------|------------|
| **AUC-ROC** | **0.9568** | > 0.80 | ✅ ĐẠT |
| **Recall (High Risk)** | **0.2143** | >= 0.85 | ⚠️ CHƯA ĐẠT |
| F1-Score (High Risk) | 0.3333 | — | — |
| Accuracy | 0.91 | — | — |

**Top 5 Feature Importance:**

| Thứ tự | Đặc trưng | Importance |
|--------|-----------|------------|
| 1 | `llp_ratio` (Tỷ lệ dự phòng rủi ro) | 0.2105 |
| 2 | `roe` (Tỷ suất sinh lời trên vốn CSH) | 0.1149 |
| 3 | `cir` (Tỷ lệ chi phí trên thu nhập) | 0.1103 |
| 4 | `roa` (Tỷ suất sinh lời trên tổng TS) | 0.0985 |
| 5 | `lta` (Tỷ lệ cho vay trên tổng TS) | 0.0492 |

**Nhận xét**:
- **AUC-ROC 0.9568** vượt xa ngưỡng 0.80 → mô hình phân biệt rất tốt giữa 2 nhóm rủi ro.
- **Recall 0.2143 chưa đạt ngưỡng 0.85**: Nguyên nhân là dữ liệu mất cân bằng nặng (chỉ 14 mẫu High Risk trong tập test). Khi tích hợp BigQuery với đầy đủ 46 ngân hàng x 20 năm, có thể cải thiện bằng cách:
  - Tăng cường dữ liệu (SMOTE oversampling)
  - Điều chỉnh ngưỡng quyết định (threshold tuning) thay vì mặc định 0.5
  - Thêm hyperparameter tuning (GridSearchCV)
- **Feature Importance**: `llp_ratio` (tỷ lệ dự phòng rủi ro) là yếu tố quan trọng nhất, tiếp theo là `roe` và `cir` — phù hợp với giả thuyết Q3 của dự án.

---

## 4. Đối Chiếu Với Task (docs/tasks.md)

| Task ID | Mô tả | Trạng thái Local |
|---------|-------|-------------------|
| C-01 | Feature Engineering cổ phiếu | ✅ Đã tính price_change_pct, volume_change_pct |
| C-02 | Feature Engineering ngân hàng | ✅ Đã dùng 11 chỉ số CAMELS + StandardScaler |
| C-03 | ARIMA Baseline | ⏳ Chưa chạy (cần BigQuery hoặc viết thêm baseline local) |
| C-04 | LSTM Train | ✅ Chạy thành công, RMSE=1.65, MAPE T+1=1.87% |
| C-05 | LSTM Predictions → BigQuery | ⏳ Xuất CSV local. Chờ BigQuery để đẩy lên |
| C-06 | PCA cho ngân hàng | ✅ 4 components, 82.67% variance |
| C-07 | K-Means Elbow + Silhouette | ✅ k=2, Silhouette=0.71 |
| C-08 | K-Means Predictions → BigQuery | ⏳ Xuất CSV local. Chờ BigQuery |
| C-09 | Logistic Regression Baseline | ⏳ Chưa chạy (cần BigQuery hoặc viết thêm) |
| C-10 | Random Forest Train | ✅ AUC-ROC=0.96, Recall=0.21 (cần cải thiện) |
| C-11 | Feature Importance | ✅ llp_ratio là feature quan trọng nhất |
| C-12 | RF Predictions → BigQuery | ⏳ Xuất CSV local. Chờ BigQuery |

---

## 5. Biểu Đồ Đã Sinh Ra (data/ML_data/figures/)

1. `pca_explained_variance.png` — Biểu đồ phương sai tích lũy PCA
2. `kmeans_elbow_silhouette.png` — Biểu đồ Elbow và Silhouette cho K-Means
3. `kmeans_cluster_scatter.png` — Bản đồ phân cụm trên PC1-PC2
4. `rf_feature_importance.png` — Biểu đồ độ quan trọng đặc trưng
5. `rf_roc_curve.png` — Đường cong ROC

---

## 6. Hướng Dẫn Chạy Lại

```bash
# Từ thư mục gốc dự án
python3 src/models/local/data_loader.py
python3 src/models/local/train_lstm_local.py
python3 src/models/local/train_kmeans_local.py
python3 src/models/local/train_random_forest_local.py
```

## 7. Bước Tiếp Theo

1. **Chờ BigQuery sẵn sàng**: Khi team ETL hoàn thành pipeline, chỉ cần thay đổi phần đọc data từ CSV sang BigQuery query trong các file `src/models/` chính thức.
2. **Cải thiện Recall RF**: Áp dụng threshold tuning hoặc SMOTE.
3. **Chạy ARIMA baseline**: So sánh RMSE với LSTM để đạt acceptance criteria.
4. **Chạy Logistic Regression baseline**: So sánh AUC-ROC với Random Forest.
