# -*- coding: utf-8 -*-
"""Script chup man hinh Streamlit Dashboard bang Playwright - v2"""
import asyncio
import sys
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

SCREENSHOTS_DIR = Path("docs/report/screenshots")
BASE_URL = "http://localhost:8501"

# Navigation labels EXACTLY as in app.py radio button options
NAV_OPTIONS = [
    "Tổng Quan Dự Án",
    "Phân Tích Khám Phá (EDA)",
    "Dự Báo Giá Cổ Phiếu (LSTM)",
    "Phân Nhóm Ngân Hàng (K-Means)",
    "Phân Loại Rủi Ro Tín Dụng (Random Forest)",
    "Trạng Thái Hệ Thống DWH",
    "Kết Luận & Nghiệm Thu",
    "Thông Tin Thêm (About)"
]


async def capture_screenshots():
    from playwright.async_api import async_playwright

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        print("Opening Streamlit...", flush=True)
        try:
            await page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        except Exception as e:
            print(f"Load: {e}", flush=True)
        await page.wait_for_timeout(5000)

        async def click_sidebar_option(label):
            """Click a radio button in sidebar by exact label"""
            try:
                # Streamlit radio labels are inside <label> or <div role='radiogroup'>
                locator = page.locator(f"label:has-text('{label}')").first
                await locator.click(timeout=8000)
                await page.wait_for_timeout(3500)
                print(f"  Navigated to: {label}", flush=True)
                return True
            except Exception as e:
                print(f"  Failed nav to '{label}': {type(e).__name__}", flush=True)
                # Try alternative: find by text in sidebar
                try:
                    await page.get_by_text(label, exact=True).first.click(timeout=5000)
                    await page.wait_for_timeout(3500)
                    return True
                except Exception:
                    return False

        async def click_inner_radio(label):
            """Click inner radio/selectbox on main content area"""
            try:
                await page.locator(f"label:has-text('{label}')").last.click(timeout=5000)
                await page.wait_for_timeout(2500)
                return True
            except Exception as e:
                print(f"  Inner radio failed for '{label}': {type(e).__name__}", flush=True)
                return False

        async def save_screenshot(filename, scroll_px=0):
            out_path = SCREENSHOTS_DIR / filename
            if scroll_px > 0:
                await page.evaluate(f"window.scrollTo(0, {scroll_px})")
                await page.wait_for_timeout(800)
            try:
                await page.screenshot(path=str(out_path), full_page=True)
                print(f"  SAVED: {filename}", flush=True)
                return True
            except Exception as e:
                print(f"  FAILED {filename}: {e}", flush=True)
                return False

        # ===== S10: DWH Status =====
        print("\n[S10] DWH Status", flush=True)
        await click_sidebar_option("Trạng Thái Hệ Thống DWH")
        await save_screenshot("s10_dwh_status.png")

        # ===== S1-S4: LSTM =====
        print("\n[S1] LSTM - Main view", flush=True)
        await click_sidebar_option("Dự Báo Giá Cổ Phiếu (LSTM)")
        await save_screenshot("s1_lstm_comparison_bid.png")

        # Try inner tabs for comparison
        print("\n[S2] LSTM - RMSE table (So sanh thuc nghiem)", flush=True)
        await click_sidebar_option("Dự Báo Giá Cổ Phiếu (LSTM)")
        await click_inner_radio("So sánh thực nghiệm")
        await save_screenshot("s2_lstm_rmse_table.png")

        print("\n[S3/S4] LSTM - Correlation", flush=True)
        await click_sidebar_option("Dự Báo Giá Cổ Phiếu (LSTM)")
        await click_inner_radio("Phân tích tương quan")
        await save_screenshot("s3_pearson_heatmap.png")
        await save_screenshot("s4_dtw_heatmap.png", scroll_px=1200)

        # ===== S5-S6: K-Means =====
        print("\n[S5] K-Means PCA scatter", flush=True)
        await click_sidebar_option("Phân Nhóm Ngân Hàng (K-Means)")
        await page.wait_for_timeout(5000)
        await save_screenshot("s5_pca_scatter.png")
        await save_screenshot("s6_cluster_profiles.png", scroll_px=1500)

        # ===== S7-S8: Random Forest =====
        print("\n[S7] RF Feature Importance", flush=True)
        await click_sidebar_option("Phân Loại Rủi Ro Tín Dụng (Random Forest)")
        await page.wait_for_timeout(5000)
        await save_screenshot("s7_feature_importance.png")
        await save_screenshot("s8_threshold_curve.png", scroll_px=1200)

        # ===== S9: EDA Individual Bank =====
        print("\n[S9] EDA Individual Bank", flush=True)
        await click_sidebar_option("Phân Tích Khám Phá (EDA)")
        await page.wait_for_timeout(3000)
        # Try to click inner radio for individual bank
        await click_inner_radio("Phân Tích Theo Từng Ngân Hàng")
        # Try to select VCB
        try:
            await page.locator("select").first.select_option("VCB")
            await page.wait_for_timeout(2000)
        except Exception:
            pass
        await save_screenshot("s9_individual_bank_vcb.png")

        await browser.close()
        print("\nAll done!", flush=True)


if __name__ == "__main__":
    asyncio.run(capture_screenshots())
