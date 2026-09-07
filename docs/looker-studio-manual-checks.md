# Looker Studio — Checklist Kiểm Tra Thủ Công Hàng Quý

> Tài liệu này giúp người dùng (PO, BA, data steward) tự kiểm tra dashboard Looker Studio của dự án VN Banking DWH Analytics mỗi quý (3 tháng một lần), nhằm đảm bảo dữ liệu, scorecard, biểu đồ và kết nối BigQuery vẫn hoạt động đúng.
>
> **Đối tượng**: người không code, dùng Chrome trên desktop.
> **Trình duyệt khuyến nghị**: Chrome bản mới nhất, đã đăng nhập tài khoản Google có quyền xem Looker Studio.

---

## Quy trình chung

1. Mở Chrome, truy cập link dashboard Looker Studio được share trong team channel.
2. Đợi dashboard load hoàn toàn.
3. Đi theo thứ tự 15 mục kiểm tra dưới đây, tick `[x]` khi đạt, ghi chú `[!]` nếu có vấn đề.
4. Cuối phiên, copy bảng kết quả vào issue tracker hoặc email báo cáo (xem mẫu ở cuối file).

---

## CH-01 — Dashboard load nhanh trong 10 giây

- **Mục đích**: Đảm bảo trang không bị chậm do cache hết hạn hoặc query quá tải.
- **Bước làm trong Chrome**:
  1. Mở dashboard bằng tab mới (Ctrl + T).
  2. Nhìn góc phải-trên: Looker Studio hiện spinner trong lúc load.
  3. Dùng đồng hồ bấm giờ từ lúc nhấn Enter đến khi thấy đủ tất cả biểu đồ.
- **Expected value**: Tổng thời gian load ≤ 10 giây với kết nối Internet bình thường.
- **Nếu sai thì sao**:
  - Kiểm tra DevTools → Network, xem request BigQuery nào đang chậm.
  - Liên hệ data engineer để xem lại schedule refresh hoặc partition của bảng nguồn.

---

## CH-02 — Scorecard "Tổng số ngân hàng" = 45

- **Mục đích**: Xác nhận dimension `dim_bank` đầy đủ, không bị thiếu hoặc trùng sau khi SCD Type 2 chạy.
- **Bước làm trong Chrome**:
  1. Tìm scorecard tiêu đề "Tổng số ngân hàng" trên trang Overview.
  2. Đọc con số hiển thị lớn nhất.
- **Expected value**: Đúng bằng **45**.
- **Nếu sai thì sao**:
  - Nếu nhỏ hơn 45 → thiếu ngân hàng mới, chạy lại `python -m src.etl.populate_dim_bank`.
  - Nếu lớn hơn 45 → có dòng trùng surrogate key, kiểm tra unique constraint.

---

## CH-03 — Scorecard "Số lượng ngân hàng cảnh báo đỏ" khớp BigQuery

- **Mục đích**: Đảm bảo ngưỡng Random Forest risk (`npl_ratio >= 0.03`) đang áp dụng đúng tại Looker Studio.
- **Bước làm trong Chrome**:
  1. Đọc scorecard "Số lượng ngân hàng cảnh báo đỏ" trên trang Risk.
  2. Mở BigQuery console (tab mới), chạy:
     ```sql
     SELECT COUNT(*) AS so_ngan_hang_do
     FROM `project.vn_banking_dwh.mart_bank_risk_predictions`
     WHERE is_high_risk = TRUE
       AND prediction_date = (SELECT MAX(prediction_date) FROM ...);
     ```
- **Expected value**: Con số trên Looker Studio bằng con số BigQuery trả về. Ví dụ tham chiếu: **145**.
- **Nếu sai thì sao**:
  - Kiểm tra filter date range trên Looker Studio có khớp với `prediction_date` không.
  - Nếu lệch > 0, refresh data source trong Looker Studio (Resource → manage added data sources → Refresh).

---

## CH-04 — Scorecard "Tỷ lệ nợ xấu trung bình" nằm trong khoảng 0.02 – 0.05

