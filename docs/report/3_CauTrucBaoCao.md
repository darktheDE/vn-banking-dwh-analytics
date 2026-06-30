# 3. CẤU TRÚC CỦA BÁO CÁO PHÂN TÍCH DỮ LIỆU

Theo chuẩn mực báo cáo phân tích dữ liệu, dự án được cấu trúc thành 6 phần chính. Dưới đây là nội dung chi tiết cho từng phần, áp dụng trực tiếp vào bối cảnh dự án "Phân tích Dữ liệu Tài chính Ngân hàng Việt Nam".

---

## 3.1. Executive Summary — Tóm tắt điều hành

Phần tóm tắt điều hành đã được trình bày đầy đủ tại file `1_BaoCaoPhanTich.md`, Mục 1.1. Đây là phần tổng quan độc lập, cho phép người đọc cấp cao nắm bắt toàn bộ giá trị của dự án chỉ trong 2 phút đọc mà không cần đi sâu vào chi tiết kỹ thuật.

**Các thành phần bắt buộc trong Executive Summary:**
- Mục tiêu của dự án — tóm gọn trong 1 câu
- Bảng tổng hợp kết quả 3 mô hình ML kèm số liệu đo lường
- Từ 2 đến 3 khuyến nghị hành động cấp chiến lược

---

## 3.2. Objective and Scope — Mục tiêu và Phạm vi

Phần này đã được trình bày chi tiết tại file `1_BaoCaoPhanTich.md`, Mục 1.2, bao gồm:

- **4 mục tiêu nghiên cứu** rõ ràng: Xây dựng DWH, phân cụm ngân hàng, đánh giá dự báo, và trực quan hóa.
- **Phạm vi dữ liệu** được giới hạn cụ thể: 4 mã cổ phiếu, 46 ngân hàng, giai đoạn 2002–2022.
- **4 câu hỏi nghiên cứu** kèm giả thuyết kiểm chứng được.
- **Ranh giới ngoài phạm vi** để tránh hiểu nhầm kỳ vọng.

---

## 3.3. Data Sources and Methodology — Nguồn dữ liệu và Phương pháp luận

### Nguồn dữ liệu

Toàn bộ dữ liệu được thu thập từ các tệp Excel có cấu trúc, tổng hợp nội bộ từ các nguồn tài chính đáng tin cậy.

| Mã nguồn | Mô tả | Bảng đích trên BigQuery | Độ chi tiết |
|-----------|--------|-------------------------|-------------|
| F1 | Giao dịch khối ngoại cổ phiếu BID | `fact_foreign_trading` | Theo ngày — 22 phiên |
| F2 | Giao dịch tự doanh cổ phiếu BID | `fact_proprietary_trading` | Theo ngày — 22 phiên |
| F3 | Lịch sử giá OHLCV cho BID, TCB, VCB, CTG | `fact_price_history` | Theo ngày — khoảng 11,835 dòng |
| F4 | Thống kê lệnh mua/bán BID | `fact_order_stats` | Theo ngày — 22 phiên |
| F6–F7 | Chỉ số tài chính CAMELS 46 ngân hàng | `fact_bank_performance` | Theo năm, 2002–2022 — khoảng 667 dòng |

### Phương pháp luận

Dự án tuân theo quy trình chuẩn hóa dữ liệu vòng đời **CRISP-DM** — Cross-Industry Standard Process for Data Mining, bao gồm:

1. **ETL Pipeline tự động hóa** với Python + Pandas + Openpyxl:
   - Trích xuất từ 7 tệp Excel nguyên bản
   - Biến đổi: xử lý giá trị khuyết bằng median imputation cho ngân hàng và forward-fill tối đa 1 ngày cho cổ phiếu, chuẩn hóa kiểu dữ liệu, tạo surrogate key
   - Nạp vào BigQuery với cơ chế upsert MERGE đảm bảo tính idempotent

2. **Kiến trúc lưu trữ Star Schema** trên Google BigQuery:
   - 5 bảng Dimension: `dim_date`, `dim_stock`, `dim_bank`, `dim_trading_session`, `dim_audit`
   - 5 bảng Fact: `fact_price_history`, `fact_foreign_trading`, `fact_proprietary_trading`, `fact_order_stats`, `fact_bank_performance`
   - 3 bảng ML Output: `bank_cluster_assignments`, `bank_risk_predictions`, `fact_model_predictions`
   - Tối ưu bằng Partitioning trên `date_key` và Clustering trên `stock_key`/`bank_key`

