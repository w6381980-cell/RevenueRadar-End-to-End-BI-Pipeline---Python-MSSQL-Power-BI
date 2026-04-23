# ============================================================
# prediction_report.py - RevenueRadar
# ============================================================
# YEH FILE KYA KARTI HAI:
#   Forecast aur churn prediction ko ek PDF report mein
#   compile karta hai. Management dekh sake ki aage kya hoga.
#
# RUN: python 05_reports/prediction_report.py
# OUTPUT: 08_output/prediction_report_MMYYYY.pdf
# ============================================================

from fpdf import FPDF
import pandas as pd
import sys, os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.config import (get_engine, CLEANED_TABLE,
                            OUTPUT_DIR, COMPANY_NAME)

DARK_BLUE  = (26,  60, 107)
MID_BLUE   = (46, 109, 164)
ORANGE     = (216, 90,  48)
LIGHT_GRAY = (245, 245, 245)
WHITE      = (255, 255, 255)
BLACK      = (30,  30,  30)
GREEN_C    = (29, 122,  74)
PURPLE     = (83,  74, 183)

class PredictionReport(FPDF):
    def __init__(self):
        super().__init__()
        self.set_doc_option('core_fonts_encoding', 'windows-1252')
    def header(self):
        self.set_fill_color(*DARK_BLUE)
        self.rect(0, 0, 210, 18, "F")
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*WHITE)
        self.set_xy(10, 4)
        self.cell(0, 10, "REVENUERADAR - PREDICTION & FORECAST REPORT")
        self.set_xy(0, 4)
        self.cell(200, 10, datetime.now().strftime("%B %Y"), align="R")
        self.ln(14)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 6,
                  f"RevenueRadar Confidential | Page {self.page_no()}",
                  align="C")

    def section_title(self, title):
        self.set_fill_color(*PURPLE)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 8, f"  {title}", fill=True, ln=True)
        self.ln(3)
        self.set_text_color(*BLACK)

    def body_text(self, text):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*BLACK)
        self.set_x(10)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def highlight_box(self, text, color=None):
        if color is None:
            color = PURPLE
        self.set_fill_color(*color)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 10)
        self.set_x(10)
        self.cell(0, 10, f"  {text}", fill=True, ln=True)
        self.set_text_color(*BLACK)
        self.ln(3)


