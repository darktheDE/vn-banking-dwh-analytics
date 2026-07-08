# OverView_Project02_Gruop02

## 1. Tóm Tắt Dự Án

**Bối cảnh:** Thị trường chứng khoán và hệ thống ngân hàng Việt Nam đang có sự biến động mạnh mẽ về dòng tiền và chất lượng tài sản, đòi hỏi các quyết định đầu tư và quản trị rủi ro phải dựa trên dữ liệu thay vì cảm tính.

**Vấn đề:** Các nhà đầu tư và tổ chức tài chính hiện thiếu một hệ thống phân tích tập trung, có khả năng đánh giá toàn diện từ dữ liệu giao dịch vi mô theo từng giây trên sàn chứng khoán đến dữ liệu vĩ mô về sức khỏe tài chính của các ngân hàng trong nhiều thập kỷ.

**Mục tiêu:** Xây dựng thành công Kho dữ liệu tài chính tập trung trên nền tảng đám mây và triển khai 3 mô hình học máy, kỳ vọng đưa ra dự báo giá cổ phiếu ngắn hạn và phân loại chính xác sức khỏe tài chính của 45 ngân hàng với độ tin cậy trên 85%.

**Giải pháp:** Xây dựng Data Warehouse với mô hình Star Schema trên Google BigQuery để lưu trữ và chuẩn hóa dữ liệu. Sau đó, áp dụng các kỹ thuật Phân tích chuỗi thời gian, Phân cụm và Phân loại học máy để khám phá thông tin chi tiết.

---

## 2. Câu Hỏi Nghiên Cứu & Giả Thuyết

**Q1:** Dòng tiền từ nhà đầu tư nước ngoài và khối tự doanh có tác động như thế nào đến biến động giá ngắn hạn của cổ phiếu ngân hàng BID?
-> **Giả thuyết:** Hành vi mua ròng liên tục từ khối ngoại và tự doanh có tương quan thuận chiều mạnh mẽ với xu hướng tăng giá của cổ phiếu BID trong khung thời gian T+1 đến T+5.

**Q2:** Xu hướng biến động giá đóng cửa ngắn hạn của 4 cổ phiếu ngân hàng BID, TCB, VCB, CTG có sự đồng pha hay phân hóa?
-> **Giả thuyết:** Có sự đồng pha mạnh mẽ trong ngắn hạn giữa các cổ phiếu thuộc nhóm quốc doanh (BID, VCB, CTG), trong khi nhóm cổ phần tư nhân (TCB) có xu hướng biến động độc lập hơn.

**Q3:** Những chỉ số tài chính nào quyết định việc một ngân hàng rơi vào nhóm có rủi ro nợ xấu cao?
-> **Giả thuyết:** Các ngân hàng có tỷ lệ chi phí trên thu nhập cao và tỷ lệ vốn chủ sở hữu trên tổng tài sản thấp sẽ có khả năng rơi vào nhóm rủi ro nợ xấu vượt mức 3%.

**Q4:** Có thể phân loại rõ rệt chiến lược hoạt động của các nhóm ngân hàng tại Việt Nam dựa trên dữ liệu tài chính không?
-> **Giả thuyết:** Phân tích dữ liệu sẽ tách biệt rõ ràng hệ thống thành 3 cụm chính bao gồm: Ngân hàng quốc doanh tối ưu quy mô, Ngân hàng cổ phần tối ưu lợi nhuận và Ngân hàng ngoại tối ưu an toàn vốn.

---

## 3. Tổng Quan Dữ Liệu - Data Overview

**Nguồn dữ liệu:** Dữ liệu nội bộ tự thu thập và tổng hợp thông qua các tệp Excel định dạng có cấu trúc.

**Kích thước:**

- Dữ liệu cổ phiếu BID, TCB, VCB, CTG: Hơn 11,835 dòng dữ liệu giá lịch sử hàng ngày.

- Dữ liệu ngân hàng: 667 dòng và hơn 47 cột, bao phủ 45 ngân hàng trong khoảng thời gian 20 năm từ 2002 đến 2022.

**Các biến chính - Data Dictionary sơ lược:**

- Ngày giao dịch - Date kiểu Datetime: Mốc thời gian diễn ra giao dịch cổ phiếu hoặc ghi nhận báo cáo tài chính.
- Khối lượng giao dịch ròng - Net Volume kiểu Integer: Chênh lệch giữa tổng khối lượng mua và tổng khối lượng bán trong một phiên.
- Giá đóng cửa - Close Price kiểu Float: Mức giá cuối cùng được khớp lệnh trong một ngày giao dịch của cổ phiếu.
- ROA và ROE kiểu Float: Tỷ suất sinh lời trên tổng tài sản và tỷ suất sinh lời trên vốn chủ sở hữu, đánh giá hiệu quả sinh lời của ngân hàng.
- NPLRATIO kiểu Float: Tỷ lệ nợ xấu trên tổng dư nợ, đại diện cho rủi ro tín dụng của ngân hàng.
- NIM kiểu Float: Biên lãi ròng, thể hiện chênh lệch giữa thu nhập từ lãi và chi phí trả lãi.
- ETA kiểu Float: Tỷ lệ vốn chủ sở hữu trên tổng tài sản, thước đo năng lực vốn và sự an toàn tài chính.

