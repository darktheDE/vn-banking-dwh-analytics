# ADR-0003: Phân Tầng Bộ Kiểm Thử Tự Động (Modular Test Suite)

* **Trạng thái:** Accepted
* **Ngày:** 2026-09-07
* **Tác giả:** Đỗ Kiến Hưng & Antigravity Agent
* **Phạm vi:** `tests/`, `tests/test_pipeline_imports.py`

---

## 1. Bối cảnh & Vấn đề (Context)
Trong phiên bản ban đầu, file `tests/test_pipeline_imports.py` gom toàn bộ 22 module của dự án (từ Utils, ETL, ML TensorFlow, cho đến Streamlit Dashboard) vào trong một danh sách kiểm tra duy nhất.
Khi chạy kiểm thử trên môi trường Python 3.12 (chưa cài đủ các thư viện nặng như `tensorflow`, `streamlit`, `vnstock`), test trả về `FAIL` 9/22 module, làm sập toàn bộ quy trình CI/CD kiểm thử tự động, mặc dù tầng ETL và Data Warehouse cốt lõi vẫn hoạt động hoàn hảo 100%.

## 2. Quyết định (Decision)
1. Tách cấu trúc kiểm thử theo 3 phân tầng độc lập (Tiers):
   - **Tầng 1 - `etl` (Core Data Pipeline):** Gồm `src.utils.*` và 10 module sản xuất của `src.etl.*`. Chỉ yêu cầu các thư viện tiêu chuẩn: `pandas`, `openpyxl`, `google-cloud-bigquery`.
   - **Tầng 2 - `ml` (Machine Learning Models):** Gồm 8 module mô hình trong `src.models.*`. Yêu cầu `scikit-learn`, `statsmodels`, `tensorflow`.
   - **Tầng 3 - `dashboard` (Presentation & Audit):** Gồm `src.dashboard.app` và `scripts.*`. Yêu cầu `streamlit`, `plotly`.
2. Bổ sung tham số dòng lệnh `--tier {etl, ml, dashboard, all}` vào script `tests/test_pipeline_imports.py` để người phát triển có thể kiểm thử riêng biệt từng tầng theo năng lực của môi trường máy chủ.

## 3. Hệ quả (Consequences)
* **Tích cực:** Quá trình kiểm tra tầng ETL và DWH diễn ra cực kỳ nhanh chóng (< 1 giây), không bị chặn bởi các dependency phức tạp của Deep Learning.