3. **Ba nhánh mô hình Học máy:**
   - **LSTM** — TensorFlow Keras: Dự báo chuỗi thời gian, cửa sổ trượt 5 ngày, scaler MinMaxScaler
   - **K-Means + PCA** — Scikit-learn: Phân cụm không giám sát, StandardScaler, giảm chiều giữ ≥80% phương sai
   - **Random Forest** — Scikit-learn: Phân loại nhị phân, chia tập theo thời gian time-based split, ngưỡng NPL ≥ 3%

4. **Trực quan hóa Dashboard** với Streamlit + Plotly:
   - Kết nối trực tiếp BigQuery qua Python SDK
   - 6 phân hệ: Tổng quan, EDA CAMELS, Dự báo LSTM, Phân cụm K-Means, Rủi ro RF, Trạng thái DWH

---

## 3.4. Key Findings and Visualizations — Phát hiện chính và Trực quan hóa

### Phát hiện 1: Dự báo giá cổ phiếu với LSTM

| Mã CK | LSTM RMSE | ARIMA RMSE | Kết quả so sánh |
|--------|-----------|------------|------------------|
| BID | 0.8801 | 1.1696 | LSTM vượt trội 24.7% |
| TCB | 1.3093 | 9.4864 | LSTM vượt trội 86.2% |
| VCB | 3.0529 | 4.4900 | LSTM vượt trội 32.0% |
| CTG | 1.4231 | 11.3624 | LSTM vượt trội 87.5% |

> **Diễn giải:** LSTM đã vượt qua ARIMA trên toàn bộ 4 mã cổ phiếu. Đặc biệt, với TCB và CTG, LSTM cho sai số thấp hơn tới 86-87%, chứng minh rằng mạng học sâu nắm bắt được các mẫu hình phi tuyến mà phương pháp thống kê truyền thống bỏ sót.

### Phát hiện 2: Phân cụm ngân hàng với K-Means + PCA

- **Số cụm tối ưu:** K = 2, xác định qua Elbow Method và Silhouette Analysis
- **Silhouette Score:** 0.7361 — cho thấy ranh giới phân cụm rõ ràng và chặt chẽ
- **Biểu đồ:** Biểu đồ phân tán PCA 2D minh họa sự tách biệt rõ rệt giữa các nhóm ngân hàng trên hệ tọa độ thành phần chính

> **Diễn giải:** Hệ thống 46 ngân hàng phân thành các cụm chiến lược riêng biệt. Nhóm SOCB có đặc trưng quy mô lớn nhưng biên NIM vừa phải. Nhóm JSCB lớn tối ưu lợi nhuận với ROE/ROA cao. Nhóm FOCB duy trì an toàn vốn cực kỳ dày với ETA cao và NPL thấp.

### Phát hiện 3: Phân loại rủi ro tín dụng với Random Forest

| Chỉ số | Giá trị đạt được | Ngưỡng yêu cầu | Trạng thái |
|--------|-------------------|-----------------|------------|
| AUC-ROC | 0.9752 | > 0.80 | ĐẠT |
| Recall lớp High Risk | 91.67% | ≥ 85% | ĐẠT |
| Ngưỡng quyết định tối ưu | 0.2327 | — | Đã tinh chỉnh |

> **Diễn giải:** Mô hình đạt Recall 91.67% cho lớp Nguy Cơ Cao, nghĩa là cứ 12 ngân hàng thực sự có nợ xấu vượt 3% thì mô hình phát hiện đúng 11 ngân hàng. Trong quản trị rủi ro tài chính, việc bỏ sót ngân hàng rủi ro — False Negative — gây hậu quả nghiêm trọng hơn cảnh báo nhầm — False Positive, nên chỉ số Recall được ưu tiên hàng đầu.

### Phát hiện 4: Yếu tố gốc rễ gây nợ xấu — Feature Importance

