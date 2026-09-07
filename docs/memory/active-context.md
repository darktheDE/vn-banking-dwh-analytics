# Ngữ Cảnh Hoạt Động Hiện Tại (Active Context)

Tài liệu này lưu lại trạng thái tức thời (Hot Context) của phiên làm việc để bất kỳ Agent hoặc kỹ sư nào tiếp quản cũng nắm bắt được ngay hiện trạng hệ thống.

---

## 1. Trạng Thái Hiện Tại
* **Nhánh làm việc Git:** `main` (clean working tree).
* **Release Version:** Tag `v1.1.0` đã phát hành và đẩy lên GitHub.
* **CI/CD Pipeline:** Đã thiết lập GitHub Actions ([.github/workflows/ci.yml](../../.github/workflows/ci.yml)). Run 34100220340: **SUCCESS** trên cả Python 3.10 và 3.11.
* **GCP BigQuery Environment:** Dataset `financial_dwh` trong project `vn-banking-dwh-analytics` (`asia-southeast1`). Toàn bộ 10 bảng (5 Dim, 2 Fact, 3 ML Output) sạch, không trùng lặp (0 duplicate keys), chất lượng dữ liệu CAMELS đạt chuẩn Thông tư SBV.
* **Harness Architecture:** Hoàn tất 11 tài liệu kỹ thuật chuẩn trong `docs/spec/`, `docs/adr/`, `docs/plan/`, `docs/memory/`.

---

## 2. Kết Quả Kiểm Thử & CI Tự Động
1. **Compilation Check**: `python -m compileall -q src tests scripts` -> **PASS**.
2. **Core DWH Smoke Test**: `python tests/test_pipeline_imports.py --tier etl` -> **13/13 PASS**.
3. **Data Integrity & Star Schema**: `python -m src.etl.validate_integrity` -> **TOTAL ERRORS FOUND: 0**.
4. **Primary Key Uniqueness**: `python scripts/check_duplicates.py` -> **0 duplicate keys trên toàn bộ 9 bảng**.
