# ============================================================
# cleaner.py — RevenueRadar
# ============================================================
# YEH FILE KYA KARTI HAI:
#   MSSQL ke raw_sales table se data uthata hai,
#   sari cleaning karta hai pandas se, aur clean dataframe
#   return karta hai. Har step mein kitne records fix hue
#   woh bhi print hota hai — taaki report mein dikh sake.
#
# RUN: python 02_data_cleaning/cleaner.py
# ============================================================

import pandas as pd
import numpy as np
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.config import get_engine, RAW_TABLE

def load_from_mssql():
    """MSSQL se raw data fetch karo."""
    print("📥 MSSQL se raw data fetch ho raha hai...")
    engine = get_engine()
    df     = pd.read_sql(f"SELECT * FROM {RAW_TABLE}", engine)
    print(f"   Raw rows loaded: {len(df):,}")
    return df

def clean_data(df):
    """
    MAIN CLEANING FUNCTION
    Har step explain kiya hai — samajhna easy ho.
    """
    report = {}   # Cleaning report track karne ke liye
    original_count = len(df)
    print("\n🧹 Cleaning pipeline start...")
    print("=" * 50)

    # ── STEP 1: Duplicate rows hatao ────────────────────────
    # LOGIC: order_id same ho toh duplicate hai.
    #        keep='first' matlab pehla rakho, baaki hatao.
    before = len(df)
    df = df.drop_duplicates(subset=["order_id"], keep="first")
    dupes_removed = before - len(df)
    report["duplicates_removed"] = dupes_removed
    print(f"✅ Step 1 — Duplicates removed : {dupes_removed:,}")

    # ── STEP 2: Null values handle karo ─────────────────────
    # LOGIC:
    #   - total_amount null hai → row useless hai → drop karo
    #   - customer_email null hai → 'unknown@email.com' se fill
    #   - baki nulls → forward fill ya default value

    # Critical nulls drop karo
    before = len(df)
    df = df.dropna(subset=["total_amount", "order_id", "sale_date"])
    nulls_dropped = before - len(df)
    report["nulls_dropped"] = nulls_dropped
    print(f"✅ Step 2a — Critical nulls dropped: {nulls_dropped:,}")

    # Non-critical nulls fill karo
    df["customer_email"]  = df["customer_email"].fillna("unknown@noemail.com")
    df["customer_phone"]  = df["customer_phone"].fillna("0000000000")
    df["discount_pct"]    = df["discount_pct"].fillna(0)
    df["discount_amt"]    = df["discount_amt"].fillna(0)
    df["payment_method"]  = df["payment_method"].fillna("Unknown")
    print(f"✅ Step 2b — Non-critical nulls filled")

    # ── STEP 3: Date validation ──────────────────────────────
    # LOGIC: sale_date future mein nahi ho sakti (2099 wali entries wrong hain)
    #        aur 2020 se pehle ki data bhi project scope mein nahi.
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")

    today = pd.Timestamp.today()
    before = len(df)
    df = df[
        (df["sale_date"] >= "2023-01-01") &
        (df["sale_date"] <= today)
    ]
    date_issues = before - len(df)
    report["invalid_dates_removed"] = date_issues
    print(f"✅ Step 3  — Invalid dates removed : {date_issues:,}")

    # ── STEP 4: Negative / zero amounts fix karo ────────────
    # LOGIC: total_amount negative ya zero nahi ho sakta
    #        (jo -999 inject kiye the woh yahan hatenge)
    before = len(df)
    df = df[df["total_amount"] > 0]
    neg_removed = before - len(df)
    report["negative_amounts_removed"] = neg_removed
    print(f"✅ Step 4  — Negative amounts removed: {neg_removed:,}")

    # ── STEP 5: Outlier detection (IQR method) ───────────────
    # LOGIC: Outlier woh value hai jo bahut zyada alag ho.
    #        IQR (Interquartile Range) method:
    #          Q1 = 25th percentile, Q3 = 75th percentile
    #          IQR = Q3 - Q1
    #          Lower bound = Q1 - 1.5 * IQR
    #          Upper bound = Q3 + 1.5 * IQR
    #        Isse baahar wali values outlier hain.
    Q1  = df["total_amount"].quantile(0.25)
    Q3  = df["total_amount"].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    before = len(df)
    df = df[
        (df["total_amount"] >= lower) &
        (df["total_amount"] <= upper)
    ]
    outliers_removed = before - len(df)
    report["outliers_removed"] = outliers_removed
    print(f"✅ Step 5  — Outliers removed (IQR) : {outliers_removed:,}")

    # ── STEP 6: Text standardisation ────────────────────────
    # LOGIC: "electronics" aur "Electronics" same category hain.
    #        .str.title() se pehla letter capital ho jaata hai.
    df["category"]      = df["category"].str.strip().str.title()
    df["region"]        = df["region"].str.strip().str.title()
    df["order_status"]  = df["order_status"].str.strip().str.title()
    df["payment_method"]= df["payment_method"].str.strip().str.title()
    df["city"]          = df["city"].str.strip().str.title()
    print(f"✅ Step 6  — Text standardised")

    # ── STEP 7: Derived columns add karo ────────────────────
    # LOGIC: Analytics ke liye extra columns useful hain
    df["year"]        = df["sale_date"].dt.year
    df["month"]       = df["sale_date"].dt.month
    df["month_name"]  = df["sale_date"].dt.strftime("%B")
    df["quarter"]     = df["sale_date"].dt.quarter
    df["day_of_week"] = df["sale_date"].dt.day_name()
    df["is_weekend"]  = df["sale_date"].dt.dayofweek >= 5

    # Revenue band (segment karne ke liye)
    df["revenue_band"] = pd.cut(
        df["total_amount"],
        bins=[0, 1000, 5000, 20000, np.inf],
        labels=["Low", "Medium", "High", "Premium"]
    ).astype(str)

    print(f"✅ Step 7  — Derived columns added (year, month, quarter, band)")

    # ── STEP 8: Final report ─────────────────────────────────
    report["final_rows"]    = len(df)
    report["rows_removed"]  = original_count - len(df)
    report["cleaning_pct"]  = round(
        (report["rows_removed"] / original_count) * 100, 2
    )

    print("\n" + "=" * 50)
    print("📊 CLEANING SUMMARY:")
    print(f"   Original rows  : {original_count:,}")
    print(f"   Final rows     : {report['final_rows']:,}")
    print(f"   Rows removed   : {report['rows_removed']:,}")
    print(f"   Data quality % : {100 - report['cleaning_pct']:.1f}%")
    print("=" * 50)

    return df, report


if __name__ == "__main__":
    print("🚀 RevenueRadar — Data Cleaning Module")
    print("=" * 55)

    df_raw = load_from_mssql()
    df_clean, cleaning_report = clean_data(df_raw)

    print(f"\n📋 Clean Data Preview:")
    print(df_clean[["order_id","product_name","total_amount",
                     "sale_date","region","revenue_band"]].head(5).to_string(index=False))

    print("\n➡️  Agla step: python 02_data_cleaning/save_cleaned_to_mssql.py")