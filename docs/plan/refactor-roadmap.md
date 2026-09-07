# Lộ Trình Refactor Chi Tiết (Refactor Master Roadmap)

Tài liệu này đóng vai trò kế hoạch thực thi chính thức của dự án qua 6 giai đoạn refactor, kết nối giữa các quyết định kiến trúc (`docs/adr/`) và danh sách tác vụ chi tiết (`docs/plan/tasks-phase2-to-phase5.md`).

---

## Tổng Quan 6 Giai Đoạn

| Giai đoạn | Tên mục tiêu | Trạng thái | Đầu ra chính |
|---|---|---|---|
| **Phase R1** | Snapshot, Hygiene & Harness Setup | **Đang hoàn thiện** | Tag `v1.0.0`, nhánh `v1-stable`, bộ khung `docs/{spec,adr,plan,memory}`, modular tests. |
| **Phase R2** | BigQuery Zero-Duplicate (Idempotency) | **Sẵn sàng** | Fallback `WRITE_TRUNCATE` trong `load_to_bigquery.py`, script `scripts/check_duplicates.py`. |
| **Phase R3** | Fix Data Quality CAMELS | **Chờ R2** | Xử lý 28 dòng nợ xấu sai lệch, bounds checking có phân biệt FOCB. |
| **Phase R4** | Sync Docs ↔ Code & Deprecation | **Chờ R3** | Đánh dấu `@deprecated` 4 script ETL cũ, sửa claim "7 bảng" thành "10 bảng", 40 dòng ML. |
| **Phase R5** | Release v1.1.0 & Backup | **Chờ R4** | Tag `v1.1.0`, merge `refactor/v1-cleanup` vào `main`, release notes. |
| **Phase R6** | Chuẩn bị Hạ tầng v2 | **Kế hoạch tương lai** | `docs/v2-roadmap.md` (Airflow orchestration, Great Expectations, CI/CD GitHub Actions). |
