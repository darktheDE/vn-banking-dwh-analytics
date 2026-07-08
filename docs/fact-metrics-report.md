# Báo Cáo Đặc Tả Chỉ Số Tính Toán Trong Các Bảng Sự Kiện (Fact Tables)

Báo cáo này làm rõ việc thiết lập và tính toán các chỉ số (Calculated Metrics) trong hai bảng sự kiện chính của Kho dữ liệu (DWH): `fact_bank_performance` và `fact_stock_daily_metrics`. Các chỉ số này được đối chiếu trực tiếp với các tiêu chuẩn tài chính doanh nghiệp của Công ty Chứng khoán Ngân hàng Ngoại thương Việt Nam (VCBS) và hệ thống KPI tài chính chuẩn quốc tế của NetSuite.

---

## 1. Nguyên tắc thiết kế Bảng Sự Kiện (Fact Table Design)

Trong kiến trúc Kho dữ liệu hiện đại, một bảng sự kiện chuẩn chỉnh không chỉ đóng vai trò là nơi nạp dữ liệu thô (Raw ingestion), mà phải chứa các thuộc tính đo lường được tính toán trước (Calculated/Derived Measures). Việc tính toán trước các chỉ số ở tầng ETL mang lại các lợi ích lớn:
1.  **Tối ưu hóa hiệu năng truy vấn:** Giảm thiểu việc tính toán phức tạp trên hàng triệu dòng dữ liệu khi người dùng truy vấn trên các công cụ BI (Looker Studio, Streamlit).
2.  **Đảm bảo tính nhất quán (Single Source of Truth):** Các chỉ số được định nghĩa công thức duy nhất tại tầng ETL, loại bỏ hoàn toàn sự sai lệch công thức giữa các báo cáo khác nhau.
3.  **Tích hợp trực tiếp cho Học máy (ML-ready):** Dữ liệu trong các bảng Fact sẵn sàng được trích xuất làm đặc trưng huấn luyện cho các mô hình AI/ML mà không cần xử lý lại từ đầu.

---

## 2. Đặc tả các chỉ số trong bảng `fact_bank_performance`

Bảng sự kiện hiệu năng ngân hàng lưu trữ dữ liệu 20 năm của 45 ngân hàng Việt Nam. Hệ thống tự động tính toán các chỉ số CAMELS cốt lõi theo tiêu chuẩn VCBS và NetSuite:

### Bảng tổng hợp chỉ số hiệu năng ngân hàng:

