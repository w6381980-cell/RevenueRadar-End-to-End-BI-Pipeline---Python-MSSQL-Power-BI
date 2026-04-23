# ============================================================
# kpi_engine.py — RevenueRadar
# ============================================================
# YEH FILE KYA KARTI HAI:
#   Cleaned data se important business metrics calculate karta hai.
#   KPI = Key Performance Indicator (business health dikhata hai)
#   Yeh sab numbers reports aur Power BI mein use honge.
#
# RUN: python 03_analytics/kpi_engine.py
# ============================================================

import pandas as pd
import numpy as np
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.config import get_engine, CLEANED_TABLE

def load_clean_data():
    engine = get_engine()
    df = pd.read_sql(f"SELECT * FROM {CLEANED_TABLE}", engine)
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    return df

def calculate_kpis(df):
    """
    Sare important KPIs calculate karo.
    Har KPI ka formula samjhaya gaya hai.
    """
    print("📊 KPIs calculate ho rahe hain...")

    kpis = {}

    # ── REVENUE KPIs ─────────────────────────────────────────

    # Total Revenue = sum of all delivered orders
    delivered = df[df["order_status"] == "Delivered"]
    kpis["total_revenue"]   = round(delivered["total_amount"].sum(), 2)
    kpis["total_orders"]    = len(delivered)
    kpis["total_customers"] = df["customer_email"].nunique()

    # AOV = Average Order Value
    # LOGIC: Ek order mein average kitna spend hua
    kpis["avg_order_value"] = round(
        kpis["total_revenue"] / kpis["total_orders"], 2
    )

    # ── GROWTH KPI ───────────────────────────────────────────
    # MoM = Month over Month growth
    # LOGIC: Is mahine ka revenue vs pichle mahine
    monthly = (
        delivered.groupby(["year","month"])["total_amount"]
        .sum()
        .reset_index()
        .sort_values(["year","month"])
    )
    if len(monthly) >= 2:
        this_month = monthly.iloc[-1]["total_amount"]
        last_month = monthly.iloc[-2]["total_amount"]
        mom_growth = round(((this_month - last_month) / last_month) * 100, 2)
        kpis["mom_growth_pct"]    = mom_growth
        kpis["this_month_rev"]    = round(this_month, 2)
        kpis["last_month_rev"]    = round(last_month, 2)
    else:
        kpis["mom_growth_pct"] = 0

    # ── RETURN RATE ──────────────────────────────────────────
    # LOGIC: Kitne % orders return hue
    returns = len(df[df["order_status"] == "Returned"])
    kpis["return_rate_pct"] = round((returns / len(df)) * 100, 2)

    # ── TOP PERFORMERS ───────────────────────────────────────
    kpis["top_category"] = (
        delivered.groupby("category")["total_amount"]
        .sum().idxmax()
    )
    kpis["top_region"]   = (
        delivered.groupby("region")["total_amount"]
        .sum().idxmax()
    )
    kpis["top_product"]  = (
        delivered.groupby("product_name")["total_amount"]
        .sum().idxmax()
    )

    # ── DISCOUNT ANALYSIS ────────────────────────────────────
    kpis["avg_discount_pct"] = round(df["discount_pct"].mean(), 2)
    kpis["total_discount"]   = round(df["discount_amt"].sum(), 2)

    # ── CATEGORY BREAKDOWN ───────────────────────────────────
    category_rev = (
        delivered.groupby("category")["total_amount"]
        .sum()
        .sort_values(ascending=False)
        .round(2)
        .to_dict()
    )
    kpis["category_revenue"] = category_rev

    # ── MONTHLY TREND ────────────────────────────────────────
    kpis["monthly_trend"] = monthly.to_dict("records")

    # ── PRINT SUMMARY ────────────────────────────────────────
    print("\n" + "=" * 50)
    print("💰 RevenueRadar — KPI Summary")
    print("=" * 50)
    print(f"  Total Revenue      : ₹{kpis['total_revenue']:,.2f}")
    print(f"  Total Orders       : {kpis['total_orders']:,}")
    print(f"  Unique Customers   : {kpis['total_customers']:,}")
    print(f"  Avg Order Value    : ₹{kpis['avg_order_value']:,.2f}")
    print(f"  MoM Growth         : {kpis['mom_growth_pct']:+.2f}%")
    print(f"  Return Rate        : {kpis['return_rate_pct']}%")
    print(f"  Top Category       : {kpis['top_category']}")
    print(f"  Top Region         : {kpis['top_region']}")
    print(f"  Avg Discount       : {kpis['avg_discount_pct']}%")
    print("=" * 50)

    return kpis


if __name__ == "__main__":
    print("🚀 RevenueRadar — KPI Engine")
    df    = load_clean_data()
    kpis  = calculate_kpis(df)
    print("\n➡️  Agla step: python 04_prediction/sales_forecast.py")