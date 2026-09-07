# SPEC-02: CAMELS Financial Indicators Data Quality Specification

## 1. Mục đích
Tài liệu này chuẩn hóa các quy tắc kiểm tra chất lượng dữ liệu (Data Quality Rules) và miền giá trị hợp lệ của 10 chỉ số tài chính CAMELS được lưu trữ trong `fact_bank_performance` và phục vụ các mô hình phân cụm K-Means, phân loại rủi ro Random Forest.

## 2. Quy tắc Miền Giá Trị (Domain Constraints)

| Chỉ số | Tên đầy đủ | Công thức tính toán | Miền giá trị hợp lệ | Quy tắc xử lý ngoại lệ (Sanity Rules) |
|---|---|---|---|---|
| `npl_ratio` | Non-Performing Loans Ratio | $\frac{\text{npl\_amount}}{\text{total\_loans}}$ | $[0.0, 1.0]$ | 1. Nếu $\text{total\_loans} \le 0$ hoặc null: gán null.<br>2. Nếu giá trị $> 1.0$ (dữ liệu thô gõ $3.5$ thay vì $0.035$): chia cho 100.<br>3. Chặn trần tại $[0.0, 1.0]$. |
| `llp_ratio` | Loan Loss Provision Ratio | $\frac{\text{loan\_loss\_provision}}{\text{total\_loans}}$ | $[0.0, 0.5]$ | Tỷ lệ trích lập dự phòng rủi ro tín dụng. Giá trị $> 0.20$ ghi warning log. |
| `roa` | Return on Assets | $\frac{\text{profit\_after\_tax}}{\text{total\_assets}}$ | $[-0.20, 0.20]$ | Biên lợi nhuận trên tổng tài sản. |
| `roe` | Return on Equity | $\frac{\text{profit\_after\_tax}}{\text{total\_equity}}$ | $[-1.0, 1.0]$ | Biên lợi nhuận trên vốn chủ sở hữu. |
| `nim` | Net Interest Margin | $\frac{\text{net\_interest\_income}}{\text{total\_assets}}$ | $[0.0, 0.15]$ | Đối với NHTM nội địa (`SOCB`, `JSCB`), `nim` thực tế $2.5\% - 4.5\%$. Nếu $\text{nim} > 0.20$ ghi warning log. |
| `cir` | Cost-to-Income Ratio | $\frac{\text{non\_interest\_expense}}{\text{net\_interest\_income} + \text{non\_interest\_income}}$ | $[0.0, 2.0]$ | Tỷ lệ chi phí vận hành trên tổng thu nhập hoạt động. Lọc bỏ các trường hợp mẫu số âm. |
| `eta` | Equity to Assets | $\frac{\text{total\_equity}}{\text{total\_assets}}$ | $[0.0, 1.0]$ | Đệm vốn chủ sở hữu trên tổng tài sản. Khối ngoại (FOCB) có thể đạt giá trị rất cao. |
| `etd` | Equity to Deposits | $\frac{\text{total\_equity}}{\text{total\_deposits}}$ | $[0.0, 5.0]$ | Khối ngoại huy động tiền gửi ít, tỷ số này có thể $> 2.0$. |
| `lta` | Loans to Assets | $\frac{\text{total\_loans}}{\text{total\_assets}}$ | $[0.0, 1.0]$ | Tỷ trọng dư nợ tín dụng trên tổng tài sản. |
| `ltd` | Loans to Deposits | $\frac{\text{total\_loans}}{\text{total\_deposits}}$ | $[0.0, 5.0]$ | Ngân hàng nội địa tuân thủ Thông tư 22/2019/TT-NHNN tối đa $85\%$ ($0.85$). Khối ngoại (FOCB) cho phép $> 2.0$. |

## 3. Quy tắc phân nhóm Ngân hàng khi kiểm tra Outliers
- **Nhóm 1: Ngân hàng thương mại nội địa (SOCB, JSCB):** Áp dụng trần kiểm soát cảnh báo chặt chẽ: `nim <= 0.20`, `ltd <= 2.0`.
- **Nhóm 2: Ngân hàng ngoại & Liên doanh (FOCB):** Do đặc thù nhận vốn từ ngân hàng mẹ và ít nhận tiền gửi cá nhân, các tỷ số `ltd` hoặc `etd` có thể cao tự nhiên. **Tuyệt đối không tự ý gán giá trị Median toàn ngành** cho nhóm này nhằm bảo tồn sự tách biệt trong phân cụm K-Means Cụm 2.