| Tên Chỉ Số (Canonical) | Công Thức Tính Toán Trong ETL | Phân Loại (NetSuite / VCBS) | Ý Nghĩa Nghiệp Vụ & Vai Trò Trong Đồ Án |
|-------------------------|--------------------------------|------------------------------|-----------------------------------------|
| **`net_interest_income`** <br>(Thu nhập lãi thuần) | `interest_income - interest_expense` | Khả năng sinh lời (Profitability) | Đo lường hiệu quả hoạt động tín dụng cốt lõi của ngân hàng trước khi trừ các chi phí vận hành và rủi ro. |
| **`roa`** <br>(Tỷ suất sinh lời trên tài sản) | `profit_after_tax / total_assets` | Khả năng sinh lời (Profitability) | **VCBS & NetSuite KPI #23:** Đo lường mức độ hiệu quả của ban điều hành trong việc sử dụng tổng tài sản để tạo ra lợi nhuận ròng. |
| **`roe`** <br>(Tỷ suất sinh lời trên vốn CSH) | `profit_after_tax / total_equity` | Khả năng sinh lời (Profitability) | **VCBS & NetSuite KPI #16:** Đo lường mức độ sinh lời trên mỗi đồng vốn góp của cổ đông, là chỉ số quan trọng hàng đầu để định giá ngân hàng. |
| **`nim`** <br>(Tỷ suất biên lãi ròng) | `net_interest_income / total_assets` | Khả năng sinh lời (Profitability) | **Tiêu chuẩn VCBS:** Đo lường sự chênh lệch giữa thu nhập lãi thu về và chi phí lãi phải trả trên quy mô tài sản sinh lời. |
| **`cir`** <br>(Tỷ lệ chi phí trên thu nhập) | `non_interest_expense / (net_interest_income.abs() + non_interest_income.abs())` | Hiệu quả hoạt động (Efficiency) | **Tiêu chuẩn VCBS:** Đo lường chi phí vận hành chiếm bao nhiêu phần trăm tổng thu nhập hoạt động, phản ánh năng lực quản lý chi phí. |
| **`npl_ratio`** <br>(Tỷ lệ nợ xấu) | `npl_amount / total_loans` | Chất lượng tài sản (Asset Quality) | **Tiêu chuẩn VCBS & Giám sát rủi ro:** Phản ánh tỷ lệ nợ nhóm 3-5 trên tổng dư nợ cho vay. Đây là **biến mục tiêu phân loại rủi ro tín dụng**. |
| **`llp_ratio`** <br>(Tỷ lệ trích lập dự phòng) | `loan_loss_provision / total_loans` | Chất lượng tài sản (Asset Quality) | Đo lường mức độ phòng thủ rủi ro tín dụng của ngân hàng. Đặc trưng quan trọng nhất trong mô hình Random Forest. |
| **`eta`** <br>(Tỷ lệ Vốn CSH / Tổng tài sản) | `total_equity / total_assets` | An toàn vốn (Capital Adequacy) | Phản ánh tỷ lệ đòn bẩy tài chính và mức độ tự chủ vốn của ngân hàng đối phó với rủi ro mất mát tài sản. |
| **`etd`** <br>(Tỷ lệ Vốn CSH / Tổng tiền gửi) | `total_equity / total_deposits` | An toàn vốn (Capital Adequacy) | Đo lường mức độ đảm bảo của nguồn vốn tự có đối với nghĩa vụ trả tiền gửi cho khách hàng. |
| **`lta`** <br>(Tỷ lệ Cho vay / Tổng tài sản) | `total_loans / total_assets` | Tính thanh khoản (Liquidity) | Đo lường mức độ tập trung tài sản vào hoạt động cho vay sinh lời nhưng đi kèm rủi ro tín dụng cao. |
| **`ltd`** <br>(Tỷ lệ Cho vay / Tổng tiền gửi) | `total_loans / total_deposits` | Tính thanh khoản (Liquidity) | **Tiêu chuẩn VCBS & Ngân hàng Nhà nước:** Đo lường mức độ sử dụng nguồn vốn huy động để cho vay, kiểm soát rủi ro thanh khoản. |

---

## 3. Đặc tả các chỉ số trong bảng `fact_stock_daily_metrics`

Nhằm đáp ứng yêu cầu chuyển đổi dữ liệu thô thành các chỉ số hữu ích cho trực quan hóa và học máy, hệ thống tự động tính toán 5 chỉ số chứng khoán mới tại tầng ETL:

### Bảng tổng hợp chỉ số thị trường chứng khoán:

| Tên Chỉ Số (Canonical) | Công Thức Tính Toán Trong ETL | Phân Loại (Thị Trường / VCBS) | Ý Nghĩa Nghiệp Vụ & Vai Trò Trong Đồ Án |
|-------------------------|--------------------------------|--------------------------------|-----------------------------------------|
| **`price_change`** <br>(Biến động giá tuyệt đối) | `close_price - open_price` | Biến động nội phiên (Volatility) | Lượng hóa mức độ dao động tuyệt đối của giá cổ phiếu trong phiên giao dịch, phản ánh áp lực mua/bán khớp lệnh. |
| **`price_change_pct`** <br>(Tỷ lệ % thay đổi giá) | `(close_price - close_price_t-1) / close_price_t-1` | Đà tăng giá (Momentum) | **Đầu vào cốt lõi cho LSTM Đa biến:** Đo lường tốc độ tăng trưởng giá liên tục hàng ngày để mô hình nắm bắt xu hướng giá ngắn hạn. |
| **`price_amplitude`** <br>(Biên độ dao động) | `(high_price - low_price) / open_price` | Mức độ rủi ro (Risk Measure) | Đo lường biên độ biến động cực đại trong ngày của cổ phiếu, làm đầu vào so sánh mức độ rủi ro giữa các cổ phiếu (Q2). |
| **`volume_change_pct`** <br>(Biến động % khối lượng) | `(trading_volume - trading_volume_t-1) / trading_volume_t-1` | Thanh khoản (Liquidity Change) | **Đầu vào cốt lõi cho LSTM Đa biến:** Phát hiện các điểm bùng nổ thanh khoản (dòng tiền Smart Money gia nhập), báo hiệu đảo chiều xu hướng. |
| **`trading_value`** <br>(Giá trị giao dịch ước tính) | `close_price * trading_volume` | Dòng tiền (Value Flow) | Lượng hóa quy mô dòng tiền thực tế bằng tiền mặt (VND) chảy vào cổ phiếu hàng ngày để so sánh chính xác thị phần thanh khoản. |

