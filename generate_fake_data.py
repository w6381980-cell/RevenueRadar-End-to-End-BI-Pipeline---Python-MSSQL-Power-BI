# ============================================================
# generate_fake_data.py — RevenueRadar
# ============================================================
# YEH FILE KYA KARTI HAI:
#   Faker library se 50,000 realistic retail rows banata hai.
#   Real company jaisi data — customer names, products,
#   regions, sales amounts, dates sab kuch included.
#   Kuch intentional errors bhi daale hain (nulls, duplicates,
#   wrong dates) taaki cleaning step ka kaam dikhaye.
#
# RUN: python 01_data_generation/generate_fake_data.py
# OUTPUT: 01_data_generation/raw_sales_data.csv
# ============================================================

import pandas as pd
import numpy as np
import random
from faker import Faker
from datetime import datetime, timedelta
import os
import sys

# Config import karo (root se path fix karo)
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.config import DATA_DIR

fake = Faker('en_IN')   # Indian locale — Indian names milenge
random.seed(42)          # Seed set karo — same data bar bar generate ho
np.random.seed(42)

print("🚀 RevenueRadar: Data Generation shuru ho raha hai...")
print("=" * 55)

# ── STEP 1: Master lists banao ───────────────────────────────
# LOGIC: Real retail mein yeh categories hoti hain

PRODUCTS = [
    ("Laptop",        "Electronics",  25000, 85000),
    ("Smartphone",    "Electronics",  8000,  60000),
    ("Headphones",    "Electronics",  500,   8000),
    ("Refrigerator",  "Appliances",   12000, 45000),
    ("Washing Machine","Appliances",  8000,  35000),
    ("T-Shirt",       "Fashion",      299,   2500),
    ("Jeans",         "Fashion",      800,   5000),
    ("Running Shoes", "Fashion",      1200,  12000),
    ("Rice 5kg",      "Grocery",      250,   450),
    ("Cooking Oil 1L","Grocery",      150,   300),
    ("Sofa Set",      "Furniture",    15000, 75000),
    ("Study Table",   "Furniture",    3000,  18000),
    ("Notebook A4",   "Stationery",   50,    200),
    ("Face Cream",    "Beauty",       200,   3000),
    ("Shampoo 400ml", "Beauty",       150,   800),
]

REGIONS    = ["North", "South", "East", "West", "Central"]
CITIES     = {
    "North":   ["Delhi", "Chandigarh", "Lucknow", "Jaipur"],
    "South":   ["Bangalore", "Chennai", "Hyderabad", "Kochi"],
    "East":    ["Kolkata", "Bhubaneswar", "Patna", "Guwahati"],
    "West":    ["Mumbai", "Pune", "Ahmedabad", "Surat"],
    "Central": ["Nagpur", "Bhopal", "Indore", "Raipur"],
}
PAYMENT    = ["UPI", "Credit Card", "Debit Card", "Net Banking", "Cash", "EMI"]
STATUS     = ["Delivered", "Returned", "Cancelled", "Pending"]
STATUS_W   = [0.75, 0.10, 0.10, 0.05]   # Weights — 75% delivered hogi

# ── STEP 2: Date range banao ─────────────────────────────────
# LOGIC: 2 saal ka data — trends dikhane ke liye
start_date = datetime(2023, 1, 1)
end_date   = datetime(2025, 3, 31)
date_range = (end_date - start_date).days

# ── STEP 3: 50,000 rows generate karo ───────────────────────
print("📦 50,000 rows generate ho rahi hain...")

rows = []
TOTAL = 50_000

for i in range(TOTAL):
    # Progress bar
    if i % 10000 == 0:
        print(f"   {i:,} / {TOTAL:,} rows done...")

    # Product choose karo
    prod_name, category, min_price, max_price = random.choice(PRODUCTS)

    # Region aur city
    region = random.choice(REGIONS)
    city   = random.choice(CITIES[region])

    # Price (realistic variation)
    unit_price = round(random.uniform(min_price, max_price), 2)

    # Quantity (1-5, weighted — mostly 1)
    qty = random.choices([1, 2, 3, 4, 5], weights=[55, 25, 10, 6, 4])[0]

    # Discount (0-30%)
    discount_pct = random.choices(
        [0, 5, 10, 15, 20, 25, 30],
        weights=[40, 20, 15, 10, 8, 4, 3]
    )[0]
    discount_amt = round((unit_price * qty * discount_pct) / 100, 2)
    total_amount = round((unit_price * qty) - discount_amt, 2)

    # Sale date (weekdays zyada sales — realistic)
    rand_days   = random.randint(0, date_range)
    sale_date   = start_date + timedelta(days=rand_days)

    # Order status
    status = random.choices(STATUS, weights=STATUS_W)[0]

    row = {
        "order_id":       f"ORD{100000 + i}",
        "customer_name":  fake.name(),
        "customer_email": fake.email(),
        "customer_phone": fake.phone_number(),
        "product_name":   prod_name,
        "category":       category,
        "unit_price":     unit_price,
        "quantity":       qty,
        "discount_pct":   discount_pct,
        "discount_amt":   discount_amt,
        "total_amount":   total_amount,
        "payment_method": random.choice(PAYMENT),
        "region":         region,
        "city":           city,
        "sale_date":      sale_date.strftime("%Y-%m-%d"),
        "order_status":   status,
        "salesperson":    fake.name(),
    }
    rows.append(row)

df = pd.DataFrame(rows)

# ── STEP 4: Intentional errors inject karo ──────────────────
# LOGIC: Real data mein yeh problems hoti hain.
#        Cleaning step mein yahi fix honge.
print("\n🐛 Realistic data errors inject kar rahe hain...")

# 4a. Null values (2% rows mein)
null_idx = df.sample(frac=0.02).index
df.loc[null_idx, "customer_email"] = None

null_idx2 = df.sample(frac=0.015).index
df.loc[null_idx2, "total_amount"] = None

# 4b. Duplicate rows (500 rows duplicate)
dupes = df.sample(500)
df = pd.concat([df, dupes], ignore_index=True)

# 4c. Wrong dates (100 rows mein future date)
wrong_idx = df.sample(100).index
df.loc[wrong_idx, "sale_date"] = "2099-01-01"

# 4d. Negative amount (50 rows)
neg_idx = df.sample(50).index
df.loc[neg_idx, "total_amount"] = -999

# 4e. Category mismatch (casing)
df.loc[df.sample(200).index, "category"] = df.loc[
    df.sample(200).index, "category"
].str.lower()

print(f"   ✅ Total rows (with errors): {len(df):,}")

# ── STEP 5: CSV mein save karo ──────────────────────────────
output_path = os.path.join(DATA_DIR, "raw_sales_data.csv")
df.to_csv(output_path, index=False)

print(f"\n✅ Data saved: {output_path}")
print(f"   Rows   : {len(df):,}")
print(f"   Columns: {len(df.columns)}")
print(f"\n📋 Preview:")
print(df.head(3).to_string(index=False))
print("\n➡️  Agla step: python 01_data_generation/load_to_mssql.py")