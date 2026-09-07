# Quy Chuẩn Nghiệp Vụ Ngân Hàng Việt Nam (Domain Rules)

Tài liệu này định nghĩa các căn cứ pháp lý, chuẩn mực quản trị rủi ro và công thức tài chính bắt buộc áp dụng cho toàn bộ các mô hình và tầng dữ liệu trong dự án.

---

## 1. Căn Cứ Pháp Quy Của Ngân Hàng Nhà Nước Việt Nam (SBV)

1. **Thông tư 11/2021/TT-NHNN** (Thay thế Thông tư 02/2013/TT-NHNN):
   - Quy định về phân loại tài sản có, mức trích, phương pháp trích lập dự phòng rủi ro và việc sử dụng dự phòng để xử lý rủi ro trong hoạt động của TCTD.
   - Nợ xấu (NPL - Non-Performing Loans) bao gồm các khoản nợ thuộc **Nhóm 3 (Nợ dưới tiêu chuẩn)**, **Nhóm 4 (Nợ nghi ngờ)** và **Nhóm 5 (Nợ có khả năng mất vốn)**.
   - **Ngưỡng cảnh báo đỏ 3%:** Các ngân hàng có tỷ lệ nợ xấu $\ge 3\%$ sẽ bị SBV giới hạn tăng trưởng tín dụng, kiểm soát đặc biệt và hạn chế chi trả cổ tức bằng tiền mặt. Đây là căn cứ để bài toán Random Forest chọn ngưỡng phân loại nhị phân $1$ ($\text{NPL} \ge 3\%$) và $0$ ($\text{NPL} < 3\%$).
2. **Thông tư 22/2019/TT-NHNN**:
   - Quy định các giới hạn, tỷ lệ bảo đảm an toàn trong hoạt động của ngân hàng.
   - Tỷ lệ dư nợ cho vay so với tổng tiền gửi (LDR / LTD) tối đa là **85%** đối với ngân hàng thương mại.

---

## 2. Khung Chỉ Số CAMELS Ứng Dụng Trong DWH

| Ký hiệu | Thành tố CAMELS | Chỉ số cốt lõi | Ý nghĩa tài chính |
|---|---|---|---|
| **C** | Capital Adequacy (An toàn vốn) | `eta` (Vốn CSH / Tổng tài sản)<br>`etd` (Vốn CSH / Tiền gửi) | Năng lực tự chủ vốn và đệm hấp thụ rủi ro của ngân hàng. |
| **A** | Asset Quality (Chất lượng tài sản) | `npl_ratio` (Tỷ lệ nợ xấu)<br>`llp_ratio` (Tỷ lệ trích lập dự phòng) | Phản ánh mức độ suy giảm chất lượng tín dụng và tính thận trọng trích lập của ban điều hành. |
| **M** | Management (Năng lực quản trị) | `cir` (Chi phí hoạt động / Tổng thu nhập) | Năng lực tối ưu hóa chi phí vận hành và hiệu quả theo quy mô. |
| **E** | Earnings (Hiệu quả sinh lời) | `roa` (LNST / Tổng tài sản)<br>`roe` (LNST / Vốn CSH)<br>`nim` (Thu nhập lãi thuần / Tài sản sinh lời) | Thước đo khả năng tạo ra dòng tiền bền vững và biên lãi ròng. |
| **L** | Liquidity (Thanh khoản) | `lta` (Dư nợ / Tổng tài sản)<br>`ltd` (Dư nợ / Tổng tiền gửi) | Năng lực đáp ứng nghĩa vụ chi trả tiền gửi của khách hàng. |
| **S** | Sensitivity (Độ nhạy cảm thị trường) | `gta` (Dư nợ cho vay / Tài sản)<br>`off_balance_sheet` | Mức độ phụ thuộc vào thị trường tín dụng truyền thống và các cam kết ngoại bảng. |
