# ============================================================
# impact_scorer.py — RevenueRadar
# ============================================================
# YEH FILE KYA KARTI HAI:
#   Har category aur region ko ek "impact score" deta hai.
#   Score = Revenue + Growth + Volume ka weighted combination.
#   Impact report mein yahi score use hoga.
#
# IMPACT SCORE FORMULA:
#   Score = (Revenue_norm * 0.5)
#         + (Growth_norm  * 0.3)
#         + (Orders_norm  * 0.2)
#   Normalize = value ko 0-100 scale pe laana
#
# RUN: python 03_analytics/impact_scorer.py
# ============================================================

import pandas as pd
import numpy as np
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.config import get_engine, CLEANED_TABLE

def normalize(series):
    """
    LOGIC: Min-Max Normalization
      0 = sabse kam value
      100 = sabse zyada value
      Formula: (x - min) / (max - min) * 100
    """
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series([50.0] * len(series), index=series.index)
    return ((series - mn) / (mx - mn) * 100).round(2)

def score_categories(df):
    """
    Category-wise impact score calculate karo.
    """
    delivered = df[df["order_status"] == "Delivered"]

    # Monthly revenue for growth calc
    monthly_cat = (
        delivered.groupby(["category", "year", "month"])["total_amount"]
        .sum().reset_index().sort_values(["category","year","month"])
    )

    # Last 2 months growth per category
    growth = {}
    for cat, grp in monthly_cat.groupby("category"):
        if len(grp) >= 2:
            last  = grp.iloc[-1]["total_amount"]
            prev  = grp.iloc[-2]["total_amount"]
            growth[cat] = ((last - prev) / prev * 100) if prev else 0
        else:
            growth[cat] = 0

    # Aggregate
    agg = (
        delivered.groupby("category")
        .agg(
            revenue = ("total_amount", "sum"),
            orders  = ("order_id",     "count"),
        )
        .reset_index()
    )
    agg["growth_pct"] = agg["category"].map(growth).fillna(0)

    # Normalize each metric
    agg["rev_score"]    = normalize(agg["revenue"])
    agg["growth_score"] = normalize(agg["growth_pct"])
    agg["vol_score"]    = normalize(agg["orders"])

    # Weighted impact score
    agg["impact_score"] = (
        agg["rev_score"]    * 0.50 +
        agg["growth_score"] * 0.30 +
        agg["vol_score"]    * 0.20
    ).round(1)

    # Grade
    def grade(s):
        if s >= 75: return "A — High Impact"
        elif s >= 50: return "B — Medium Impact"
        elif s >= 25: return "C — Low Impact"
        else: return "D — Needs Attention"

    agg["grade"] = agg["impact_score"].apply(grade)
    agg = agg.sort_values("impact_score", ascending=False)

    return agg

def score_regions(df):
    """Region-wise impact score."""
    delivered = df[df["order_status"] == "Delivered"]

    agg = (
        delivered.groupby("region")
        .agg(
            revenue  = ("total_amount", "sum"),
            orders   = ("order_id",     "count"),
            avg_val  = ("total_amount", "mean"),
        )
        .reset_index()
    )
    agg["rev_score"] = normalize(agg["revenue"])
    agg["vol_score"] = normalize(agg["orders"])
    agg["val_score"] = normalize(agg["avg_val"])

    agg["impact_score"] = (
        agg["rev_score"] * 0.60 +
        agg["vol_score"] * 0.25 +
        agg["val_score"] * 0.15
    ).round(1)

    agg = agg.sort_values("impact_score", ascending=False)
    return agg


if __name__ == "__main__":
    print("🚀 RevenueRadar — Impact Scorer")
    print("=" * 55)

    engine = get_engine()
    df     = pd.read_sql(f"SELECT * FROM {CLEANED_TABLE}", engine)
    df["sale_date"] = pd.to_datetime(df["sale_date"])

    cat_scores = score_categories(df)
    reg_scores = score_regions(df)

    print("\n📊 CATEGORY IMPACT SCORES:")
    print(cat_scores[["category","revenue","growth_pct",
                       "impact_score","grade"]].to_string(index=False))

    print("\n🗺️  REGION IMPACT SCORES:")
    print(reg_scores[["region","revenue","orders",
                       "impact_score"]].to_string(index=False))

    print("\n✅ Impact scoring complete!")
    print("➡️  Agla step: python 04_prediction/churn_model.py")