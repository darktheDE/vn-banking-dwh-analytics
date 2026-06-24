# Hướng dẫn Thiết lập Google BigQuery và Phân quyền IAM Thành viên

Tài liệu này cung cấp hướng dẫn chi tiết từng bước để quản trị viên thiết lập dự án Google Cloud Platform (GCP), tạo Google BigQuery Dataset, tạo Service Account cho các tiến trình tự động và phân quyền IAM cho 4 thành viên trong nhóm.

---

## 1. Bản đồ Công việc và Mapping với tasks.md

Việc thực hiện các bước trong hướng dẫn này sẽ giải quyết trực tiếp và hỗ trợ hoàn thành các nhiệm vụ sau trong [tasks.md](file:///Users/aura/Desktop/KIENHUNG/vn-banking-dwh-analytics/docs/tasks.md):

*   **A-03 (Hoàn thành 100%)**: Tạo GCP Service Account với vai trò `BigQuery Data Editor` và `BigQuery Job User`, sau đó xuất khóa JSON key để sử dụng dưới môi trường local.
*   **A-04 (Hỗ trợ hoàn thành)**: Cung cấp tệp JSON key vừa tạo cho cả 4 thành viên cấu hình biến môi trường `GOOGLE_APPLICATION_CREDENTIALS`.
*   **B-01 (Hoàn thành 100%)**: Tạo BigQuery Dataset dựa trên cấu hình `BQ_DATASET_ID` từ tệp `.env`.
*   **D-01 (Hỗ trợ hoàn thành)**: Phân quyền tài khoản cá nhân cho các thành viên phụ trách Business Intelligence (BI) để kết nối Looker Studio bằng BigQuery Native Connector.

---

## 2. Thông tin Nhóm và Vai trò Phân quyền

Nhóm dự án gồm 4 thành viên với vai trò cụ thể như sau:

1.  **Trần Minh Khánh** (Data Engineering / ETL): Cần quyền ghi/đọc BigQuery để thực hiện tải dữ liệu.
2.  **Nguyễn Đặng Quốc Anh** (DWH / ML): Cần quyền tạo bảng, ghi/đọc dữ liệu để thiết lập Schema và chạy mô hình ML.
3.  **Đỗ Kiến Hưng** (BI / ETL): Cần quyền đọc dữ liệu để kết nối Looker Studio và tạo báo cáo.
4.  **Phạm Minh Quân** (ML / BI): Cần quyền đọc/ghi dữ liệu cho mô hình ML và Looker Studio.

---

## 3. Hướng dẫn Thiết lập Từng bước (Step-by-Step)

### Bước 1: Khởi tạo Google Cloud Project
1.  Truy cập vào [Google Cloud Console](https://console.cloud.google.com/).
2.  Đăng nhập bằng tài khoản Google cá nhân hoặc tài khoản tổ chức.
3.  Ở góc trên cùng bên trái (bên cạnh logo Google Cloud), nhấp vào menu chọn dự án và chọn **New Project** (Dự án mới).
4.  Nhập thông tin dự án:
    *   **Project Name** (Tên dự án): `vn-banking-dwh-analytics`
    *   **Project ID**: GCP sẽ tự động tạo ID. Bạn có thể chỉnh sửa nếu muốn có ID dễ nhớ hơn (ví dụ: `vn-banking-dwh-dwh`). Ghi lại ID này để điền vào biến `GCP_PROJECT_ID` trong tệp `.env`.
5.  Nhấp vào **Create** (Tạo) và đợi hệ thống khởi tạo dự án trong vài giây.
6.  Chọn dự án vừa tạo từ thanh chọn dự án để bắt đầu làm việc.

### Bước 2: Kích hoạt BigQuery API
1.  Nhấp vào biểu tượng menu (3 thanh ngang) ở góc trên bên trái, chọn **APIs & Services** (API và Dịch vụ) > **Library** (Thư viện).
2.  Trong thanh tìm kiếm, nhập từ khóa `BigQuery API`.
3.  Chọn kết quả **BigQuery API** từ danh sách tìm kiếm.
4.  Nhấp vào nút **Enable** (Kích hoạt) nếu trạng thái chưa được kích hoạt.

### Bước 3: Tạo Service Account và Xuất Khóa JSON (Giải quyết Task A-03)
Service Account là tài khoản dịch vụ được các tập lệnh Python (ETL và ML) chạy dưới local sử dụng để tương tác tự động với BigQuery mà không cần xác thực thủ công.
1.  Nhấp vào menu chính, di chuyển tới mục **IAM & Admin** > **Service Accounts** (Tài khoản dịch vụ).
2.  Nhấp vào **+ Create Service Account** (Tạo tài khoản dịch vụ) ở thanh công cụ phía trên.
3.  Nhập thông tin chi tiết:
    *   **Service account name**: `bq-pipeline-sa` (hoặc tên tương đương).
    *   **Service account ID**: Hệ thống sẽ tự động điền dựa trên tên.
    *   **Description**: `Service account for automated Python ETL and ML pipelines.`
4.  Nhấp vào **Create and Continue** (Tạo và tiếp tục).
5.  Tại mục **Grant this service account access to project** (Cấp cho tài khoản dịch vụ quyền truy cập vào dự án), lần lượt thêm 2 vai trò (Roles) sau:
    *   **BigQuery Data Editor** (Cho phép đọc, ghi, cập nhật dữ liệu và bảng trong BigQuery).
    *   **BigQuery Job User** (Cho phép khởi chạy các job truy vấn dữ liệu và tác vụ load dữ liệu trong dự án).
6.  Nhấp vào **Continue** (Tiếp tục) rồi chọn **Done** (Hoàn tất).
7.  Trong danh sách Service Accounts, nhấp vào địa chỉ email của tài khoản vừa tạo.
8.  Chuyển sang tab **Keys** (Khóa).
9.  Nhấp vào **Add Key** (Thêm khóa) > **Create new key** (Tạo khóa mới).
10. Chọn định dạng **JSON** và nhấp vào **Create** (Tạo).
11. Trình duyệt sẽ tải xuống tệp khóa định dạng `.json`. Lưu trữ tệp này an toàn trên máy tính cá nhân.
    *   *Lưu ý*: Đổi tên tệp thành tên ngắn gọn (ví dụ: `gcp-key.json`). Đặt tệp này tại thư mục an toàn và thêm đường dẫn tuyệt đối của nó vào biến `GOOGLE_APPLICATION_CREDENTIALS` trong tệp `.env`. Không bao giờ đẩy tệp này lên GitHub.
12. Chia sẻ tệp JSON key này một cách an toàn (qua kênh bảo mật nội bộ) cho 3 thành viên còn lại để họ hoàn thành **A-04**.

### Bước 4: Tạo BigQuery Dataset (Giải quyết Task B-01)
1.  Nhấp vào menu chính, di chuyển tới mục **BigQuery** > **BigQuery Studio**.
2.  Trong ngăn điều hướng bên trái (Explorer), tìm tên dự án của bạn (ví dụ: `vn-banking-dwh-analytics`). Nhấp vào biểu tượng 3 chấm bên cạnh tên dự án và chọn **Create dataset** (Tạo tập dữ liệu).
3.  Điền các tham số cấu hình:
    *   **Dataset ID**: Nhập `financial_dwh` (Phải khớp chính xác với biến `BQ_DATASET_ID` cấu hình trong tệp `.env`).
    *   **Data location** (Vị trí dữ liệu): Chọn vùng địa lý phù hợp, khuyến nghị chọn vùng có độ trễ thấp như **asia-southeast1 (Singapore)** hoặc đa vùng **US (United States)**. Hãy thống nhất vùng này cho toàn bộ thành viên.
    *   **Default table expiration**: Giữ nguyên mặc định (Never) để dữ liệu không tự động bị xóa.
    *   **Encryption**: Chọn **Google-managed encryption key** (Khóa mã hóa do Google quản lý).
4.  Nhấp vào **Create Dataset** (Tạo tập dữ liệu) để hoàn thành.

### Bước 5: Thêm 4 Thành viên vào Dự án và Phân quyền IAM (Giải quyết Task D-01)
Để các thành viên có thể truy cập dự án GCP, xem cấu trúc dữ liệu hoặc liên kết tài khoản Google của họ với Looker Studio thông qua BigQuery Native Connector, họ cần được cấp quyền cụ thể trên dự án.
1.  Nhấp vào menu chính, chọn **IAM & Admin** > **IAM**.
2.  Nhấp vào nút **+ Grant Access** (Cấp quyền truy cập) ở đầu trang.
3.  Tại ô **New principals** (Thành viên mới), nhập địa chỉ email Google của 4 thành viên trong nhóm.
4.  Tại mục **Assign roles** (Gán vai trò), cấp các vai trò sau cho tài khoản cá nhân của họ:
    *   **BigQuery User** (Cấp ở mức dự án): Vai trò này cho phép thành viên chạy các tác vụ truy vấn (jobs) trên dự án và sử dụng tài nguyên tính toán của dự án để chạy câu lệnh SQL. Đây là quyền bắt buộc để kết nối Looker Studio.
    *   **BigQuery Data Viewer** (Cấp ở mức dự án hoặc mức dataset `financial_dwh`): Vai trò này cho phép thành viên xem cấu trúc bảng và đọc dữ liệu từ các bảng trong dataset mà không có quyền thay đổi dữ liệu hay xóa bảng. Quyền này tối ưu cho việc phân tích và hiển thị Dashboard.
    *   *(Tùy chọn cho nhà phát triển kho dữ liệu - Nguyễn Đặng Quốc Anh)*: Nếu thành viên cần quyền tạo, chỉnh sửa bảng trực tiếp thông qua console hoặc script mà không dùng service account, có thể bổ sung vai trò **BigQuery Data Editor** trên dataset `financial_dwh`.
5.  Nhấp vào **Save** (Lưu) để hoàn thành việc phân quyền.

---

## 4. Xác minh Cấu hình và Sử dụng

Sau khi hoàn tất cài đặt, hướng dẫn các thành viên thực hiện các bước kiểm tra sau để xác minh:

1.  **Kiểm tra xác thực cục bộ (Local Credentials):**
    Lệnh này được chạy dưới **Terminal trên máy tính cá nhân (local)** của bạn. Nếu máy macOS của bạn chưa cài đặt bộ công cụ `gcloud` CLI (Google Cloud SDK), lệnh `gcloud` sẽ báo lỗi `command not found`.

    Bạn có hai phương án để xác minh:

    *   **Phương án A: Sử dụng Python (Khuyên dùng - Không cần cài gcloud CLI)**
        Vì tất cả thành viên đã cài đặt các thư viện trong `requirements.txt` (ở Task A-02), bạn có thể chạy một đoạn mã Python ngắn để kiểm tra kết nối tới BigQuery. Tạo một tệp nháp `test_bq.py` tại thư mục gốc của dự án với nội dung sau:
        ```python
        import os
        from google.cloud import bigquery

        # Kiểm tra biến môi trường
        print("GOOGLE_APPLICATION_CREDENTIALS:", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

        try:
            client = bigquery.Client()
            datasets = list(client.list_datasets())
            print("Xác thực thành công!")
            print("Các dataset hiện có trong project:")
            for ds in datasets:
                print(f"- {ds.dataset_id}")
        except Exception as e:
            print("Lỗi xác thực hoặc kết nối:", str(e))
        ```
        Chạy tệp này bằng lệnh: `python test_bq.py`. Nếu kết quả in ra "Xác thực thành công!" cùng danh sách các dataset, việc cấu hình đã hoàn tất.

    *   **Phương án B: Cài đặt gcloud CLI trên macOS**
        Nếu muốn chạy lệnh xác thực `gcloud` như trong `tasks.md`, bạn cần cài đặt Google Cloud SDK trên máy Mac của mình:
        1. Sử dụng Homebrew (nếu máy có cài sẵn):
           ```bash
           brew install --cask google-cloud-sdk
           ```
        2. Hoặc tải trực tiếp trình cài đặt dành cho macOS (Apple Silicon hoặc Intel) tại [Google Cloud CLI Install](https://cloud.google.com/sdk/docs/install#mac).
        3. Sau khi cài đặt, khởi tạo bằng lệnh `gcloud init`.
        4. Thiết lập biến môi trường và chạy kiểm tra:
           ```bash
           export GOOGLE_APPLICATION_CREDENTIALS="/đường-dẫn-tới-tệp/gcp-key.json"
           gcloud auth application-default print-access-token
           ```

2.  **Kiểm tra kết nối Looker Studio (Task D-01):**
    *   Thành viên truy cập [Looker Studio](https://lookerstudio.google.com/).
    *   Tạo báo cáo mới, chọn nguồn dữ liệu (Data Source) là **BigQuery**.
    *   Chọn kết nối **My Projects** (Dự án của tôi) > Chọn dự án `vn-banking-dwh-analytics` > Chọn Dataset `financial_dwh`.
    *   Nếu thành viên nhìn thấy danh sách các bảng (sau khi đã chạy tập lệnh tạo bảng ở Task B-02 và B-03), việc phân quyền IAM đã hoạt động chính xác.
