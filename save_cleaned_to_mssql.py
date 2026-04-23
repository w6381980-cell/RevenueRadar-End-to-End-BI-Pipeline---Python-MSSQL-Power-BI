# ============================================================
# save_cleaned_to_mssql.py — RevenueRadar
# ============================================================
# YEH FILE KYA KARTI HAI:
#   cleaner.py se clean dataframe leti hai aur
#   MSSQL ke cleaned_sales table mein save karti hai.
#   Power BI yahi table use karega.
#
# RUN: python 02_data_cleaning/save_cleaned_to_mssql.py
# ============================================================

import pandas as pd
import pyodbc
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.config import get_connection_string, get_engine, CLEANED_TABLE
from cleaner import load_from_mssql, clean_data

print("🚀 Cleaned data MSSQL mein save ho raha hai...")
print("=" * 55)

# ── Clean data lo ────────────────────────────────────────────
df_raw          = load_from_mssql()
df_clean, report = clean_data(df_raw)

# ── MSSQL mein cleaned_sales table banao ────────────────────
create_sql = f"""
IF OBJECT_ID('{CLEANED_TABLE}', 'U') IS NOT NULL
    DROP TABLE {CLEANED_TABLE};

CREATE TABLE {CLEANED_TABLE} (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    order_id        VARCHAR(20),
    customer_name   NVARCHAR(100),
    customer_email  NVARCHAR(150),
    product_name    NVARCHAR(100),
    category        NVARCHAR(50),
    unit_price      DECIMAL(12,2),
    quantity        INT,
    discount_pct    DECIMAL(5,2),
    discount_amt    DECIMAL(12,2),
    total_amount    DECIMAL(12,2),
    payment_method  NVARCHAR(50),
    region          NVARCHAR(30),
    city            NVARCHAR(50),
    sale_date       DATE,
    order_status    NVARCHAR(30),
    salesperson     NVARCHAR(100),
    year            INT,
    month           INT,
    month_name      NVARCHAR(15),
    quarter         INT,
    day_of_week     NVARCHAR(15),
    is_weekend      BIT,
    revenue_band    NVARCHAR(20),
    loaded_at       DATETIME DEFAULT GETDATE()
);
"""

try:
    conn = pyodbc.connect(get_connection_string())
    cursor = conn.cursor()
    cursor.execute(create_sql)
    conn.commit()
    conn.close()
    print(f"✅ Table '{CLEANED_TABLE}' created in MSSQL")
except Exception as e:
    print(f"❌ Table creation failed: {e}")
    sys.exit(1)

# ── Columns align karo (extra columns drop) ─────────────────
# LOGIC: DataFrame mein 'id' column nahi hoga (auto-generated),
#        aur kuch extra columns hain jo table schema mein nahi.
cols_to_keep = [
    "order_id","customer_name","customer_email","product_name",
    "category","unit_price","quantity","discount_pct","discount_amt",
    "total_amount","payment_method","region","city","sale_date",
    "order_status","salesperson","year","month","month_name",
    "quarter","day_of_week","is_weekend","revenue_band"
]
df_clean = df_clean[[c for c in cols_to_keep if c in df_clean.columns]]

# ── Data insert karo ─────────────────────────────────────────
# ── Data insert karo ─────────────────────────────────────────
print(f"\n⬆️  {len(df_clean):,} clean rows upload ho rahi hain...")

try:
    import math, io, csv

    # Sab kuch string/native Python types mein convert karo
    df_clean["is_weekend"] = df_clean["is_weekend"].astype(int)
    df_clean["year"]       = df_clean["year"].astype(int)
    df_clean["month"]      = df_clean["month"].astype(int)
    df_clean["quarter"]    = df_clean["quarter"].astype(int)
    df_clean["quantity"]   = df_clean["quantity"].astype(int)
    df_clean["unit_price"]   = df_clean["unit_price"].astype(float).round(2)
    df_clean["discount_pct"] = df_clean["discount_pct"].astype(float).round(2)
    df_clean["discount_amt"] = df_clean["discount_amt"].astype(float).round(2)
    df_clean["total_amount"] = df_clean["total_amount"].astype(float).round(2)
    df_clean["sale_date"]  = pd.to_datetime(df_clean["sale_date"]).dt.strftime("%Y-%m-%d")

    conn   = pyodbc.connect(get_connection_string())
    cursor = conn.cursor()
    cursor.fast_executemany = True

    cols         = list(df_clean.columns)
    placeholders = ",".join(["?" for _ in cols])
    col_names    = ",".join(cols)
    insert_sql   = f"INSERT INTO {CLEANED_TABLE} ({col_names}) VALUES ({placeholders})"

    # DataFrame ko pure Python list of tuples mein convert karo
    # json se convert karo — numpy types automatically handle
    import json
    rows = []
    for rec in df_clean.to_dict(orient="records"):
        row = []
        for col in cols:
            val = rec[col]
            if val is None or (isinstance(val, float) and math.isnan(val)):
                row.append(None)
            elif isinstance(val, bool):
                row.append(int(val))
            else:
                row.append(val)
        rows.append(tuple(row))

    BATCH   = 200
    total   = len(rows)
    batches = math.ceil(total / BATCH)

    for i in range(batches):
        batch = rows[i*BATCH:(i+1)*BATCH]
        cursor.executemany(insert_sql, batch)
        conn.commit()
        print(f"   Batch {i+1}/{batches} — {min((i+1)*BATCH, total):,}/{total:,} rows")

    cursor.close()
    conn.close()
    print(f"✅ {total:,} rows successfully saved to '{CLEANED_TABLE}'!")

except Exception as e:
    print(f"❌ Insert failed: {e}")
    sys.exit(1)

# ── Verify ───────────────────────────────────────────────────
conn = pyodbc.connect(get_connection_string())
cursor = conn.cursor()
cursor.execute(f"SELECT COUNT(*) FROM {CLEANED_TABLE}")
count = cursor.fetchone()[0]
conn.close()
print(f"🔍 Verified — MSSQL mein rows: {count:,}")
print("\n✅ Cleaning + Save complete!")
print("➡️  Agla step: python 03_analytics/kpi_engine.py")