---

## 4. Ứng dụng thực tiễn giải quyết câu hỏi nghiên cứu và vẽ biểu đồ Dashboard

Việc bổ sung và tính toán sẵn các chỉ số trên phục vụ trực tiếp cho việc trả lời các câu hỏi nghiên cứu cốt lõi của đồ án và cung cấp dữ liệu cho Streamlit Dashboard:

### 4.1. Giải quyết câu hỏi nghiên cứu Q1 (So sánh LSTM Đa biến vs Đơn biến vs ARIMA)
-   **Ứng dụng:** Hai chỉ số phái sinh `price_change_pct` và `volume_change_pct` được đưa trực tiếp vào cấu hình đa biến (7 features) của mô hình LSTM.
-   **Kiểm chứng:** Kết quả thực nghiệm cho thấy mô hình LSTM Đa biến tích hợp các biến động giá và khối lượng đạt sai số RMSE thấp hơn đáng kể so với LSTM Đơn biến (chỉ dùng giá đóng cửa), khẳng định động lực học về khối lượng và biên độ dao động có giá trị dự báo cực cao trong ngắn hạn.

### 4.2. Giải quyết câu hỏi nghiên cứu Q2 (Đồng pha hay Phân hóa của nhóm cổ phiếu)
-   **Ứng dụng:** Chỉ số biên độ dao động rủi ro `price_amplitude` và biến động giá nội phiên `price_change` giúp so sánh trực tiếp cấu trúc biến động giữa 4 cổ phiếu.
-   **Vẽ biểu đồ Dashboard:**
    -   **Biểu đồ hộp (Box Plot):** Biểu diễn phân phối của `price_amplitude` cho 4 mã cổ phiếu (BID, TCB, VCB, CTG) trên Streamlit Dashboard. Giúp người dùng nhìn thấy VCB có hộp phân phối hẹp hơn (biến động thấp, an toàn hơn) so với CTG và TCB.
    -   **Biểu đồ cột chồng (Stacked Bar Chart):** Biểu diễn thị phần dòng tiền dựa trên `trading_value` qua từng tháng, giúp so sánh tỷ trọng thanh khoản giữa 4 ngân hàng.

### 4.3. Giải quyết câu hỏi nghiên cứu Q3 & Q4 (Mô hình K-Means & Random Forest)
-   **Ứng dụng:** Các chỉ số tài chính tính toán sẵn trong `fact_bank_performance` như `roa`, `roe`, `nim`, `cir`, `eta`, `etd`, `ltd` là các biến đầu vào bắt buộc cho các thuật toán phân cụm và phân loại.
-   **Vẽ biểu đồ Dashboard:**
    -   **Biểu đồ phân tán 2D (PCA Scatter Plot):** Biểu diễn kết quả gom cụm dựa trên các chỉ số CAMELS chuẩn hóa.
    -   **Biểu đồ cột nhóm (Grouped Bar Chart):** So sánh giá trị trung bình của các chỉ số tài chính tính toán (như NIM, CIR, ROE) giữa 3 cụm ngân hàng để mô tả đặc trưng chiến lược hoạt động của từng cụm.
