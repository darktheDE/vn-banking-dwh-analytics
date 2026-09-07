# SPEC-03: Code Hygiene and Testing Standards Specification

## 1. Mục đích
Quy chuẩn hóa cấu trúc mã nguồn, quy tắc logging, và phân tầng kiểm thử tự động nhằm đảm bảo tính ổn định, dễ bảo trì và khả năng tích hợp CI/CD cho dự án.

## 2. Tiêu chuẩn Code Hygiene
1. **Tuyệt đối cấm dùng `print()` trong mã nguồn sản xuất (`src/`):**
   - Mọi log ghi nhận trạng thái, lỗi, cảnh báo bắt buộc phải sử dụng `src.utils.logger.get_logger(__name__)`.
   - Mức độ log:
     - `logger.info()`: Thông báo tiến trình hoàn thành các giai đoạn (ETL, load bảng, epoch huấn luyện).
     - `logger.warning()`: Cảnh báo giá trị dữ liệu bất thường hoặc kích hoạt fallback.
     - `logger.error()`: Báo lỗi thất bại có stack trace.
2. **Không gây side-effects ở cấp độ Module Root:**
   - Cấm đặt các thao tác ghi đĩa (`os.makedirs`), gọi API (`vnstock`), hoặc ghi log banner bên ngoài khối hàm hoặc ngoài `if __name__ == '__main__':`.
   - Việc `import` một module chỉ nhằm mục đích tải định nghĩa hàm/lớp, không được phép làm thay đổi trạng thái hệ thống.

## 3. Phân tầng Kiểm thử Tự động (Modular Test Suite)
Do các thư viện Deep Learning (`tensorflow`) và Trực quan hóa (`streamlit`) có dung lượng lớn và phụ thuộc chặt vào phiên bản Python, hệ thống test được chia thành 3 tầng độc lập:

1. **Tầng 1 - Core & ETL Test (`--tier etl`):**
   - Kiểm tra import và cú pháp của các module nền tảng (`src.utils.*`) và đường ống trích xuất dữ liệu (`src.etl.*`).
   - Phải chạy được ngay trên môi trường Python tối thiểu chỉ với `pandas`, `openpyxl`, `google-cloud-bigquery`.
2. **Tầng 2 - ML Test (`--tier ml`):**
   - Kiểm tra các module huấn luyện và suy luận (`src.models.*`).
   - Yêu cầu môi trường có `scikit-learn`, `statsmodels`, `tensorflow`.
3. **Tầng 3 - Presentation Test (`--tier dashboard`):**
   - Kiểm tra `src.dashboard.app` và các script audit BI.