- **Mục đích**: Xác nhận aggregation NPL đúng và median imputation không làm sai lệch giá trị.
- **Bước làm trong Chrome**:
  1. Đọc scorecard "Tỷ lệ nợ xấu trung bình".
  2. Giá trị hiển thị dưới dạng phần trăm, ví dụ `3.45%`.
- **Expected value**: Tỷ lệ nằm trong khoảng **2% – 5%** (0.02 – 0.05).
- **Nếu sai thì sao**:
  - Nếu > 5% → kiểm tra outlier, có thể TNB hoặc một bank lỗi thời bị lọt.
  - Nếu < 2% → median imputation đang thay quá nhiều giá trị, xem lại `feature_engineering_bank.py`.

---

## CH-05 — Kết nối BigQuery data source còn hoạt động

- **Mục đích**: Đảm bảo report không bị mất quyền truy cập BigQuery (token hết hạn, dataset bị xóa, đổi tên project).
- **Bước làm trong Chrome**:
  1. Vào menu **Resource** (góc phải-trên khi ở chế độ Edit).
  2. Chọn **Manage added data sources**.
  3. Xem cột "Last refreshed" và "Status".
- **Expected value**: Mỗi data source hiện trạng thái "Connected" và thời gian refresh ≤ 24 giờ.
- **Nếu sai thì sao**:
  - Nếu "Disconnected" → bấm "Reconnect" rồi cấp quyền lại.
  - Nếu dataset lỗi thời (renamed/deleted), liên hệ data engineer cập nhật lại tên bảng.

---

## CH-06 — Date range filter cập nhật tất cả biểu đồ

- **Mục đích**: Đảm bảo bộ lọc ngày áp dụng đồng bộ cho toàn trang.
- **Bước làm trong Chrome**:
  1. Tìm date range control ở đầu trang.
  2. Đổi khoảng thành "Last 12 months" → quan sát tất cả chart.
  3. Đổi thành "Custom range: 2020-01-01 → 2020-12-31".
- **Expected value**: Mọi chart (line, bar, pie, scorecard) đều co lại/giãn ra theo khoảng ngày mới. Không chart nào báo "No data" một cách bất thường.
- **Nếu sai thì sao**:
  - Có chart chỉ dùng một date dimension riêng (không phải filter chung). Sửa bằng cách đặt cùng field `report_date` cho filter.

---

## CH-07 — Dropdown chọn mã cổ phiếu (BID/TCB/VCB/CTG)

- **Mục đích**: Kiểm tra parameter control cho trang Stock Forecast.
- **Bước làm trong Chrome**:
  1. Sang trang "Stock Forecast".
  2. Mở dropdown "Chọn mã cổ phiếu".
  3. Tick đủ 4 mã: BID, TCB, VCB, CTG.
- **Expected value**: Dropdown liệt kê đủ 4 mã, chọn mã nào thì biểu đồ forecast đổi theo mã đó.
- **Nếu sai thì sao**:
  - Thiếu mã → kiểm tra `dim_stock` có 4 ticker đó chưa (chạy `populate_dim_stock`).
  - Dropdown không phản hồi → parameter bị ngắt khỏi chart, kéo lại dây parameter trong Edit mode.

---

## CH-08 — Scatter plot hiển thị 3 cụm (clusters) tách biệt

- **Mục đích**: Xác nhận K-Means đã gán nhãn 3 cluster đúng và PCA giữ được phân tách trên 2D.
- **Bước làm trong Chrome**:
  1. Sang trang "Bank Clustering".
  2. Nhìn scatter plot PCA1 vs PCA2.
- **Expected value**: Có **3 nhóm màu** rõ ràng, các điểm trong cùng nhóm gần nhau, khoảng cách giữa các nhóm tách biệt.
- **Nếu sai thì sao**:
  - Các điểm trộn lẫn → chạy lại `python -m src.models.train_kmeans` với random_state cố định.
  - Thiếu cluster → kiểm tra bảng `mart_bank_clusters` có đủ 3 cluster label không.

---

