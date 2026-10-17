"""
Phase 2: PySpark reads from PostgreSQL, cleans data, and writes to DuckDB (Silver).
"""
import os
os.environ['HADOOP_HOME'] = r'E:\hadoop'
import json
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, upper, trim, to_date, when, coalesce, lit

# ---------- Fix Windows Spark Python Issue ----------
import sys
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

# ---------- Config ----------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = PROJECT_ROOT / "logs" / "row_counts.json"
DUCKDB_PATH = str(PROJECT_ROOT / "warehouse" / "warehouse.duckdb")

PG_URL = "jdbc:postgresql://localhost:5432/etl_project"
PG_PROPS = {
    "user": "etl_user",
    "password": "etl_pass",
    "driver": "org.postgresql.Driver"
}

# ---------- 1. Setup Spark ----------
print("[INFO] Starting Spark Session...")
spark = SparkSession.builder \
    .appName("BronzeToSilver") \
    .master("local[*]") \
    .config("spark.jars.packages", "org.postgresql:postgresql:42.7.3") \
    .getOrCreate()

# ---------- 2. Extract ----------
print("[INFO] Reading from PostgreSQL...")
df_raw = spark.read.jdbc(url=PG_URL, table="raw_sales", properties=PG_PROPS)

# ---------- 3. Transform (Clean) ----------
print("[INFO] Cleaning data...")

df_clean = df_raw \
    .dropDuplicates() \
    .withColumn("Order_Date", to_date(col("Order_Date"), "yyyy-MM-dd")) \
    .withColumn("Quantity", col("Quantity").cast("integer")) \
    .withColumn("Unit_Price_USD", col("Unit_Price_USD").cast("double")) \
    .withColumn("Discount_Percent", col("Discount_Percent").cast("double")) \
    .withColumn("Customer_Rating", col("Customer_Rating").cast("double")) \
    .withColumn("Payment_Method", upper(trim(col("Payment_Method")))) \
    .withColumn("Country", upper(trim(col("Country")))) \
    .withColumn("Shipping_City", trim(col("Shipping_City"))) \
    .withColumn("Order_Status", upper(trim(col("Order_Status")))) \
    .withColumn("Discount_Percent", coalesce(col("Discount_Percent"), lit(0.0))) \
    .filter(col("Quantity") > 0)

# Get Silver row count
silver_count = df_clean.count()
print(f"[VERIFY] Silver row count after cleaning: {silver_count}")

# ---------- 4. Load (to DuckDB) ----------
print("[INFO] Writing to DuckDB Silver layer...")
# Convert to Pandas (safe for 12k rows) to push into DuckDB
df_pandas = df_clean.toPandas()

import duckdb
con = duckdb.connect(DUCKDB_PATH)
con.execute("CREATE SCHEMA IF NOT EXISTS silver;")
con.execute("CREATE OR REPLACE TABLE silver.sales_cleaned AS SELECT * FROM df_pandas")
con.close()

print("[INFO] Successfully loaded into DuckDB (silver.sales_cleaned)")

# ---------- 5. Save Metrics ----------
existing = json.loads(LOG_PATH.read_text())
existing["silver_row_count"] = silver_count
LOG_PATH.write_text(json.dumps(existing, indent=2))
print(f"[INFO] Updated metrics written to {LOG_PATH}")

spark.stop()
print("[INFO] Phase 2 complete!")