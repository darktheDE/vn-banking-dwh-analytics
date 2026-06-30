# 2. PHÂN LOẠI BÁO CÁO PHÂN TÍCH

Dự án "Phân tích Dữ liệu Tài chính Ngân hàng Việt Nam" bao phủ đầy đủ cả **bốn cấp độ phân tích dữ liệu**, từ mô tả hiện trạng đến đề xuất hành động. Mỗi cấp độ được ánh xạ trực tiếp vào các thành phần kỹ thuật cụ thể của dự án.

---

## 2.1. Ánh xạ bốn cấp độ phân tích vào dự án

| Cấp độ phân tích | Câu hỏi cốt lõi | Thành phần dự án tương ứng | Đối tượng sử dụng |
|:---|:---|:---|:---|
| **Mô tả — Descriptive** | Điều gì đã xảy ra trong hệ thống ngân hàng Việt Nam suốt 20 năm qua? | EDA trên Dashboard: Phân phối chỉ số CAMELS, xu hướng ROA/ROE/NIM theo thời gian, ma trận tương quan. Star Schema DWH lưu trữ toàn bộ lịch sử. | Nhà phân tích dữ liệu, Giảng viên |
| **Chẩn đoán — Diagnostic** | Tại sao một số ngân hàng lại có nợ xấu cao hơn? | K-Means + PCA phân cụm 46 ngân hàng để bộc lộ sự phân hóa cấu trúc. Feature Importance từ Random Forest chỉ ra nguyên nhân gốc rễ bao gồm llp_ratio, ROE, CIR. | Nhà quản trị rủi ro, Chuyên viên chiến lược |
| **Dự đoán — Predictive** | Giá cổ phiếu ngân hàng sẽ biến động như thế nào trong 5 ngày tới? Ngân hàng nào có nguy cơ nợ xấu vượt 3%? | LSTM dự báo giá T+1 đến T+5 cho BID, TCB, VCB, CTG. Random Forest phân loại rủi ro tín dụng: Healthy vs High Risk. | Nhà đầu tư, Bộ phận tự doanh |
| **Đề xuất — Prescriptive** | Nên phân bổ vốn và giám sát ngân hàng nào? | Bảng giám sát rủi ro trên Dashboard — Risk Monitoring Table — với cảnh báo màu sắc. Khuyến nghị cụ thể dựa trên kết quả phân cụm và phân loại. | Ban điều hành cấp cao, Trưởng bộ phận |

---

## 2.2. Phân loại theo dạng báo cáo

Dự án sinh ra bốn dạng báo cáo phân tích cụ thể, mỗi dạng phục vụ một mục đích nghiệp vụ khác nhau:

### Báo cáo Khám phá — Exploratory
- **Mục đích:** Khám phá các mẫu hình ẩn trong dữ liệu tài chính 20 năm.
- **Phương pháp:** Phân tích khám phá dữ liệu — EDA — thông qua biểu đồ phân phối, ma trận tương quan Pearson, biểu đồ xu hướng theo thời gian.
- **Ví dụ cụ thể:** Phát hiện mối tương quan cực mạnh với hệ số > 0.8 giữa ROA và ROE; xác nhận CIR tương quan âm rõ rệt với khả năng sinh lời.

### Báo cáo Xác nhận — Confirmatory
- **Mục đích:** Xác thực hoặc bác bỏ bốn giả thuyết nghiên cứu đã đặt ra.
- **Phương pháp:** So sánh kết quả mô hình với ngưỡng chấp nhận Acceptance Criteria đã định trước.
- **Ví dụ cụ thể:** Giả thuyết "LSTM vượt trội hơn ARIMA" được xác nhận khi LSTM RMSE của BID = 0.88 thấp hơn ARIMA RMSE = 1.17 trên cùng tập kiểm thử.

### Báo cáo Dự đoán — Predictive
- **Mục đích:** Dự báo kết quả tương lai để hỗ trợ quyết định đầu tư và quản trị rủi ro.
- **Phương pháp:** Mô hình LSTM cho dự báo chuỗi thời gian và Random Forest cho phân loại nhị phân.
- **Ví dụ cụ thể:** Bảng dự phóng giá đóng cửa BID cho 5 ngày giao dịch tiếp theo từ T+1 đến T+5. Bảng phân loại 46 ngân hàng thành "An Toàn" hoặc "Nguy Cơ Cao" kèm xác suất dự đoán.

### Báo cáo Đề xuất hành động — Prescriptive
- **Mục đích:** Đưa ra các hành động cụ thể, có thể thực hiện ngay.
- **Phương pháp:** Tổng hợp insight từ cả ba mô hình và trình bày trên Dashboard tương tác.
- **Ví dụ cụ thể:** Đề xuất "Gia tăng tỷ trọng giải ngân ngắn hạn khi phát hiện dòng tiền tự doanh dương kết hợp lệnh mua chủ động đột biến" hoặc "Thắt chặt quy trình tín dụng đối với nhóm ngân hàng bị gắn nhãn Nguy Cơ Cao".