## CH-09 — CIR trung bình mỗi cluster < 0.7

- **Mục đích**: Kiểm tra chỉ số Cost-to-Income Ratio (CIR) hợp lý theo từng cụm ngân hàng.
- **Bước làm trong Chrome**:
  1. Tại trang "Bank Clustering", xem bảng "Cluster summary".
  2. Tìm cột **Avg CIR** của mỗi cluster.
- **Expected value**: Cả 3 cluster đều có Avg CIR **< 0.7** (70%).
- **Nếu sai thì sao**:
  - Cluster nào > 0.7 → outlier ngân hàng chi phí cao, mở BigQuery kiểm tra `cost_to_income_ratio` các bank trong cụm đó.

---

## CH-10 — TNB 2008 NPL < 6% (sau khi sửa data quality)

- **Mục đích**: Xác nhận bản vá dữ liệu TNB năm 2008 đã được áp dụng đến Looker Studio.
- **Bước làm trong Chrome**:
  1. Trang "Bank Trajectory", dùng filter chọn ngân hàng **TNB**, năm **2008**.
  2. Đọc chỉ số NPL ratio.
- **Expected value**: NPL < **6%** (kết quả đúng sau fix).
- **Nếu sai thì sao**:
  - Nếu vẫn ≥ 6%, refresh data source của Looker Studio rồi kiểm tra `fact_bank_performance` đã cập nhật giá trị chưa.

---

## CH-11 — Pie chart phân bố bank_category

- **Mục đích**: Đảm bảo phân loại nhóm ngân hàng (state-owned, private, foreign...) phản ánh đúng dimension.
- **Bước làm trong Chrome**:
  1. Trang "Bank Overview", nhìn pie chart "Phân bố bank_category".
  2. Đếm số miếng và so với BigQuery:
     ```sql
     SELECT bank_category, COUNT(*) AS n
     FROM `project.vn_banking_dwh.dim_bank`
     GROUP BY bank_category;
     ```
- **Expected value**: Tổng số miếng bằng tổng số ngân hàng đang active (≤ 45), không có miếng "Unknown".
- **Nếu sai thì sao**:
  - Có miếng "Unknown" → chạy lại `populate_dim_bank` để gắn category.
  - Sai số lượng → kiểm tra SCD Type 2 đang lọc đúng bản ghi hiện tại.

---

## CH-12 — Line chart quỹ đạo NPL hiển thị 2003 – 2022

- **Mục đích**: Xác nhận đủ dải năm lịch sử, không bị mất gap do filter mặc định.
- **Bước làm trong Chrome**:
  1. Trang "Bank Trajectory", line chart "NPL ratio over time".
  2. Đặt filter ngày về "All time".
- **Expected value**: Trục X chạy từ **2003 đến 2022**, đủ ~20 năm.
- **Nếu sai thì sao**:
  - Thiếu năm đầu/đuôi → kiểm tra `dim_date` đã populate đủ chưa, chạy `populate_dim_date` cho năm còn thiếu.

---

## CH-13 — Feature importance bar chart hiển thị top-10

- **Mục đích**: Đảm bảo bảng importance từ Random Forest được join đúng vào Looker.
- **Bước làm trong Chrome**:
  1. Trang "Risk Model", bar chart "Feature importance".
  2. Quan sát trục Y: phải có đúng **10 feature** xếp theo importance giảm dần.
- **Expected value**: 10 thanh bar, thanh trên cùng là feature quan trọng nhất (thường `npl_ratio_lag1` hoặc `roe`).
- **Nếu sai thì sao**:
  - Thiếu thanh → Looker bị giới hạn row count, tăng "Row limit" lên ≥ 10 trong Edit.
  - Sai thứ tự → kiểm tra bảng `mart_feature_importance` đã sort desc chưa.

---

## CH-14 — Bảng Granger causality hiển thị p-values

- **Mục đích**: Đảm bảo kết quả kiểm định Granger từ notebook EDA đã được publish lên BigQuery.
- **Bước làm trong Chrome**:
  1. Trang "Causality Analysis".
  2. Mở bảng "Granger causality results".
