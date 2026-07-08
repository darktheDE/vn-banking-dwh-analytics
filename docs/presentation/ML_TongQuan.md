# TỔNG QUAN CÁC MÔ HÌNH HỌC MÁY TRONG ĐỒ ÁN

**Dự án:** Kho Dữ Liệu và Nền Tảng Phân Tích Học Máy Hệ Thống Ngân Hàng Việt Nam
**Nhóm:** 2 — Bộ môn Hệ thống Thông tin, HCMUTE

---

## MỤC LỤC

1. [Tổng quan ba mô hình ML](#1-tổng-quan-ba-mô-hình-ml)
2. [Mô hình 1 — LSTM: Dự báo giá cổ phiếu ngắn hạn](#2-mô-hình-1--lstm-dự-báo-giá-cổ-phiếu-ngắn-hạn)
3. [Mô hình 2 — K-Means + PCA: Phân cụm chiến lược ngân hàng](#3-mô-hình-2--k-means--pca-phân-cụm-chiến-lược-ngân-hàng)
4. [Mô hình 3 — Random Forest: Phân loại rủi ro tín dụng](#4-mô-hình-3--random-forest-phân-loại-rủi-ro-tín-dụng)
5. [Tổng hợp kết quả và ý nghĩa cho bài toán](#5-tổng-hợp-kết-quả-và-ý-nghĩa-cho-bài-toán)
6. [Hướng dẫn trình bày Dashboard](#6-hướng-dẫn-trình-bày-dashboard)

---

## 1. TỔNG QUAN BA MÔ HÌNH ML

Dự án triển khai **3 mô hình học máy**, mỗi mô hình giải quyết một bài toán nghiệp vụ riêng biệt trong lĩnh vực tài chính ngân hàng:

| Mô hình | Loại ML | Bài toán giải quyết | Câu hỏi nghiên cứu |
|---------|---------|---------------------|---------------------|
| **LSTM** | Học có giám sát — Hồi quy chuỗi thời gian | Dự báo giá đóng cửa cổ phiếu T+1 đến T+5 | Q1: LSTM đa biến có vượt trội hơn LSTM đơn biến và ARIMA trong dự báo giá ngắn hạn? Q2: Biến động giá 4 cổ phiếu đồng pha hay phân hóa? |
| **K-Means + PCA** | Học không giám sát — Phân cụm | Phân nhóm 45 ngân hàng thương mại theo chiến lược hoạt động | Q4: Có phân loại rõ rệt chiến lược hoạt động ngân hàng không? |
| **Random Forest** | Học có giám sát — Phân loại nhị phân | Cảnh báo sớm ngân hàng có nguy cơ nợ xấu cao | Q3: Chỉ số tài chính nào quyết định việc nợ xấu vượt ngưỡng 3%? |

---

## 2. MÔ HÌNH 1 — LSTM: DỰ BÁO GIÁ CỔ PHIẾU NGẮN HẠN

### 2.1 Giới thiệu thuật toán

**LSTM — Long Short-Term Memory** là một biến thể đặc biệt của mạng nơ-ron hồi quy RNN, được thiết kế để học các mẫu hình phụ thuộc thời gian trong dữ liệu chuỗi. Điểm khác biệt cốt lõi so với RNN thông thường là LSTM sở hữu cơ chế **"cổng" — gate mechanism** gồm ba cổng: Cổng quên (Forget Gate), Cổng đầu vào (Input Gate) và Cổng đầu ra (Output Gate). Ba cổng này cho phép mạng tự quyết định thông tin nào cần lưu giữ, thông tin nào cần loại bỏ qua từng bước thời gian.

**Thường dùng để giải quyết bài toán gì?**
- Dự báo chuỗi thời gian: giá cổ phiếu, tỷ giá, doanh thu, nhu cầu tiêu thụ điện.
- Xử lý ngôn ngữ tự nhiên: dịch máy, sinh văn bản, phân tích cảm xúc.
- Nhận dạng giọng nói và chuỗi tín hiệu liên tục.

**Tại sao chọn LSTM cho đồ án này?**
- Giá cổ phiếu là dữ liệu **chuỗi thời gian phi tuyến** — giá ngày hôm nay phụ thuộc vào giá và khối lượng giao dịch của nhiều phiên trước đó.
- LSTM có khả năng nắm bắt các **mẫu hình phi tuyến và tính chu kỳ** mà các phương pháp thống kê truyền thống như ARIMA hoàn toàn bỏ sót.
- LSTM cho phép đưa vào **nhiều biến đầu vào cùng lúc** — bao gồm giá lịch sử, khối lượng giao dịch, và các chỉ số động lực học tỷ lệ biến động — để mô hình học được mối liên hệ đa chiều.

**Trong đồ án, LSTM phụ trách trả lời:**
- **Q1:** Mô hình LSTM đa biến có vượt trội hơn mô hình LSTM đơn biến và baseline ARIMA trong dự báo giá cổ phiếu ngắn hạn không?
- **Q2:** Biến động giá đóng cửa ngắn hạn của 4 cổ phiếu ngân hàng BID, TCB, VCB, CTG có đồng pha hay phân hóa?

### 2.2 Các biến đầu vào và ý nghĩa

LSTM của đồ án được triển khai cho cả 4 cổ phiếu ngân hàng (BID, TCB, VCB, CTG) với hai cấu hình để so sánh hiệu năng:

- **LSTM Univariate (Đơn biến):** Chỉ sử dụng 1 đặc trưng đầu vào là giá đóng cửa lịch sử (`close_price`).
- **LSTM Multivariate (Đa biến):** Sử dụng 7 đặc trưng đầu vào bao gồm giá và khối lượng giao dịch cùng các đặc trưng phái sinh:

| Biến | Ý nghĩa | Tại sao chọn |
|------|----------|--------------|
| `close_price` | Giá đóng cửa phiên giao dịch | Biến mục tiêu — đây là giá trị mà mô hình cần dự báo |
| `open_price` | Giá mở cửa phiên giao dịch | Phản ánh tâm lý thị trường đầu phiên, chênh lệch open-close cho biết xu hướng nội phiên |
| `high_price` | Giá cao nhất trong phiên | Xác định ngưỡng kháng cự — mức giá mà lực bán mạnh lên |
| `low_price` | Giá thấp nhất trong phiên | Xác định ngưỡng hỗ trợ — mức giá mà lực mua bắt đáy xuất hiện |
| `trading_volume` | Khối lượng giao dịch trong phiên | Thước đo thanh khoản, khối lượng tăng đột biến thường đi kèm đảo chiều xu hướng |
| `price_change_pct` | Tỷ lệ phần trăm thay đổi giá đóng cửa so với phiên trước | Biến phái sinh phản ánh momentum — đà tăng/giảm của giá |
| `volume_change_pct` | Tỷ lệ phần trăm thay đổi khối lượng giao dịch so với phiên trước | Biến phái sinh phản ánh sự gia tăng hay suy kiệt dòng tiền |

**Mục tiêu so sánh:** Thực nghiệm này nhằm chứng minh xem việc bổ sung thông tin đa biến (biên độ dao động và dòng tiền thanh khoản) có cải thiện hiệu năng dự báo so với chỉ sử dụng thông tin đơn biến và mô hình baseline ARIMA hay không.

### 2.3 Đầu ra và ý nghĩa

**Đầu ra:** Giá đóng cửa dự báo cho 5 phiên giao dịch tiếp theo — T+1, T+2, T+3, T+4, T+5.

**Tại sao chọn đầu ra này?**
- Giá đóng cửa (`close_price`) là mức giá quan trọng nhất trong phân tích kỹ thuật — đây là mức giá cuối cùng mà thị trường đồng thuận trong phiên.
- Khoảng dự báo 5 phiên (tương đương 1 tuần giao dịch) phù hợp với chu kỳ ra quyết định của bộ phận tự doanh và quỹ đầu tư ngắn hạn.

### 2.4 Cách đọc kết quả

| Chỉ số đánh giá | Giá trị | Cách đọc |
|------------------|---------|----------|
| **RMSE — Root Mean Squared Error** | BID: **0.9634**, TCB: **1.2589**, VCB: **2.8278**, CTG: **1.3733** | Đơn vị tính giống đơn vị giá (nghìn VND). RMSE 0.9634 nghĩa là trung bình mỗi dự báo lệch khoảng 963 VND so với giá thực tế. RMSE càng thấp càng tốt. |
| **ARIMA RMSE** (Baseline) | BID: **1.1696**, TCB: **9.4864**, VCB: **4.4900**, CTG: **11.3624** | Sai số của mô hình thống kê truyền thống ARIMA. Dùng để so sánh — nếu LSTM thấp hơn ARIMA thì LSTM vượt trội. |
| **Mức cải thiện** | BID: giảm 17.6% sai số, TCB: giảm 86.7%, VCB: giảm 37.0%, CTG: giảm 87.9% | LSTM đa biến vượt trội hoàn toàn so với ARIMA trên cả 4 mã. Đặc biệt, TCB và CTG cải thiện trên 86%. |

**Ý nghĩa cho bài toán:**
- Kết quả chứng minh rằng mạng học sâu LSTM có khả năng nắm bắt các mẫu hình phi tuyến trong biến động giá cổ phiếu ngân hàng mà phương pháp thống kê truyền thống ARIMA không thể làm được.
- Việc so sánh cho thấy mô hình LSTM đa biến (kết hợp các thông tin OHLCV và biến động khối lượng) đạt hiệu năng cao hơn so với LSTM đơn biến (ví dụ như ở BID: RMSE đa biến 0.9634 tốt hơn đơn biến 1.4500), chứng minh các tín hiệu bổ trợ như thanh khoản và dao động biên độ có giá trị dự báo cao trong ngắn hạn đối với thị trường chứng khoán Việt Nam.

---

## 3. MÔ HÌNH 2 — K-MEANS + PCA: PHÂN CỤM CHIẾN LƯỢC NGÂN HÀNG

### 3.1 Giới thiệu thuật toán

**K-Means** là thuật toán học không giám sát phổ biến nhất cho bài toán phân cụm. Nguyên lý hoạt động: chia N điểm dữ liệu thành K nhóm sao cho tổng khoảng cách bình phương từ mỗi điểm đến trọng tâm cụm của nó là nhỏ nhất. Thuật toán lặp đi lặp lại hai bước: gán mỗi điểm vào cụm có trọng tâm gần nhất, rồi cập nhật lại trọng tâm dựa trên các điểm mới được gán.

**PCA — Principal Component Analysis** là kỹ thuật giảm chiều dữ liệu. Khi dữ liệu có quá nhiều biến (47+ biến tài chính), PCA tìm ra các "trục chính" chứa nhiều thông tin nhất và chiếu dữ liệu lên các trục đó, giảm từ 47 chiều xuống chỉ còn 2-3 chiều mà vẫn giữ lại phần lớn thông tin.

**Thường dùng để giải quyết bài toán gì?**
- Phân khúc khách hàng trong marketing.
- Phân nhóm bệnh nhân dựa trên triệu chứng lâm sàng.
- Phát hiện mẫu hình tiêu dùng, hành vi người dùng.
- Phân loại tài liệu và hình ảnh.

**Tại sao chọn K-Means + PCA cho đồ án này?**
- Bài toán không có "nhãn đúng" cho sẵn — không ai biết trước ngân hàng nào thuộc nhóm nào. Đây đúng là bài toán **học không giám sát** mà K-Means giải quyết tốt nhất.
- 45 ngân hàng được mô tả bởi 47+ chỉ số tài chính — quá nhiều chiều để trực quan hóa hoặc phân tích thủ công. PCA giảm chiều giúp nhìn thấy cấu trúc dữ liệu trên không gian 2D.
- K-Means yêu cầu dữ liệu đã chuẩn hóa và ít nhiễu — PCA đáp ứng cả hai yêu cầu này.

**Trong đồ án, K-Means + PCA phụ trách trả lời:**
- **Q4:** Các chiến lược hoạt động của các ngân hàng Việt Nam có được phân nhóm rõ rệt dựa trên dữ liệu tài chính không?

### 3.2 Các biến đầu vào và ý nghĩa

K-Means sử dụng **11 biến tỷ số CAMELS** đã được chuẩn hóa bằng StandardScaler:

| Biến | Ý nghĩa | Nhóm CAMELS |
|------|----------|-------------|
| `roa` | Tỷ suất sinh lời trên tổng tài sản — Return on Assets | **E** — Earnings (Khả năng sinh lời) |
| `roe` | Tỷ suất sinh lời trên vốn chủ sở hữu — Return on Equity | **E** — Earnings |
| `nim` | Biên lãi thuần — Net Interest Margin | **E** — Earnings |
| `cir` | Tỷ lệ chi phí trên thu nhập — Cost-to-Income Ratio | **M** — Management (Chất lượng quản lý) |
| `eta` | Vốn chủ sở hữu trên tổng tài sản — Equity to Assets | **C** — Capital (An toàn vốn) |
| `etd` | Vốn chủ sở hữu trên tiền gửi — Equity to Deposits | **C** — Capital |
| `lta` | Dư nợ cho vay trên tổng tài sản — Loans to Assets | **A** — Asset Quality (Chất lượng tài sản) |
| `ltd` | Dư nợ cho vay trên tiền gửi — Loans to Deposits | **L** — Liquidity (Thanh khoản) |
| `gta` | Cho vay gộp trên tổng tài sản — Gross Loans to Assets | **A** — Asset Quality |
| `npl_ratio` | Tỷ lệ nợ xấu — Non-Performing Loan Ratio | **A** — Asset Quality |
| `llp_ratio` | Tỷ lệ trích lập dự phòng — Loan Loss Provision Ratio | **S** — Sensitivity (Độ nhạy rủi ro) |

**Tại sao phải chuẩn hóa (StandardScaler)?** Vì K-Means dựa trên khoảng cách Euclidean. Nếu không chuẩn hóa, biến có giá trị lớn như `total_assets` (hàng nghìn tỷ) sẽ chi phối hoàn toàn kết quả, trong khi biến như `roa` (chỉ 0.01 đến 0.02) gần như bị bỏ qua.

**Tại sao loại bỏ 6 ngân hàng ngoại lệ?** Các ngân hàng DAB, CB, GPB, WEB, VBSP, MDB có đặc điểm cực kỳ đặc thù — ngân hàng chính sách, đã sáp nhập, hoặc đang tái cơ cấu — nếu giữ lại sẽ bóp méo cấu trúc phân cụm của 39 ngân hàng thương mại còn lại.

### 3.3 Đầu ra và ý nghĩa

**Đầu ra:** Mỗi ngân hàng được gắn một nhãn `cluster_id` từ 0 đến 2, đại diện cho nhóm chiến lược hoạt động mà ngân hàng đó thuộc về.

| Cụm | Số lượng | Đặc trưng | Diễn giải nghiệp vụ |
|-----|----------|-----------|---------------------|
| **Cụm 0** | 13 ngân hàng | ETA trung bình, NIM khá tốt, CIR cao | TMCP quy mô nhỏ đến vừa — đang tích lũy đệm tài sản, chưa tối ưu hóa được quy mô vận hành |
| **Cụm 1** | 24 ngân hàng | ROE/ROA lành mạnh, quy mô tài sản lớn, NIM bền vững | Trụ cột hệ thống — bao gồm các ngân hàng lớn như VCB, BID, CTG, TCB, ACB, MBB |
| **Cụm 2** | 2 ngân hàng | ETA cực cao, LTD cực thấp, NPL gần 0 | Ngân hàng nước ngoài/Liên doanh — ưu tiên an toàn tuyệt đối, ít cho vay |

**Tại sao chọn K = 3?** Kết hợp Elbow Method và Silhouette Analysis cho thấy K = 3 cân bằng tốt nhất giữa tính phân tách thống kê và khả năng diễn giải nghiệp vụ, phù hợp với giả thuyết Q4 rằng hệ thống ngân hàng phân hóa theo 3 nhóm chiến lược.

### 3.4 Cách đọc kết quả

| Chỉ số đánh giá | Giá trị | Cách đọc |
|------------------|---------|----------|
| **Số thành phần PCA** | **3** thành phần (giữ lại **85.92%** phương sai) | PCA giảm từ 11 biến CAMELS xuống chỉ 3 "trục chính" mà vẫn bảo toàn 85.92% lượng thông tin. Ngưỡng yêu cầu tối thiểu là 80%, kết quả này vượt yêu cầu. |
| **Silhouette Score** | **0.3222** | Thang đo từ -1 đến 1. Giá trị dương cho thấy các cụm tách biệt rõ ràng — điểm dữ liệu gần trọng tâm cụm của mình hơn so với trọng tâm cụm lân cận. Giá trị trên 0.25 được coi là phân cụm hợp lý. |
| **Davies-Bouldin Index** | **0.9746** | Thang đo từ 0 đến vô cực, giá trị càng thấp càng tốt (cụm càng tách biệt, càng gọn). Giá trị dưới 1.0 cho thấy các cụm có độ phân tách tốt. |

**Ý nghĩa cho bài toán:**
- Kết quả xác nhận giả thuyết Q4: hệ thống ngân hàng Việt Nam **thực sự phân hóa rõ rệt thành 3 nhóm chiến lược** kinh doanh khác biệt, phản ánh chân thực bản chất cấu trúc sở hữu và mô hình vận hành.
- Thông tin phân cụm có giá trị trực tiếp cho việc phân bổ danh mục đầu tư theo chiến lược đa dạng hóa có cơ sở khoa học.

---

## 4. MÔ HÌNH 3 — RANDOM FOREST: PHÂN LOẠI RỦI RO TÍN DỤNG

### 4.1 Giới thiệu thuật toán

**Random Forest — Rừng ngẫu nhiên** là thuật toán học có giám sát thuộc họ Ensemble Learning. Nguyên lý hoạt động: xây dựng hàng trăm cây quyết định (Decision Tree) từ các tập con dữ liệu được lấy mẫu ngẫu nhiên, rồi tổng hợp kết quả bằng bỏ phiếu đa số (phân loại) hoặc trung bình (hồi quy). Mỗi cây được huấn luyện trên một tập dữ liệu con khác nhau và một tập biến con ngẫu nhiên, giúp mô hình tổng thể vừa chính xác vừa ổn định.

**Thường dùng để giải quyết bài toán gì?**
- Phân loại: phát hiện gian lận thẻ tín dụng, chẩn đoán bệnh, lọc spam.
- Hồi quy: dự báo giá nhà, ước tính chi phí bảo hiểm.
- Xếp hạng tín dụng, phát hiện bất thường trong giao dịch tài chính.

**Tại sao chọn Random Forest cho đồ án này?**
- Random Forest **không yêu cầu chuẩn hóa dữ liệu** (khác với SVM hay Neural Network) — rất phù hợp với dữ liệu tài chính có thang đo khác nhau.
- Thuật toán này cung cấp bảng **Feature Importance** cho biết biến nào quan trọng nhất trong quyết định phân loại — đây là yêu cầu bắt buộc của đồ án để trả lời câu hỏi Q3.
- Khả năng xử lý **mất cân bằng lớp** rất tốt thông qua tham số `class_weight='balanced'` — phù hợp vì số ngân hàng "An Toàn" nhiều hơn rất nhiều so với ngân hàng "Nguy Cơ Cao".
- Ít bị overfitting hơn so với Decision Tree đơn lẻ nhờ cơ chế bagging.

**Trong đồ án, Random Forest phụ trách trả lời:**
- **Q3:** Chỉ số tài chính nào quyết định việc ngân hàng rơi vào nhóm rủi ro nợ xấu cao (NPL ≥ 3%)?

### 4.2 Các biến đầu vào và ý nghĩa

Random Forest sử dụng **14 biến** kết hợp cả tỷ số CAMELS lẫn quy mô tài sản:

| Biến | Ý nghĩa | Tại sao chọn |
|------|----------|--------------|
| `roa` | Tỷ suất sinh lời / Tổng tài sản | Ngân hàng sinh lời kém dễ mất khả năng hấp thụ nợ xấu |
| `roe` | Tỷ suất sinh lời / Vốn CSH | ROE cao bất thường kèm đòn bẩy cao là tín hiệu cảnh báo |
| `nim` | Biên lãi thuần | Biên lãi co hẹp báo hiệu áp lực cạnh tranh và suy giảm chất lượng tài sản |
| `cir` | Chi phí / Thu nhập | CIR cao phản ánh vận hành kém hiệu quả, bào mòn lợi nhuận phòng thủ |
| `eta` | Vốn CSH / Tổng tài sản | Đệm vốn mỏng nghĩa là ít dư địa chịu đựng tổn thất |
| `etd` | Vốn CSH / Tiền gửi | Mức độ bảo vệ tiền gửi của khách hàng |
| `lta` | Dư nợ / Tổng tài sản | Tỷ trọng cho vay cao tăng nguy cơ tập trung rủi ro |
| `ltd` | Dư nợ / Tiền gửi | Tỷ lệ vượt trần an toàn tạo rủi ro thanh khoản |
| `gta` | Cho vay gộp / Tổng tài sản | Bổ sung cho LTA, đo mức độ phụ thuộc vào hoạt động tín dụng |
| `llp_ratio` | Tỷ lệ trích lập dự phòng | Biến quan trọng nhất — trích lập mỏng để "làm đẹp" lợi nhuận chính là dấu hiệu nợ xấu tiềm ẩn |
| `total_assets` | Tổng tài sản | Ngân hàng lớn có khả năng phân tán rủi ro tốt hơn |
| `total_deposits` | Tổng tiền gửi | Quy mô huy động vốn, nền tảng thanh khoản |
| `total_loans` | Tổng dư nợ cho vay | Quy mô danh mục tín dụng, trực tiếp liên quan đến rủi ro nợ xấu |
| `total_equity` | Tổng vốn chủ sở hữu | Bộ đệm hấp thụ tổn thất cuối cùng |

**Lưu ý quan trọng:** Biến `npl_ratio` — tỷ lệ nợ xấu — **KHÔNG** được đưa vào làm biến đầu vào vì nó chính là nguồn tạo ra biến mục tiêu (`risk_label`). Nếu đưa vào sẽ gây ra hiện tượng rò rỉ dữ liệu — data leakage.

### 4.3 Đầu ra và ý nghĩa

**Đầu ra:** Mỗi ngân hàng tại mỗi thời điểm báo cáo được gắn:
- `risk_label`: nhãn nhị phân — **0** nếu "An Toàn" (NPL dưới 3%), **1** nếu "Nguy Cơ Cao" (NPL từ 3% trở lên).
- `risk_probability`: xác suất dự báo ngân hàng thuộc nhóm rủi ro cao (từ 0.0 đến 1.0).

**Tại sao chọn ngưỡng NPL 3%?** Đây là ngưỡng giám sát pháp lý mà Ngân hàng Nhà nước Việt Nam sử dụng để phân loại nợ xấu và quyết định mức can thiệp. Ngân hàng vượt ngưỡng 3% bị xếp vào diện cảnh báo và chịu các biện pháp thắt chặt.

**Tại sao chia tập dữ liệu theo thời gian thay vì ngẫu nhiên?** Chia tập theo thời gian (Time-based Split) đảm bảo mô hình chỉ học từ dữ liệu quá khứ để dự đoán tương lai, giống cách sử dụng thực tế. Chia ngẫu nhiên sẽ gây rò rỉ dữ liệu — mô hình "nhìn thấy" tương lai trong quá trình huấn luyện.

### 4.4 Cách đọc kết quả

| Chỉ số đánh giá | Giá trị | Ngưỡng yêu cầu | Cách đọc |
|------------------|---------|-----------------|----------|
| **AUC-ROC** | **0.9370** | Trên 0.80 | Diện tích dưới đường cong ROC. AUC-ROC = 1.0 là phân loại hoàn hảo. Giá trị 0.9370 cho thấy mô hình phân biệt cực kỳ tốt giữa ngân hàng "An Toàn" và "Nguy Cơ Cao". **Đạt chỉ tiêu.** |
| **Recall — Độ nhạy lớp Nguy Cơ Cao** | **85.71%** | Từ 85% trở lên | Trong 100 ngân hàng thực sự có nợ xấu cao, mô hình phát hiện đúng 85-86 ngân hàng. Đây là ràng buộc quan trọng nhất — bỏ sót ngân hàng rủi ro (False Negative) nguy hiểm hơn nhiều so với cảnh báo nhầm. **Đạt chỉ tiêu.** |
| **Ngưỡng quyết định** | **0.2822** | — | Mô hình đã được tinh chỉnh ngưỡng từ 0.5 xuống 0.2822 để ưu tiên phát hiện rủi ro. Nghĩa là: nếu xác suất dự báo từ 28.22% trở lên, ngân hàng sẽ bị gắn cờ cảnh báo. |

**Feature Importance — Top 3 biến quan trọng nhất:**

| Hạng | Biến | Trọng số | Diễn giải |
|------|------|----------|-----------|
| 1 | `llp_ratio` | **21.05%** | Tỷ lệ trích lập dự phòng là biến số 1 dự báo nợ xấu. Ngân hàng trích lập mỏng để "làm đẹp" báo cáo lợi nhuận chính là nhóm tích lũy rủi ro cao nhất. |
| 2 | `roe` | **11.49%** | Tỷ suất sinh lời / Vốn CSH. ROE quá cao kèm đòn bẩy lớn là tín hiệu cảnh báo đỏ. |
| 3 | `cir` | **11.03%** | Tỷ lệ chi phí / Thu nhập. Hiệu quả vận hành kém trực tiếp bào mòn khả năng phòng thủ nợ xấu. |

**Ý nghĩa cho bài toán:**
- Kết quả xác nhận rằng ba yếu tố then chốt dẫn đến nợ xấu là: trích lập dự phòng không đủ, đòn bẩy tài chính quá mức, và quản lý chi phí vận hành kém.
- Hệ thống cảnh báo sớm này cho phép phát hiện trước 1-2 chu kỳ báo cáo, giúp thanh tra viên và kiểm toán viên có bằng chứng định lượng để yêu cầu ngân hàng cải thiện.

---

## 5. TỔNG HỢP KẾT QUẢ VÀ Ý NGHĨA CHO BÀI TOÁN

| Câu hỏi nghiên cứu | Mô hình ML | Kết luận chính |
|---------------------|------------|----------------|
| **Q1:** LSTM đa biến (OHLCV và biến động) có vượt trội hơn LSTM đơn biến và ARIMA trong dự báo giá ngắn hạn? | LSTM | Có — LSTM đa biến đạt RMSE thấp nhất trên cả 4 cổ phiếu (BID: 0.9634, TCB: 1.2589, VCB: 2.8278, CTG: 1.3733), vượt trội hoàn toàn so với ARIMA baseline và LSTM đơn biến. |
| **Q2:** 4 cổ phiếu đồng pha hay phân hóa? | LSTM | Nhóm quốc doanh BID, VCB, CTG có tương quan trên 0.85 — biến động đồng pha mạnh. TCB biến động độc lập, RMSE khác biệt rõ so với nhóm còn lại. |
| **Q3:** Chỉ số nào quyết định nợ xấu cao? | Random Forest | `llp_ratio` (21.05%), `roe` (11.49%), `cir` (11.03%) là ba biến quan trọng nhất. AUC-ROC đạt 0.9370, Recall đạt 85.71%. |
| **Q4:** Chiến lược ngân hàng có phân nhóm rõ không? | K-Means + PCA | Có — 3 cụm rõ rệt: 24 trụ cột lớn, 13 TMCP nhỏ, 2 ngân hàng ngoại. Silhouette Score 0.3222, PCA giữ lại 85.92% phương sai. |

---

## 6. HƯỚNG DẪN TRÌNH BÀY DASHBOARD

### 6.1 Phần LSTM — "Dự Báo Giá Cổ Phiếu"

**Vào mục:** Thanh điều hướng bên trái → "Dự Báo Giá Cổ Phiếu (LSTM)"

**Cách trình bày khi thuyết trình:**

> "Dashboard này hiển thị kết quả dự báo giá đóng cửa 5 phiên tiếp theo cho 4 cổ phiếu ngân hàng trọng điểm. Bên trái là biểu đồ đường Line Chart, trong đó đường liền xanh biểu diễn giá thực tế lịch sử và đường đứt khúc đỏ là giá dự báo LSTM. Chúng ta có thể thấy đường dự báo bám sát đường giá thực tế, chứng tỏ mô hình đã học được xu hướng biến động giá.
>
> Bên phải là bảng số liệu dự báo T+1 đến T+5 kèm phần trăm biến động so với giá đóng cửa gần nhất. Nhà đầu tư có thể sử dụng thông tin này để xác định đà giá trong tuần tới.
>
> Bộ lọc Dropdown ở trên cho phép chuyển đổi giữa 4 mã BID, TCB, VCB, CTG để quan sát riêng từng cổ phiếu."

### 6.2 Phần K-Means — "Phân Nhóm Ngân Hàng"

**Vào mục:** Thanh điều hướng bên trái → "Phân Nhóm Ngân Hàng (K-Means)"

**Cách trình bày khi thuyết trình:**

> "Dashboard phân cụm gồm 3 phần chính. Phần đầu tiên là biểu đồ phân tán PCA 2D, mỗi điểm đại diện cho một ngân hàng, tô màu theo nhóm cluster_id và gắn nhãn mã ngân hàng. Chúng ta thấy rõ 3 cụm tách biệt nhau: Cụm hồng (Trụ cột lớn — 24 ngân hàng) nằm tập trung ở trung tâm, Cụm xanh dương (TMCP nhỏ — 13 ngân hàng) tách sang một bên, và Cụm xanh lá (Ngân hàng ngoại — 2 ngân hàng) nằm biệt lập ở góc.
>
> Phần thứ hai là biểu đồ cột nhóm Grouped Bar Chart so sánh giá trị trung bình 10 chỉ số CAMELS giữa 3 cụm. Tại đây chúng ta thấy rõ sự phân hóa: Cụm 2 có ETA vượt trội, Cụm 1 có ROE/ROA lành mạnh nhất, Cụm 0 có biên NIM khiêm tốn hơn.
>
> Phần thứ ba là bảng danh sách thành viên cho phép chọn từng cụm để xem chi tiết ngân hàng nào thuộc nhóm nào."

### 6.3 Phần Random Forest — "Phân Loại Rủi Ro Tín Dụng"

**Vào mục:** Thanh điều hướng bên trái → "Phân Loại Rủi Ro Tín Dụng (Random Forest)"

**Cách trình bày khi thuyết trình:**

> "Dashboard cảnh báo rủi ro tín dụng gồm 3 phần. Bên trái là biểu đồ tròn Pie Chart cho thấy tỷ lệ phân bố: 94.64% ngân hàng ở trạng thái An Toàn (màu xanh lá) và 5.36% bị gắn cờ Nguy Cơ Cao (màu đỏ).
>
> Bên phải là biểu đồ thanh ngang Feature Importance hiển thị 8 biến quan trọng nhất. Chúng ta thấy `llp_ratio` chiếm trọng số lớn nhất — trên 20% — cho thấy tỷ lệ trích lập dự phòng là thước đo hàng đầu dự báo nợ xấu. Đây là phát hiện quan trọng: ngân hàng nào trích lập dự phòng mỏng để làm đẹp lợi nhuận chính là nhóm có xác suất bùng phát nợ xấu cao nhất.
>
> Phía dưới cùng là Bảng giám sát rủi ro toàn bộ ngân hàng. Các dòng màu đỏ (Nguy Cơ Cao) được đưa lên trên cùng, kèm theo xác suất dự báo nợ xấu và tỷ lệ NPL thực tế để đối chiếu. Nhà quản trị rủi ro có thể sử dụng bảng này để quyết định kiểm toán đặc biệt đối với nhóm cảnh báo đỏ."

---

*Tài liệu này được tổng hợp từ mã nguồn thực tế của dự án và kết quả chạy huấn luyện chính thức trên Kho dữ liệu BigQuery.*
