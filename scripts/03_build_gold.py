"""
Phase 3: Build the Gold layer using DuckDB SQL.
Aggregates the Silver data into business-level summary tables.
"""
import json
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DUCKDB_PATH = str(PROJECT_ROOT / "warehouse" / "warehouse.duckdb")
LOG_PATH = PROJECT_ROOT / "logs" / "row_counts.json"

print("[INFO] Connecting to DuckDB...")
con = duckdb.connect(DUCKDB_PATH)

# 1. Create Gold Schema
con.execute("CREATE SCHEMA IF NOT EXISTS gold;")

print("[INFO] Building gold.daily_sales...")
# 2. Aggregate: Daily Sales Summary
con.execute("""
    CREATE OR REPLACE TABLE gold.daily_sales AS
    SELECT 
        Order_Date,
        COUNT(DISTINCT Order_ID) as total_orders,
        SUM(Quantity) as total_items_sold,
        ROUND(SUM(Unit_Price_USD * Quantity * (1 - Discount_Percent/100)), 2) as total_revenue
    FROM silver.sales_cleaned
    WHERE Order_Status != 'CANCELLED'
    GROUP BY Order_Date
    ORDER BY Order_Date DESC;
""")

print("[INFO] Building gold.category_performance...")
# 3. Aggregate: Category Performance
con.execute("""
    CREATE OR REPLACE TABLE gold.category_performance AS
    SELECT 
        Product_Category,
        COUNT(Order_ID) as total_orders,
        SUM(Quantity) as total_items_sold,
        ROUND(AVG(Customer_Rating), 2) as average_rating
    FROM silver.sales_cleaned
    WHERE Order_Status != 'CANCELLED'
    GROUP BY Product_Category
    ORDER BY total_items_sold DESC;
""")

# 4. Get Gold row counts for the README
gold_daily_count = con.execute("SELECT COUNT(*) FROM gold.daily_sales").fetchone()[0]
gold_cat_count = con.execute("SELECT COUNT(*) FROM gold.category_performance").fetchone()[0]

con.close()
print(f"[VERIFY] gold.daily_sales rows: {gold_daily_count}")
print(f"[VERIFY] gold.category_performance rows: {gold_cat_count}")

# 5. Save metrics
existing = json.loads(LOG_PATH.read_text())
existing["gold_daily_sales_rows"] = gold_daily_count
existing["gold_category_rows"] = gold_cat_count
LOG_PATH.write_text(json.dumps(existing, indent=2))
print(f"[INFO] Phase 3 complete! Metrics saved to {LOG_PATH}")