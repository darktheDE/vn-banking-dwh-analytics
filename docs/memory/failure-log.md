# Bảng Nhật Ký Lỗi & Cơ Chế Phòng Chống (Failure Log & Prevention)

Tài liệu này lưu giữ toàn bộ các lỗi thực tế được phát hiện qua đợt đại kiểm tra v1 (11 lỗi B-01 đến B-11 và 6 lỗi Looker L-01 đến L-06), nguyên nhân cốt lõi và bài học kinh nghiệm để không bao giờ lặp lại trong các phiên làm việc của AI và kỹ sư.

---

## 1. Danh Mục Lỗi Hệ Thống & ETL (B-* Issues)

| Mã lỗi | Mô tả sự cố | Mức độ | Nguyên nhân gốc rễ | Cơ chế phòng chống vĩnh viễn |
|---|---|---|---|---|
| **B-01** | BigQuery duplicate rows (x2 số dòng trên 6/10 bảng) | 🔴 Critical | Fallback `WRITE_APPEND` khi chạy BigQuery không có billing. | Bắt buộc dùng `WRITE_TRUNCATE` khi fallback (ADR-0001, SPEC-01). |
| **B-02** | Docs claim sai phạm vi LSTM | 🟠 High | Docs cũ ghi LSTM chỉ chạy BID trong khi code chạy cả 4 mã. | Đồng bộ hóa `AGENTS.md` và `README.md` theo thực tế code. |
| **B-03** | Docs claim "7 bảng" thay vì "10 bảng" | 🟠 High | Docs không tính 3 bảng kết quả ML (`fact_model_predictions`, `bank_risk_predictions`, `bank_cluster_assignments`). | Thống nhất định nghĩa DWH gồm 5 Dim + 2 Fact + 3 ML Output = 10 bảng. |
| **B-04** | `HUONG_DAN_DU_AN.md` chứa lệnh pytest không tồn tại | 🟡 Medium | Copy tài liệu mẫu chưa qua kiểm chứng môi trường. | Viết smoke test thật trong `tests/` và chuẩn hóa lệnh chạy. |
| **B-05** | 4 module ETL cũ bị bỏ rơi | 🟡 Medium | Sau khi gộp vào `consolidate_stock_metrics`, các module cũ không được dọn dẹp. | Đánh dấu `@deprecated` rõ ràng trong docstrings (Phase R4). |
| **B-06** | `load_price_history` song song tồn tại với `consolidate_stock_metrics` | 🟡 Medium | Chưa xóa code cũ sau refactor gộp bảng fact. | Đánh dấu deprecated và loại bỏ khỏi pipeline production. |
| **B-07** | `load_price_history` đọc file Excel thô | 🟠 High | Hardcode file Excel `BID_price_history.xlsx`. | Chỉ đọc từ `data/processed/` thông qua `Config`. |
| **B-08** | Dữ liệu CAMELS nợ xấu out-of-range (28 dòng) | 🔴 Critical | Mẫu số dư nợ $\le 0$ hoặc lẫn lộn giữa % và thập phân. | Bổ sung bounds checking và ép tỷ lệ $[0, 1]$ (ADR-0002). |
| **B-09** | `extract_data.py` dùng `print()` thay vì `logger` | 🟡 Medium | Vi phạm quy tắc chuẩn hóa logging của `AGENTS.md`. | Thay thế 100% `print()` bằng `logger` của module (Phase R1). |
| **B-10** | `extract_data.py` hardcode `DATA_DIR` | 🟡 Medium | Dùng `os.path.dirname(__file__)` nối chuỗi tĩnh. | Đọc đường dẫn từ `Config` thông qua biến môi trường (Phase R1). |
| **B-11** | Looker Studio không audit tự động được | 🟡 Medium | Rào cản xác thực OAuth và giao diện Cloud. | Viết script đối soát `scripts/verify_looker_scorecards.py`. |

---

## 2. Danh Mục Lỗi Dashboard Looker Studio (L-* Issues)

| Mã lỗi | Mô tả sự cố | Biểu hiện | Giải pháp |
|---|---|---|---|
| **L-01** | Thiếu dashboard Market Movement | URL Looker chỉ có 2 trang | Bổ sung trang Market Movement theo `docs/dashboard-spec.md`. |
| **L-02** | CIR trung bình cụm hiển thị cao bất thường | CIR có ca đạt $> 0.70$ | Lọc bỏ các giá trị mẫu số âm của CIR. |
| **L-03** | TNB 2008 nợ xấu vọt đỉnh $11\%$ | Outlier trực quan trên biểu đồ đường | Xử lý triệt để trong tầng ETL CAMELS (ADR-0002). |
| **L-04** | Nhầm lẫn giữa Scorecard và Table filter | Số lượng High Risk hiển thị lệch | Cập nhật filter mặc định trên Looker Studio. |
| **L-05** | PCA Scatter plot thiếu chú thích tâm cụm | 3 cụm chưa làm nổi bật tâm cụm | Thêm bảng tọa độ tâm cụm vào báo cáo. |
| **L-06** | Trục thời gian không liên tục | Bỏ qua các năm nghỉ sáp nhập | Sử dụng trường `year` từ `dim_date` làm trục chuẩn. |
