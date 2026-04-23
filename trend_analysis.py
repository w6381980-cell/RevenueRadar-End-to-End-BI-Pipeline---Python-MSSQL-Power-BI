# ============================================================
# trend_analysis.py — RevenueRadar
# ============================================================
# YEH FILE KYA KARTI HAI:
#   Revenue trends analyze karta hai — monthly, weekly,
#   category-wise, region-wise. Charts bhi save karta hai.
#   Impact report aur Power BI dono yahan se data lenge.
#
# RUN: python 03_analytics/trend_analysis.py
# ============================================================

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.config import get_engine, CLEANED_TABLE, OUTPUT_DIR

def load_data():
    engine = get_engine()
    df     = pd.read_sql(f"SELECT * FROM {CLEANED_TABLE}", engine)
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    return df[df["order_status"] == "Delivered"]

def monthly_trend(df):
    """
    LOGIC:
      Har mahine ka total revenue calculate karo.
      phir MoM (Month-over-Month) % change nikalo:
      ((is_mahine - pichla_mahine) / pichla_mahine) * 100
    """
    monthly = (
        df.groupby(["year", "month", "month_name"])
        .agg(
            revenue = ("total_amount", "sum"),
            orders  = ("order_id",     "count"),
            avg_val = ("total_amount", "mean"),
        )
        .reset_index()
        .sort_values(["year", "month"])
    )
    monthly["revenue"]  = monthly["revenue"].round(2)
    monthly["avg_val"]  = monthly["avg_val"].round(2)

    # MoM growth
    monthly["mom_growth_pct"] = (
        monthly["revenue"].pct_change() * 100
    ).round(2)

    return monthly

def category_trend(df):
    """Category-wise revenue har mahine."""
    cat = (
        df.groupby(["year", "month", "category"])["total_amount"]
        .sum()
        .reset_index()
        .rename(columns={"total_amount": "revenue"})
        .sort_values(["year", "month"])
    )
    cat["revenue"] = cat["revenue"].round(2)
    return cat

def region_trend(df):
    """Region-wise performance."""
    reg = (
        df.groupby("region")
        .agg(
            revenue  = ("total_amount", "sum"),
            orders   = ("order_id",     "count"),
            avg_val  = ("total_amount", "mean"),
        )
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    reg["revenue"] = reg["revenue"].round(2)
    reg["avg_val"] = reg["avg_val"].round(2)
    return reg

def weekend_vs_weekday(df):
    """Weekend vs Weekday revenue comparison."""
    wk = (
        df.groupby("is_weekend")
        .agg(revenue=("total_amount","sum"), orders=("order_id","count"))
        .reset_index()
    )
    wk["label"] = wk["is_weekend"].map({True:"Weekend", False:"Weekday",
                                         1:"Weekend", 0:"Weekday"})
    return wk

def save_charts(monthly, category, region):
    """Sare charts ek figure mein save karo."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("RevenueRadar — Trend Analysis Dashboard",
                 fontsize=14, fontweight="bold", y=1.01)

    COLOR_MAIN = "#1A3C6B"
    COLOR_ACC  = "#D85A30"

    # ── Chart 1: Monthly Revenue Bar ─────────────────────────
    ax1   = axes[0, 0]
    label = monthly["month_name"].astype(str) + "\n" + monthly["year"].astype(str)
    bars  = ax1.bar(label, monthly["revenue"], color=COLOR_MAIN, alpha=0.85)
    ax1.set_title("Monthly Revenue", fontsize=11)
    ax1.set_ylabel("Revenue (₹)")
    ax1.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"₹{x/1e6:.1f}M")
    )
    ax1.tick_params(axis="x", labelsize=7, rotation=45)
    ax1.grid(axis="y", alpha=0.3)

    # ── Chart 2: MoM Growth Line ─────────────────────────────
    ax2 = axes[0, 1]
    mom = monthly.dropna(subset=["mom_growth_pct"])
    colors_bar = [COLOR_MAIN if v >= 0 else COLOR_ACC
                  for v in mom["mom_growth_pct"]]
    lbl2 = mom["month_name"].astype(str) + "\n" + mom["year"].astype(str)
    ax2.bar(lbl2, mom["mom_growth_pct"], color=colors_bar, alpha=0.85)
    ax2.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax2.set_title("Month-over-Month Growth %", fontsize=11)
    ax2.set_ylabel("Growth %")
    ax2.tick_params(axis="x", labelsize=7, rotation=45)
    ax2.grid(axis="y", alpha=0.3)

    # ── Chart 3: Region Revenue ───────────────────────────────
    ax3 = axes[1, 0]
    ax3.barh(region["region"], region["revenue"],
             color=COLOR_MAIN, alpha=0.85)
    ax3.set_title("Region-wise Revenue", fontsize=11)
    ax3.set_xlabel("Revenue (₹)")
    ax3.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"₹{x/1e6:.1f}M")
    )
    ax3.grid(axis="x", alpha=0.3)

    # ── Chart 4: Category Pie ─────────────────────────────────
    ax4     = axes[1, 1]
    cat_sum = category.groupby("category")["revenue"].sum()
    colors  = plt.cm.Set2(np.linspace(0, 1, len(cat_sum)))
    ax4.pie(cat_sum.values, labels=cat_sum.index,
            autopct="%1.1f%%", colors=colors,
            textprops={"fontsize": 8})
    ax4.set_title("Category Revenue Share", fontsize=11)

    plt.tight_layout()
    chart_path = os.path.join(OUTPUT_DIR, "trend_analysis.png")
    plt.savefig(chart_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 Charts saved: {chart_path}")
    return chart_path


if __name__ == "__main__":
    print("🚀 RevenueRadar — Trend Analysis Module")
    print("=" * 55)

    df       = load_data()
    monthly  = monthly_trend(df)
    category = category_trend(df)
    region   = region_trend(df)
    weekend  = weekend_vs_weekday(df)

    print("\n📈 Monthly Revenue (last 6 months):")
    print(monthly[["year","month_name","revenue","mom_growth_pct"]]
          .tail(6).to_string(index=False))

    print("\n🗺️  Region Performance:")
    print(region.to_string(index=False))

    chart_path = save_charts(monthly, category, region)

    print("\n✅ Trend analysis complete!")
    print("➡️  Agla step: python 03_analytics/impact_scorer.py")