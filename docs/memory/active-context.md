# Ngữ Cảnh Hoạt Động Hiện Tại (Active Context)

Tài liệu này lưu lại trạng thái tức thời (Hot Context) của phiên làm việc để bất kỳ Agent hoặc kỹ sư nào tiếp quản cũng nắm bắt được ngay hiện trạng hệ thống.

---

## 1. Trạng Thái Hiện Tại
* **Nhánh làm việc Git:** `refactor/v1-cleanup`
* **Commit gần nhất:** `1b114bf feat: add Looker Studio scorecard verification script and pipeline import smoke tests`
* **Mục tiêu phiên:** Hoàn tất Phase R1 (Hygiene & Harness) -> Thực thi Phase R2 (BigQuery Zero-Duplicate) -> Phase R3 (CAMELS Data Quality).
* **Tiến độ bộ khung Harness:**
  - `docs/spec/`: Hoàn thành 3 spec (`01-dwh-idempotency`, `02-camels-data-quality`, `03-code-hygiene-testing`).
  - `docs/adr/`: Hoàn thành 3 ADR (`0001-idempotent-bigquery-loading`, `0002-camels-bounds-and-outliers`, `0003-modular-test-suite`).
  - `docs/plan/`: Hoàn thành lộ trình tổng thể và checklist tác vụ chi tiết.
  - `docs/memory/`: Hoàn thành nhật ký lỗi và quy chuẩn nghiệp vụ.

## 2. Việc Đang Triển Khai Tiếp Theo
1. Hoàn tất Phase R1:
   - Sửa side-effect ở `src/etl/extract_data.py`.
   - Cập nhật `tests/test_pipeline_imports.py` hỗ trợ `--tier {etl, ml, dashboard, all}`.
2. Triển khai Phase R2:
   - Sửa `src/etl/load_to_bigquery.py` fallback sang `WRITE_TRUNCATE`.
   - Viết `scripts/check_duplicates.py`.
3. Triển khai Phase R3:
   - Sửa `src/etl/load_bank_performance.py` cho `npl_ratio` và bounds CAMELS.