**(47+ biến):**

- **Thông tin chung:** NE, NB (Số nhân viên, số chi nhánh)
- **Quy mô:** DEPOSITS, EQUITY, LOANS, TASSETS
- **Chất lượng tài sản:** LLP, NPL (Dự phòng rủi ro, nợ xấu)
- **Thu nhập/Chi phí:** II, NI, IE, NIE, PE, OE
- **Hiệu suất CAMELS:** ROA, ROE, NIM, CIR
- **Thanh khoản:** ETA, ETD, LTA, LTD
- **Rủi ro:** NPLRATIO, LLPRATIO, GTA
- **Khác:** OBS, PBT, PAT

---

## 4. Quy Trình Thực Hiện

**Bước 1: Thu thập & Làm sạch - Data Cleaning**
Trích xuất dữ liệu từ các tệp Excel thông qua thư viện Python. Tiến hành đồng bộ định dạng chuỗi thời gian, xử lý các giá trị khuyết thiếu trong bộ dữ liệu ngân hàng 20 năm bằng phương pháp nội suy, đồng thời chuẩn hóa kiểu dữ liệu cho các biến tài chính.

**Bước 2: Phân tích khám phá - EDA**
Khảo sát phân phối của các biến số, tìm kiếm xu hướng giá cổ phiếu theo thời gian. Sử dụng ma trận tương quan để đánh giá mối liên hệ giữa các chỉ số hiệu suất ngân hàng chuẩn CAMELS và sự biến động dòng tiền cổ phiếu.

**Bước 3: Feature Engineering**
Tạo thêm các biến phái sinh nhằm phục vụ mô hình hóa, bao gồm biến tính toán phần trăm thay đổi giá hàng ngày, biến đánh giá tỷ trọng lệnh mua chủ động, và biến phân nhóm nhãn chất lượng tài sản ngân hàng thành các hạng mức an toàn hoặc rủi ro.

**Bước 4: Phân tích chuyên sâu và Model**

- **Xây dựng Data Warehouse:** Thiết kế và triển khai mô hình Star Schema tinh gọn gồm 7 bảng (5 Dimensions, 2 Facts) trên Cloud Google BigQuery, loại bỏ hoàn toàn các bảng giả lập rời rạc và hợp nhất thành một bảng Fact giá chứng khoán sạch duy nhất `fact_stock_daily_metrics` với 11.835 dòng dữ liệu thực tế. Hoãn tích hợp Supabase OLTP để tập trung cho chất lượng kho dữ liệu OLAP.
- **Time Series Forecasting:** Huấn luyện và so sánh thực nghiệm mô hình LSTM Đơn biến (chỉ dùng giá đóng cửa) và LSTM Đa biến (giá + khối lượng + biến động) cho cả 4 ngân hàng (BID, TCB, VCB, CTG), lấy ARIMA làm đường cơ sở (baseline) so sánh.
- **Clustering:** Sử dụng thuật toán K-Means kết hợp PCA để giảm chiều dữ liệu từ 47+ chỉ số tài chính CAMELS thực tế và phân cụm hành vi tài chính của 39 ngân hàng thương mại Việt Nam.
- **Causality & Classification:** Kiểm định nhân quả Granger và Hồi quy bảng trễ Fixed Effects cho cặp biến `llp_ratio` -> `npl_ratio` để tìm tính nhân quả thực tế. Triển khai thuật toán Random Forest Classifier để cảnh báo sớm các ngân hàng có rủi ro nợ xấu vượt mức 3%.

---

## 5. Kết Quả Kinh Doanh & Phát Hiện Cốt Lõi

*Dưới đây là các kết quả kỳ vọng dựa trên mục tiêu thiết kế dự án ( Dự kiến )*

**Insight 1:** Dòng tiền mua ròng từ khối ngoại và tự doanh chiếm tỷ trọng chi phối trong việc hình thành các nhịp tăng giá ngắn hạn của cổ phiếu BID, với độ trễ phản ứng của giá thường rơi vào mốc T cộng 1.

**Insight 2:** Tỷ lệ chi phí trên thu nhập và biên lãi ròng là hai yếu tố phân tách rõ rệt nhất giữa nhóm ngân hàng thương mại cổ phần tư nhân linh hoạt và nhóm ngân hàng quốc doanh. Các ngân hàng có tốc độ tăng trưởng tín dụng quá nóng thường có tỷ lệ nợ xấu tăng vọt sau chu kỳ 3 năm.