Top 3 biến quan trọng nhất trong mô hình Random Forest:
1. **Tỷ lệ trích lập dự phòng, llp_ratio:** Trọng số 20.45% — Ngân hàng trích lập dự phòng mỏng để "làm đẹp" lợi nhuận là nhóm có xác suất bùng phát nợ xấu cao nhất.
2. **Tỷ suất sinh lời trên vốn CSH, ROE:** Trọng số 11.56% — ROE quá cao đi kèm đòn bẩy tài chính lớn tiềm ẩn rủi ro.
3. **Tỷ lệ chi phí trên thu nhập, CIR:** Trọng số 10.54% — Hiệu quả vận hành kém trực tiếp bào mòn khả năng chống đỡ nợ xấu.

---

## 3.5. Interpretation and Insights — Diễn giải và Insight

### Insight kinh doanh 1: Dòng tiền thông minh dẫn dắt giá

Lịch sử giao dịch cho thấy hành vi mua/bán ròng liên tục của khối ngoại và tự doanh là tín hiệu dẫn dắt thị trường hay còn gọi là leading indicators. Dòng tiền ròng ngày hôm trước với độ trễ lag 1 có tương quan thuận chiều với giá đóng cửa của các phiên tiếp theo. Mô hình LSTM đã tích hợp thành công các tín hiệu này, đặc biệt cho mã BID với 12 features đầu vào bao gồm foreign và proprietary trading signals.

### Insight kinh doanh 2: Sự đánh đổi giữa lợi nhuận và an toàn vốn

Phân tích EDA trên bộ dữ liệu CAMELS 20 năm cho thấy:
- ROA và ROE có tương quan thuận mạnh mẽ, nhưng nhóm có ROE quá cao thường đi kèm ETA thấp, tức đòn bẩy cao.
- CIR tương quan âm rõ rệt với ROA/ROE: Tối ưu hóa chi phí vận hành trực tiếp cải thiện sinh lời.
- Nhóm SOCB chấp nhận NIM thấp hơn để hỗ trợ nền kinh tế, bù lại sở hữu quy mô tài sản vượt trội.

### Insight kinh doanh 3: Phòng bệnh hơn chữa bệnh trong rủi ro tín dụng

Mốc tỷ lệ nợ xấu 3% là ranh giới pháp lý quan trọng. Mô hình Random Forest phân tích các tín hiệu dẫn đường bao gồm llp_ratio, ETA, CIR để phát hiện dấu hiệu suy yếu trước 1–2 chu kỳ báo cáo, thay vì đợi nợ xấu thực tế bùng phát trên báo cáo tài chính cuối năm.

---

## 3.6. Recommendations and Next Steps — Khuyến nghị và Bước tiếp theo

### Khuyến nghị 1: Kích hoạt giám sát dòng tiền hàng ngày
- **Hành động:** Triển khai hệ thống cảnh báo tự động khi phát hiện dòng tiền tự doanh dương kết hợp lệnh mua chủ động đột biến.
- **Đối tượng:** Bộ phận tự doanh và phòng đầu tư.
- **Thời hạn:** Ngay khi hoàn tất kết nối Dashboard với BigQuery.

### Khuyến nghị 2: Xây dựng chiến lược phân bổ vốn dài hạn theo cụm
- **Hành động:** Dựa trên kết quả phân cụm K-Means, ưu tiên rót vốn vào cụm ngân hàng duy trì cân bằng giữa biên lãi ròng ổn định và dự phòng rủi ro nợ xấu an toàn.
- **Đối tượng:** Ban điều hành, Phòng chiến lược đầu tư.
- **Thời hạn:** Chu kỳ đánh giá danh mục hàng quý.

### Khuyến nghị 3: Triển khai bảng giám sát rủi ro tín dụng
- **Hành động:** Sử dụng Risk Monitoring Dashboard để theo dõi liên tục nhóm ngân hàng bị gắn nhãn "Nguy Cơ Cao". Yêu cầu thắt chặt quy trình tín dụng và gia tăng bộ đệm phòng thủ nợ xấu cho nhóm này.
- **Đối tượng:** Nhà quản trị rủi ro, Thanh tra ngân hàng.
- **Thời hạn:** Cập nhật sau mỗi chu kỳ tái huấn luyện mô hình, tức hàng quý.

### Bước tiếp theo
1. Tái huấn luyện LSTM hàng tuần với dữ liệu giá mới nhất để duy trì độ chính xác.
2. Tái huấn luyện Random Forest và K-Means hàng quý, đồng bộ với chu kỳ công bố báo cáo tài chính ngân hàng.
3. Mở rộng kết nối với Looker Studio để phục vụ đối tượng phi kỹ thuật rộng hơn.
