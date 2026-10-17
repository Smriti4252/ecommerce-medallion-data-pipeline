"""
Phase 1: Load raw CSV into PostgreSQL (Bronze source layer).
Also profiles the data so we have 'before' metrics for the README.
"""
import os
import sys
import json
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path

# ---------- Config ----------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "ecommerce_retail_transactions_raw.csv"
LOG_PATH = PROJECT_ROOT / "logs" / "row_counts.json"

PG_CONN = {
    "host": "localhost",
    "port": 5432,
    "dbname": "etl_project",
    "user": "etl_user",
    "password": "etl_pass",
}

TABLE_NAME = "raw_sales"

# ---------- 1. Profile the CSV (before numbers) ----------
def profile_csv(df: pd.DataFrame) -> dict:
    return {
        "total_rows": int(len(df)),
        "total_columns": int(len(df.columns)),
        "duplicate_rows": int(df.duplicated().sum()),
        "nulls_per_column": {col: int(df[col].isna().sum()) for col in df.columns},
        "columns": list(df.columns),
    }

# ---------- 2. Load CSV ----------
def load_csv() -> pd.DataFrame:
    if not CSV_PATH.exists():
        sys.exit(f"[ERROR] CSV not found at {CSV_PATH}")
    print(f"[INFO] Reading {CSV_PATH}")
    df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False, na_values=[""])
    print(f"[INFO] Loaded {len(df)} rows, {len(df.columns)} columns")
    return df

# ---------- 3. Create table (all TEXT to preserve raw dirtiness) ----------
def create_table(conn, columns):
    safe_cols = [c.strip().lower().replace(" ", "_").replace("-", "_") for c in columns]
    col_defs = ", ".join(f'"{c}" TEXT' for c in safe_cols)
    with conn.cursor() as cur:
        cur.execute(f"DROP TABLE IF EXISTS {TABLE_NAME};")
        cur.execute(f"CREATE TABLE {TABLE_NAME} ({col_defs});")
    conn.commit()
    return safe_cols

# ---------- 4. Insert rows ----------
def insert_rows(conn, df: pd.DataFrame, safe_cols: list):
    df_clean = df.where(pd.notna(df), None)
    rows = [tuple(r) for r in df_clean.itertuples(index=False, name=None)]
    collist = ", ".join(f'"{c}"' for c in safe_cols)
    with conn.cursor() as cur:
        execute_values(
            cur,
            f"INSERT INTO {TABLE_NAME} ({collist}) VALUES %s",
            rows,
            page_size=1000,
        )
    conn.commit()
    print(f"[INFO] Inserted {len(rows)} rows into {TABLE_NAME}")

# ---------- 5. Verify row count in PG ----------
def verify_count(conn) -> int:
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME};")
        return cur.fetchone()[0]

# ---------- Main ----------
def main():
    df = load_csv()

    print("\n===== CSV PROFILE (BEFORE) =====")
    profile = profile_csv(df)
    print(json.dumps(profile, indent=2, default=str))

    conn = psycopg2.connect(**PG_CONN)
    try:
        safe_cols = create_table(conn, df.columns)
        df.columns = safe_cols
        insert_rows(conn, df, safe_cols)
        pg_count = verify_count(conn)
        print(f"\n[VERIFY] PostgreSQL {TABLE_NAME} row count = {pg_count}")

        LOG_PATH.parent.mkdir(exist_ok=True)
        existing = {}
        if LOG_PATH.exists():
            existing = json.loads(LOG_PATH.read_text())
        existing["bronze_csv_profile"] = profile
        existing["bronze_pg_row_count"] = pg_count
        LOG_PATH.write_text(json.dumps(existing, indent=2))
        print(f"[INFO] Profile written to {LOG_PATH}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()