def generate_prediction_report():
    print("📄 Prediction Report generate ho rahi hai (PDF)...")

    engine = get_engine()
    df     = pd.read_sql(f"SELECT * FROM {CLEANED_TABLE}", engine)
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    delivered = df[df["order_status"] == "Delivered"]

    # Monthly revenue for simple trend-based forecast
    monthly = (
        delivered.groupby(["year","month"])["total_amount"]
        .sum().reset_index().sort_values(["year","month"])
    )
    last_3_avg = monthly["total_amount"].tail(3).mean()
    last_month = monthly["total_amount"].iloc[-1] if len(monthly) else 0

    # Simple growth-based projection
    if len(monthly) >= 2:
        growth = (monthly["total_amount"].pct_change().tail(3).mean()) or 0.02
    else:
        growth = 0.02

    forecast_next1 = last_month * (1 + growth)
    forecast_next3 = sum(
        last_month * ((1 + growth) ** i) for i in range(1, 4)
    )

    # Churn stats
    today      = df["sale_date"].max()
    cust_agg   = delivered.groupby("customer_email")["sale_date"].max()
    churned    = (cust_agg < today - pd.Timedelta(days=90)).sum()
    total_cust = len(cust_agg)
    churn_rate = round(churned / total_cust * 100, 1) if total_cust else 0

    # Build PDF
    pdf = PredictionReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(0, 10, "Sales Prediction & Forecast Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, COMPANY_NAME, ln=True, align="C")
    pdf.ln(8)

    # ── SECTION 1: Revenue Forecast ───────────────────────────
    pdf.section_title("01. REVENUE FORECAST - NEXT 90 DAYS")
    pdf.ln(2)

    pdf.set_fill_color(*LIGHT_GRAY)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*BLACK)

    forecasts = [
        ("Next Month Forecast",  f"INR {forecast_next1/1e6:.2f}M",
         f"{growth*100:+.1f}% projected growth"),
        ("Next Quarter Forecast",f"INR {forecast_next3/1e6:.2f}M",
         "Cumulative 3-month projection"),
        ("Avg Monthly Baseline", f"INR {last_3_avg/1e6:.2f}M",
         "3-month rolling average"),
    ]

    for label, value, note in forecasts:
        pdf.set_fill_color(*LIGHT_GRAY)
        pdf.set_x(10)
        pdf.cell(80, 8, label,  fill=True)
        pdf.cell(50, 8, value,  fill=True, align="C")
        pdf.cell(0,  8, note,   fill=True)
        pdf.ln(9)

    pdf.ln(5)
    pdf.body_text(
        f"Based on historical trends, revenue is expected to "
        f"{'grow' if growth >= 0 else 'decline'} by "
        f"{abs(growth)*100:.1f}% month-over-month. "
        f"The next quarter projection stands at INR {forecast_next3/1e6:.2f}M. "
        f"These projections assume no major market disruptions."
    )

    # ── SECTION 2: Churn Forecast ────────────────────────────
    pdf.section_title("02. CUSTOMER CHURN FORECAST")
    pdf.ln(2)

    pdf.highlight_box(
        f"Current Churn Rate: {churn_rate}% ({churned:,} of {total_cust:,} customers at risk)",
        color=ORANGE if churn_rate > 20 else MID_BLUE
    )

    pdf.body_text(
        f"A total of {churned:,} customers have not placed an order in the last 90 days "
        f"and are classified as 'at risk of churning'. This represents {churn_rate}% "
        f"of the total customer base. Proactive engagement (email campaigns, discounts) "
        f"can recover an estimated 20-30% of these customers."
    )

    churn_revenue_risk = churned * (delivered["total_amount"].mean() if len(delivered) else 0)
    pdf.body_text(
        f"Estimated Revenue at Risk from Churn: INR {churn_revenue_risk/1e6:.2f}M "
        f"(based on average customer lifetime value)."
    )

    # ── SECTION 3: Category Forecast ─────────────────────────
    pdf.section_title("03. CATEGORY-WISE GROWTH FORECAST")
    pdf.ln(2)

    cat_monthly = (
        delivered.groupby(["category","year","month"])["total_amount"]
        .sum().reset_index().sort_values(["category","year","month"])
    )

    pdf.set_fill_color(*MID_BLUE)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_x(10)
    pdf.cell(70, 7, "Category", fill=True)
    pdf.cell(55, 7, "Last Month (INR)", fill=True, align="C")
    pdf.cell(55, 7, "Projected (INR)", fill=True, align="C")
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*BLACK)
    for i, (cat, grp) in enumerate(cat_monthly.groupby("category")):
        last_rev = grp["total_amount"].iloc[-1]
        if len(grp) >= 2:
            cat_g = (grp["total_amount"].pct_change().mean()) or growth
        else:
            cat_g = growth
        projected = last_rev * (1 + cat_g)

        fill_c = LIGHT_GRAY if i % 2 == 0 else WHITE
        pdf.set_fill_color(*fill_c)
        pdf.set_x(10)
        pdf.cell(70, 6, cat, fill=True)
        pdf.cell(55, 6, f"INR {last_rev/1e6:.2f}M", fill=True, align="C")
        pdf.cell(55, 6, f"INR {projected/1e6:.2f}M", fill=True, align="C")
        pdf.ln(6)

    pdf.ln(5)

    # ── SECTION 4: Forecast Chart ─────────────────────────────
    chart_path = os.path.join(OUTPUT_DIR, "forecast_chart.png")
    if os.path.exists(chart_path):
        pdf.section_title("04. FORECAST VISUALIZATION")
        pdf.ln(2)
        pdf.image(chart_path, x=10, w=190)
        pdf.ln(5)
    else:
        pdf.body_text(
            "Note: Forecast chart not found. "
            "Run 04_prediction/sales_forecast.py to generate it."
        )

    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f"prediction_report_{datetime.now().strftime('%b%Y')}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)
    pdf.output(filepath)
    print(f"✅ Prediction Report saved: {filepath}")
    return filepath


if __name__ == "__main__":
    print("🚀 RevenueRadar - Prediction Report Generator")
    print("=" * 55)
    path = generate_prediction_report()
    print(f"\n📁 Open karo: {path}")
    print("➡️  Agla step: python 05_reports/coach_report.py")