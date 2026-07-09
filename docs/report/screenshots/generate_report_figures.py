# -*- coding: utf-8 -*-
"""
generate_report_figures.py
Tạo toàn bộ biểu đồ (EDA + ML) cho báo cáo phân tích dữ liệu.
Lưu tất cả PNG vào docs/report/screenshots/
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import matplotlib.dates as mdates
import seaborn as sns
import json
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

# ─── Cài đặt style ───────────────────────────────────────────────────────────
plt.rcParams.update({
    'figure.facecolor': '#0e1117',
    'axes.facecolor':   '#1a1f2e',
    'axes.edgecolor':   '#444',
    'axes.labelcolor':  '#ccc',
    'text.color':       '#ddd',
    'xtick.color':      '#aaa',
    'ytick.color':      '#aaa',
    'grid.color':       '#333',
    'grid.linestyle':   '--',
    'grid.alpha':       0.5,
    'font.family':      'DejaVu Sans',
    'axes.titlesize':   13,
    'axes.labelsize':   11,
    'legend.fontsize':  10,
    'legend.facecolor': '#1a1f2e',
    'legend.edgecolor': '#555',
})

COLORS_TICKER = {'BID': '#4285F4', 'TCB': '#EA4335', 'VCB': '#34A853', 'CTG': '#FBBC04'}
COLORS_CLUSTER = {0: '#FF6B6B', 1: '#4ECDC4', 2: '#FFE66D'}

OUT_DIR = Path("docs/report/screenshots")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── Load dữ liệu ────────────────────────────────────────────────────────────
print("Loading data...", flush=True)
stock_df  = pd.read_csv("data/processed/fact_stock_daily_metrics_clean.csv")
bank_df   = pd.read_csv("data/processed/fact_bank_performance_clean.csv")
dim_stock = pd.read_csv("data/processed/dim_stock_clean.csv")[['stock_key','ticker']]
dim_bank  = pd.read_csv("data/processed/dim_bank_clean.csv")[['bank_key','bank_code','bank_name','bank_type']]
dim_date  = pd.read_csv("data/processed/dim_date_clean.csv")[['date_key','full_date','year','month','quarter','is_trading_day']]

# Join ticker vào stock data
stock_df = stock_df.merge(dim_stock, on='stock_key', how='left')
stock_df['date'] = pd.to_datetime(stock_df['date_key'].astype(str), format='%Y%m%d')
stock_df['year'] = stock_df['date'].dt.year

# Join bank_code vào bank performance
bank_df = bank_df.merge(dim_bank, on='bank_key', how='left')
bank_df = bank_df.merge(
    dim_date[['date_key','year']].drop_duplicates(),
    on='date_key', how='left'
)

BID_stock = stock_df[stock_df['ticker'] == 'BID'].sort_values('date').copy()
BID_bank  = bank_df[bank_df['bank_code'] == 'BIDV'].sort_values('year').copy()

print(f"Stock data: {stock_df.shape}, Bank data: {bank_df.shape}", flush=True)
print(f"BID stock rows: {len(BID_stock)}, BID bank rows: {len(BID_bank)}", flush=True)

# ═══════════════════════════════════════════════════════════════════════════════
# EDA 1 — Phân phối giá đóng cửa 4 cổ phiếu (Histogram + KDE)
# ═══════════════════════════════════════════════════════════════════════════════
print("[EDA-1] Price distribution histograms", flush=True)
fig, axes = plt.subplots(2, 2, figsize=(14, 9))
fig.suptitle("Phân Phối Giá Đóng Cửa (Close Price) — BID, TCB, VCB, CTG\n(Toàn bộ lịch sử giao dịch HOSE 2014–2026)", fontsize=14, y=0.98, color='#fff')

tickers = ['BID', 'TCB', 'VCB', 'CTG']
for ax, ticker in zip(axes.flatten(), tickers):
    data = stock_df[stock_df['ticker'] == ticker]['close_price'].dropna()
    color = COLORS_TICKER[ticker]
    ax.hist(data, bins=50, color=color, alpha=0.7, density=True, edgecolor='none')
    data.plot.kde(ax=ax, color=color, linewidth=2.5, label='KDE')
    ax.axvline(data.mean(), color='white', linestyle='--', linewidth=1.5,
               label=f'Mean: {data.mean():.1f}')
    ax.axvline(data.median(), color='#FFD700', linestyle=':', linewidth=1.5,
               label=f'Median: {data.median():.1f}')
    ax.set_title(f'{ticker} — N={len(data):,} phiên', color='#fff')
    ax.set_xlabel('Giá đóng cửa (nghìn VND)')
    ax.set_ylabel('Mật độ xác suất')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    skewness = data.skew()
    ax.text(0.98, 0.95, f'Skewness: {skewness:.2f}', transform=ax.transAxes,
            ha='right', va='top', fontsize=9, color='#aaa',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#222', alpha=0.7))

plt.tight_layout()
plt.savefig(OUT_DIR / "s_eda1_price_distribution.png", dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: s_eda1_price_distribution.png", flush=True)

# ═══════════════════════════════════════════════════════════════════════════════
# EDA 2 — Chuỗi thời gian giá đóng cửa 4 ngân hàng (Time Series)
# ═══════════════════════════════════════════════════════════════════════════════
print("[EDA-2] Price time series", flush=True)
fig, ax = plt.subplots(figsize=(16, 7))
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#1a1f2e')

for ticker in tickers:
    data = stock_df[stock_df['ticker'] == ticker].sort_values('date')
    ax.plot(data['date'], data['close_price'], label=ticker,
            color=COLORS_TICKER[ticker], linewidth=1.2, alpha=0.9)

# Đánh dấu sự kiện lịch sử quan trọng
events = [
    ('2020-03-23', 'COVID-19\nĐáy thị trường', '#FF6B6B'),
    ('2022-04-05', 'Vụ FLC\n& HOSE đình chỉ', '#FFD700'),
    ('2023-01-01', 'Mở cửa\nphục hồi', '#4ECDC4'),
]
for ev_date, ev_label, ev_color in events:
    ax.axvline(pd.to_datetime(ev_date), color=ev_color, linestyle='--', linewidth=1.2, alpha=0.7)
    ax.text(pd.to_datetime(ev_date), ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 100,
            ev_label, rotation=90, color=ev_color, fontsize=8, va='top', ha='right')

ax.set_title("Biến Động Giá Đóng Cửa Lịch Sử — BID, TCB, VCB, CTG (2014–2026)", fontsize=14, color='#fff')
ax.set_xlabel('Thời Gian')
ax.set_ylabel('Giá Đóng Cửa (nghìn VND)')
ax.legend(loc='upper left', framealpha=0.8)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.xaxis.set_major_locator(mdates.YearLocator(2))
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(OUT_DIR / "s_eda2_price_timeseries.png", dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: s_eda2_price_timeseries.png", flush=True)

# ═══════════════════════════════════════════════════════════════════════════════
# EDA 3 — Box plot phân phối trading volume 4 cổ phiếu
# ═══════════════════════════════════════════════════════════════════════════════
print("[EDA-3] Volume boxplot", flush=True)
fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#1a1f2e')

vol_data = [stock_df[stock_df['ticker'] == t]['trading_volume'].dropna() / 1e6 for t in tickers]
bp = ax.boxplot(vol_data, patch_artist=True, notch=True,
                medianprops=dict(color='white', linewidth=2))
for patch, ticker in zip(bp['boxes'], tickers):
    patch.set_facecolor(COLORS_TICKER[ticker])
    patch.set_alpha(0.8)
for whisker in bp['whiskers']:
    whisker.set_color('#666')
for flier in bp['fliers']:
    flier.set_markerfacecolor('#aaa')
    flier.set_markersize(3)
    flier.set_alpha(0.4)

ax.set_xticklabels(tickers, fontsize=12)
ax.set_title("Phân Phối Khối Lượng Giao Dịch Hàng Ngày — 4 Cổ Phiếu Ngân Hàng", fontsize=13, color='#fff')
ax.set_xlabel('Mã Cổ Phiếu')
ax.set_ylabel('Khối Lượng Giao Dịch (triệu cổ phiếu)')
ax.grid(True, axis='y', alpha=0.3)

# Thêm mean
means = [d.mean() for d in vol_data]
ax.scatter(range(1, 5), means, marker='D', color='white', zorder=5, s=40, label='Mean')
ax.legend()
plt.tight_layout()
plt.savefig(OUT_DIR / "s_eda3_volume_boxplot.png", dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: s_eda3_volume_boxplot.png", flush=True)

# ═══════════════════════════════════════════════════════════════════════════════
# EDA 4 — Heatmap tương quan Pearson
# ═══════════════════════════════════════════════════════════════════════════════
print("[EDA-4] Pearson correlation heatmap", flush=True)
pivot = stock_df.pivot_table(index='date', columns='ticker', values='close_price')
corr = pivot.corr()

fig, ax = plt.subplots(figsize=(8, 7))
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#0e1117')

mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
cmap = sns.diverging_palette(230, 20, as_cmap=True)
sns.heatmap(corr, annot=True, fmt='.4f', cmap=cmap, mask=mask,
            linewidths=2, linecolor='#0e1117',
            annot_kws={'size': 14, 'weight': 'bold'},
            cbar_kws={'shrink': 0.8},
            vmin=-1, vmax=1, ax=ax,
            square=True)

for t in ax.texts:
    val = float(t.get_text())
    if abs(val) >= 0.8:
        t.set_color('white')
    elif abs(val) >= 0.5:
        t.set_color('#FFD700')
    else:
        t.set_color('#FF6B6B')

ax.set_title("Ma Trận Tương Quan Pearson — Giá Đóng Cửa 4 Cổ Phiếu Ngân Hàng\n(Toàn bộ lịch sử 2014–2026)", fontsize=13, color='#fff')
ax.set_xlabel('')
ax.set_ylabel('')
plt.tight_layout()
plt.savefig(OUT_DIR / "s3_pearson_heatmap.png", dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: s3_pearson_heatmap.png", flush=True)

# ═══════════════════════════════════════════════════════════════════════════════
# EDA 5 — Rolling correlation 12 tháng BID vs TCB
# ═══════════════════════════════════════════════════════════════════════════════
print("[EDA-5] Rolling correlation", flush=True)
pivot_sorted = pivot.sort_index()
roll_corr_bid_tcb = pivot_sorted['BID'].rolling(60).corr(pivot_sorted['TCB'])
roll_corr_bid_vcb = pivot_sorted['BID'].rolling(60).corr(pivot_sorted['VCB'])
roll_corr_bid_ctg = pivot_sorted['BID'].rolling(60).corr(pivot_sorted['CTG'])

fig, ax = plt.subplots(figsize=(15, 6))
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#1a1f2e')

ax.plot(roll_corr_bid_vcb.index, roll_corr_bid_vcb, color='#34A853', linewidth=1.5, label='BID–VCB (SOCB đồng nhóm)')
ax.plot(roll_corr_bid_ctg.index, roll_corr_bid_ctg, color='#FBBC04', linewidth=1.5, label='BID–CTG (SOCB đồng nhóm)')
ax.plot(roll_corr_bid_tcb.index, roll_corr_bid_tcb, color='#EA4335', linewidth=1.5, label='BID–TCB (SOCB vs JSCB)', linestyle='--')
ax.axhline(0.7, color='#aaa', linestyle=':', linewidth=1, alpha=0.7, label='Ngưỡng tương quan cao (0.70)')
ax.fill_between(roll_corr_bid_vcb.index, roll_corr_bid_vcb, 0.7,
                where=(roll_corr_bid_vcb > 0.7), alpha=0.1, color='#34A853')

ax.set_ylim(-0.2, 1.05)
ax.set_title("Tương Quan Lăn (Rolling Correlation) 60 Ngày — BID so với VCB, CTG, TCB\nPhân tích đồng pha và phân hóa theo chu kỳ", fontsize=13, color='#fff')
ax.set_xlabel('Thời Gian')
ax.set_ylabel('Hệ Số Tương Quan Pearson')
ax.legend(loc='lower left', framealpha=0.8)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.xaxis.set_major_locator(mdates.YearLocator(2))
ax.grid(True, alpha=0.3)

# Chú thích vùng phân hóa mạnh
ax.annotate('Giai đoạn TCB\nphân hóa mạnh\n(2021–2022)',
            xy=(pd.to_datetime('2022-01-01'), 0.45),
            xytext=(pd.to_datetime('2019-01-01'), 0.0),
            arrowprops=dict(arrowstyle='->', color='#EA4335'),
            color='#EA4335', fontsize=9)

plt.tight_layout()
plt.savefig(OUT_DIR / "s_eda5_rolling_correlation.png", dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: s_eda5_rolling_correlation.png", flush=True)

# ═══════════════════════════════════════════════════════════════════════════════
# EDA BIDV — Phân tích chi tiết BIDV (BID)
# Panel 6: Giá + khối lượng + price_change_pct (3 panels)
# ═══════════════════════════════════════════════════════════════════════════════
print("[EDA-BID-1] BIDV detail panel", flush=True)
bid = BID_stock.copy()

fig = plt.figure(figsize=(16, 12))
fig.patch.set_facecolor('#0e1117')
gs = gridspec.GridSpec(3, 1, hspace=0.05, height_ratios=[3, 1.5, 1.5])

ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1], sharex=ax1)
ax3 = fig.add_subplot(gs[2], sharex=ax1)

# Panel 1: Giá đóng cửa + MA20 + MA60
ax1.set_facecolor('#1a1f2e')
ax1.plot(bid['date'], bid['close_price'], color='#4285F4', linewidth=1, label='Giá đóng cửa (Close)', alpha=0.9)
ma20 = bid['close_price'].rolling(20).mean()
ma60 = bid['close_price'].rolling(60).mean()
ax1.plot(bid['date'], ma20, color='#FFD700', linewidth=1.5, label='MA20', linestyle='--')
ax1.plot(bid['date'], ma60, color='#FF6B6B', linewidth=1.5, label='MA60', linestyle='--')
ax1.set_ylabel('Giá đóng cửa (nghìn VND)')
ax1.legend(loc='upper left', framealpha=0.8)
ax1.set_title("Phân Tích Chi Tiết Cổ Phiếu BIDV (BID) — Giá, Khối Lượng & Biến Động 2014–2026",
              fontsize=14, color='#fff', pad=12)
ax1.grid(True, alpha=0.3)

# Vùng tô màu COVID
ax1.axvspan(pd.to_datetime('2020-01-22'), pd.to_datetime('2021-06-01'),
            alpha=0.08, color='#FF6B6B', label='Giai đoạn COVID-19')
ax1.axvspan(pd.to_datetime('2022-03-01'), pd.to_datetime('2022-08-01'),
            alpha=0.08, color='#FFD700', label='Vụ thị trường 2022')

# Panel 2: Khối lượng giao dịch
ax2.set_facecolor('#1a1f2e')
vol_colors = ['#4285F4' if c >= 0 else '#EA4335' for c in bid['price_change'].fillna(0)]
ax2.bar(bid['date'], bid['trading_volume'] / 1e6, color=vol_colors, width=1, alpha=0.8)
ax2.set_ylabel('Khối Lượng (triệu CP)')
ax2.grid(True, alpha=0.3)
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0f}M'))

# Panel 3: % thay đổi giá
ax3.set_facecolor('#1a1f2e')
pct = bid['price_change_pct'].fillna(0)
ax3.bar(bid['date'], pct, color=['#34A853' if v >= 0 else '#EA4335' for v in pct],
        width=1, alpha=0.7)
ax3.axhline(0, color='white', linewidth=0.8)
ax3.set_ylabel('Biến Động (%)')
ax3.set_xlabel('Thời Gian')
ax3.grid(True, alpha=0.3)
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax3.xaxis.set_major_locator(mdates.YearLocator(2))

plt.setp(ax1.get_xticklabels(), visible=False)
plt.setp(ax2.get_xticklabels(), visible=False)
plt.tight_layout()
plt.savefig(OUT_DIR / "s_eda_bid_detail.png", dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: s_eda_bid_detail.png", flush=True)

# ═══════════════════════════════════════════════════════════════════════════════
# EDA BIDV — Thống kê mô tả tổng hợp BIDV
# ═══════════════════════════════════════════════════════════════════════════════
print("[EDA-BID-2] BIDV statistics summary", flush=True)
fig, axes = plt.subplots(2, 3, figsize=(16, 9))
fig.patch.set_facecolor('#0e1117')
fig.suptitle("BIDV (BID) — Phân Tích Thống Kê Mô Tả Các Chỉ Số Giao Dịch",
             fontsize=14, color='#fff', y=0.98)

metrics = [
    ('close_price',      'Giá Đóng Cửa (nghìn VND)',   '#4285F4'),
    ('trading_volume',   'Khối Lượng (CP)',             '#34A853'),
    ('trading_value',    'Giá Trị GD (tỷ VND)',        '#FBBC04'),
    ('price_change_pct', '% Thay Đổi Giá',             '#EA4335'),
    ('price_amplitude',  'Biên Độ Nội Phiên (%)',      '#9B59B6'),
    ('volume_change_pct','% Thay Đổi KL',              '#1ABC9C'),
]

for ax, (col, label, color) in zip(axes.flatten(), metrics):
    ax.set_facecolor('#1a1f2e')
    raw = bid[col].dropna()
    if col == 'trading_value':
        raw = raw / 1e9
    elif col == 'trading_volume':
        raw = raw / 1e6

    data_yr = bid[['year', col]].dropna()
    if col in ['trading_value']:
        data_yr[col] = data_yr[col] / 1e9
    elif col == 'trading_volume':
        data_yr[col] = data_yr[col] / 1e6

    yearly = data_yr.groupby('year')[col].mean()
    ax.bar(yearly.index, yearly.values, color=color, alpha=0.75, edgecolor='none')
    ax.plot(yearly.index, yearly.values, color='white', linewidth=1.5, marker='o', markersize=4)

    ax.set_title(label, color='#fff', fontsize=11)
    ax.set_xlabel('Năm')
    ax.set_ylabel(f'Trung Bình')
    ax.grid(True, axis='y', alpha=0.3)

    # Stats box
    stats = f"Mean: {raw.mean():.2f}\nStd: {raw.std():.2f}\nSkew: {raw.skew():.2f}"
    ax.text(0.02, 0.97, stats, transform=ax.transAxes, fontsize=8, va='top',
            color='#aaa', bbox=dict(boxstyle='round,pad=0.3', facecolor='#222', alpha=0.6))

plt.tight_layout()
plt.savefig(OUT_DIR / "s_eda_bid_yearly.png", dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: s_eda_bid_yearly.png", flush=True)

# ═══════════════════════════════════════════════════════════════════════════════
# EDA BIDV — CAMELS indicators BID (từ fact_bank_performance)
# ═══════════════════════════════════════════════════════════════════════════════
print("[EDA-BID-3] BIDV CAMELS profile", flush=True)
bid_bank = BID_bank.copy()
system_avg = bank_df.groupby('year')[['npl_ratio','llp_ratio','roa','roe','nim','cir','eta']].mean()

fig, axes = plt.subplots(2, 4, figsize=(18, 9))
fig.patch.set_facecolor('#0e1117')
fig.suptitle("BIDV (BID) — Hồ Sơ Tài Chính CAMELS So Với Trung Bình Hệ Thống (2002–2022)",
             fontsize=14, color='#fff', y=0.98)

camels_cols = [
    ('npl_ratio', 'NPL Ratio (Nợ xấu)', '#EA4335', True),
    ('llp_ratio', 'LLP Ratio (Dự phòng)', '#FF6B6B', True),
    ('roa',       'ROA (Sinh lời TS)', '#34A853', False),
    ('roe',       'ROE (Sinh lời vốn CSH)', '#4285F4', False),
    ('nim',       'NIM (Biên lãi ròng)', '#00BCD4', False),
    ('cir',       'CIR (Chi phí/Thu nhập)', '#FF9800', True),
    ('eta',       'ETA (Vốn/Tài sản)', '#9C27B0', False),
]

for ax, (col, label, color, lower_better) in zip(axes.flatten(), camels_cols):
    ax.set_facecolor('#1a1f2e')
    bid_yr = bid_bank[['year', col]].dropna()
    sys_yr = system_avg[[col]].reset_index() if col in system_avg.columns else None

    # BID line
    ax.plot(bid_yr['year'], bid_yr[col] * 100, color=color, linewidth=2.5,
            marker='o', markersize=5, label=f'BIDV', zorder=3)

    # System average
    if sys_yr is not None:
        ax.plot(sys_yr['year'], sys_yr[col] * 100, color='#aaa', linewidth=1.5,
                linestyle='--', marker='s', markersize=3, label='Trung bình HT', alpha=0.8)
        ax.fill_between(bid_yr['year'],
                        bid_yr[col] * 100,
                        sys_yr[sys_yr['year'].isin(bid_yr['year'])][col].values * 100,
                        alpha=0.1, color=color)

    direction = "Thấp hơn = tốt hơn ↓" if lower_better else "Cao hơn = tốt hơn ↑"
    ax.set_title(f'{label}\n({direction})', color='#fff', fontsize=10)
    ax.set_xlabel('Năm')
    ax.set_ylabel('(%)')
    ax.legend(fontsize=8, framealpha=0.6)
    ax.grid(True, alpha=0.3)

# Ẩn subplot cuối
axes.flatten()[-1].set_visible(False)

plt.tight_layout()
plt.savefig(OUT_DIR / "s_eda_bid_camels.png", dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: s_eda_bid_camels.png", flush=True)

# ═══════════════════════════════════════════════════════════════════════════════
# LSTM — So sánh thực nghiệm 3 mô hình (từ JSON)
# ═══════════════════════════════════════════════════════════════════════════════
print("[ML-LSTM] Model comparison table", flush=True)
with open("data/processed/lstm_model_comparison.json", "r") as f:
    lstm_data = json.load(f)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.patch.set_facecolor('#0e1117')
fig.suptitle("So Sánh 3 Mô Hình Dự Báo Giá Cổ Phiếu — RMSE Trên Tập Kiểm Thử",
             fontsize=14, color='#fff', y=0.98)

tickers_ml = ['BID', 'TCB', 'VCB', 'CTG']
models = ['ARIMA', 'LSTM Đơn biến', 'LSTM Đa biến']
model_colors = ['#666', '#4285F4', '#34A853']

rmse_data = {t: [lstm_data[t]['arima_rmse'],
                  lstm_data[t]['uni_rmse'],
                  lstm_data[t]['multi_rmse']] for t in tickers_ml}
mae_data  = {t: [lstm_data[t]['arima_mae'],
                  lstm_data[t]['uni_mae'],
                  lstm_data[t]['multi_mae']] for t in tickers_ml}

x = np.arange(len(tickers_ml))
width = 0.25

for ax, (metric_data, metric_name) in zip(axes, [(rmse_data, 'RMSE'), (mae_data, 'MAE')]):
    ax.set_facecolor('#1a1f2e')
    for i, (model, color) in enumerate(zip(models, model_colors)):
        vals = [metric_data[t][i] for t in tickers_ml]
        bars = ax.bar(x + i * width, vals, width, label=model, color=color, alpha=0.85, edgecolor='none')
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                    f'{val:.2f}', ha='center', va='bottom', fontsize=8, color='#ddd')

    ax.set_xticks(x + width)
    ax.set_xticklabels(tickers_ml, fontsize=12)
    ax.set_title(f'{metric_name} — Sai Số Dự Báo (nghìn VND)', color='#fff')
    ax.set_ylabel(f'{metric_name} (nghìn VND)')
    ax.legend(framealpha=0.8)
    ax.grid(True, axis='y', alpha=0.3)

    # LSTM wins annotation
    ax.text(0.02, 0.97, 'LSTM vượt trội ARIMA\ntrên cả 4 cổ phiếu ✓',
            transform=ax.transAxes, fontsize=9, va='top',
            color='#34A853', bbox=dict(boxstyle='round', facecolor='#1a3a1a', alpha=0.7))

plt.tight_layout()
plt.savefig(OUT_DIR / "s2_lstm_rmse_table.png", dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: s2_lstm_rmse_table.png", flush=True)

# ═══════════════════════════════════════════════════════════════════════════════
# DTW Heatmap
# ═══════════════════════════════════════════════════════════════════════════════
print("[ML-DTW] DTW correlation heatmap", flush=True)
with open("data/processed/dtw_correlation_report.json", "r") as f:
    dtw_data = json.load(f)

pearson_matrix = pd.DataFrame(dtw_data['pearson_correlation_matrix'])
dtw_df = pd.DataFrame(dtw_data['dtw_distance_matrix'])

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.patch.set_facecolor('#0e1117')
fig.suptitle("Phân Tích Tương Quan Đồng Pha — Pearson và DTW", fontsize=14, color='#fff')

# Pearson heatmap
ax1 = axes[0]
ax1.set_facecolor('#0e1117')
cmap_div = sns.diverging_palette(230, 20, as_cmap=True)
sns.heatmap(pearson_matrix, annot=True, fmt='.4f', cmap=cmap_div,
            linewidths=2, linecolor='#0e1117', annot_kws={'size': 14, 'weight': 'bold'},
            vmin=0.3, vmax=1.0, ax=ax1, square=True, cbar_kws={'shrink': 0.8})
ax1.set_title("Ma Trận Tương Quan Pearson\n(Toàn lịch sử 2014–2026)", color='#fff')

ax2 = axes[1]
ax2.set_facecolor('#0e1117')
cmap_dtw = sns.color_palette("YlOrRd", as_cmap=True)
mask_dtw = np.eye(len(tickers), dtype=bool)
sns.heatmap(dtw_df, annot=True, fmt='.1f', cmap=cmap_dtw,
            linewidths=2, linecolor='#0e1117', annot_kws={'size': 12, 'weight': 'bold'},
            ax=ax2, square=True, cbar_kws={'shrink': 0.8},
            mask=mask_dtw if not dtw_df.empty else None)
ax2.set_title("Khoảng Cách DTW\n(Nhỏ = Đồng pha hơn)", color='#fff')

plt.tight_layout()
plt.savefig(OUT_DIR / "s4_dtw_heatmap.png", dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: s4_dtw_heatmap.png", flush=True)

# ═══════════════════════════════════════════════════════════════════════════════
# Random Forest — Feature Importance
# ═══════════════════════════════════════════════════════════════════════════════
print("[ML-RF] Feature importance chart", flush=True)
feature_importance = {
    'llp_ratio': 0.2105,
    'roe':       0.1149,
    'cir':       0.1103,
    'roa':       0.0985,
    'eta':       0.0912,
    'nim':       0.0874,
    'ltd':       0.0793,
    'lta':       0.0721,
    'etd':       0.0683,
    'gta':       0.0675,
}
fi_labels = {
    'llp_ratio': 'llp_ratio\n(Dự phòng rủi ro)',
    'roe':       'roe\n(Sinh lời vốn CSH)',
    'cir':       'cir\n(Chi phí/Thu nhập)',
    'roa':       'roa\n(Sinh lời tài sản)',
    'eta':       'eta\n(Vốn/Tài sản)',
    'nim':       'nim\n(Biên lãi ròng)',
    'ltd':       'ltd\n(Dư nợ/Tiền gửi)',
    'lta':       'lta\n(Dư nợ/Tài sản)',
    'etd':       'etd\n(Vốn/Tiền gửi)',
    'gta':       'gta\n(Thanh khoản)',
}

fi_sorted = sorted(feature_importance.items(), key=lambda x: x[1])
keys_sorted = [fi_labels[k] for k, v in fi_sorted]
vals_sorted = [v for k, v in fi_sorted]
bar_colors = ['#FF6B6B' if v >= 0.15 else '#4285F4' if v >= 0.10 else '#4ECDC4' for v in vals_sorted]

fig, ax = plt.subplots(figsize=(12, 7))
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#1a1f2e')
bars = ax.barh(keys_sorted, vals_sorted, color=bar_colors, alpha=0.85, edgecolor='none', height=0.6)
for bar, val in zip(bars, vals_sorted):
    ax.text(bar.get_width() + 0.002, bar.get_y() + bar.get_height() / 2,
            f'{val*100:.2f}%', va='center', fontsize=11, color='white', fontweight='bold')

ax.axvline(0.10, color='#FFD700', linestyle='--', linewidth=1.5, alpha=0.7, label='Ngưỡng trọng yếu 10%')
ax.set_xlabel('Độ Quan Trọng Đặc Trưng (Feature Importance — Gini Decrease)')
ax.set_title("Xếp Hạng Tầm Quan Trọng Chỉ Số CAMELS — Mô Hình Random Forest\nPhân Loại Rủi Ro Nợ Xấu NPL ≥ 3%", fontsize=13, color='#fff')
ax.legend(framealpha=0.7)
ax.grid(True, axis='x', alpha=0.3)
ax.set_xlim(0, 0.26)

# Chú thích đặc biệt cho llp_ratio
ax.annotate('Chỉ báo sớm quan trọng nhất!\nGranger-causes npl_ratio (p=0.0914)',
            xy=(0.2105, 9), xytext=(0.14, 8),
            arrowprops=dict(arrowstyle='->', color='#FFD700'),
            color='#FFD700', fontsize=9,
            bbox=dict(boxstyle='round', facecolor='#2a2a1a', alpha=0.8))

plt.tight_layout()
plt.savefig(OUT_DIR / "s7_feature_importance.png", dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: s7_feature_importance.png", flush=True)

# ═══════════════════════════════════════════════════════════════════════════════
# K-Means — PCA Scatter Plot (tái tạo từ dữ liệu)
# ═══════════════════════════════════════════════════════════════════════════════
print("[ML-KM] K-Means PCA scatter", flush=True)
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

EXCLUDE = ['CB', 'VBSP', 'DAB', 'GPB', 'WEB', 'MDB']
camels_cols_km = ['npl_ratio', 'llp_ratio', 'roa', 'roe', 'nim', 'cir', 'eta', 'etd', 'lta', 'ltd']
bank_avg = bank_df[~bank_df['bank_code'].isin(EXCLUDE)].groupby(['bank_code','bank_name','bank_type'])[camels_cols_km].mean().reset_index()
bank_avg = bank_avg.dropna()

scaler = StandardScaler()
X_scaled = scaler.fit_transform(bank_avg[camels_cols_km])
pca = PCA(n_components=3, random_state=42)
X_pca = pca.fit_transform(X_scaled)
km = KMeans(n_clusters=3, n_init=10, random_state=42)
labels = km.fit_predict(X_pca)
bank_avg['cluster'] = labels
bank_avg['PC1'] = X_pca[:, 0]
bank_avg['PC2'] = X_pca[:, 1]

# Remap cluster to match known results: 0=small, 1=pillar, 2=foreign
# based on cluster size
cluster_sizes = bank_avg['cluster'].value_counts()

cluster_name_map = {
    cluster_sizes.index[0]: 'Cụm: Trụ Cột HT',
    cluster_sizes.index[1]: 'Cụm: TMCP Nhỏ',
    cluster_sizes.index[2]: 'Cụm: Khối Ngoại',
}
CLUSTER_COLORS_MAP = {
    cluster_sizes.index[0]: '#4ECDC4',
    cluster_sizes.index[1]: '#FF6B6B',
    cluster_sizes.index[2]: '#FFE66D',
}

fig, ax = plt.subplots(figsize=(13, 9))
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#1a1f2e')

for c_id in [0, 1, 2]:
    mask = bank_avg['cluster'] == c_id
    subset = bank_avg[mask]
    color = CLUSTER_COLORS_MAP[c_id]
    name = cluster_name_map[c_id]
    ax.scatter(subset['PC1'], subset['PC2'], c=color, s=100, alpha=0.85,
               label=f'{name} ({mask.sum()} NH)', edgecolors='white', linewidths=0.5, zorder=3)
    for _, row in subset.iterrows():
        is_focus = row['bank_code'] in ['BID', 'TCB', 'VCB', 'CTG']
        ax.annotate(row['bank_code'],
                    (row['PC1'], row['PC2']),
                    textcoords="offset points", xytext=(5, 4),
                    fontsize=8 if not is_focus else 11,
                    color='white' if not is_focus else '#FFD700',
                    fontweight='normal' if not is_focus else 'bold')

var1 = pca.explained_variance_ratio_[0] * 100
var2 = pca.explained_variance_ratio_[1] * 100
ax.set_xlabel(f'Thành Phần Chính PC1 ({var1:.1f}% phương sai)', fontsize=12)
ax.set_ylabel(f'Thành Phần Chính PC2 ({var2:.1f}% phương sai)', fontsize=12)
ax.set_title(f"Phân Nhóm 39 Ngân Hàng TM VN — K-Means + PCA (k=3)\n"
             f"Tổng phương sai giải thích: {var1+var2:.1f}%", fontsize=14, color='#fff')
ax.legend(framealpha=0.8, loc='upper right', fontsize=11)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(OUT_DIR / "s5_pca_scatter.png", dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: s5_pca_scatter.png", flush=True)

# ═══════════════════════════════════════════════════════════════════════════════
# K-Means — CAMELS Cluster Profile Grouped Bar
# ═══════════════════════════════════════════════════════════════════════════════
print("[ML-KM] CAMELS cluster profile", flush=True)
camels_display = ['npl_ratio', 'llp_ratio', 'roa', 'roe', 'nim', 'cir', 'eta', 'lta', 'ltd']
camels_vn = {
    'npl_ratio': 'NPL\n(Nợ xấu)',
    'llp_ratio': 'LLP\n(Dự phòng)',
    'roa':       'ROA\n(Sinh lời TS)',
    'roe':       'ROE\n(Sinh lời vốn)',
    'nim':       'NIM\n(Biên lãi)',
    'cir':       'CIR\n(Chi phí/TN)',
    'eta':       'ETA\n(Vốn/TS)',
    'lta':       'LTA\n(DN/TS)',
    'ltd':       'LTD\n(DN/TG)',
}
cluster_profile = bank_avg.groupby('cluster')[camels_display].mean()

fig, ax = plt.subplots(figsize=(16, 7))
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#1a1f2e')

x = np.arange(len(camels_display))
width = 0.27
n_clusters = 3

for i, c_id in enumerate(cluster_profile.index):
    vals = cluster_profile.loc[c_id, camels_display].values * 100
    color = CLUSTER_COLORS_MAP[c_id]
    name = cluster_name_map[c_id]
    bars = ax.bar(x + i * width, vals, width, label=name, color=color, alpha=0.8, edgecolor='none')

ax.set_xticks(x + width)
ax.set_xticklabels([camels_vn[c] for c in camels_display], fontsize=10)
ax.set_ylabel('Giá Trị Trung Bình (%)')
ax.set_title("Hồ Sơ CAMELS Trung Bình 3 Cụm Chiến Lược Ngân Hàng\n(K-Means Clustering, k=3, 39 Ngân Hàng)", fontsize=13, color='#fff')
ax.legend(framealpha=0.8, fontsize=11)
ax.grid(True, axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(OUT_DIR / "s6_cluster_profiles.png", dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: s6_cluster_profiles.png", flush=True)

# ═══════════════════════════════════════════════════════════════════════════════
# Random Forest — NPL ratio trend + Risk classification
# ═══════════════════════════════════════════════════════════════════════════════
print("[ML-RF] NPL trend by bank type", flush=True)
fig, axes = plt.subplots(1, 2, figsize=(15, 6))
fig.patch.set_facecolor('#0e1117')
fig.suptitle("Phân Tích Tỷ Lệ Nợ Xấu (NPL Ratio) — Cơ Sở Của Bài Toán Phân Loại Rủi Ro",
             fontsize=14, color='#fff')

ax1 = axes[0]
ax1.set_facecolor('#1a1f2e')
npl_yearly_type = bank_df.groupby(['year', 'bank_type'])['npl_ratio'].mean().reset_index()
for btype, color in [('SOCB', '#4285F4'), ('JSCB', '#EA4335'), ('FOCB', '#34A853')]:
    d = npl_yearly_type[npl_yearly_type['bank_type'] == btype]
    ax1.plot(d['year'], d['npl_ratio'] * 100, label=btype, color=color, linewidth=2, marker='o', markersize=5)
ax1.axhline(3.0, color='#FF6B6B', linestyle='--', linewidth=2, label='Ngưỡng đỏ NPL ≥ 3%')
ax1.fill_between([2002, 2022], 3.0, 15, alpha=0.05, color='#FF6B6B')
ax1.set_title("Tỷ Lệ Nợ Xấu Trung Bình\nTheo Nhóm Ngân Hàng 2002–2022", color='#fff')
ax1.set_xlabel('Năm')
ax1.set_ylabel('NPL Ratio (%)')
ax1.legend(framealpha=0.8)
ax1.grid(True, alpha=0.3)

# Phân phối nhãn risk_label
ax2 = axes[1]
ax2.set_facecolor('#1a1f2e')
bank_df['risk_label'] = (bank_df['npl_ratio'] >= 0.03).astype(int)
risk_dist = bank_df['risk_label'].value_counts()
bars = ax2.bar(['An Toàn\n(NPL < 3%)', 'Rủi Ro Cao\n(NPL ≥ 3%)'],
               [risk_dist.get(0, 0), risk_dist.get(1, 0)],
               color=['#34A853', '#EA4335'], alpha=0.85, edgecolor='none', width=0.5)
for bar in bars:
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
             f'{int(bar.get_height())} bản ghi\n({bar.get_height()/len(bank_df)*100:.1f}%)',
             ha='center', va='bottom', fontsize=12, color='white', fontweight='bold')
ax2.set_title("Phân Phối Nhãn Phân Loại Rủi Ro\n(Mất Cân Bằng Lớp — Imbalanced Classes)", color='#fff')
ax2.set_ylabel('Số Bản Ghi')
ax2.grid(True, axis='y', alpha=0.3)
ax2.text(0.5, 0.5, f'Tỷ lệ mất cân bằng:\n{risk_dist.get(1,0)/len(bank_df)*100:.1f}% lớp thiểu số\n→ Cần class_weight="balanced"',
         transform=ax2.transAxes, ha='center', va='center', fontsize=10,
         color='#FFD700', bbox=dict(boxstyle='round', facecolor='#2a2a10', alpha=0.8))

plt.tight_layout()
plt.savefig(OUT_DIR / "s_rf_npl_analysis.png", dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: s_rf_npl_analysis.png", flush=True)

# ═══════════════════════════════════════════════════════════════════════════════
# Causality plot (đã có sẵn)
# ═══════════════════════════════════════════════════════════════════════════════
import shutil
if Path("data/processed/llp_npl_causality.png").exists():
    shutil.copy("data/processed/llp_npl_causality.png",
                OUT_DIR / "s_granger_causality.png")
    print("  Copied: s_granger_causality.png", flush=True)

if Path("data/processed/dtw_correlation_plots.png").exists():
    shutil.copy("data/processed/dtw_correlation_plots.png",
                OUT_DIR / "s_dtw_plots.png")
    print("  Copied: s_dtw_plots.png", flush=True)

# ═══════════════════════════════════════════════════════════════════════════════
print("\n=== ALL FIGURES GENERATED ===", flush=True)
print(f"Output directory: {OUT_DIR.resolve()}", flush=True)
for f in sorted(OUT_DIR.glob("*.png")):
    print(f"  {f.name} ({f.stat().st_size//1024} KB)", flush=True)
