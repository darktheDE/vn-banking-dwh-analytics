# Checklist Tác Vụ Chi Tiết (Phase R2 - Phase R5)

> **Quy ước trạng thái:** `[ ]` Chưa bắt đầu | `[/]` Đang thực hiện | `[x]` Đã hoàn thành

---

## Phase R1: Hygiene & Harness Completion
- `[x]` **R1-01**: Thiết lập cấu trúc thư mục Harness: `docs/spec/`, `docs/adr/`, `docs/plan/`, `docs/memory/`.
- `[x]` **R1-02**: Viết SPEC-01, SPEC-02, SPEC-03.
- `[x]` **R1-03**: Viết ADR-0001, ADR-0002, ADR-0003.
- `[x]` **R1-04**: Loại bỏ side-effects tại root module của `src/etl/extract_data.py`.
- `[x]` **R1-05**: Thêm tùy chọn `--tier` cho `tests/test_pipeline_imports.py`.

---

## Phase R2: BigQuery Zero-Duplicate Implementation
- `[x]` **R2-01**: Sửa `src/etl/load_to_bigquery.py`: Đổi fallback sang `WRITE_TRUNCATE`.
- `[x]` **R2-02**: Hỗ trợ cờ `--full-reload` để chủ động reload sạch dữ liệu.
- `[x]` **R2-03**: Viết script `scripts/check_duplicates.py` kiểm tra khóa chính trên BigQuery.
- `[x]` **R2-04**: Chạy `python -m src.etl.load_to_bigquery --full-reload` và xác minh row counts khớp CSV 100% (dim_date: 9131, dim_bank: 45, fact_stock: 11835, fact_bank: 667).

---

## Phase R3: CAMELS Data Quality Enforcement
- `[x]` **R3-01**: Sửa hàm `_standardize_raw_frame` trong `src/etl/load_bank_performance.py` cho `npl_ratio` (xử lý contra-assets và chuẩn hóa non-negative $[0, 1]$).
- `[x]` **R3-02**: Bổ sung warning log cho `nim` và `ltd` áp dụng theo nhóm sở hữu `bank_type` (bảo tồn Cụm 2 Khối Ngoại).
- `[x]` **R3-03**: Chạy lại `python -m src.etl.load_bank_performance` và xác nhận 28 dòng nợ xấu out-of-range giảm về 0.
- `[x]` **R3-04**: Chạy `python -m src.etl.validate_integrity` xác nhận `ERRORS FOUND: 0`.

---

## Phase R4: Code Deprecation & Documentation Synchronization
- `[x]` **R4-01**: Thêm cảnh báo `@deprecated` vào 4 file ETL cũ (`load_price_history.py`, `load_foreign_trading.py`, `load_order_stats.py`, `load_proprietary_trading.py`).
- `[x]` **R4-02**: Cập nhật `README.md` và `docs/project-overview.md`: Sửa "7 bảng" -> "10 bảng", cập nhật 40 dòng ML.
- `[x]` **R4-03**: Cập nhật `RESULT.md` và bổ sung DDL cho 3 bảng ML trong `sql/bigquery_schema.sql`.

---

## Phase R5: Release v1.1.0 & Tagging
- `[x]` **R5-01**: Commit các thay đổi hoàn tất vào nhánh `refactor/v1-cleanup`.
- `[x]` **R5-02**: Merge nhánh `refactor/v1-cleanup` vào `main`.
- `[x]` **R5-03**: Tạo git tag `v1.1.0` với changelog chi tiết.
