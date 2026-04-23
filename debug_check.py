import sys, os
sys.path.append('.')
sys.path.append('./02_data_cleaning')
from config.config import get_engine, CLEANED_TABLE
from cleaner import load_from_mssql, clean_data
import pandas as pd
import sys, os
sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('./02_data_cleaning'))

df_raw = load_from_mssql()
df_clean, _ = clean_data(df_raw)

cols_to_keep = [
    "order_id","customer_name","customer_email","product_name",
    "category","unit_price","quantity","discount_pct","discount_amt",
    "total_amount","payment_method","region","city","sale_date",
    "order_status","salesperson","year","month","month_name",
    "quarter","day_of_week","is_weekend","revenue_band"
]
df_clean = df_clean[[c for c in cols_to_keep if c in df_clean.columns]]

print("\n=== NUMERIC COLUMN RANGES ===")
for col in ["unit_price","discount_pct","discount_amt","total_amount"]:
    print(f"{col}: min={df_clean[col].min()}, max={df_clean[col].max()}, nulls={df_clean[col].isnull().sum()}")

print("\n=== INT COLUMN RANGES ===")
for col in ["quantity","year","month","quarter","is_weekend"]:
    print(f"{col}: min={df_clean[col].min()}, max={df_clean[col].max()}, dtype={df_clean[col].dtype}")