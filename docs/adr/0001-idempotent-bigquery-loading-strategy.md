# ADR-0001: Chiến Lược Nạp Dữ Liệu BigQuery Đảm Bảo Tính Bất Biến (Idempotency)

* **Trạng thái:** Accepted
* **Ngày:** 2026-09-07
* **Tác giả:** Đỗ Kiến Hưng & Antigravity Agent
* **Phạm vi:** `src/etl/load_to_bigquery.py`, `financial_dwh`

---

## 1. Bối cảnh & Vấn đề (Context)
Trong phiên bản v1, hệ thống lưu trữ BigQuery gặp phải lỗi nhân đôi dữ liệu (Issue B-01): 6/10 bảng có số dòng gấp đôi dữ liệu thực tế (ví dụ: `dim_date` bị 18.262 dòng thay vì 9.131 dòng, `fact_bank_performance` 1.334 dòng thay vì 667 dòng).
Nguyên nhân gốc rễ: Đoạn mã `src/etl/load_to_bigquery.py` có cơ chế fallback khi lệnh `MERGE` thất bại vì tài khoản không có Billing (`billingNotEnabled`):
```python
job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
```
Mỗi lần chạy lại pipeline để kiểm thử hoặc cập nhật dữ liệu, toàn bộ file CSV lại bị append thêm một lần, gây ra duplicate.

Kế hoạch ban đầu trong `refactor-v1.md` đề xuất: *"Bỏ fallback WRITE_APPEND và ép buộc chỉ dùng MERGE (fail loud nếu billing tắt)"*.

## 2. Phân tích Các Phương án (Decision Drivers)
1. **Ràng buộc BigQuery Sandbox:** Theo tài liệu chính thức của Google Cloud, BigQuery Sandbox (miễn phí, không add credit card) **hoàn toàn không hỗ trợ các lệnh DML (`MERGE`, `UPDATE`, `DELETE`)**. Nếu chỉ cho phép `MERGE`, bất kỳ ai clone repo về chạy thử nghiệm ở chế độ miễn phí sẽ bị sập pipeline ngay tại bước load.
2. **Hỗ trợ của BigQuery LoadJob:** Thao tác tải tệp hàng loạt (`client.load_table_from_dataframe`) được hỗ trợ đầy đủ trong Sandbox và hỗ trợ tùy chọn `write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE`.
3. **Yêu cầu Idempotent:** Chạy lại lệnh nhiều lần phải cho ra cùng một kết quả duy nhất.

## 3. Quyết định (Decision)
1. Trong môi trường Production có Billing kích hoạt: Tiếp tục duy trì luồng tải qua bảng tạm (Staging) và chạy câu lệnh `MERGE` SQL upsert theo khóa chính (Primary Key).
2. Khi phát hiện lỗi `billingNotEnabled` (hoặc khi người dùng truyền tham số CLI `--full-reload`): Chuyển đổi fallback sang sử dụng **`WRITE_TRUNCATE`** thay vì `WRITE_APPEND`.
3. Bổ sung script tự động `scripts/check_duplicates.py` để xác thực tính toàn vẹn và độ duy nhất của khóa chính sau mỗi lần load.

## 4. Hệ quả (Consequences)
* **Tích cực:** 
  - Triệt tiêu hoàn toàn nguy cơ nhân đôi dữ liệu (Zero Duplicate).
  - Pipeline chạy trơn tru cả trên Google Cloud Billing lẫn BigQuery Sandbox miễn phí.
* **Tiêu cực / Đánh đổi:** 
  - Khi chạy ở chế độ Sandbox (dùng `WRITE_TRUNCATE`), toàn bộ bảng đích sẽ được ghi đè thay vì cập nhật từng dòng. Điều này chấp nhận được đối với khối lượng dữ liệu hiện tại (~12.000 dòng fact cổ phiếu và 667 dòng fact ngân hàng).
