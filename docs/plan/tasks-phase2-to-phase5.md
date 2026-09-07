# Checklist Tác Vụ Chi Tiết (Phase R2 - Phase R5)

> **Quy ước trạng thái:** `[ ]` Chưa bắt đầu | `[/]` Đang thực hiện | `[x]` Đã hoàn thành

---

## Phase R1: Hygiene & Harness Completion
- `[x]` **R1-01**: Thiết lập cấu trúc thư mục Harness: `docs/spec/`, `docs/adr/`, `docs/plan/`, `docs/memory/`.
- `[x]` **R1-02**: Viết SPEC-01, SPEC-02, SPEC-03.
- `[x]` **R1-03**: Viết ADR-0001, ADR-0002, ADR-0003.
- `[/]` **R1-04**: Loại bỏ side-effects tại root module của `src/etl/extract_data.py`.
- `[/]` **R1-05**: Thêm tùy chọn `--tier` cho `tests/test_pipeline_imports.py`.

---

## Phase R2: BigQuery Zero-Duplicate Implementation
- `[ ]` **R2-01**: Sửa `src/etl/load_to_bigquery.py`: Đổi fallback sang `WRITE_TRUNCATE`.
- `[ ]` **R2-02**: Hỗ trợ cờ `--full-reload` để chủ động reload sạch dữ liệu.
- `[ ]` **R2-03**: Viết script `scripts/check_duplicates.py` kiểm tra khóa chính trên BigQuery.
- `[ ]` **R2-04**: Chạy `python -m src.etl.load_to_bigquery --full-reload` và xác minh row counts khớp CSV 100%.

---

## Phase R3: CAMELS Data Quality Enforcement
- `[ ]` **R3-01**: Sửa hàm `_standardize_raw_frame` trong `src/etl/load_bank_performance.py` cho `npl_ratio`.
- `[ ]` **R3-02**: Bổ sung warning log cho `nim` và `ltd` áp dụng theo nhóm sở hữu `bank_type`.
- `[ ]` **R3-03**: Chạy lại `python -m src.etl.load_bank_performance` và xác nhận 28 dòng nợ xấu out-of-range giảm về 0.
- `[ ]` **R3-04**: Chạy `python -m src.etl.validate_integrity` xác nhận `ERRORS FOUND: 0`.

---

## Phase R4: Code Deprecation & Documentation Synchronization
- `[ ]` **R4-01**: Thêm cảnh báo `@deprecated` vào 4 file ETL cũ (`load_price_history.py`, `load_foreign_trading.py`, `load_order_stats.py`, `load_proprietary_trading.py`).
- `[ ]` **R4-02**: Cập nhật `README.md`: Sửa "7 bảng" -> "10 bảng", cập nhật 40 dòng ML.
- `[ ]` **R4-03**: Cập nhật `RESULT.md` và `HUONG_DAN_DU_AN.md`.

---

## Phase R5: Release v1.1.0 & Tagging
- `[ ]` **R5-01**: Merge nhánh `refactor/v1-cleanup` vào `main`.
- `[ ]` **R5-02**: Tạo git tag `v1.1.0` với changelog chi tiết.
