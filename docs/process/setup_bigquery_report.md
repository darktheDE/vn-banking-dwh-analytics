# Báo cáo Tiến độ Thiết lập Môi trường & Kết nối Google BigQuery

Tài liệu này tổng hợp toàn bộ các bước thiết lập hạ tầng đám mây (Google Cloud Platform) và môi trường phát triển cục bộ đã được hoàn thành cho dự án **vn-banking-dwh-analytics**.

---

## 1. Các Công việc Đã Hoàn thành (GCP & IAM)
Theo đúng hướng dẫn tại [bigquery_setup_guide.md](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/project2/vn-banking-dwh-analytics/docs/process/bigquery_setup_guide.md), bạn đã hoàn tất **Bước 5** bao gồm:

*   **Khởi tạo GCP Project:** Tạo dự án `vn-banking-dwh-analytics`.
*   **Kích hoạt BigQuery API:** Bật dịch vụ BigQuery trên GCP.
*   **Tạo Service Account (Task A-03):** Tạo tài khoản dịch vụ `bq-pipeline-sa` có vai trò `BigQuery Data Editor` và `BigQuery Job User`, sau đó xuất khóa JSON key đặt tại thư mục gốc của dự án.
*   **Tạo BigQuery Dataset (Task B-01):** Khởi tạo dataset `financial_dwh` để chuẩn bị chứa cấu trúc Star Schema.
*   **Phân quyền thành viên IAM (Task D-01):** Thêm 4 thành viên trong nhóm vào dự án GCP và phân quyền `BigQuery User` / `BigQuery Data Viewer` nhằm kết nối báo cáo Looker Studio.

---

## 2. Thiết lập Môi trường Phát triển Cục bộ (Local Environment)
Chúng ta đã cấu hình thành công môi trường chạy thực tế trên máy Windows của bạn:

*   **Khởi tạo Virtual Environment (Task A-01):** Tạo môi trường ảo cục bộ `venv` chạy Python 3.12.
*   **Cài đặt Thư viện (Task A-02):** Cài đặt đầy đủ tất cả các gói dependencies từ [requirements.txt](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/project2/vn-banking-dwh-analytics/requirements.txt), bao gồm các gói xử lý dữ liệu (`pandas`, `openpyxl`), máy học (`tensorflow`, `scikit-learn`, `statsmodels`), kết nối dữ liệu (`google-cloud-bigquery`, `pandas-gbq`) và thư viện lấy dữ liệu tài chính (`vnstock`).
*   **Cấu hình Biến môi trường di động (Task A-05):** 
    *   Tạo file [.env](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/project2/vn-banking-dwh-analytics/.env) từ file mẫu.
    *   Sử dụng đường dẫn tương đối (relative path) giúp dự án linh hoạt khi di chuyển sang máy khác:
        ```env
        GOOGLE_APPLICATION_CREDENTIALS=./vn-banking-dwh-analytics-67f213ad7317.json
        GCP_PROJECT_ID=vn-banking-dwh-analytics
        BQ_DATASET_ID=financial_dwh
        ```

---

## 3. Kết quả Xác minh Kết nối (Verification Results)
Chạy script [test_bq_connection.py](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/project2/vn-banking-dwh-analytics/test_bq_connection.py) kiểm thử kết nối hai chiều thành công:

```text
[*] Project ID: vn-banking-dwh-analytics
[*] Dataset ID: financial_dwh
[*] Credentials Path: ./vn-banking-dwh-analytics-67f213ad7317.json
[*] Initializing BigQuery Client...
[*] Testing basic query execution (SELECT 1)...
[+] Data retrieved successfully: 1
[*] Checking Dataset 'financial_dwh'...
[+] Connection successful, but Dataset 'financial_dwh' currently has no tables.

[+] ALL CONNECTIONS ARE STABLE AND READY!
```

---

## 4. Các bước tiếp theo trong Checklist
Dựa trên [tasks.md](file:///d:/HCMUTE/HCMUTE_HK6/DataAnalysis/project2/vn-banking-dwh-analytics/docs/tasks.md), nhóm có thể tiếp tục triển khai các công việc:
1.  **B-02 & B-03:** Chạy script tạo cấu trúc Star Schema (các bảng Dimension & Fact) trong BigQuery Dataset `financial_dwh` (Nguyễn Đặng Quốc Anh phụ trách).
2.  **B-04 đến B-07:** Nạp dữ liệu danh mục cho các bảng Dimension (`dim_date`, `dim_stock`, `dim_bank`, `dim_trading_session`).
