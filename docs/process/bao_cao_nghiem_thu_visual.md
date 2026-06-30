# Walkthrough — Local Data Analysis & Dashboards Plotting

We have created and successfully executed the local data analysis and plotting script to satisfy the requirements of the `ref` folder on local CSV files before deploying to BigQuery.

---

## 1. Page 1 — Market Movement (BID Stock Forecast)
This page displays the actual BIDV close price alongside the LSTM predictions (T+1 to T+5) and tracks the net transaction volumes of Foreign and Proprietary trading.

![Dự Báo Giá BID 5 Phiên Tới: Kỳ Vọng Phục Hồi Nhẹ Lên Ngưỡng 41.93 VND Sau Phiên Điều Chỉnh](../../reports/figures/dashboard/page1_market_movement.png)

- **Actual Price**: Closed at 41.70 (Thousand VND).
- **LSTM Forecast**: Expected slight dip to 41.57 (T+1) before climbing back to 41.93 (T+5).
- **Dòng tiền ròng**: Khối ngoại mua ròng tạo bệ đỡ tại vùng giá 41.00 - 42.00, trong khi tự doanh trong nước chốt lời ngắn hạn.

---

## 2. Page 2 — Bank Profiling (K-Means Clustering)
This page segments the 45 commercial banks into distinct behavioral groups using PCA and K-Means.

![Bản Đồ Vị Thế Hệ Thống: Đông Á Bank (DAB) Bị Cô Lập Hoàn Toàn Khỏi Nhóm Hoạt Động Bình Thường](../../reports/figures/dashboard/page2_bank_profiling.png)

- **Cluster 0**: 44 banks (Standard healthy commercial banks group).
- **Cluster 1**: 1 bank (**DAB** - Dong A Bank, identified as an anomalous outlier due to unique distressed CAMELS features).
- **Radar profile**: Indicates Cluster 1 (DAB) has critically low capital adequacy and profitability combined with highly abnormal NPL ratios.

---

## 3. Page 3 — Risk Monitoring (Random Forest Classification)
This page classifies the credit risk of banks and identifies early warning indicators.

![Lịch Sử Vượt Ngưỡng Nợ Xấu 3% Của Các Ngân Hàng PVB, BVB và PGB](../../reports/figures/dashboard/page3_risk_monitoring.png)

- **High-Risk Flagged**: PVB, BVB, and PGB had actual/predicted NPL ratios exceeding the 3% regulatory limit in historical years (2019 and 2021).
- **Top Credit Risk Feature**: `llp_ratio` (Loan Loss Provision Ratio) is identified as the most significant metric predicting credit risk (NPL $\ge$ 3%), accounting for over 21% of feature importance.

---

## Task Checklist Updates (task.md)
- `[x]` Create `generate_dashboard_plots.py` at `src/models/local/`
- `[x]` Execute `generate_dashboard_plots.py` and verify outputs
- `[x]` Create `walkthrough.md` summarizing the completed work
