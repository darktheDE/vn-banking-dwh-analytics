# ADR-0002: Kiểm Soát Miền Giá Trị CAMELS và Xử Lý Ngoại Lệ Ngân Hàng

* **Trạng thái:** Accepted
* **Ngày:** 2026-09-07
* **Tác giả:** Đỗ Kiến Hưng & Antigravity Agent
* **Phạm vi:** `src/etl/load_bank_performance.py`, `fact_bank_performance`

---

## 1. Bối cảnh & Vấn đề (Context)
Trong phiên bản v1, phát hiện có 28 bản ghi trong `fact_bank_performance` có tỷ lệ nợ xấu `npl_ratio` vượt ngoài khoảng hợp lệ $[0, 1]$ (âm hoặc lớn hơn 100%), và một số chỉ số biên như `nim > 0.50`, `ltd > 3.0` (Issue B-08).
Kế hoạch ban đầu trong `refactor-v1.md` đề xuất: *"Khi gặp nim > 0.20 hoặc ltd > 2.0 thì log warning và fallback về median toàn ngành"*.

## 2. Phân tích Các Phương án (Decision Drivers)
1. **Lỗi toán học vs Đặc thù kinh doanh:**
   - Với `npl_ratio`: Định nghĩa theo Thông tư 11/2021/TT-NHNN là tỷ lệ nợ xấu trên tổng dư nợ cho vay. Do đó, việc giá trị nằm ngoài $[0, 1]$ thuần túy là lỗi toán học (chia cho mẫu số $\le 0$) hoặc lỗi định dạng (gõ $3.5$ thay vì $0.035$). Đây là lỗi cần phải sửa trực tiếp trong công thức tính toán.
   - Với `nim`, `ltd`, `eta`: Bộ dữ liệu Harvard Dataverse bao gồm 45 ngân hàng với 3 nhóm sở hữu: NHTM Nhà nước (`SOCB`), NHTM Cổ phần (`JSCB`), và Ngân hàng Ngoại/Liên doanh (`FOCB`).
   - Các ngân hàng FOCB (như Indovina Bank, VRB) hoạt động chủ yếu bằng vốn cấp từ công ty mẹ hoặc vay liên ngân hàng, hầu như không nhận tiền gửi cá nhân. Do đó, tỷ lệ `ltd` ($\text{dư nợ} / \text{tiền gửi}$) và `eta` ($\text{vốn} / \text{tài sản}$) của họ cao bất thường một cách tự nhiên.
2. **Ảnh hưởng tới mô hình học máy (K-Means Clustering):**
   - Nghiên cứu Q4 đã phân chia 39 ngân hàng thành 3 cụm, trong đó Cụm 2 đại diện riêng cho **"Khối Ngoại & Đặc thù"** với đặc trưng đệm vốn cực cao và dư nợ tín dụng/tiền gửi dị biệt.
   - Nếu áp đặt quy tắc "gán về Median toàn ngành" cho các ngân hàng FOCB, ta sẽ vô tình xóa bỏ các đặc trưng dị biệt này, dẫn đến việc phân cụm K-Means bị co cụm sai lệch.

## 3. Quyết định (Decision)
1. **Đối với `npl_ratio`:**
   - Kiểm tra điều kiện mẫu số $\text{total\_loans} > 0$. Nếu $\le 0$ thì gán `np.nan` thay vì thực hiện phép chia.
   - Nếu giá trị sau chuẩn hóa $> 1.0$, tự động chia cho 100 để đưa về dạng số thập phân.
   - Ràng buộc chặt chẽ giá trị trong đoạn $[0.0, 1.0]$.
2. **Đối với `nim` và `ltd`:**
   - Phân biệt theo loại hình ngân hàng `bank_type`:
     - Nếu là `SOCB` hoặc `JSCB` (ngân hàng nội địa): Đặt ngưỡng cảnh báo nếu $\text{nim} > 0.20$ hoặc $\text{ltd} > 2.0$.
     - Nếu là `FOCB` (ngân hàng ngoại): Cho phép giữ nguyên giá trị thực tế và ghi chú thích trong từ điển dữ liệu.

## 4. Hệ quả (Consequences)
* **Tích cực:** 
  - Loại bỏ hoàn toàn 28 dòng nợ xấu sai lệch toán học.
  - Bảo tồn nguyên vẹn ý nghĩa kinh tế lượng và hồ sơ tài chính của Cụm 2 (Khối Ngoại) trong phân cụm K-Means.
