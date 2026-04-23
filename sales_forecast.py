# ============================================================
# sales_forecast.py — RevenueRadar
# ============================================================
# YEH FILE KYA KARTI HAI:
#   Facebook Prophet ML model se agale 90 din ka
#   revenue forecast karta hai.
#
#   PROPHET LOGIC:
#   - Time series data chahiye: date + value
#   - Prophet trend, seasonality (weekly, yearly) seekhta hai
#   - Future dates banata hai aur predict karta hai
#   - yhat = predicted value
#   - yhat_lower/upper = confidence interval (range)
#
# RUN: python 04_prediction/sales_forecast.py
# ============================================================

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")    # GUI nahi chahiye — file mein save
import matplotlib.pyplot as plt
import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.config import get_engine, CLEANED_TABLE, OUTPUT_DIR

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    print("⚠️  Prophet install nahi hai. Chalao: pip install prophet")

def prepare_prophet_data(df):
    """
    LOGIC: Prophet ko exact format chahiye —
           column 'ds' (date) aur 'y' (value)
    """
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    delivered = df[df["order_status"] == "Delivered"]

    daily_rev = (
        delivered.groupby("sale_date")["total_amount"]
        .sum()
        .reset_index()
        .rename(columns={"sale_date": "ds", "total_amount": "y"})
    )
    return daily_rev

def run_forecast(df, forecast_days=90):
    """
    PROPHET MODEL:
    1. Data feed karo
    2. Model train karo (fit)
    3. Future dates banao (make_future_dataframe)
    4. Predict karo (predict)
    """
    print(f"🔮 Prophet model train ho raha hai ({forecast_days} din ka forecast)...")

    prophet_df = prepare_prophet_data(df)
    print(f"   Training data: {len(prophet_df)} days")

    model = Prophet(
        yearly_seasonality  = True,    # Yearly trend seekhe
        weekly_seasonality  = True,    # Weekly pattern seekhe
        daily_seasonality   = False,   # Daily too noisy
        changepoint_prior_scale = 0.05 # Trend change sensitivity
    )

    model.fit(prophet_df)
    print("   ✅ Model trained!")

    # Future dates banao
    future = model.make_future_dataframe(periods=forecast_days)

    # Predict karo
    forecast = model.predict(future)

    # Sirf future rows rakho (historical nahi)
    forecast_only = forecast[forecast["ds"] > prophet_df["ds"].max()].copy()
    forecast_only["yhat"]       = forecast_only["yhat"].round(2)
    forecast_only["yhat_lower"] = forecast_only["yhat_lower"].round(2)
    forecast_only["yhat_upper"] = forecast_only["yhat_upper"].round(2)

    # Summary
    total_predicted = forecast_only["yhat"].sum()
    print(f"\n📈 Forecast Results:")
    print(f"   Next {forecast_days} days predicted revenue: ₹{total_predicted:,.2f}")
    print(f"   Avg daily revenue: ₹{forecast_only['yhat'].mean():,.2f}")
    print(f"   Peak day: {forecast_only.loc[forecast_only['yhat'].idxmax(), 'ds'].strftime('%Y-%m-%d')}")

    # Chart save karo
    _save_forecast_chart(prophet_df, forecast_only)

    return forecast_only, total_predicted

def _save_forecast_chart(historical, forecast):
    """Forecast chart PNG mein save karo."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(historical["ds"], historical["y"],
            color="#378ADD", linewidth=1.2, label="Historical Revenue")
    ax.plot(forecast["ds"], forecast["yhat"],
            color="#D85A30", linewidth=2, linestyle="--", label="Forecast")
    ax.fill_between(forecast["ds"],
                    forecast["yhat_lower"],
                    forecast["yhat_upper"],
                    alpha=0.2, color="#D85A30", label="Confidence Range")

    ax.set_title("RevenueRadar — 90-Day Sales Forecast", fontsize=14, pad=15)
    ax.set_xlabel("Date")
    ax.set_ylabel("Revenue (₹)")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    chart_path = os.path.join(OUTPUT_DIR, "forecast_chart.png")
    plt.savefig(chart_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"   📊 Chart saved: {chart_path}")


if __name__ == "__main__":
    print("🚀 RevenueRadar — Sales Forecast Module")
    print("=" * 55)

    engine = get_engine()
    df     = pd.read_sql(f"SELECT * FROM {CLEANED_TABLE}", engine)
    df["sale_date"] = pd.to_datetime(df["sale_date"])

    if PROPHET_AVAILABLE:
        forecast_df, total = run_forecast(df, forecast_days=90)
        print(f"\n✅ Forecast complete!")
    else:
        print("Prophet install karo: pip install prophet")

    print("➡️  Agla step: python 05_reports/excel_mis_report.py")