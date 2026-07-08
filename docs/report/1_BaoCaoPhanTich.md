# 1. BÁO CÁO PHÂN TÍCH

## 1.1. Tóm tắt điều hành — Executive Summary

Dự án **"Phân tích Dữ liệu Tài chính Ngân hàng Việt Nam"** xây dựng một nền tảng phân tích dữ liệu đầu-cuối end-to-end, tích hợp Kho dữ liệu đám mây Google BigQuery và ba mô hình Học máy nhằm chuyển hóa dữ liệu tài chính thô thành các insight hỗ trợ ra quyết định.

**Các phát hiện quan trọng:**

| Mô hình | Kết quả chính | Ý nghĩa kinh doanh |
|---------|---------------|---------------------|
| **LSTM** | RMSE thấp hơn ARIMA cho cả 4 mã BID, TCB, VCB, CTG — cụ thể BID LSTM RMSE = 0.88 vs ARIMA = 1.17 | Dự báo giá ngắn hạn T+1 đến T+5 đáng tin cậy hơn phương pháp thống kê truyền thống |
| **K-Means + PCA** | Silhouette Score = 0.74, tách biệt rõ ràng 3 nhóm ngân hàng | Xác nhận sự phân hóa chiến lược giữa SOCB, JSCB lớn và FOCB |
| **Random Forest** | AUC-ROC = 0.975, Recall lớp High Risk = 91.67% | Hệ thống cảnh báo sớm nợ xấu đạt độ nhạy vượt ngưỡng yêu cầu 85% |

**Khuyến nghị chính:**
1. Kích hoạt hệ thống giám sát dòng tiền khối ngoại và tự doanh theo ngày để hỗ trợ quyết định giao dịch ngắn hạn.
2. Sử dụng kết quả phân cụm để xây dựng chiến lược phân bổ vốn dài hạn, ưu tiên nhóm ngân hàng duy trì cân bằng giữa biên lãi ròng và dự phòng rủi ro.
3. Triển khai bảng giám sát rủi ro tín dụng — Risk Monitoring Dashboard — cho các ngân hàng bị phân loại "Nguy Cơ Cao" để can thiệp kịp thời.

---

## 1.2. Mục tiêu và Phạm vi — Objective and Scope

### Mục tiêu nghiên cứu

Dự án được dẫn dắt bởi bốn mục tiêu cốt lõi:

1. **Xây dựng Kho dữ liệu tập trung:** Thiết kế và triển khai Data Warehouse trên Google BigQuery với kiến trúc Star Schema gồm 5 bảng Dimension, 5 bảng Fact, 3 bảng ML Output, đảm bảo tính toàn vẹn và tối ưu truy vấn.
2. **Đo lường sự phân hóa hệ thống ngân hàng:** Sử dụng PCA giảm chiều từ 47+ biến tài chính và K-Means phân cụm 46 ngân hàng để xác định các nhóm chiến lược hoạt động.
3. **Đánh giá chất lượng dự báo và phân loại:** So sánh LSTM với ARIMA trong bài toán dự báo giá, và Random Forest với Logistic Regression trong bài toán phân loại rủi ro thông qua các chỉ số RMSE, AUC-ROC, Recall.
4. **Chuyển hóa kết quả thành Dashboard tương tác:** Trực quan hóa insight trên Streamlit Dashboard kết nối trực tiếp BigQuery, phục vụ hai nhóm đối tượng: Nhà quản trị rủi ro và Nhà phân tích đầu tư.

### Phạm vi dữ liệu

| Phạm vi | Chi tiết |
|---------|----------|
| **Dữ liệu cổ phiếu** | Lịch sử giá OHLCV hàng ngày của 4 mã: BID, TCB, VCB, CTG — khoảng 11,835 dòng |
| **Dữ liệu tài chính ngân hàng** | 45 ngân hàng thương mại, 47+ chỉ số CAMELS, giai đoạn 2002–2022 — khoảng 667 dòng |
| **Ngoài phạm vi** | Giao dịch thuật toán tự động HFT, phân tích ngôn ngữ tự nhiên NLP, mở rộng toàn bộ VN-Index |

### Câu hỏi nghiên cứu và Giả thuyết

**Q1:** Mô hình LSTM đa biến (kết hợp OHLCV và phần trăm biến động) có vượt trội hơn mô hình LSTM đơn biến và mô hình baseline ARIMA trong việc dự báo giá đóng cửa ngắn hạn của các cổ phiếu ngân hàng không?
> **Giả thuyết:** Mô hình LSTM đa biến đạt sai số RMSE và MAE thấp hơn so với cả mô hình LSTM đơn biến và ARIMA, nhờ bổ sung các đặc trưng động lực học về khối lượng giao dịch và biên độ dao động.

**Q2:** Xu hướng biến động giá đóng cửa ngắn hạn của 4 cổ phiếu ngân hàng BID, TCB, VCB, CTG có sự đồng pha hay phân hóa?
> **Giả thuyết:** Có sự đồng pha mạnh mẽ trong ngắn hạn giữa các cổ phiếu thuộc nhóm quốc doanh gồm BID, VCB, CTG, trong khi nhóm cổ phần tư nhân như TCB có xu hướng biến động độc lập hơn.

**Q3:** Những chỉ số tài chính nào quyết định việc một ngân hàng rơi vào nhóm có rủi ro nợ xấu cao?
> **Giả thuyết:** Các ngân hàng có chỉ số CIR — tỷ lệ chi phí trên thu nhập — ở mức cao và chỉ số ETA — tỷ lệ vốn chủ sở hữu trên tổng tài sản — ở mức thấp sẽ có khả năng rơi vào nhóm rủi ro nợ xấu vượt mức 3%.

**Q4:** Có thể phân loại rõ rệt chiến lược hoạt động của các nhóm ngân hàng tại Việt Nam dựa trên dữ liệu tài chính không?
> **Giả thuyết:** Phân tích dữ liệu sẽ tách biệt rõ ràng hệ thống thành 3 cụm chính: Ngân hàng quốc doanh tối ưu quy mô, Ngân hàng cổ phần tối ưu lợi nhuận, và Ngân hàng ngoại tối ưu an toàn vốn.
