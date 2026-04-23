# ============================================================
# validator.py — RevenueRadar
# ============================================================
# YEH FILE KYA KARTI HAI:
#   Cleaning ke baad data quality check karta hai.
#   Ek "report card" deta hai — kitna % data clean hai.
#   Agar quality 80% se kam ho toh warning deta hai.
#
# RUN: python 02_data_cleaning/validator.py
# ============================================================

import pandas as pd
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.config import get_engine, CLEANED_TABLE

def validate_data(df):
    """
    LOGIC:
      Har check ek rule hai jo data ko satisfy karna chahiye.
      Pass = rule satisfy hua.
      Fail = problem hai data mein.
    """
    print("🔍 Data Validation shuru ho rahi hai...")
    print("=" * 55)

    checks = []

    # ── CHECK 1: Koi null nahi critical columns mein ─────────
    critical_cols = ["order_id", "total_amount", "sale_date",
                     "category", "region"]
    for col in critical_cols:
        null_count = df[col].isnull().sum()
        status = "✅ PASS" if null_count == 0 else f"❌ FAIL ({null_count} nulls)"
        checks.append({
            "Check": f"No nulls in '{col}'",
            "Status": status,
            "Pass": null_count == 0
        })

    # ── CHECK 2: Duplicate order_id nahi hona chahiye ────────
    dupes = df["order_id"].duplicated().sum()
    checks.append({
        "Check": "No duplicate order_ids",
        "Status": "✅ PASS" if dupes == 0 else f"❌ FAIL ({dupes} dupes)",
        "Pass": dupes == 0
    })

    # ── CHECK 3: total_amount > 0 hona chahiye ────────────────
    neg = (df["total_amount"] <= 0).sum()
    checks.append({
        "Check": "All amounts > 0",
        "Status": "✅ PASS" if neg == 0 else f"❌ FAIL ({neg} rows)",
        "Pass": neg == 0
    })

    # ── CHECK 4: sale_date valid range mein ho ────────────────
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    future_dates = (df["sale_date"] > pd.Timestamp.today()).sum()
    checks.append({
        "Check": "No future sale dates",
        "Status": "✅ PASS" if future_dates == 0 else f"❌ FAIL ({future_dates} rows)",
        "Pass": future_dates == 0
    })

    # ── CHECK 5: Category valid values ────────────────────────
    valid_cats = {"Electronics", "Appliances", "Fashion",
                  "Grocery", "Furniture", "Stationery", "Beauty"}
    invalid_cats = (~df["category"].isin(valid_cats)).sum()
    checks.append({
        "Check": "Valid category values",
        "Status": "✅ PASS" if invalid_cats == 0 else f"⚠️  WARN ({invalid_cats} unknown)",
        "Pass": invalid_cats == 0
    })

    # ── CHECK 6: Minimum row count ────────────────────────────
    min_rows = 1000
    checks.append({
        "Check": f"Row count >= {min_rows:,}",
        "Status": f"✅ PASS ({len(df):,} rows)" if len(df) >= min_rows else f"❌ FAIL",
        "Pass": len(df) >= min_rows
    })

    # ── RESULT ────────────────────────────────────────────────
    total  = len(checks)
    passed = sum(1 for c in checks if c["Pass"])
    score  = round((passed / total) * 100, 1)

    for c in checks:
        print(f"  {c['Status']:<30} | {c['Check']}")

    print("=" * 55)
    print(f"  📊 Quality Score: {score}% ({passed}/{total} checks passed)")

    if score >= 90:
        print("  🟢 Data quality: EXCELLENT — pipeline ke liye ready!")
    elif score >= 75:
        print("  🟡 Data quality: ACCEPTABLE — kuch issues hain")
    else:
        print("  🔴 Data quality: POOR — cleaning dobara chalao!")

    return score, checks


if __name__ == "__main__":
    print("🚀 RevenueRadar — Data Validator")
    engine   = get_engine()
    df       = pd.read_sql(f"SELECT * FROM {CLEANED_TABLE}", engine)
    score, _ = validate_data(df)
    print(f"\n✅ Validation complete! Score: {score}%")
    print("➡️  Agla step: python 03_analytics/kpi_engine.py")