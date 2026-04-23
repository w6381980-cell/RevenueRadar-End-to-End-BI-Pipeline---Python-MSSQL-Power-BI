# ============================================================
# load_to_mssql.py — RevenueRadar
# ============================================================
# YEH FILE KYA KARTI HAI:
#   generate_fake_data.py se bana CSV file uthata hai
#   aur MSSQL ke raw_sales table mein daal deta hai.
#   Pehli baar table create karega, dobara chalao toh
#   purana data delete karke naya daal deta hai (replace).
#
# RUN: python 01_data_generation/load_to_mssql.py
# REQUIRE: generate_fake_data.py pehle chala hona chahiye
# ============================================================

import pandas as pd
import pyodbc
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.config import (
    get_connection_string, get_engine,
    RAW_TABLE, DATA_DIR
)

print("🚀 MSSQL Load shuru ho raha hai...")
print("=" * 55)

# ── STEP 1: CSV padho ────────────────────────────────────────
csv_path = os.path.join(DATA_DIR, "raw_sales_data.csv")

if not os.path.exists(csv_path):
    print("❌ raw_sales_data.csv nahi mila!")
    print("   Pehle chalao: python 01_data_generation/generate_fake_data.py")
    sys.exit(1)

print(f"📂 CSV pad raha hai: {csv_path}")
df = pd.read_csv(csv_path)
print(f"   Rows loaded: {len(df):,}")

# ── STEP 2: Data types fix karo pandas mein ─────────────────
# LOGIC: MSSQL ko sahi data types chahiye
df["sale_date"]    = pd.to_datetime(df["sale_date"], errors="coerce")
df["unit_price"]   = pd.to_numeric(df["unit_price"],  errors="coerce")
df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce")
df["quantity"]     = pd.to_numeric(df["quantity"],     errors="coerce")

print("   Data types fixed ✅")

# ── STEP 3: MSSQL mein table banao (agar pehle se nahi hai) ─
# LOGIC: Pehle CREATE TABLE SQL chalate hain manually
#        taaki exact column types control mein rahein.
#        Phir pandas se data insert karte hain.
print(f"\n📊 MSSQL mein '{RAW_TABLE}' table bana/replace raha hai...")

create_table_sql = f"""
IF OBJECT_ID('{RAW_TABLE}', 'U') IS NOT NULL
    DROP TABLE {RAW_TABLE};

CREATE TABLE {RAW_TABLE} (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    order_id        VARCHAR(20),
    customer_name   NVARCHAR(100),
    customer_email  NVARCHAR(150),
    customer_phone  NVARCHAR(30),
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
    loaded_at       DATETIME DEFAULT GETDATE()
);
"""

# pyodbc se table create karo
try:
    conn = pyodbc.connect(get_connection_string())
    cursor = conn.cursor()
    cursor.execute(create_table_sql)
    conn.commit()
    conn.close()
    print(f"   Table '{RAW_TABLE}' ready ✅")
except Exception as e:
    print(f"❌ Table creation failed: {e}")
    sys.exit(1)

# ── STEP 4: Data insert karo SQLAlchemy se ──────────────────
# LOGIC: pandas ka to_sql() SQLAlchemy engine use karta hai
#        chunksize=1000 matlab 1000 rows ek baar mein insert —
#        memory efficient aur fast.
print(f"\n⬆️  Data upload ho raha hai ({len(df):,} rows)...")
print("   (Isme 1-2 minute lag sakte hain...)")

try:
    engine = get_engine()
    df.to_sql(
        name      = RAW_TABLE,
        con       = engine,
        if_exists = "append",
        index     = False,
        chunksize = 90,
    )

    print(f"✅ {len(df):,} rows successfully inserted!")

except Exception as e:
    print(f"❌ Data insert failed: {e}")
    sys.exit(1)

# ── STEP 5: Verify karo — count check ───────────────────────
print("\n🔍 MSSQL mein verify kar rahe hain...")
try:
    conn   = pyodbc.connect(get_connection_string())
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {RAW_TABLE}")
    count = cursor.fetchone()[0]
    conn.close()
    print(f"   Rows in MSSQL: {count:,} ✅")
except Exception as e:
    print(f"   Verify failed: {e}")

print("\n✅ Load complete!")
print("➡️  Agla step: python 02_data_cleaning/cleaner.py")