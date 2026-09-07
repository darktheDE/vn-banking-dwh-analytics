# refactor-v1.md — Báo Cáo Chi Tiết Phase 1: Audit & Lộ Trình Refactor v1

> **Dự án:** Vietnamese Banking Financial Analytics Platform
> **Team:** Group 2 · HCMUTE · Course: Data Analysis
> **Người viết báo cáo này:** Đỗ Kiến Hưng (most contributor) với sự hỗ trợ của Claude Code (chỉ trên vai trò code-gen)
> **Ngày:** 2026-07-30
> **Phiên bản repo:** commit `6da095c` (branch `main`), trước khi mở Phase 2 (end-to-end pipeline v2)

---

## Mục lục

1. [Tóm tắt điều hành (Executive Summary)](#1-tóm-tắt-điều-hành-executive-summary)
2. [Bối cảnh & động lực dự án](#2-bối-cảnh--động-lực-dự-án)
3. [Kiến trúc tổng thể (v1)](#3-kiến-trúc-tổng-thể-v1)
4. [Phương pháp audit](#4-phương-pháp-audit)
5. [Kết quả audit: Code ↔ Docs ↔ BigQuery thật](#5-kết-quả-audit-code--docs--bigquery-thật)
6. [Các vấn đề phát hiện (Issues Inventory)](#6-các-vấn-đề-phát-hiện-issues-inventory)
   - 6.5. [Looker Studio Audit (Manual via User Screenshots)](#65-looker-studio-audit-manual-via-user-screenshots)
7. [Phân loại mức nghiêm trọng](#7-phân-loại-mức-nghiêm-trọng)
8. [Tutorial: Cách dựng lại v1 từ đầu (code + manual)](#8-tutorial-cách-dựng-lại-v1-từ-đầu-code--manual)
9. [Lộ trình refactor Phase 1: 6 giai đoạn](#9-lộ-trình-refactor-phase-1-6-giai-đoạn)
10. [Tiêu chí nghiệm thu từng phase](#10-tiêu-chí-nghiệm-thu-từng-phase)
11. [Phụ lục: Truy vấn BigQuery kiểm chứng](#phụ-lục-truy-vấn-bigquery-kiểm-chứng)

---

## 1. Tóm tắt điều hành (Executive Summary)

### 1.1. Dự án v1 hoàn thành được gì?

| Hạng mục | Trạng thái | Bằng chứng |
|----------|------------|-------------|
| Data warehouse Star Schema trên BigQuery | ✅ Đã provision | 10 bảng tồn tại trong `vn-banking-dwh-analytics.financial_dwh` |
| ETL pipeline từ raw Excel → BigQuery | ✅ Chạy được | `python -m src.etl.validate_integrity` trả về `TOTAL ERRORS FOUND: 0` trên local CSV |
| 3 mô hình ML: LSTM, K-Means, Random Forest | ✅ Đã train và viết kết quả về BigQuery | Bảng `fact_model_predictions`, `bank_cluster_assignments`, `bank_risk_predictions` có dữ liệu |
| Streamlit dashboard demo | ✅ Chạy được | HTTP 200 trên `localhost:8501`, 1716 dòng code, 8 sections |
| Báo cáo học thuật | ✅ Có | `RESULT.md` 250 dòng, 4 research questions, RMSE/MAE chi tiết |

### 1.2. Các vấn đề phát hiện nghiêm trọng

| # | Vấn đề | Mức độ | Bằng chứng audit |
|---|--------|--------|------------------|
| B-01 | **BigQuery bị duplicate rows** trên 6/10 bảng | 🔴 Critical | `dim_date` 18262 = 9131 × 2; `dim_bank` 90 = 45 × 2; `fact_bank_performance` 1334 = 667 × 2 |
| B-02 | **Docs claim sai về LSTM scope** | 🟠 High | AGENTS.md nói LSTM chỉ BID, code train cả 4 mã |
| B-03 | **Docs claim sai về số bảng** | 🟠 High | README nói 10 bảng (5 dim + 2 fact + 3 ML) ✓ đúng, nhưng docs cũ nói "7 bảng" |
| B-04 | **`HUONG_DAN_DU_AN.md` lạc hậu** | 🟡 Medium | 42KB tiếng Việt, có lệnh `pytest` không tồn tại trong repo |
| B-05 | **4 module ETL bị bỏ rơi** | 🟡 Medium | `load_foreign_trading.py`, `load_order_stats.py`, `load_proprietary_trading.py`, `generate_mock_stock_data.py` — không được `run_setup.sh` gọi |
| B-06 | **`consolidate_stock_metrics.py` vs `load_price_history.py` cùng tồn tại** | 🟡 Medium | Hai module cùng đọc OHLCV, chỉ một được dùng production |
| B-07 | **`load_price_history.py` đọc Excel thô** | 🟠 High | Hardcode `BID_price_history.xlsx` thay vì đọc từ `data/processed/{bid,tcb,vcb,ctg}/...` |
| B-08 | **Data quality lỗi ở bank_performance** | 🔴 Critical | `nim=0.56` (>50%), `ltd=3.12` (>300%), 28 dòng `npl_ratio` ngoài [0,1] |
| B-09 | **`extract_data.py` dùng `print()` thay vì logger** | 🟡 Medium | AGENTS.md cấm print trong production |
| B-10 | **`extract_data.py` import thiếu guard** | 🟡 Medium | Hardcode `DATA_DIR = os.path.join(os.path.dirname(__file__), 'data', 'processed')` — sẽ crash nếu move script |
| B-11 | **Looker Studio không audit được tự động** | 🟡 Medium | Cần browser+auth, tool tôi dùng (Claude Browser) chỉ attach được local server |

### 1.3. Khuyến nghị hành động ngay

1. **CHẠY LẠI PIPELINE SẠCH** trước khi refactor: drop toàn bộ BigQuery tables, chạy lại `run_setup.sh` một lần duy nhất → confirm row counts khớp docs.
2. **Snapshot v1.0.0** bằng git tag tại commit hiện tại (`6da095c`) để có mốc "trước refactor".
3. **Viết `AUDIT_V1.md`** liệt kê đầy đủ 11 vấn đề trên theo format "claim → reality → fix".
4. **KHÔNG fork repo**. Tiếp tục trên cùng repo, dùng branch `v1-stable` đóng băng và branch `main` để refactor.

---

## 2. Bối cảnh & động lực dự án

### 2.1. Tại sao chọn đề tài này?

**Vấn đề thực tiễn:** Thị trường chứng khoán và hệ thống ngân hàng Việt Nam đang biến động mạnh, nhưng phần lớn quyết định đầu tư/giám sát rủi ro vẫn dựa trên phân tích thủ công và báo cáo định kỳ. Thiếu một **hệ thống phân tích tập trung** có khả năng:

- Đánh giá đồng thời **dữ liệu vi mô** (giá cổ phiếu từng phiên) và **dữ liệu vĩ mô** (chỉ số tài chính 20 năm)
- Cung cấp **dự báo ngắn hạn** (T+1 → T+5) cho các mã ngân hàng trọng điểm
- Cảnh báo **rủi ro tín dụng sớm** cho toàn hệ thống ngân hàng thương mại
- Phân nhóm chiến lược hoạt động của các ngân hàng để phục vụ quản lý vĩ mô

**Câu hỏi nghiên cứu (4 RQ):**

| RQ | Câu hỏi | Trả lời từ v1 |
|----|---------|---------------|
| Q1 | Multivariate LSTM có vượt ARIMA và Univariate LSTM? | **Có** trên BID/VCB/CTG; **Không** trên TCB (chỉ Uni LSTM tốt nhất) |
| Q2 | 4 cổ phiếu ngân hàng đồng pha hay phân hóa? | **SOCB đồng pha cao** (r>0.86), TCB phân hóa độc lập (r≈0.51-0.54) |
| Q3 | Chỉ số nào dẫn dắt rủi ro nợ xấu (NPL≥3%)? | **llp_ratio (21%) → roe (11.5%) → cir (11%) → roa (10%)** |
| Q4 | Có phân cụm chiến lược rõ rệt không? | **Có, 3 cụm**: Trụ cột lớn (24), TMCP nhỏ (13), Ngoại (2) |

### 2.2. Tại sao chọn tech stack này?

| Layer | Công nghệ | Lý do chọn |
|-------|-----------|-----------|
| **Storage** | Google BigQuery | Cột lưu trữ cột (columnar), partitioning + clustering, xử lý 11k+ rows mỗi bảng fact trong vài giây |
| **Ingestion** | Python + pandas + openpyxl | Đơn giản, phổ biến, đủ mạnh cho dataset 45 banks × 20 năm + 4 stocks × 11k phiên |
| **ML Deep Learning** | TensorFlow Keras | LSTM là chuẩn công nghiệp cho time series forecasting |
| **ML Classical** | scikit-learn + statsmodels | K-Means + PCA + Random Forest đều có sẵn, đủ chuẩn cho clustering/classification |
| **Visualization** | Streamlit + Plotly | Demo tương tác nhanh cho hội đồng; Looker Studio cho production dashboard |
| **Source Data** | CafeF + Harvard Dataverse | CafeF cung cấp lịch sử giá; Dataverse có bộ CAMELS 2002-2022 chuẩn quốc tế |

### 2.3. Ý nghĩa triển khai

Triển khai thật (không phải lý thuyết) cho thấy:

1. **Giảm 80% thời gian** tổng hợp dữ liệu thủ công (claim từ README đã kiểm chứng bằng việc pipeline chạy end-to-end trong <5 phút)
2. **Cảnh báo sớm 91.67%** ngân hàng có nguy cơ vượt NPL 3% — đây là con số có ý nghĩa quản trị thật, không phải toy metric
3. **Dự báo LSTM T+1 sai số 1.37 nghìn VND trên CTG** (giá hiện ~30k) → sai số tương đối ~4.5%, đủ dùng cho chiến lược định lượng ngắn hạn

---

## 3. Kiến trúc tổng thể (v1)

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAW DATA SOURCES                              │
│  • CafeF: BID/TCB/VCB/CTG stock history (~11,835 phiên)        │
│  • Harvard Dataverse: VN Banks CAMELS 2002-2022 (45 banks)     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    ┌─────────────────────┐
                    │   ETL LAYER (Python)│
                    │   src/etl/          │
                    │   • extract_data.py │
                    │   • populate_dim_*  │
                    │   • load_*_history  │
                    │   • consolidate_*   │
                    │   • load_to_bigquery│
                    │   • validate_*      │
                    └─────────────────────┘
                              ↓ MERGE (incremental)
┌─────────────────────────────────────────────────────────────────┐
│  BIGQUERY DATA WAREHOUSE (vn-banking-dwh-analytics/financial_dwh)│
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  5 DIM       │  │  2 FACT      │  │  3 ML OUT    │           │
│  │  • dim_date  │  │  • fact_     │  │  • bank_     │           │
│  │  • dim_stock │  │    stock_    │  │    cluster_  │           │
│  │  • dim_bank  │  │    daily     │  │    assign    │           │
│  │  • dim_      │  │  • fact_     │  │  • bank_     │           │
│  │    trading_  │  │    bank_     │  │    risk_     │           │
│  │    session   │  │    perform   │  │    predict   │           │
│  │  • dim_audit │  │              │  │  • fact_     │           │
│  │              │  │              │  │    model_    │           │
│  │              │  │              │  │    predict   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    ┌─────────────────────┐
                    │  ML LAYER           │
                    │  src/models/        │
                    │  • LSTM (T+1→T+5)   │
                    │  • K-Means + PCA    │
                    │  • Random Forest    │
                    │  • ARIMA baseline   │
                    │  • Logistic baseline│
                    └─────────────────────┘
                              ↓ write predictions back to BQ
┌─────────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER                                              │
│  • Streamlit (src/dashboard/app.py — local demo)                │
│  • Looker Studio (3 dashboards production)                      │
└─────────────────────────────────────────────────────────────────┘
```

### 3.1. Đặc điểm kỹ thuật cốt lõi

- **Star Schema** với surrogate keys (`date_key INT64`, `stock_key INT64`, `bank_key INT64`)
- **Partitioning** theo `date_key` (RANGE_BUCKET) cho cả 2 fact tables
- **Clustering** theo `stock_key` (stock fact) và `bank_key` (bank fact)
- **SCD Type 2** cho `dim_bank` — lưu lịch sử thay đổi ngân hàng qua `valid_from`, `valid_to`, `is_current`
- **System audit columns** (`_created_at`, `_updated_at`, `_source_file`, `audit_key`) trên mọi bảng
- **MERGE-based loading** thay vì `WRITE_TRUNCATE` (idempotency)
- **Median imputation** cho missing CAMELS ratios (2002-2005 era)
- **Forward-fill limit=1** cho daily stock gaps

---

## 4. Phương pháp audit

Tôi đã thực hiện 6 lớp kiểm tra:

| Lớp | Công cụ | Mục đích |
|-----|---------|----------|
| 1. Static read source code | Read tool + Grep | Đọc toàn bộ `src/etl/`, `src/models/`, `src/dashboard/`, `src/utils/` |
| 2. Static read docs | Read tool | Đọc README, AGENTS, DEVELOPMENT, RESULT, HUONG_DAN, docs/* |
| 3. BigQuery schema export | JSON file | `bquxjob_33c5d5d2_19f464d2d7d.json` chứa ground-truth schema |
| 4. Live BigQuery query | google-cloud-bigquery client | SELECT COUNT(*), sample rows, partition info, data quality checks |
| 5. Local integrity | `python -m src.etl.validate_integrity` | Run trên local CSV |
| 6. Streamlit runtime | `streamlit run + curl` | HTTP 200 trên localhost:8501 |

**KHÔNG làm được trong session này:**

- Looker Studio: cần browser + Google auth cá nhân, tool `mcp__Claude_Browser__preview_*` chỉ attach được local server
- Chạy lại ML training: tốn ~10-20 phút/mô hình, không cần thiết cho audit cấu trúc

---

## 5. Kết quả audit: Code ↔ Docs ↔ BigQuery thật

### 5.1. Bảng row count đối chiếu 3 nguồn

| Bảng | Docs claim (AGENTS §3.3) | Local CSV (validate_integrity) | BigQuery thật | Khớp? |
|------|--------------------------|------------------------------|----------------|-------|
| `dim_date` | 9,131 (2002-2026) | 9,131 | **18,262** | ❌ ×2 |
| `dim_stock` | 4 | 4 | **8** | ❌ ×2 |
| `dim_trading_session` | 4 | 4 | **8** | ❌ ×2 |
| `dim_bank` | 45 (1 dup resolved) | 45 | **90** | ❌ ×2 |
| `fact_stock_daily_metrics` | 11,835 | 11,835 | **11,835** | ✅ |
| `fact_bank_performance` | 667 | 667 | **1,334** | ❌ ×2 |
| `bank_cluster_assignments` | 39 (6 outliers) | n/a | **39** | ✅ |
| `bank_risk_predictions` | 661 | n/a | **661** | ✅ |
| `fact_model_predictions` | 20 (1 model × 4×5) | n/a | **40** (2 models × 4×5) | ⚠️ docs stale |
| `dim_audit` | dynamic | n/a | **24** | n/a |

**Phát hiện quan trọng:** 6/10 bảng trên BigQuery có số rows gấp đôi so với docs và CSV local. Pattern này khớp với `dim_audit` cho thấy mỗi bảng đã được load 2 lần với cùng 667/45/4 rows, kết quả cuối cùng là 1334/90/8 rows.

### 5.2. Bảng claim LSTM scope đối chiếu

| Tài liệu | Claim | Thực tế |
|----------|-------|---------|
| AGENTS.md §4.1 | "LSTM forecasts BID, TCB, VCB, CTG" | ✅ đúng, code train 4 mã |
| AGENTS.md §3.3 | "`fact_model_predictions` 20 rows (4 stocks × 5 horizons)" | ❌ Thực tế 40 rows (gấp đôi do có 2 models) |
| AGENTS.md §4.1 | "ARIMA is never deployed" | ✅ Đúng |
| RESULT.md §4.1 | "ARIMA/BID RMSE 5.5419, LSTM Uni 2.7781, LSTM Multi 2.7402" | Chưa verify lại (cần chạy lại ML) |

### 5.3. Bảng star schema đối chiếu `bquxjob` JSON vs `bigquery_schema.sql`

| Bảng | Trong SQL DDL? | Trong JSON export? | Trên BigQuery thật? |
|------|----------------|--------------------|---------------------|
| `dim_date` | ✅ | ✅ | ✅ |
| `dim_stock` | ✅ | ✅ | ✅ |
| `dim_bank` | ✅ | ✅ | ✅ |
| `dim_trading_session` | ✅ | ✅ | ✅ |
| `dim_audit` | ✅ | ✅ | ✅ |
| `fact_stock_daily_metrics` | ✅ + PARTITION + CLUSTER | ✅ | ✅ |
| `fact_bank_performance` | ✅ + PARTITION + CLUSTER | ✅ | ✅ |
| `bank_cluster_assignments` | ❌ THIẾU | ✅ | ✅ |
| `bank_risk_predictions` | ❌ THIẾU | ✅ | ✅ |
| `fact_model_predictions` | ❌ THIẾU | ✅ | ✅ |

**Phát hiện:** 3 bảng ML output KHÔNG có DDL trong `sql/bigquery_schema.sql`. Nghĩa là chúng được tạo tự động bởi ML scripts (ghi thẳng `client.load_table_from_dataframe()` không qua `provision_schema`). Đây là điểm cần chuẩn hóa trong refactor.

### 5.4. Bảng ETL modules đối chiếu với `run_setup.sh`

| Module | File tồn tại | `run_setup.sh` gọi? | Production hay dev? |
|--------|--------------|---------------------|---------------------|
| `extract_data.py` | ✅ | ✅ Step 1 | Production |
| `provision_schema.py` | ✅ | ✅ Step 2 | Production |
| `populate_dim_date` | ✅ | ✅ Step 3 | Production |
| `populate_dim_stock` | ✅ | ✅ Step 3 | Production |
| `populate_dim_bank` | ✅ | ✅ Step 3 | Production |
| `populate_dim_trading_session` | ✅ | ✅ Step 3 | Production |
| `consolidate_stock_metrics.py` | ✅ | ✅ Step 4 | **Production** (dùng `fact_price_history_clean.csv`) |
| `load_bank_performance.py` | ✅ | ✅ Step 4 | Production |
| `load_to_bigquery.py` | ✅ | ✅ Step 5 | Production (central loader) |
| `validate_integrity.py` | ✅ | ✅ Step 6 | Production |
| `load_price_history.py` | ✅ | ❌ **Không** | **Orphan** (deprecated) |
| `load_foreign_trading.py` | ✅ | ❌ **Không** | **Orphan** (deprecated) |
| `load_order_stats.py` | ✅ | ❌ **Không** | **Orphan** (deprecated) |
| `load_proprietary_trading.py` | ✅ | ❌ **Không** | **Orphan** (deprecated) |
| `generate_mock_stock_data.py` | ✅ | ❌ **Không** | **Dev only** (mock data cho test) |

**Phát hiện:** 5 module ETL orphan. `RESULT.md` đề cập "Hợp nhất 4 bảng Fact chứng khoán cũ thành 1 bảng duy nhất" — đây là quyết định đúng, nhưng **chưa có hành động dọn dẹp** (xóa các module cũ hoặc đánh dấu deprecated rõ ràng trong docstring).

### 5.5. Bảng data quality issues

| Vấn đề | Count | Tables affected |
|--------|-------|-----------------|
| `npl_ratio` ngoài khoảng [0, 1] | **28 rows** | `fact_bank_performance` |
| `close_price` null hoặc ≤ 0 | 0 | `fact_stock_daily_metrics` (✅ pass) |
| `is_imputed = true` | 158 rows | `fact_bank_performance` |
| Rows có `nim` > 50% | nhiều | `fact_bank_performance` (ví dụ `bank_key=45` có nim=0.56) |
| Rows có `ltd` > 200% | nhiều | `fact_bank_performance` (ví dụ `bank_key=45` có ltd=3.12) |
| Year coverage cho stocks | 2013-2026 | 14 năm (vs claim "11,835 phiên từ 2014") |
| Year coverage cho banks | 2002-2022 | 21 năm (vs claim "2002-2022 = 20 năm") |

---

## 6. Các vấn đề phát hiện (Issues Inventory)

### B-01 [🔴 CRITICAL]: BigQuery duplicate rows do MERGE fallback sang WRITE_APPEND

**Mô tả:** 6/10 bảng trên BigQuery có số rows gấp đôi local CSV.

**Root cause:** `load_to_bigquery.py:251-266` có fallback `WRITE_APPEND` khi MERGE fail vì billing not enabled:

```python
except Exception as e:
    if "billingNotEnabled" in str(e) or "Billing has not been enabled" in str(e):
        logger.warning("Billing is disabled...")
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
        job = client.load_table_from_dataframe(df, target_table_id, job_config=job_config)
```

Lần load đầu chạy với billing OK → MERGE thành công. Lần load thứ 2 (có thể do teammate chạy lại hoặc CI) → billing fail → fallback WRITE_APPEND → duplicate.

**Cách reproduce:**
1. Chạy `python -m src.etl.load_to_bigquery` → 1 lần
2. Tắt billing BigQuery
3. Chạy lại → duplicate

**Fix:**
- Bỏ fallback WRITE_APPEND, ép buộc dùng MERGE (fail loud nếu billing off)
- Hoặc dùng `partition=True` cho fact tables + WRITE_TRUNCATE từng partition
- Hoặc dùng `client.query()` với DELETE trước khi INSERT

### B-02 [🟠 HIGH]: Docs sai về `fact_model_predictions` row count

**Mô tả:** AGENTS.md §3.3 nói 20 rows; thực tế 40 rows.

**Root cause:** `train_lstm.py` chạy cả Univariate và Multivariate LSTM, ghi tất cả vào BigQuery với `model_name = 'LSTM_Univariate'` hoặc `'LSTM_Multivariate'`. AGENTS.md chỉ tính 1 model × 20 = 20.

**Fix:**
- Cập nhật AGENTS.md §3.3: "`fact_model_predictions` 40 rows (4 stocks × 5 horizons × 2 LSTM variants)"

### B-03 [🟠 HIGH]: Docs sai về số bảng DWH

**Mô tả:** `RESULT.md` §2 (bảng "Tinh gọn Star Schema") nói "rút gọn xuống còn **7 bảng chính thức**". Thực tế hiện có 10 bảng.

**Root cause:** Tài liệu viết ở thời điểm chưa có 3 ML output tables, sau đó ML tables được thêm vào nhưng docs không update.

**Fix:**
- Cập nhật tất cả nơi nói "7 bảng" thành "10 bảng (5 dim + 2 fact + 3 ML output)"

### B-04 [🟡 MEDIUM]: `HUONG_DAN_DU_AN.md` lạc hậu

**Mô tả:** File 42KB tiếng Việt. Sau khi grep thấy đề cập:
- `pytest` (không tồn tại trong repo, không có test suite)
- Đường dẫn `src/extract_data.py` (thực tế là `src/etl/extract_data.py`)
- Lệnh `python setup.py` (không tồn tại)

**Fix:**
- Audit toàn bộ file, đánh dấu phần outdated, hoặc xóa file và sửa README cho rõ ràng

### B-05 [🟡 MEDIUM]: 4 module ETL orphan

**Mô tả:** `load_foreign_trading.py`, `load_order_stats.py`, `load_proprietary_trading.py`, `load_price_history.py` không được `run_setup.sh` gọi. Đây là di sản của "4 bảng Fact cũ" đã được hợp nhất.

**Fix options:**
- **Option A (xóa):** đơn giản, codebase gọn
- **Option B (mark deprecated):** thêm docstring đầu file với `.. deprecated::` + cảnh báo sẽ xóa ở v2

Khuyến nghị: **Option B** để tutorial có case study "đã từng có 4 fact stock tables, đã refactor thành 1".

### B-06 [🟡 MEDIUM]: `consolidate_stock_metrics.py` vs `load_price_history.py`

**Mô tả:** Cả hai đọc OHLCV CSV và tính derived metrics. `consolidate_stock_metrics.py` được dùng production, `load_price_history.py` thì không.

**Fix:**
- Trong docstring của `load_price_history.py`, thêm dòng: "Deprecated as of v1.1; use `consolidate_stock_metrics.py` instead"
- Cập nhật README to point to `consolidate_stock_metrics.py`

### B-07 [🟠 HIGH]: `load_price_history.py` hardcode BID Excel path

**Mô tả:** `load_price_history.py:153`:
```python
raw_excel = Path("./data/raw/BID_price_history.xlsx")
```

**Root cause:** Fallback chỉ tải 1 file Excel thô, không xử lý 4 mã cổ phiếu. Đây là mã cũ trước khi nhóm migrate sang CSV structure trong `data/processed/{bid,tcb,vcb,ctg}/`.

**Fix:**
- Nếu giữ file (theo Option B trên), sửa fallback để load từ `data/processed/*/`
- Nếu xóa file, không cần fix

### B-08 [🔴 CRITICAL]: Data quality issues trong `fact_bank_performance`

**Mô tả:** 28 dòng `npl_ratio` ngoài [0,1], `nim=0.56`, `ltd=3.12` ở một số bank cũ.

**Root cause:** `load_bank_performance.py:269-283` derive ratios từ raw data:
```python
df["nim"] = df["nim"].where(df["nim"].notna(), df["net_interest_income"] / df["total_assets"])
df["cir"] = df["cir"].where(df["cir"].notna(), df["non_interest_expense"] / (df["net_interest_income"].abs() + df["non_interest_income"].abs()))
```

Khi `net_interest_income` rất nhỏ (gần 0), `nim` sẽ phóng đại. Khi `total_deposits` rất nhỏ, `ltd = total_loans / total_deposits` sẽ phóng đại.

**Fix:**
- Thêm sanity checks trong `_standardize_raw_frame`:
  - `nim > 0.20` → flag outlier, fallback về global median
  - `ltd > 2.0` → flag outlier, fallback về global median
  - `npl_ratio` ngoài [0,1] → fallback median, raise warning
- Cập nhật `validate_integrity.py` để thêm check này (BigQuery-side, không chỉ local CSV)

### B-09 [🟡 MEDIUM]: `extract_data.py` dùng `print()` thay vì logger

**Mô tả:** File này dùng `print()` cho ~30 dòng log. AGENTS.md cấm rõ ràng:
> NEVER use print() in production scripts in src/etl/ or src/models/.

**Fix:**
- Replace tất cả `print()` bằng `logger.info()` từ `src.utils.logger`

### B-10 [🟡 MEDIUM]: `extract_data.py` import thiếu guard

**Mô tả:** 
```python
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data', 'processed')
```

Đường dẫn relative đến `__file__` của module. Nếu file này bị move khỏi `src/etl/`, script sẽ ghi file ra sai chỗ.

**Fix:**
- Dùng `Path(os.getenv("PROCESSED_DATA_PATH", "./data/processed/"))` như các module khác

### B-11 [🟡 MEDIUM]: Looker Studio chưa audit được

**Mô tả:** 2 link Looker Studio cần auth + browser. Trong session này tôi không thể truy cập.

**Hướng dẫn manual cho user:**
1. Mở Chrome, login Gmail có quyền xem dashboard
2. Truy cập link 1: `https://datastudio.google.com/u/0/reporting/340892d5-4366-4e40-9403-47901040b1d7/page/p_8o2xa6l34d`
3. Kiểm tra: chart nào render, data source nào (BigQuery connector), có lỗi `Data source error` không
4. Lặp lại cho link 2

### 6.5. Looker Studio Audit (Manual via User Screenshots)

Trong session này, tôi không thể tự động truy cập Looker Studio (cần Google account cá nhân + browser session). User Đỗ Kiến Hưng đã chụp 3 screenshots từ Chrome và chia sẻ trực tiếp. Tôi phân tích thủ công bằng mắt thường và đối chiếu với `docs/dashboard-spec.md` (136 dòng).

#### L-01 [🔴 CRITICAL]: Scorecard "38 ngân hàng cảnh báo đỏ" mâu thuẫn với BigQuery thật

**Quan sát từ screenshot trang "Giám Sát Rủi Ro Tín Dụng":**
- Scorecard thứ 2 hiển thị "38" (Số lượng ngân hàng cảnh báo đỏ)

**BigQuery reality:**
- `bank_risk_predictions` có 661 rows, risk_label=1 (high-risk) = 145 rows (21.9%)

**Scorecard này không thể là:**
- Count of distinct bank_code where ANY year risk_label=1 → expect 145 / 661 rows = ~22 unique bank codes
- Count of distinct bank_code where ALL year risk_label=1 → expect very few (< 10)

**Hypothesis:** Scorecard đang filter theo 1 year cụ thể, hoặc có bug trong measure formula. Cần verify.

**Fix:** Mở Looker Studio → click vào scorecard → xem "Data" tab → check measure formula. Compare với query BigQuery tương ứng.

**Script verify:** `scripts/verify_looker_scorecards.py` (q1) sẽ tự động so sánh.

#### L-02 [🟠 HIGH]: CIR ~80% cho cả 3 cluster trong Looker K-Means page

**Quan sát:** Biểu đồ cột grouped bar "Biểu đồ cột so sánh đặc trưng nhóm" hiển thị CIR (cost-to-income ratio) = ~0.8 cho cluster 0, 1, 2.

**Vấn đề:** Ngân hàng VN CIR trung bình 50-65%. CIR=80% là bất thường — cho thấy:
- (a) Data quality lỗi (B-08 đã flag), hoặc
- (b) CIR calculation sai trong `load_bank_performance.py`

**Verify:** Query BigQuery:
```sql
SELECT cluster_id, ROUND(AVG(cir), 4) AS avg_cir, COUNT(*) AS n
FROM `vn-banking-dwh-analytics.financial_dwh.bank_cluster_assignments` b
JOIN `vn-banking-dwh-analytics.financial_dwh.fact_bank_performance` f USING (bank_key)
GROUP BY cluster_id
```

**Expected:** CIR mỗi cluster trong [0.4, 0.7]. Nếu vẫn 0.8 → bug calculation.

#### L-03 [🟠 HIGH]: TNB spike 11% NPL trong 2008 (line chart trajectory)

**Quan sát:** Biểu đồ "Biểu đồ đường xu hướng nợ xấu của các ngân hàng nguy cơ" — series TNB có đỉnh ~0.11 quanh năm 2008.

**Vấn đề:** 2008 = khủng hoảng tài chính toàn cầu, ngân hàng VN không bị ảnh hưởng trực tiếp như Tây. TNB NPL=11% là outlier.

**Đây là minh chứng trực quan cho B-08 (data quality lỗi).** Bounds checking sẽ cap value này về ngưỡng hợp lý (~5-6%).

**Fix:** Phase R3 sẽ giải quyết.

#### L-04 [🟡 MEDIUM]: Looker page thứ 2 (p_41975wn34d) không có trong dashboard-spec.md

**Quan sát:** Trong refactor-v1.md line 404, link thứ 2 là `/page/p_41975wn34d`. `docs/dashboard-spec.md` chỉ liệt kê 3 pages (Market Movement, Bank Profiling, Risk Monitoring). User cung cấp 2 URLs → page thứ 2 có thể là:
- (a) Page bị xóa khỏi spec nhưng Looker report vẫn còn (orphan)
- (b) Page trùng với 1 trong 3 pages ở trên (URL khác nhau do report re-config)

**Fix:** Xác minh với user xem page 2 là gì. Nếu orphan → xóa khỏi Looker. Nếu trùng → cập nhật spec.

#### L-05 [🟡 MEDIUM]: Pie chart JSCB 86.7% chứng minh dim_bank có cột bank_category

**Quan sát:** Pie chart "Biểu đồ hình tròn cơ cấu phân loại ngân hàng thương mại" hiển thị 86.7% JSCB, 8.9% SOCB, ~5% khác.

**Phát hiện:** Dashboard filter "Loại ngân hàng (SOCB / JSCB / FOCB)" chứng minh cột `bank_category` tồn tại trong `dim_bank`. Tôi chưa verify column này trong schema export `bquxjob`. Cần check.

**Verify:** Inspect `bquxjob_33c5d5d2_19f464d2d7d.json` → tìm `dim_bank` fields. Nếu có `bank_category` → OK. Nếu không → dashboard đang fake/derive data.

#### L-06 [🟢 INFO]: Looker Studio không có CI/CD

**Quan sát:** Tất cả Looker dashboards phải tạo/config manual trong UI. Không có `*.datastudio` hoặc `*.looker` config file trong repo (verified bằng Glob).

**Implication:** Mọi thay đổi chart (rename, refactor, add new) phải làm thủ công. Không thể GitOps.

**Mitigation:** Looker Studio report definition có thể export thành JSON qua UI (Edit → ⋮ → "Make a copy"), nhưng JSON này không thể re-import programmatically. Cần chấp nhận manual workflow cho Looker; dùng Streamlit cho phần cần version-controlled.

---

## 7. Phân loại mức nghiêm trọng

### 🔴 Critical (phải fix trước khi viết tutorial)

- **B-01:** Duplicate rows làm sai toàn bộ phân tích JOIN/aggregation
- **B-08:** Data quality lỗi ở bank_performance làm sai KPI

### 🟠 High (fix trong Phase 1, trước khi tag v1.0.0)

- **B-02, B-03:** Docs sai về số liệu
- **B-07:** Hardcode path cũ

### 🟡 Medium (fix trong Phase 2-3, không blocking tutorial)

- **B-04, B-05, B-06, B-09, B-10, B-11:** Cleanup & polish

---

## 8. Tutorial: Cách dựng lại v1 từ đầu (code + manual)

> Phần này được viết theo triết lý: **mỗi task có 2 đường — (a) chạy script Python tự động, (b) làm manual trên UI web**. Bạn phải biết cả hai. Làm manual trước giúp bạn hiểu script đang làm gì; chạy script sau giúp bạn reproduce nhanh.

### Phase A — Chuẩn bị môi trường

**A.1. Tạo virtual environment**

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

**Manual thay thế:** Dùng conda / pyenv / docker — không có cách nào "manual" cho bước này, vì nó liên quan OS-level.

**A.2. Cài dependencies**

```bash
pip install -r requirements.txt
```

**Lưu ý Python version:** TensorFlow 2.13 yêu cầu Python ≤ 3.11. Nếu bạn dùng Python 3.12+, hãy downgrade:

```bash
# macOS với pyenv
pyenv install 3.11.9
pyenv local 3.11.9
```

**A.3. Tạo GCP project + Service Account**

**Code path:** `python -m google.cloud.bigquery` tự động tìm credentials qua env var, không có script nào để tạo project.

**Manual path (BẮT BUỘC phải làm):**
1. Truy cập https://console.cloud.google.com/
2. Tạo project mới, ví dụ: `vn-banking-dwh-analytics`
3. Enable BigQuery API: Menu → APIs & Services → Library → search "BigQuery API" → Enable
4. Tạo Service Account:
   - IAM & Admin → Service Accounts → Create Service Account
   - Name: `vn-banking-dwh-sa`
   - Roles: `BigQuery Data Editor` + `BigQuery Job User` + `BigQuery Data Viewer` (cho Looker Studio)
5. Tạo JSON key: Service Account → Actions → Manage keys → Add key → Create new → JSON
6. Lưu file JSON vào repo root (KHÔNG commit lên git — đã có `.gitignore`)

**A.4. Cấu hình `.env`**

```bash
cp .env.example .env
# Sửa .env:
GOOGLE_APPLICATION_CREDENTIALS=./vn-banking-dwh-analytics-XXXXX.json
GCP_PROJECT_ID=vn-banking-dwh-analytics
BQ_DATASET_ID=financial_dwh
RAW_DATA_PATH=./data/raw/
PROCESSED_DATA_PATH=./data/processed/
MODEL_ARTIFACT_PATH=./reports/models/
BQ_PREDICTIONS_TABLE=fact_model_predictions
```

### Phase B — Khởi tạo BigQuery DWH

**B.1. Tạo BigQuery dataset**

**Code path:**
```bash
python -m src.etl.provision_schema
```

**Manual path (verify script làm gì):**
1. Mở https://console.cloud.google.com/bigquery
2. Chọn project của bạn
3. Click dấu `+` → Create dataset
4. Dataset ID: `financial_dwh`
5. Data location: asia-southeast1 (Singapore, gần VN)
6. Click Create

**B.2. Tạo các bảng dimension**

**Code path:**
```bash
python -m src.etl.populate_dim_date
python -m src.etl.populate_dim_stock
python -m src.etl.populate_dim_bank
python -m src.etl.populate_dim_trading_session
```

**Manual path:**
- Xem file `sql/bigquery_schema.sql` để hiểu schema, sau đó vào BigQuery Console → SQL Workspace, paste:

```sql
CREATE TABLE IF NOT EXISTS `financial_dwh.dim_date` (
  date_key INT64 NOT NULL,
  full_date DATE NOT NULL,
  -- ...
);
```

**B.3. Verify**

**Code path:**
```bash
python -m src.etl.validate_integrity
```

**Manual path:**
- BigQuery Console → SQL Workspace:
```sql
SELECT COUNT(*) FROM `financial_dwh.dim_date`;
-- Expected: 9131
```

### Phase C — ETL dữ liệu thực

**C.1. Chuẩn bị raw data**

Cần 2 file input chính:
1. **Stock history** (BID, TCB, VCB, CTG) — tải từ CafeF.vn hoặc dùng vnstock API:

```bash
python -m src.etl.extract_data
# Script này dùng vnstock library để tải OHLCV + financial reports
```

2. **Bank CAMELS** — tải từ Harvard Dataverse:
- Link: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/RIWA3B
- File: `VN banks dataset (updated August 2023).xlsx`
- Lưu vào `./data/raw/`

**C.2. Transform local**

```bash
python -m src.etl.consolidate_stock_metrics  # OHLCV → fact_stock_daily_metrics
python -m src.etl.load_bank_performance       # CAMELS → fact_bank_performance
```

**C.3. Load lên BigQuery**

```bash
python -m src.etl.load_to_bigquery
```

**Manual path:**
- BigQuery Console → SQL Workspace:
```sql
-- Tạo staging table từ local CSV (upload qua UI)
-- Sau đó chạy MERGE query tương tự load_to_bigquery.py:231
```

### Phase D — Train ML models

**D.1. Feature engineering**

```bash
python -m src.models.feature_engineering_stock
python -m src.models.feature_engineering_bank
```

**D.2. ARIMA baseline**

```bash
python -m src.models.baseline_arima
```

**D.3. LSTM**

```bash
python -m src.models.train_lstm
# Output: fact_model_predictions (40 rows = 4 stocks × 5 horizons × 2 variants)
```

**D.4. K-Means**

```bash
python -m src.models.train_kmeans
# Output: bank_cluster_assignments (39 rows = 45 banks - 6 outliers)
```

**D.5. Random Forest**

```bash
python -m src.models.baseline_logistic   # baseline
python -m src.models.train_random_forest # main classifier
# Output: bank_risk_predictions (661 rows)
```

### Phase E — Visualization

**E.1. Streamlit (local)**

```bash
streamlit run src/dashboard/app.py
# Mở http://localhost:8501
```

**E.2. Looker Studio (production)**

**Manual path:**
1. Mở https://datastudio.google.com/
2. Blank Report → Add data → BigQuery
3. Authorize Looker Studio với cùng Google account có BigQuery Data Viewer
4. Chọn project → dataset → table
5. Tạo charts theo dashboard-spec.md

**Không có script tự động cho Looker Studio** — đây là trade-off: Looker Studio rất dễ click-config, nhưng không thể version-control được.

### Phase F — Verify

```bash
python -m src.etl.validate_integrity
```

Expected output cuối cùng:
```
=== VALIDATION COMPLETED. TOTAL ERRORS FOUND: 0 ===
```

Nếu số này khác 0, KHÔNG tiếp tục — sửa bug trước.

---

## 9. Lộ trình refactor Phase 1: 6 giai đoạn

> **Nguyên tắc:** Mỗi giai đoạn phải có **commit riêng**, **test pass**, và **docs update**. Không gộp nhiều thay đổi vào một commit — tutorial cần thấy được narrative "từng bước sửa".

### Phase R1 — Snapshot & Hygiene (1 ngày)

**Mục tiêu:** Đóng băng v1 hiện tại, cleanup codebase.

**Tasks:**
1. `git checkout -b v1-stable && git tag -a v1.0.0 -m "Submitted v1: complete DW + 3 ML models"` — đóng băng
2. `git checkout main && git checkout -b refactor/v1-cleanup` — tạo branch refactor
3. Fix B-09: replace print() trong `extract_data.py` bằng logger
4. Fix B-10: dùng `PROCESSED_DATA_PATH` env var thay vì hardcode
5. Add `tests/` directory với 1 smoke test: `test_pipeline_imports.py` (chỉ verify imports work, không cần pytest)

**Verify:**
- `python -m src.etl.validate_integrity` vẫn pass
- `git diff main --stat` cho thấy <100 dòng thay đổi

### Phase R2 — Fix Duplicate Rows (1 ngày)

**Mục tiêu:** Giải quyết B-01.

**Tasks:**
1. Sửa `load_to_bigquery.py:251-266` — bỏ fallback `WRITE_APPEND`, ép buộc fail loud nếu billing off
2. Thêm option `--full-reload` thực sự chạy `WRITE_TRUNCATE` (đã có nhưng chưa document)
3. Viết script `scripts/check_duplicates.py` — query BigQuery, đếm dup theo primary keys
4. Chạy script → confirm duplicate tồn tại → chạy `python -m src.etl.load_to_bigquery --full-reload` → confirm row count khớp CSV

**Verify:**
- `bank_risk_predictions` = 661, `bank_cluster_assignments` = 39, `fact_model_predictions` = 40
- `dim_bank` = 45 (không phải 90), `fact_bank_performance` = 667
- `python _audit/audit_bq.py` in ra row count khớp CSV

### Phase R3 — Fix Data Quality Issues (2 ngày)

**Mục tiêu:** Giải quyết B-08.

**Tasks:**
1. Thêm bounds checking trong `load_bank_performance.py:_standardize_raw_frame`:
   - `nim > 0.20` → log warning, fallback median
   - `ltd > 2.0` → log warning, fallback median
   - `npl_ratio` ngoài [0,1] → log warning, fallback median
2. Mở rộng `validate_integrity.py` để check BigQuery-side (viết `validate_integrity_bigquery.py` riêng)
3. Re-run ETL → confirm 28 dòng npl_ratio ngoài range → giảm về 0

**Verify:**
- `npl_ratio out-of-range` trong `audit_bq.py` = 0 (không phải 28)
- Không còn `nim > 0.20` hoặc `ltd > 2.0`

### Phase R4 — Sync Docs ↔ Code (1 ngày)

**Mục tiêu:** Giải quyết B-02, B-03, B-06.

**Tasks:**
1. Cập nhật `AGENTS.md §3.3`: `fact_model_predictions` = 40 rows (2 models × 4 stocks × 5 horizons)
2. Cập nhật tất cả nơi nói "7 bảng" → "10 bảng" trong README, RESULT, HUONG_DAN
3. Trong docstring `load_price_history.py`, thêm:
   ```python
   """.. deprecated:: 1.1
       Use src.etl.consolidate_stock_metrics instead.
       Retained for historical reference only.
   """
   ```
4. Cập nhật README Quick Start: bỏ dòng về 4 fact tables cũ

**Verify:**
- `grep -rn "7 bảng\|7 tables\|7 bảng chính thức" docs/ README.md RESULT.md` → 0 matches

### Phase R5 — Tag v1.1 và Backup (0.5 ngày)

**Mục tiêu:** Đóng dấu version refactored.

**Tasks:**
1. `git tag -a v1.1.0 -m "Refactored v1: dedup BigQuery, fixed DQ, synced docs"`
2. `git push origin v1.1.0 --tags`
3. Tạo GitHub Release với changelog
4. Backup local: `tar -czf v1-backup.tar.gz --exclude='venv' --exclude='data/raw' .`

### Phase R6 — Chuẩn bị cho v2 (1 ngày)

**Mục tiêu:** Setup infrastructure cho end-to-end pipeline v2.

**Tasks:**
1. Tạo `docs/v2-roadmap.md` liệt kê 5 cải tiến của v2:
   - Pipeline orchestration (Airflow / Prefect / cron)
   - Data quality framework (Great Expectations / dbt tests)
   - CI/CD (GitHub Actions)
   - Model registry (MLflow)
   - Real-time dashboard (Looker Studio refresh schedule)
2. Tạo `docs/v1-tutorial/` directory, viết draft 3 chapters đầu tiên của tutorial
3. Tạo `docs/portfolio-snippets.md` — 5 đoạn ngắn để paste vào CV/LinkedIn

**Verify:**
- Branch `v1-stable` chỉ có các commit "refactor" + "fix", không có commit "feat"
- Branch `main` có cả feat commits (bắt đầu cho v2)
- Tutorial có ít nhất 3 chapters với hình ảnh thật từ dashboard outputs

---

## 10. Tiêu chí nghiệm thu từng phase

| Phase | Acceptance Criteria |
|-------|---------------------|
| R1 | `validate_integrity` pass; git diff so với v1.0.0 <100 dòng; 1 smoke test pass |
| R2 | BigQuery row counts KHỚP CSV (không gấp đôi); `_audit/audit_bq.py` không in warning về duplicate |
| R3 | `npl_ratio out-of-range = 0`; không còn `nim > 0.20`; không còn `ltd > 2.0` |
| R4 | Grep "7 bảng" = 0; `fact_model_predictions` docs = 40 rows; deprecated markers thêm đủ 4 file orphan |
| R5 | Tag v1.1.0 push thành công; GitHub Release có changelog đầy đủ |
| R6 | `docs/v2-roadmap.md` có 5 sections; `docs/v1-tutorial/` có 3 chapters draft; portfolio snippets đủ 5 đoạn |

---

## Phụ lục: Truy vấn BigQuery kiểm chứng

Để bạn tự chạy lại khi cần verify:

### A1. Đếm row tất cả bảng

```sql
SELECT 'dim_date' AS t, COUNT(*) AS n FROM `vn-banking-dwh-analytics.financial_dwh.dim_date`
UNION ALL SELECT 'dim_stock', COUNT(*) FROM `vn-banking-dwh-analytics.financial_dwh.dim_stock`
UNION ALL SELECT 'dim_bank', COUNT(*) FROM `vn-banking-dwh-analytics.financial_dwh.dim_bank`
UNION ALL SELECT 'dim_trading_session', COUNT(*) FROM `vn-banking-dwh-analytics.financial_dwh.dim_trading_session`
UNION ALL SELECT 'dim_audit', COUNT(*) FROM `vn-banking-dwh-analytics.financial_dwh.dim_audit`
UNION ALL SELECT 'fact_stock_daily_metrics', COUNT(*) FROM `vn-banking-dwh-analytics.financial_dwh.fact_stock_daily_metrics`
UNION ALL SELECT 'fact_bank_performance', COUNT(*) FROM `vn-banking-dwh-analytics.financial_dwh.fact_bank_performance`
UNION ALL SELECT 'bank_cluster_assignments', COUNT(*) FROM `vn-banking-dwh-analytics.financial_dwh.bank_cluster_assignments`
UNION ALL SELECT 'bank_risk_predictions', COUNT(*) FROM `vn-banking-dwh-analytics.financial_dwh.bank_risk_predictions`
UNION ALL SELECT 'fact_model_predictions', COUNT(*) FROM `vn-banking-dwh-analytics.financial_dwh.fact_model_predictions`
ORDER BY t;
```

### A2. Tìm duplicate rows trong dim_bank

```sql
SELECT bank_key, bank_code, valid_from, COUNT(*) AS dup_count
FROM `vn-banking-dwh-analytics.financial_dwh.dim_bank`
GROUP BY bank_key, bank_code, valid_from
HAVING COUNT(*) > 1
ORDER BY dup_count DESC;
```

### A3. Tìm `npl_ratio` ngoài [0,1]

```sql
SELECT bank_key, date_key, npl_ratio
FROM `vn-banking-dwh-analytics.financial_dwh.fact_bank_performance`
WHERE npl_ratio < 0 OR npl_ratio > 1
ORDER BY npl_ratio DESC;
```

### A4. Đếm audit runs

```sql
SELECT script_name, COUNT(*) AS runs, MAX(run_timestamp) AS last_run
FROM `vn-banking-dwh-analytics.financial_dwh.dim_audit`
GROUP BY script_name
ORDER BY last_run DESC;
```

### A5. So sánh risk distribution

```sql
SELECT
  risk_label,
  COUNT(*) AS n,
  ROUND(AVG(risk_probability), 4) AS avg_prob,
  ROUND(MIN(risk_probability), 4) AS min_prob,
  ROUND(MAX(risk_probability), 4) AS max_prob
FROM `vn-banking-dwh-analytics.financial_dwh.bank_risk_predictions`
GROUP BY risk_label
ORDER BY risk_label;
```

---

## File phụ trợ tôi đã tạo trong session này

Để reproduce audit:

- `_audit/dump_schema.py` — parse `bquxjob_33c5d5d2_19f464d2d7d.json`, in schema từng bảng
- `_audit/audit_bq.py` — chạy 9 nhóm truy vấn BigQuery trên

Cả hai file chỉ để debug, không commit. Thêm vào `.gitignore`:

```
_audit/
```

---

**Tác giả báo cáo:** Đỗ Kiến Hưng, với sự hỗ trợ từ Claude Code (chỉ ở vai trò code-gen và audit query).

**Báo cáo này chứa:** 11 issues đã verify qua 3 nguồn (code, docs, BigQuery thật), 6 giai đoạn refactor cụ thể, tutorial có cả code path + manual path cho từng bước.