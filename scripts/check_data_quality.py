"""Script to query BigQuery and check data quality of fact_stock_daily_metrics.
"""

from __future__ import annotations

import os
import sys
from dotenv import load_dotenv

# Đảm bảo console in ra tiếng Việt chuẩn UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.utils.bigquery_client import get_bigquery_client, get_full_table_id
from src.utils.config import load_config


def run_checks():
    load_dotenv()
    config = load_config()
    client = get_bigquery_client()
    table_id = get_full_table_id("fact_stock_daily_metrics")
    stock_table_id = get_full_table_id("dim_stock")

    print("==================================================================")
    print("   KIỂM TRA CHẤT LƯỢNG DỮ LIỆU FACT_STOCK_DAILY_METRICS")
    print("==================================================================")

    # 1. Tổng số dòng
    query_total = f"SELECT COUNT(*) as total_rows FROM `{table_id}`"
    res_total = client.query(query_total).to_dataframe(create_bqstorage_client=False)
    total_rows = res_total.loc[0, "total_rows"]
    print(f"\n1. Tổng số dòng trong bảng fact_stock_daily_metrics: {total_rows} (Kỳ vọng: 11835)")

    # 2. Số dòng theo từng mã cổ phiếu
    query_stocks = f"""
        SELECT s.ticker, COUNT(f.date_key) as row_count, MIN(f.date_key) as min_date, MAX(f.date_key) as max_date
        FROM `{table_id}` f
        JOIN `{stock_table_id}` s ON f.stock_key = s.stock_key
        GROUP BY s.ticker
        ORDER BY s.ticker
    """
    res_stocks = client.query(query_stocks).to_dataframe(create_bqstorage_client=False)
    print("\n2. Thống kê theo từng mã cổ phiếu:")
    print(res_stocks.to_string(index=False))

    # 3. Kiểm tra giá trị Close Price không âm và không Null
    query_check_price = f"""
        SELECT 
            COUNTIF(close_price IS NULL) as null_close,
            COUNTIF(close_price <= 0) as invalid_close
        FROM `{table_id}`
    """
    res_check_price = client.query(query_check_price).to_dataframe(create_bqstorage_client=False)
    print("\n3. Kiểm định tính hợp lệ của giá đóng cửa (Close Price):")
    print(res_check_price.to_string(index=False))


if __name__ == "__main__":
    run_checks()
