# Báo Cáo Phân Tích Dữ Liệu và Dự Báo (Môi Trường Cục Bộ)

> Ngày tạo: 2026-06-30
> Phục vụ: Kiểm thử kết quả Dashboard trước khi triển khai BigQuery

---

## 1. Kết Quả Dự Báo Cổ Phiếu BIDV (Trang 1 — Market Movement)
- **Giá đóng cửa thực tế phiên cuối (2026-06-26)**: 41.70 nghìn VND
- **Dự báo LSTM phiên kế tiếp (T+1)**: 41.57 nghìn VND
- **Dự báo LSTM phiên thứ 5 (T+5)**: 41.93 nghìn VND
- **Biểu đồ biến động giá thực tế BID & LSTM dự báo**:
![Biểu đồ biến động giá thực tế BID & LSTM dự báo](page1_market_movement.png)

---

## 2. Phân Nhóm Hệ Thống Ngân Hàng (Trang 2 — Bank Profiling)
- **Số lượng ngân hàng phân cụm**:
  - **Cluster 0**: 44 ngân hàng
  - **Cluster 1**: 1 ngân hàng
- **Nhận xét**: Ngân hàng **DAB** (Đông Á Bank) được phân vào **Cluster 1** do các chỉ số tài chính cá biệt (ngoại lai), tách biệt hoàn toàn so với nhóm các ngân hàng còn lại tại Cluster 0.
- **Biểu đồ phân cụm ngân hàng & radar profile**:
![Biểu đồ phân cụm ngân hàng & radar profile](page2_bank_profiling.png)

---

## 3. Cảnh Báo Sớm Rủi Ro Nợ Xấu (Trang 3 — Risk Monitoring)
- **Danh sách ngân hàng bị cảnh báo rủi ro cao (NPL >= 3% dự kiến)**:
  - **PVB**
  - **BVB**
  - **PGB**
- **Đặc trưng CAMELS ảnh hưởng mạnh nhất đến rủi ro tín dụng**: `llp_ratio` (Độ quan trọng cao nhất).
- **Biểu đồ rủi ro nợ xấu & feature importance**:
![Biểu đồ rủi ro nợ xấu & feature importance](page3_risk_monitoring.png)

---

*Lưu ý: Báo cáo này được tự động sinh bằng code từ dữ liệu local-first trong `data/processed/` và `data/data_ml/output/`.*