- **Expected value**: Bảng có các cột: `cause`, `effect`, `lag`, `p_value`, `significant`. Ít nhất 1 dòng có `p_value < 0.05` đánh dấu significant.
- **Nếu sai thì sao**:
  - Bảng trống → chưa export từ notebook, chạy lại cell "Export Granger to BigQuery" trong `notebooks/eda_banks.ipynb`.
  - Sai tên cột → cập nhật schema trong Looker Studio (Edit → Resource → manage data sources).

---

## CH-15 — "Last refresh" timestamp khớp với lịch trình

- **Mục đích**: Đảm bảo schedule refresh BigQuery → Looker Studio vẫn chạy đúng giờ.
- **Bước làm trong Chrome**:
  1. Góc phải-trên dashboard, tìm dòng "Last refresh" hoặc icon đồng hồ.
  2. Ghi lại thời gian hiển thị.
- **Expected value**: Thời gian refresh ≤ 24 giờ trước thời điểm kiểm tra, đúng mốc đã lên lịch (ví dụ 02:00 sáng theo giờ VN).
- **Nếu sai thì sao**:
  - Quá cũ → kiểm tra scheduled refresh trong Looker Studio (File → Schedule).
  - Refresh chạy nhưng vẫn cũ → kiểm tra upstream ETL có lỗi không (xem Cloud Logging).

---

## Cách chạy checks tự động

Với 15 mục trên, một số có thể tự động hoá bằng script Python truy vấn trực tiếp BigQuery và so với giá trị kỳ vọng. Script tham khảo:

- `scripts/verify_looker_scorecards.py` — so sánh giá trị từ BigQuery với "expected value" cho CH-02, CH-03, CH-04, CH-10, CH-12. Các mục liên quan đến UI (CH-06, CH-07, CH-08, CH-11, CH-13, CH-15) vẫn cần kiểm tra thủ công trên Chrome.

Chạy script:

```bash
python scripts/verify_looker_scorecards.py
```

Exit code 0 = tất cả pass; exit code khác 0 = có mục fail, xem log để biết chi tiết.

## Tần suất chạy

- **Hàng quý**: chạy đủ 15 mục vào tuần đầu của tháng 1, 4, 7, 10. Người phụ trách: data steward hoặc BA on-call.
- **Sau bất kỳ thay đổi ETL nào**: chạy lại toàn bộ 15 mục, đặc biệt CH-03, CH-04, CH-10, CH-12.
- **Sau khi đổi schema BigQuery**: chạy thêm CH-05, CH-14 và refresh data source thủ công.

Lưu kết quả mỗi lần kiểm tra vào thư mục `docs/looker-qa-log/YYYY-Qn.md` để theo dõi xu hướng.

## Báo cáo issues

Khi phát hiện mục nào fail, copy mẫu email dưới đây, điền thông tin và gửi vào nhóm chat `vn-banking-data` (gmail) + tag `@data-engineer`.

```
Tiêu đề: [Looker QA] <Mã check> fail — <mô tả ngắn>

Chào team,

Trong lần kiểm tra dashboard Looker Studio ngày <DD/MM/YYYY>, mục <CH-XX> bị fail.

- Expected: <giá trị kỳ vọng>
- Actual: <giá trị thực tế quan sát được>
- Reproduce: <các bước tái hiện trong Chrome>
- Screenshot: <đính kèm file ảnh>
- Tác động nghi ngờ: <chart nào / quyết định nào bị ảnh hưởng>

Mình nghi vấn đề liên quan đến <module / bảng nào>. Nhờ team xem xét.
Cảm ơn!
<Người báo cáo>
```

Sau khi fix, owner issue comment lại "Resolved by PR #<num>" và đóng ticket.

---

*Tài liệu này là một phần của bộ [docs/](../) theo quy định trong [DEVELOPMENT.md](../DEVELOPMENT.md). Mọi thay đổi checklist cần cập nhật đồng bộ `scripts/verify_looker_scorecards.py`.*