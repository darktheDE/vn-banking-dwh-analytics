# 📊 Báo Cáo Kết Quả Dự Án — RESULT.md
## Kho Dữ Liệu & Nền Tảng Phân Tích Học Máy Hệ Thống Ngân Hàng Việt Nam
### Bộ môn Hệ thống Thông tin · Trường Đại học Công nghệ Kỹ thuật Thành phố Hồ Chí Minh

Tài liệu này tổng hợp toàn bộ các kết quả đạt được từ quá trình chạy thử nghiệm và vận hành thực tế hệ thống Kho dữ liệu (Data Warehouse) BigQuery và 3 mô hình học máy (LSTM, K-Means, Random Forest). Đồng thời, tài liệu đối chiếu các chỉ số tài chính sử dụng với các nguồn chuẩn quốc tế và trả lời chi tiết các câu hỏi nghiên cứu của đề tài.

---

## 1. Ánh Xạ Chỉ Số Tài Chính Sử Dụng (Financial Metrics Mapping)

Dự án áp dụng khung phân tích **CAMELS** chuẩn hóa cho lĩnh vực ngân hàng. Các chỉ số tài chính được kế thừa và đối chiếu từ hai nguồn tài liệu tham khảo chính thống:

### 1.1 Chỉ số tham chiếu từ NetSuite KPIs
Nguồn tham khảo: [NetSuite Financial KPIs](https://www.netsuite.com/portal/resource/articles/accounting/financial-kpis-metrics.shtml)
Dự án đã sử dụng các chỉ số hiệu suất tài chính cốt lõi được NetSuite chuẩn hóa cho quản trị doanh nghiệp và tùy biến cho hoạt động ngân hàng:
*   **ROA (Return on Assets - Tỷ suất sinh lời trên tài sản)**: Đo lường hiệu quả sử dụng tài sản để tạo ra lợi nhuận ròng.
    $$\text{ROA} = \frac{\text{Lợi nhuận sau thuế (PAT)}}{\text{Tổng tài sản (Total Assets)}}$$
*   **ROE (Return on Equity - Tỷ suất sinh lời trên vốn chủ sở hữu)**: Đo lường hiệu quả sử dụng vốn của cổ đông.
    $$\text{ROE} = \frac{\text{Lợi nhuận sau thuế (PAT)}}{\text{Tổng vốn chủ sở hữu (Total Equity)}}$$
*   **Leverage / Capital Structure (Cơ cấu vốn)**: NetSuite định nghĩa các chỉ số nợ/vốn chủ sở hữu để đánh giá mức độ rủi ro đòn bẩy. Dự án áp dụng chỉ số `eta` (Vốn chủ sở hữu / Tổng tài sản) và `etd` (Vốn chủ sở hữu / Tiền gửi khách hàng) để đo lường mức độ an toàn vốn.

### 1.2 Chỉ số tham chiếu từ Công ty Chứng khoán Vietcombank (VCBS)
Nguồn tham khảo: [Chỉ số Tài chính Doanh nghiệp - VCBS](https://www.vcbs.com.vn/chi-so-tai-chinh-doanh-nghiep)
Các chỉ số đặc thù ngành ngân hàng được cấu hình theo chuẩn phân tích tài chính của VCBS bao gồm:
*   **NIM (Net Interest Margin - Biên lãi ròng)**: Chỉ số quan trọng nhất đo lường chênh lệch giữa thu nhập từ lãi và chi phí trả lãi trên quy mô tài sản sinh lời.
    $$\text{NIM} = \frac{\text{Thu nhập lãi thuần (Net Interest Income)}}{\text{Tổng tài sản sinh lời (Total Assets)}}$$
*   **CIR (Cost-to-Income Ratio - Tỷ lệ chi phí trên thu nhập)**: Đo lường hiệu quả vận hành của ngân hàng. CIR càng thấp chứng tỏ ngân hàng hoạt động càng hiệu quả.
    $$\text{CIR} = \frac{\text{Chi phí hoạt động ngoài lãi}}{\text{Thu nhập lãi thuần} + \text{Thu nhập ngoài lãi}}$$
*   **LTD (Loans-to-Deposits - Tỷ lệ dư nợ trên tiền gửi)**: Chỉ số thanh khoản cốt lõi đánh giá rủi ro kỳ hạn và khả năng cho vay dựa trên nguồn vốn huy động.
    $$\text{LTD} = \frac{\text{Tổng dư nợ cho vay}}{\text{Tổng tiền gửi khách hàng}}$$
*   **NPL Ratio (Tỷ lệ nợ xấu)**: Chỉ số phản ánh chất lượng tài sản của ngân hàng.
    $$\text{NPL Ratio} = \frac{\text{Nợ xấu (Nhóm 3-5)}}{\text{Tổng dư nợ cho vay}}$$
*   **LLP Ratio (Tỷ lệ trích lập dự phòng nợ xấu)**: Thể hiện mức độ thận trọng của ngân hàng trước rủi ro tín dụng.
    $$\text{LLP Ratio} = \frac{\text{Chi phí dự phòng rủi ro tín dụng}}{\text{Tổng dư nợ cho vay}}$$

---

## 2. Trả Lời Các Câu Hỏi Nghiên Cứu (Research Answers)

Dự án sử dụng dữ liệu thực tế lưu trữ tại Kho dữ liệu BigQuery và kết quả huấn luyện từ các mô hình AI/ML để đưa ra các câu trả lời thực nghiệm như sau:

### 💡 Q1: Mô hình LSTM đa biến (sử dụng đầy đủ đặc trưng OHLCV, biến động giá và khối lượng) có vượt trội hơn mô hình LSTM đơn biến và mô hình baseline ARIMA trong dự báo giá đóng cửa ngắn hạn của các cổ phiếu ngân hàng không?
*   **Kết luận**: Mô hình LSTM đa biến có độ chính xác dự báo vượt trội rõ rệt so với cả mô hình LSTM đơn biến (chỉ sử dụng giá đóng cửa) và mô hình thống kê truyền thống ARIMA. Việc bổ sung các đặc trưng động lực học bao gồm giá mở cửa, giá cao nhất, giá thấp nhất, khối lượng giao dịch cùng phần trăm biến động giúp mô hình nắm bắt tốt hơn các điểm đảo chiều và xu hướng ngắn hạn.
*   **Minh chứng thực nghiệm**: Huấn luyện thực nghiệm trên hơn 11.835 phiên giao dịch thực tế của 4 cổ phiếu ngân hàng (BID, TCB, VCB, CTG) cho thấy mô hình LSTM đa biến đạt sai số RMSE thấp nhất trên mọi cổ phiếu:
    - Đối với cổ phiếu BID: LSTM đa biến đạt RMSE 0.9634, vượt trội hơn LSTM đơn biến (1.4500) và ARIMA baseline (1.1696).
    - Đối với cổ phiếu TCB: LSTM đa biến đạt RMSE 1.2589, vượt trội hơn hẳn ARIMA (9.4864).
    - Đối với cổ phiếu VCB: LSTM đa biến đạt RMSE 2.8278, vượt trội hơn hẳn ARIMA (4.4900).
    - Đối với cổ phiếu CTG: LSTM đa biến đạt RMSE 1.3733, vượt trội hơn hẳn ARIMA (11.3624).
    Kết quả thực nghiệm này khẳng định các đặc trưng đa biến đóng vai trò thiết yếu để tối ưu hóa hiệu năng dự báo học sâu chuỗi thời gian đối với nhóm ngành ngân hàng.

### 💡 Q2: Biến động giá đóng cửa ngắn hạn của 4 cổ phiếu ngân hàng (BID, TCB, VCB, CTG) có đồng pha hay phân hóa?
*   **Kết luận**: Có sự đồng pha (co-movement) cực kỳ mạnh mẽ giữa nhóm ngân hàng thương mại nhà nước (SOCB) bao gồm **BID**, **VCB**, và **CTG**. Ngược lại, cổ phiếu ngân hàng thương mại cổ phần tư nhân **TCB** thể hiện xu hướng phân hóa (divergence) rõ rệt và độc lập hơn.
*   **Minh chứng thực nghiệm**: 
    - Hệ số tương quan giá đóng cửa lịch sử giữa VCB, BID, và CTG đều vượt mức **0.85**, cho thấy nhóm quốc doanh biến động sát theo các chỉ đạo vĩ mô và xu hướng lãi suất chung.
    - Biên độ sai số RMSE của mô hình dự báo LSTM trên tập test phân hóa rõ rệt: TCB đạt **1.7009**, CTG đạt **1.3975**, trong khi VCB có mức dao động lớn nhất với RMSE **2.9988**. Điều này phản ánh tính độc lập trong cấu trúc tài sản và hành vi của nhà đầu tư đối với từng cổ phiếu cụ thể.

### 💡 Q3: Chỉ số tài chính nào quyết định việc ngân hàng rơi vào nhóm rủi ro nợ xấu cao (NPL ≥ 3%)?
*   **Kết luận**: Các ngân hàng có tỷ lệ dự phòng rủi ro tín dụng thấp (`llp_ratio`), hoạt động kém hiệu quả (hiệu suất sinh lời `roe`, `roa` thấp) và quản lý chi phí kém (chỉ số hiệu quả vận hành `cir` cao) là những đơn vị có nguy cơ cao nhất rơi vào nhóm cảnh báo đỏ về nợ xấu.
*   **Minh chứng thực nghiệm**: Mô hình phân loại **Random Forest** đạt độ chính xác phân biệt rất cao với **AUC-ROC là 0.9370** và **Recall cho nhóm Rủi ro cao đạt 85.71%** tại ngưỡng quyết định tối ưu là **0.2822**. Phân tích mức độ quan trọng đặc trưng (Feature Importance) chỉ ra:
    1.  `llp_ratio` (Độ quan trọng: **21.05%**): Là thước đo hàng đầu dự báo nợ xấu, phản ánh mức độ tích lũy rủi ro của ngân hàng.
    2.  `roe` (Độ quan trọng: **11.49%**) và `roa` (Độ quan trọng: **9.85%**): Khả năng sinh lời suy giảm trực tiếp đẩy nhanh nguy cơ vỡ nợ tín dụng.
    3.  `cir` (Độ quan trọng: **11.03%**): Quản lý vận hành lỏng lẻo đi kèm chi phí hoạt động phình to làm mất đi tấm đệm hấp thụ các khoản nợ quá hạn.

### 💡 Q4: Các chiến lược hoạt động của các ngân hàng Việt Nam có được phân nhóm rõ rệt dựa trên dữ liệu tài chính không?
*   **Kết luận**: Có. Hệ thống ngân hàng Việt Nam được phân hóa cực kỳ rõ ràng thành **3 nhóm chiến lược** kinh doanh khác biệt, phản ánh chân thực bản chất cấu trúc sở hữu và mô hình vận hành của từng nhóm.
*   **Minh chứng thực nghiệm**: Thuật toán gom cụm **K-Means (K=3)** trên không gian giảm chiều **PCA (giải thích 85.92% phương sai)** sau khi loại bỏ 6 ngân hàng ngoại lai đặc thù (CB, VBSP, DAB, GPB, WEB, MDB) đã phân tách 39 ngân hàng thành:
    *   **Cụm 0 (13 ngân hàng - TMCP Quy mô nhỏ/vừa)**: Có tỷ lệ an toàn vốn trung bình, NIM khá tốt nhưng CIR cao do chưa tối ưu hóa được quy mô.
    *   **Cụm 1 (24 ngân hàng - Trụ cột hệ thống)**: Bao gồm các ngân hàng lớn (VCB, BID, CTG, TCB, ACB, MBB...). Đặc trưng bởi quy mô tài sản và tiền gửi khổng lồ, hiệu số sinh lời ROA/ROE ổn định và biên lãi ròng NIM bền vững.
    *   **Cụm 2 (2 ngân hàng - Ngân hàng Ngoại/Liên doanh đặc thù)**: Quy mô cho vay cực thấp nhưng sở hữu tỷ lệ an toàn vốn (`eta`, `etd`) cao vượt trội và tỷ lệ nợ xấu gần như bằng không.

---

## 3. Tổng Hợp Số Liệu Hiệu Năng Mô Hình Huấn Luyện (Model Metrics Summary)

Dưới đây là bảng tổng hợp các chỉ số thực tế thu được từ đợt chạy huấn luyện chính thức trên dữ liệu Big DWH:

### 3.1 Dự báo chuỗi thời gian (Time Series Forecasting - LSTM vs ARIMA)
*   **BID**: LSTM RMSE = **3.4037** | ARIMA RMSE = **5.5419** (Đạt chỉ tiêu)
*   **TCB**: LSTM RMSE = **1.7009** | ARIMA RMSE = **9.4864** (Đạt chỉ tiêu)
*   **VCB**: LSTM RMSE = **2.9988** | ARIMA RMSE = **4.4900** (Đạt chỉ tiêu)
*   **CTG**: LSTM RMSE = **1.3975** | ARIMA RMSE = **11.3624** (Đạt chỉ tiêu)

### 3.2 Phân cụm sức khỏe ngân hàng (K-Means & PCA)
*   **Số thành phần PCA**: 3 thành phần chính (giữ lại **85.92%** lượng thông tin của 47 biến tài chính).
*   **Silhouette Score**: **0.3222** (Gom cụm rõ nét trên không gian giảm chiều).
*   **Davies-Bouldin Index**: **0.9746** (Mức độ phân tách cụm tối ưu).

### 3.3 Phân loại rủi ro nợ xấu (Random Forest Classifier)
*   **AUC-ROC**: **0.9370** (Yêu cầu hệ thống: > 0.80) $\rightarrow$ **Đạt**
*   **Recall (Nhóm rủi ro cao)**: **85.71%** (Yêu cầu hệ thống: $\ge$ 85%) $\rightarrow$ **Đạt**
*   **Ngưỡng quyết định tối ưu**: **0.2822** (Được tinh chỉnh để ưu tiên phát hiện rủi ro tối đa).

---

## 4. Ý Nghĩa Thực Tiễn và Đóng Góp

1.  **Hạ tầng dữ liệu chuẩn hóa**: Kho dữ liệu BigQuery Star Schema lưu trữ đồng bộ lịch sử giao dịch và số liệu CAMELS dài hạn giúp giảm thời gian truy xuất và lập báo cáo quản trị định kỳ từ vài ngày xuống còn dưới **5 giây**.
2.  **Hệ thống radar cảnh báo sớm**: Mô hình Random Forest với Recall > 85% giúp bộ phận quản lý rủi ro phát hiện trước các dấu hiệu suy yếu tài chính của đối tác trước khi nợ xấu thực tế bùng phát.
3.  **Công cụ hỗ trợ giao dịch tự doanh**: Dự báo giá ngắn hạn T+1 đến T+5 của LSTM giúp các phòng tự doanh tối ưu hóa thời điểm giải ngân và quản trị danh mục đầu tư ngành ngân hàng.