**Tác động doanh nghiệp:** Dự án thiết lập một nền tảng dữ liệu tài chính tự động, giúp giảm 80% thời gian trích xuất và lập báo cáo thủ công. Các mô hình cảnh báo sớm cung cấp cơ sở định lượng vững chắc giúp bộ phận quản trị rủi ro hoặc nhà đầu tư tái cơ cấu danh mục kịp thời, tránh tổn thất từ các rủi ro tín dụng tiềm ẩn.

---

## 6. Dự kiến

**Hành động 1:** Kích hoạt ngay hệ thống giám sát và cảnh báo tự động intraday. Khi phát hiện tỷ trọng lệnh mua chủ động đột biến kết hợp với dòng tiền tự doanh dương, cân nhắc gia tăng tỷ trọng giải ngân ngắn hạn đối với các mã cổ phiếu đang theo dõi.

**Hành động 2:** Dựa trên kết quả phân loại từ mô hình sức khỏe tài chính, các nhà đầu tư tổ chức nên xây dựng chiến lược phân bổ vốn dài hạn, ưu tiên rót vốn vào cụm ngân hàng duy trì sự cân bằng giữa biên lãi ròng ổn định và dự phòng rủi ro nợ xấu an toàn.

---

## 7. Cấu Trúc Thư Mục Dự Án - Project Structure (Dự kiến)

```
da_project/
├── data/
│   ├── raw/
│   ├── processed/
│   └── external/
├── notebooks/
│   ├── 01_EDA.ipynb
│   ├── 02_ETL_BigQuery.ipynb
│   ├── 03_ML_TimeSeries.ipynb
│   ├── 04_ML_Clustering.ipynb
│   ├── 05_ML_Classification.ipynb
│   └── 06_PCA_Visualization.ipynb
├── src/
│   ├── etl/
│   ├── models/
│   └── utils/
├── reports/
│   ├── figures/
│   └── final_report.docx
├── sql/
│   └── bigquery_schema.sql
├── requirements.txt
└── README.md
```

---

---

## PHẦN DÀNH CHO EXCALIDRAW - Thông tin sơ đồ

*Sử dụng các mô tả dưới đây để vẽ lại sơ đồ cấu trúc trên Excalidraw.*

**Sơ đồ 1: Kiến trúc Kho dữ liệu - Star Schema**

- **Trung tâm - Fact Tables:**
    - Bảng fact_foreign_trading: foreign_volume, foreign_value, ownership
    - Bảng fact_proprietary_trading: prop_buy, prop_sell, prop_net
    - Bảng fact_price_history: open, high, low, close, volume
    - Bảng fact_order_stats: buy_orders, sell_orders, matched
    - Bảng fact_bank_performance: deposits, loans, npl, roa, roe
- **Các vệ tinh xung quanh - Dimension Tables trỏ khóa ngoại vào Fact:**
    - Bảng dim_date: date_key, day, month, year, quarter
    - Bảng dim_stock: stock_key, ticker, company_name, exchange
    - Bảng dim_bank: bank_key, bank_code, bank_type, charter_capital, valid_from, valid_to, is_current
    - Bảng dim_trading_session: session_key, session_name, start_time
    - Bảng dim_audit: audit_key, run_id, run_timestamp, status

**Sơ đồ 2: Luồng xử lý dữ liệu - ETL & ML Pipeline**

- **Khối 1 Nguồn dữ liệu:** File Excel, Tài liệu yêu cầu. Mũi tên hướng sang Khối 2.
- **Khối 2 ETL Pipeline:** Extract bằng Python Pandas. Transform làm sạch dữ liệu. Load bằng Google Cloud API. Mũi tên hướng sang Khối 3.
- **Khối 3 Data Warehouse:** Google BigQuery lưu trữ 5 bảng Dim và 5 bảng Fact. Mũi tên hướng sang Khối 4.
- **Khối 4 Analytics & Machine Learning:** Trực quan hóa EDA. Chạy mô hình Học máy có giám sát và không giám sát. Xuất báo cáo Dashboard.

**Sơ đồ 3: Cấu trúc Mô hình Học máy**

- **Nhánh 1 Học có giám sát:**
    - Dự báo chuỗi thời gian: Mô hình ARIMA, LSTM dự báo giá cổ phiếu.
    - Phân loại rủi ro: Mô hình Logistic Regression, Random Forest đánh giá nợ xấu ngân hàng.
- **Nhánh 2 Học không giám sát:**
    - Phân cụm: Mô hình K-Means nhóm các ngân hàng có hiệu suất tương đồng.
    - Giảm chiều dữ liệu: Mô hình PCA tối ưu hóa tập 47 biến số tài chính để phục vụ trực quan hóa.