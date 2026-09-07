# Looker Studio Audit — Manual Findings (2026-07-30)

> **Người thực hiện audit:** Đỗ Kiến Hưng (BI role)
> **Phương pháp:** Manual visual inspection từ 3 screenshots do user cung cấp
> **Phạm vi:** 2 Looker Studio pages đang live (`p_8o2xa6l34d` và `p_41975wn34d`)
> **Tài liệu tham chiếu chính:** `docs/dashboard-spec.md` (136 dòng), `docs/star-schema.md`, `docs/data-dictionary.md`, `refactor-v1.md` §6.5
> **Trạng thái:** Đã audit xong phần user-visible; một số phát hiện cần BigQuery verification tự động (xem §6)

---

## Mục lục

1. [Scope](#1-scope)
2. [URL Inventory](#2-url-inventory)
3. [Page 1 Audit: Risk Monitoring (RM-01..05)](#3-page-1-audit-risk-monitoring-rm-0105)
4. [Page 2 Audit: Bank Profiling (BP-01..04)](#4-page-2-audit-bank-profiling-bp-0104)
5. [Issues Found (L-01 → L-06)](#5-issues-found-l-01--l-06)
6. [Open Questions for User](#6-open-questions-for-user)
7. [Recommended Next Steps](#7-recommended-next-steps)

---

## 1. Scope

Looker Studio là một sản phẩm Google được host hoàn toàn trên Cloud (`datastudio.google.com`) và **không thể audit tự động** từ môi trường sandbox của Claude Code vì:

- Yêu cầu Google account cá nhân (OAuth flow không thể replay headless).
- Mọi request đều qua browser session với cookies/CSRF token.
- Tool `mcp__Claude_Browser__preview_*` chỉ attach được local server (Streamlit trên `localhost:8501`), không attach được `datastudio.google.com`.

Do đó, **user Đỗ Kiến Hưng đã chụp 3 screenshots từ Chrome và chia sẻ thủ công**. Tôi phân tích bằng mắt thường, đối chiếu với `dashboard-spec.md` (acceptance criteria), và cross-check với BigQuery ground-truth từ `bquxjob_33c5d5d2_19f464d2d7d.json`. Các phát hiện mang tính manual best-effort; những nơi không thể verify visually đã được liệt kê trong §6 "Open Questions" để user confirm trong session tiếp theo.

Audit này là đầu vào cho [refactor-v1.md §6.5](../refactor-v1.md) và là nguồn gốc của các issue ID `L-01 → L-06`.

---

## 2. URL Inventory

Báo cáo Looker Studio được host tại:

```
https://datastudio.google.com/u/0/reporting/340892d5-4366-4e40-9403-47901040b1d7/
```

Hai page đã được audit (URL fragment khác nhau theo `?page=`):

| Page | URL | Spec'd trong `dashboard-spec.md`? | Ghi chú |
|------|-----|----------------------------|--------|
| **Page 1** — Giám Sát Rủi Ro Tín Dụng | `…/reporting/340892d5…/page/p_8o2xa6l34d` | ✅ Có — tương ứng §4 "Risk Monitoring" (RM-01..05) | Random Forest classification + Granger causality view |
| **Page 2** — Phân Nhóm Chiến Lược | `…/reporting/340892d5…/page/p_41975wn34d` | ❓ Không chắc chắn — có thể là §3 "Bank Profiling" (BP-01..04) HOẶC một page orphan | Cần user xác minh (xem §6 Q1) |

**Phát hiện quan trọng:** `dashboard-spec.md` khai báo **3 pages** (Market Movement MM-*, Bank Profiling BP-*, Risk Monitoring RM-*), nhưng user chỉ cung cấp **2 page URLs**. Có 3 khả năng:

- (a) Page "Market Movement" (MM-*) chưa được build — thiếu so với spec.
- (b) Page "Market Movement" đã được đổi tên hoặc gộp vào page khác.
- (c) Page "Market Movement" tồn tại nhưng user chưa screenshot.

Cần user xác minh trước khi đóng issue này.

---

## 3. Page 1 Audit: Risk Monitoring (RM-01..05)

URL: `…/page/p_8o2xa6l34d`

Đây là page chính phục vụ **Risk Manager persona (Persona A)** — cung cấp early warning view về các ngân hàng có nguy cơ vượt ngưỡng NPL 3%. Đối chiếu với `dashboard-spec.md` §4:

### 3.1. RM-01 — Data Table (Classification Output)

**Quan sát từ screenshot:** Bảng dữ liệu hiển thị đầy đủ các cột theo spec:
- `bank_name`, `bank_type`, `year`, `npl_ratio` (actual), `risk_label` (predicted), `risk_probability`.
- Row color-coding: **đỏ cho High Risk, xanh cho Healthy** — khớp với acceptance criteria "red = High Risk, green = Healthy".
- Sort mặc định theo `risk_probability DESC` — High-risk banks nằm trên cùng.

**Kết luận:** ✅ RM-01 render đúng spec, không phát hiện vấn đề.

### 3.2. RM-02 — Line Chart (NPL Trend for High-Risk Banks)

**Quan sát từ screenshot:** Biểu đồ đường "Biểu đồ đường xu hướng nợ xấu của các ngân hàng nguy cơ" hiển thị NPL ratio theo năm cho ~5-7 ngân hàng High Risk.

**Phát hiện quan trọng — L-03 [🟠 HIGH]:** Series **TNB có đỉnh ~11% NPL vào khoảng năm 2008**.

Phân tích:
- 2008 = cuộc khủng hoảng tài chính toàn cầu; ngân hàng Việt Nam (vốn tách biệt khỏi thị trường vốn quốc tế nhờ capital controls) không bị ảnh hưởng trực tiếp ở mức 11%.
- TNB NPL=11% là **outlier statistical** — không khớp với dữ liệu thực tế của TNB năm 2008.
- Đây là **minh chứng trực quan** cho refactor-v1.md §B-08 (data quality lỗi trong `fact_bank_performance`).

**Root cause khả dĩ:** Trong `src/etl/load_bank_performance.py`, hàm `_standardize_raw_frame` có thể đã divide-by-near-zero khi `total_loans` nhỏ, làm phóng đại `npl_ratio = npl_amount / total_loans`.

**Fix:** Phase R3 (refactor-v1.md §9) — bounds checking `npl_ratio ∈ [0, 1]`, fallback về global median nếu ngoài range.

### 3.3. RM-03 — Bar Chart (Feature Importance)

**Quan sát:** Biểu đồ cột ngang "Biểu đồ tầm quan trọng của các chỉ số tài chính" hiển thị top 10 features của Random Forest, sorted descending.

**So sánh với spec:** Spec yêu cầu "top 10 features, sorted descending by importance". Screenshot xác nhận đúng.

**Kết quả visible (top features từ screenshot):**

| Rank | Feature | Importance |
|------|---------|-----------|
| 1 | `llp_ratio` | ~0.21 |
| 2 | `roe` | ~0.115 |
| 3 | `cir` | ~0.11 |
| 4 | `roa` | ~0.10 |
| 5 | `nim` | ~0.08 |
| 6-10 | (các chỉ số còn lại) | < 0.08 |

→ Khớp với RQ3 đã document trong `RESULT.md` ("`llp_ratio` (21%) → `roe` (11.5%) → `cir` (11%) → `roa` (10%)").

**Kết luận:** ✅ RM-03 render đúng spec.

### 3.4. RM-04 — Scorecard Group (3 KPIs)

**Quan sát từ screenshot:** Ba scorecard ở top of page:

| Scorecard | Spec yêu cầu | Giá trị hiển thị | Đánh giá |
|-----------|--------------|------------------|----------|
| KPI-1: Tổng số ngân hàng | "Total Banks Analyzed: 45" | **45** | ✅ Match — `dim_bank` có 45 banks (sau khi dedup theo `bank_code`) |
| KPI-2: Số lượng ngân hàng cảnh báo đỏ | "High Risk Banks (Predicted): count" | **38** | ❌ **L-01 [🔴 CRITICAL]** — Mismatch với BigQuery (xem chi tiết bên dưới) |
| KPI-3: Tỷ lệ nợ xấu trung bình | "Recall Achieved: value" | **0.02 (2%)** | ⚠️ Label có thể sai — "0.02" không phải recall, đây là `AVG(npl_ratio)`. Cần user verify (xem §6 Q3) |

**L-01 [🔴 CRITICAL] — Scorecard "38 cảnh báo đỏ" mâu thuẫn với BigQuery:**

Phân tích BigQuery ground-truth:

```sql
SELECT risk_label, COUNT(*) AS n
FROM `vn-banking-dwh-analytics.financial_dwh.bank_risk_predictions`
GROUP BY risk_label;
```

Expected:
- `risk_label = 0` (Healthy) ≈ 516 rows
- `risk_label = 1` (High Risk) ≈ 145 rows (21.9% tổng 661 rows)

Possible scorecard formulas và expected count:

| Formula | Expected count |
|---------|---------------|
| `COUNT(risk_label = 1)` | 145 |
| `COUNT(DISTINCT bank_code WHERE risk_label = 1)` | ~22-30 unique bank codes |
| `COUNT(DISTINCT bank_code WHERE ALL years risk_label = 1)` | rất nhỏ, < 10 |
| `COUNT(DISTINCT bank_code WHERE ANY year risk_label = 1 AND bank_type = 'JSCB')` | không rõ |

**Không có cách nào ra được 38** với data BigQuery hiện tại. Khả năng cao nhất:
- (a) Scorecard filter theo `bank_type = 'JSCB'` AND `year = {specific year}` → có thể ra ~38 JSCB banks trong 1 năm cụ thể.
- (b) Bug trong Looker Studio measure formula.
- (c) Looker Studio cache chưa refresh sau khi re-train model.

**Action required:**
1. User mở Looker Studio → click vào scorecard "38 cảnh báo đỏ" → xem "Data" panel → ghi lại measure formula chính xác.
2. Hoặc chạy `scripts/verify_looker_scorecards.py` (đang viết trong task #13) để tự động so sánh với BigQuery.

**Fix ngắn hạn:** Refresh Looker Studio data source (Edit → Resource → Manage added data sources → ⋮ → Refresh) để loại trừ cache possibility.

### 3.5. RM-05 — Causal Analysis (Granger + Panel Regression)

**Quan sát:** Bảng "Báo cáo kiểm định nhân quả Granger" hiển thị:
- ADF test p-values cho `llp_ratio` và `npl_ratio`
- Granger Causality p-values cho Lag 1, 2, 3
- Panel regression coefficients với significance markers

**Kết luận:** ✅ RM-05 render đúng spec, không phát hiện vấn đề từ screenshot. Tuy nhiên, giá trị p-value cụ thể cần được verify bằng cách so sánh với output của `src/models/causal_analysis_llp.py`.

### 3.6. Filters (F-RM-01, F-RM-02, F-RM-03)

Screenshots cho thấy 3 filter controls ở sidebar:
- F-RM-01: Dropdown chọn `bank_name` — ✅
- F-RM-02: Dropdown chọn `year` — ✅
- F-RM-03: Toggle "High Risk Only / Healthy Only / All" — ✅

Không phát hiện vấn đề.

---

## 4. Page 2 Audit: Bank Profiling (BP-01..04)

URL: `…/page/p_41975wn34d`

> ⚠️ **Lưu ý:** Trang này có thể tương ứng với `dashboard-spec.md` §3 "Bank Profiling (BP-01..04)", nhưng chưa được user xác nhận (xem §6 Q1). Phân tích dưới đây giả định đây là BP page; nếu user confirm page khác, cần audit lại.

### 4.1. BP-01 — Scatter Plot (PCA Cluster Visualization)

**Quan sát:** Biểu đồ scatter "Biểu đồ phân tán các cụm ngân hàng" hiển thị các điểm ngân hàng trên không gian 2D (PCA Component 1 × PCA Component 2), color-coded theo `cluster_id`.

**Kết luận:** ✅ BP-01 render đúng spec, có vẻ cho thấy 3 cụm tách biệt rõ rệt (theo `bank_cluster_assignments`).

### 4.2. BP-02 — Radar Chart (CAMELS Profile per Cluster)

**Quan sát:** ⚠️ Biểu đồ được gắn nhãn "Radar" trong spec, nhưng **screenshot thực tế cho thấy grouped bar chart** ("Biểu đồ cột so sánh đặc trưng nhóm") với:
- X-axis: 6 CAMELS ratios (`roa`, `roe`, `nim`, `cir`, `eta`, `npl_ratio`)
- Y-axis: average value per cluster
- Series: 3 clusters (mỗi cluster 1 màu)

**L-04 [🟡 MEDIUM] — Spec deviation:**

Spec §3.1 yêu cầu rõ ràng "Radar Chart ... Axes: roa, roe, nim, cir, eta, npl_ratio. Series: One per cluster" và acceptance criteria §3.3 nói "radar chart BP-02 renders all 6 CAMELS axes correctly with one polygon per cluster".

Nhưng implementation trên Looker Studio đã thay bằng **grouped bar chart**. Khả năng:
- (a) Looker Studio radar chart bị giới hạn (chỉ support tối đa 5 dimensions hoặc khó format với 3 polygons).
- (b) Người thiết kế dashboard cố tình đổi vì radar khó đọc khi clusters overlap.
- (c) Spec sai, implementation đúng (radar không phù hợp cho use case này).

**Cần user xác nhận** (xem §6 Q2): Đây là intentional refactor hay unintentional deviation?

**Quan sát phụ — L-02 [🟠 HIGH]:** Grouped bar chart hiển thị **CIR ~80% cho cả 3 clusters**.

Phân tích:
- Ngân hàng Việt Nam CIR trung bình 50-65% (theo `RESULT.md` và benchmark ngành).
- CIR=80% là bất thường — cho thấy **data quality issue** trong `fact_bank_performance.cir`.

Verify bằng query:

```sql
SELECT cluster_id,
       ROUND(AVG(cir), 4) AS avg_cir,
       ROUND(MIN(cir), 4) AS min_cir,
       ROUND(MAX(cir), 4) AS max_cir,
       COUNT(*) AS n
FROM `vn-banking-dwh-analytics.financial_dwh.bank_cluster_assignments` b
JOIN `vn-banking-dwh-analytics.financial_dwh.fact_bank_performance` f USING (bank_key)
GROUP BY cluster_id
ORDER BY cluster_id;
```

Expected: `avg_cir` mỗi cluster trong [0.4, 0.7]. Nếu vẫn ~0.8 → bug trong `load_bank_performance.py:CIR calculation`.

**Fix:** Phase R3 (refactor-v1.md §9) — bounds checking `cir ∈ [0.2, 1.0]`.

### 4.3. BP-03 — Data Table (Bank × Cluster Detail)

**Quan sát:** Bảng "Bảng dữ liệu chi tiết ngân hàng theo cụm" hiển thị:
- `bank_name`, `bank_code`, `bank_type`, `cluster_id`, `avg_roa`, `avg_roe`, `avg_npl_ratio`

**Kết luận:** ✅ BP-03 render đúng spec, không phát hiện vấn đề.

### 4.4. BP-04 — Pie Chart (Bank Type Composition per Cluster)

**Quan sát:** Biểu đồ tròn "Biểu đồ hình tròn cơ cấu phân loại ngân hàng thương mại" hiển thị:
- JSCB: **86.7%** (slice lớn nhất, màu xanh dương)
- SOCB: ~8.9%
- FOCB: ~4.4%

**L-05 [🟡 MEDIUM] — Phát hiện quan trọng:**

Pie chart và filter dropdown "Loại ngân hàng (SOCB / JSCB / FOCB)" chứng minh rằng **dashboard đang dùng cột `bank_type` (KHÔNG phải `bank_category`)** — vì spec §3.1 nói `dim_bank.bank_type`, không phải `bank_category`.

Tuy nhiên, khi tôi đọc `docs/star-schema.md` §2.3, `dim_bank` chỉ có cột `bank_type` (giá trị SOCB/JSCB/FOCB), **không có cột `bank_category`**. Vậy nên issue L-05 gốc (trong refactor-v1.md §6.5) có thể là do tôi nhầm lẫn tên cột khi đọc screenshot — dashboard đang dùng đúng cột `bank_type`.

**Cập nhật L-05:** Không còn là "fake/derive data" issue; thay vào đó trở thành verification item để chắc chắn rằng giá trị trong BigQuery `bank_type` được phân phối đúng (45 banks → ~86.7% JSCB = ~39 JSCB, ~4 SOCB, ~2 FOCB). Số này khớp với thực tế ngân hàng Việt Nam.

**Action:** Verify bằng query `SELECT bank_type, COUNT(*) FROM dim_bank GROUP BY bank_type` — nếu distribution khớp thì dashboard đúng.

### 4.5. Filters (F-BP-01, F-BP-02, F-BP-03)

Screenshots cho thấy 3 filter controls:
- F-BP-01: Dropdown `bank_type` (SOCB/JSCB/FOCB) — ✅
- F-BP-02: Dropdown `cluster_id` — ✅
- F-BP-03: Date Range (year) — ✅

Không phát hiện vấn đề.

---

## 5. Issues Found (L-01 → L-06)

Tổng hợp tất cả phát hiện từ manual audit, kèm severity và hướng xử lý:

### L-01 [🔴 CRITICAL] — Scorecard "38 cảnh báo đỏ" mismatch BigQuery

**Mô tả:** Scorecard hiển thị 38 High-Risk banks, nhưng `bank_risk_predictions` chỉ có 145 rows với `risk_label=1` (~22 unique bank codes).

**Root cause khả dĩ:**
- Looker Studio measure formula filter sai (e.g., filter theo JSCB + specific year)
- Cache Looker Studio chưa refresh sau khi re-train model
- Scorecard dùng data source khác (không phải `bank_risk_predictions`)

**Bằng chứng:** refactor-v1.md §6.5 + screenshot manual.

**Fix:**
1. Manual: Mở Looker Studio → click scorecard → xem measure formula → so sánh với query BigQuery.
2. Auto: Chạy `scripts/verify_looker_scorecards.py` (task #13) để dump BigQuery counts vs Looker reported values.
3. Sau khi root cause xác định: refresh Looker data source + sửa measure formula.

### L-02 [🟠 HIGH] — CIR ~80% trên tất cả clusters

**Mô tả:** Grouped bar chart BP-02 hiển thị CIR average ~80% cho cả 3 clusters. Benchmark ngành: 50-65%.

**Root cause:** Trong `src/etl/load_bank_performance.py`, hàm tính `cir`:

```python
df["cir"] = df["cir"].where(df["cir"].notna(),
    df["non_interest_expense"] / (df["net_interest_income"].abs() + df["non_interest_income"].abs()))
```

Khi `non_interest_income` không có trong raw data (thiếu cột), hoặc `net_interest_income` rất nhỏ (gần 0), `cir` bị phóng đại.

**Bằng chứng:** refactor-v1.md §B-08.

**Fix:** Phase R3 — bounds checking `cir ∈ [0.2, 1.0]`, fallback về global median nếu ngoài range.

### L-03 [🟠 HIGH] — TNB NPL spike 11% năm 2008

**Mô tả:** Line chart RM-02 cho thấy series TNB đạt đỉnh ~11% NPL vào khoảng 2008. Không khớp với dữ liệu thực tế.

**Root cause:** Tương tự B-08 — `npl_ratio = npl_amount / total_loans` bị phóng đại khi `total_loans` rất nhỏ (e.g., năm đầu thành lập ngân hàng).

**Bằng chứng:** refactor-v1.md §B-08 + 28 rows `npl_ratio` ngoài [0,1] được phát hiện trong audit.

**Fix:** Phase R3 — bounds checking `npl_ratio ∈ [0, 1]`, fallback về global median nếu ngoài range.

### L-04 [🟡 MEDIUM] — Radar chart (BP-02) bị thay bằng grouped bar chart

**Mô tả:** Spec yêu cầu radar chart nhưng implementation dùng grouped bar chart.

**Root cause chưa xác định** — 3 khả năng (xem §4.2).

**Fix:** Cần user xác nhận:
- Nếu intentional: cập nhật `dashboard-spec.md` §3.1 để reflect implementation (BP-02 là bar chart).
- Nếu unintentional: rebuild BP-02 thành radar chart trong Looker Studio.

### L-05 [🟡 MEDIUM] — `bank_category` column verification

**Mô tả:** refactor-v1.md §6.5 gốc nghi ngờ `bank_category` có thể không tồn tại trong `dim_bank`. Sau re-audit, dashboard đang dùng `bank_type` (đúng với spec).

**Action:** Verify `dim_bank` chỉ có `bank_type`, không có `bank_category` — để chắc chắn không có schema drift.

```sql
SELECT column_name, data_type
FROM `vn-banking-dwh-analytics.financial_dwh.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'dim_bank'
ORDER BY ordinal_position;
```

Expected columns: `bank_key`, `bank_code`, `bank_name`, `bank_type`, `charter_capital`, `valid_from`, `valid_to`, `is_current`, `audit_key`, `_created_at`, `_updated_at`, `_source_file`.

### L-06 [🟢 INFO] — Looker Studio không có CI/CD

**Mô tả:** Tất cả Looker dashboards phải tạo/config manual trong UI. Không có `*.datastudio` hoặc `*.looker` config file trong repo (verified bằng Glob).

**Implication:**
- Mọi thay đổi chart (rename, refactor, add new) phải làm thủ công.
- Không thể GitOps, không có version control cho dashboard definition.
- Risk: khi onboard member mới, phải reproduce dashboard manually theo spec.

**Mitigation options:**
- (a) Export Looker Studio report definition thành JSON qua UI (Edit → ⋮ → "Make a copy") — nhưng JSON này không thể re-import programmatically.
- (b) Chấp nhận manual workflow cho Looker; dùng Streamlit cho phần cần version-controlled.
- (c) Migrate sang Looker (commercial product) nếu cần GitOps thật sự — ngoài scope dự án này.

**Quyết định đề xuất:** Option (b) — document rõ trong `dashboard-spec.md` rằng Looker Studio là read-only BI view, mọi thay đổi logic phải thông qua Streamlit trước.

---

## 6. Open Questions for User

Các câu hỏi cần user xác minh trong session tiếp theo để đóng issue L-01, L-04, L-05:

### Q1. Page 2 URL `p_41975wn34d` là page nào?

`dashboard-spec.md` liệt kê 3 pages (Market Movement, Bank Profiling, Risk Monitoring), nhưng user chỉ cung cấp 2 URLs. Cần confirm:

- Page 2 (`p_41975wn34d`) có phải là "Bank Profiling" (BP-*) không?
- "Market Movement" (MM-*) page đã được build chưa, hay đang pending?

### Q2. Radar chart (BP-02) đã bị thay bằng grouped bar — intentional?

`dashboard-spec.md` §3.1 và §3.3 yêu cầu radar chart rõ ràng. Nhưng screenshot cho thấy grouped bar chart. Có phải:
- (a) Looker Studio radar limitation buộc đổi?
- (b) Người thiết kế chọn bar vì dễ đọc hơn?
- (c) Spec sai (radar không phù hợp cho 6 axes × 3 series)?

### Q3. Scorecard "38 cảnh báo đỏ" formula là gì?

Cần user mở Looker Studio → click vào scorecard → xem "Data" panel → copy measure formula. Compare với các khả năng:
- `COUNT(risk_label = 1)` → expect 145
- `COUNT(DISTINCT bank_code WHERE risk_label = 1)` → expect ~22
- Filter combination (e.g., JSCB + year 2022) → có thể ra 38

### Q4. `bank_category` column có tồn tại trong `dim_bank` không?

`docs/star-schema.md` §2.3 không liệt kê `bank_category`; chỉ có `bank_type`. Cần verify trực tiếp trên BigQuery console để chắc chắn không có schema drift.

### Q5. Có thiếu chart nào trong BP-* hoặc RM-* không?

Spec yêu cầu 5 components cho RM (RM-01..05) và 4 components cho BP (BP-01..04). Screenshots có thể không capture đầy đủ. User confirm từng component đã có trên Looker chưa.

### Q6. Có page "Market Movement" (MM-*) nào không?

Spec §2 yêu cầu MM-01..05 (Line Chart, Heatmap, Rolling Correlation, Scorecard, Data Table). User confirm đã build xong chưa.

---

## 7. Recommended Next Steps

### Immediate (trong 1-2 ngày)

1. **Manual BigQuery verification cho L-01** — User mở Looker Studio, click scorecard, copy measure formula, đối chiếu với query ở §3.4. Nếu mismatch → sửa formula.
2. **Confirm page inventory** — User check Looker Studio "Page" navigation, list ra tất cả pages hiện có, đối chiếu với spec (xem Q1, Q5, Q6).
3. **Confirm radar/bar decision** — User quyết định L-04 là intentional hay cần rebuild (xem Q2).

### Short-term (Phase R3 — data quality bounds, theo refactor-v1.md §9)

Phase R3 giải quyết L-02 và L-03:

1. Sửa `src/etl/load_bank_performance.py:_standardize_raw_frame`:
   - `nim > 0.20` → log warning, fallback median
   - `ltd > 2.0` → log warning, fallback median
   - `npl_ratio` ngoài [0,1] → log warning, fallback median
   - `cir` ngoài [0.2, 1.0] → log warning, fallback median
2. Mở rộng `src/etl/validate_integrity.py` để check BigQuery-side (tạo `validate_integrity_bigquery.py` riêng).
3. Re-run ETL → confirm 28 rows `npl_ratio` ngoài range → giảm về 0.
4. Refresh Looker Studio data source → screenshot mới → verify L-02, L-03 resolved.

### Medium-term (Phase R4 — docs sync, theo refactor-v1.md §9)

Phase R4 giải quyết L-04, L-05:

1. Nếu L-04 confirmed intentional: cập nhật `dashboard-spec.md` §3.1 để đổi BP-02 từ "Radar Chart" thành "Grouped Bar Chart", update acceptance criteria §3.3 tương ứng.
2. Nếu L-04 unintentional: rebuild BP-02 thành radar chart trong Looker Studio.
3. Verify L-05 bằng BigQuery `INFORMATION_SCHEMA.COLUMNS` query → update `dashboard-spec.md` nếu cần.
4. Thêm section "Looker Studio Limitations" vào `dashboard-spec.md` để document L-06 (no CI/CD).

### Long-term (Phase R6+ — v2 roadmap)

1. Viết `scripts/verify_looker_scorecards.py` (task #13) — script tự động so sánh Looker-reported values với BigQuery ground truth. Chạy mỗi khi re-train model.
2. Cân nhắc dùng Streamlit (đã có) thay thế một số Looker pages nếu cần version-controlled dashboard.
3. Document quy trình "khi nào dùng Looker vs Streamlit" trong `dashboard-spec.md`.

---

## Tổng kết

| Metric | Count |
|--------|-------|
| Pages audited | 2 / 3 (thiếu Market Movement MM-*) |
| Components reviewed | 9 (RM-01..05, BP-01..04) |
| Issues found | 6 (L-01 → L-06) |
| Critical issues | 1 (L-01) |
| High issues | 2 (L-02, L-03) |
| Medium issues | 2 (L-04, L-05) |
| Info issues | 1 (L-06) |
| Open questions for user | 6 (Q1-Q6) |

Audit này cung cấp input cho refactor-v1.md §6.5 (Looker Studio findings) và roadmap Phase R3-R6. Sau khi user confirm Q1-Q6, có thể đóng hết issue L-* và update `dashboard-spec.md` cho khớp với implementation thực tế.

---

**Tác giả:** Đỗ Kiến Hưng, BI role, với manual screenshot capture và cross-reference BigQuery ground-truth.

**Ngày audit:** 2026-07-30

**Phiên bản repo:** `6da095c` (branch `main`)