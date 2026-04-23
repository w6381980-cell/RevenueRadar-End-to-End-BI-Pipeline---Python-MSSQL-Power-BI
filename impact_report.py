# ============================================================
# impact_report.py - RevenueRadar
# ============================================================
# YEH FILE KYA KARTI HAI:
#   Business Impact Report generate karta hai PDF format mein.
#   Kya badla, kyun badla, kiska impact pada - sab clearly
#   explain karta hai. Management ke liye ready-to-read.
#
# RUN: python 05_reports/impact_report.py
# OUTPUT: 08_output/impact_report_MMYYYY.pdf
# ============================================================

from fpdf import FPDF
import pandas as pd
import sys, os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.config import (get_engine, CLEANED_TABLE,
                            OUTPUT_DIR, COMPANY_NAME)

# ── Colors ───────────────────────────────────────────────────
DARK_BLUE  = (26,  60, 107)
MID_BLUE   = (46, 109, 164)
ORANGE     = (216, 90,  48)
LIGHT_GRAY = (245, 245, 245)
WHITE      = (255, 255, 255)
BLACK      = (30,  30,  30)
GREEN_C    = (29, 122,  74)
RED_C      = (178, 34,  34)

class ImpactReport(FPDF):
    def __init__(self):
        super().__init__()
        self.set_doc_option("core_fonts_encoding", "windows-1252")

    def header(self):
        self.set_fill_color(*DARK_BLUE)
        self.rect(0, 0, 210, 18, "F")
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*WHITE)
        self.set_xy(10, 4)
        self.cell(0, 10, "REVENUERADAR - BUSINESS IMPACT REPORT", align="L")
        self.set_xy(0, 4)
        self.cell(200, 10, datetime.now().strftime("%B %Y"), align="R")
        self.ln(14)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 6,
                  f"RevenueRadar Confidential | Page {self.page_no()} | "
                  f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}",
                  align="C")

    def section_title(self, title):
        self.set_fill_color(*MID_BLUE)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 8, f"  {title}", fill=True, ln=True)
        self.ln(3)
        self.set_text_color(*BLACK)

    def kpi_box(self, label, value, change=None, positive=True):
        """KPI box with colored change indicator."""
        x, y = self.get_x(), self.get_y()
        w = 60

        self.set_fill_color(*LIGHT_GRAY)
        self.rect(x, y, w, 22, "F")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(100, 100, 100)
        self.set_xy(x + 2, y + 2)
        self.cell(w - 4, 5, label, align="C")

        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*DARK_BLUE)
        self.set_xy(x + 2, y + 8)
        self.cell(w - 4, 7, str(value), align="C")

        if change:
            color = GREEN_C if positive else RED_C
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(*color)
            self.set_xy(x + 2, y + 16)
            self.cell(w - 4, 5, str(change), align="C")

        self.set_xy(x + w + 4, y)
        self.set_text_color(*BLACK)

    def body_text(self, text, indent=0):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*BLACK)
        self.set_x(10 + indent)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def insight_bullet(self, text, good=True):
        icon  = "+" if good else "!"
        color = GREEN_C if good else ORANGE
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*color)
        self.set_x(12)
        self.cell(6, 5, icon)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*BLACK)
        self.multi_cell(0, 5, text)


def generate_impact_report():
    print("📄 Impact Report generate ho rahi hai (PDF)...")

    # ── Load data ─────────────────────────────────────────────
    engine = get_engine()
    df     = pd.read_sql(f"SELECT * FROM {CLEANED_TABLE}", engine)
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    delivered = df[df["order_status"] == "Delivered"]

    # ── KPIs ─────────────────────────────────────────────────
    total_rev = delivered["total_amount"].sum()
    total_ord = len(delivered)
    aov       = total_rev / total_ord if total_ord else 0
    ret_rate  = round(
        len(df[df["order_status"]=="Returned"]) / len(df) * 100, 2
    )

    monthly = (
        delivered.groupby(["year","month"])["total_amount"]
        .sum().reset_index().sort_values(["year","month"])
    )
    if len(monthly) >= 2:
        this_m  = monthly.iloc[-1]["total_amount"]
        last_m  = monthly.iloc[-2]["total_amount"]
        mom_pct = round(((this_m - last_m) / last_m) * 100, 2)
    else:
        mom_pct = 0

    top_cat = delivered.groupby("category")["total_amount"].sum().idxmax()
    top_reg = delivered.groupby("region")["total_amount"].sum().idxmax()

    # ── Build PDF ─────────────────────────────────────────────
    pdf = ImpactReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title block
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(0, 10, "Business Impact Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, COMPANY_NAME, ln=True, align="C")
    pdf.cell(0, 5,
             f"Reporting Period: Jan 2023 - {datetime.now().strftime('%b %Y')}",
             ln=True, align="C")
    pdf.ln(8)

    # ── SECTION 1: Key Metrics ────────────────────────────────
    pdf.section_title("01. KEY PERFORMANCE METRICS")
    pdf.ln(2)

    metrics = [
        ("Total Revenue",   f"INR {total_rev/1e6:.2f}M",
         f"{mom_pct:+.1f}% MoM", mom_pct >= 0),
        ("Total Orders",    f"{total_ord:,}",
         None, True),
        ("Avg Order Value", f"INR {aov:,.0f}",
         None, True),
    ]
    for label, val, chg, pos in metrics:
        pdf.kpi_box(label, val, chg, pos)
    pdf.ln(28)

    pdf.kpi_box("Return Rate",   f"{ret_rate}%", None, ret_rate < 15)
    pdf.kpi_box("Top Category",  top_cat, None, True)
    pdf.kpi_box("Top Region",    top_reg, None, True)
    pdf.ln(28)

    # ── SECTION 2: Revenue Impact Analysis ───────────────────
    pdf.section_title("02. REVENUE IMPACT ANALYSIS")
    pdf.body_text(
        f"This month's revenue reached INR {this_m/1e6:.2f}M, representing a "
        f"{mom_pct:+.1f}% {'increase' if mom_pct >= 0 else 'decrease'} "
        f"compared to last month (INR {last_m/1e6:.2f}M). "
        f"The {top_cat} category continues to lead revenue contribution, "
        f"while the {top_reg} region remains the highest performing geography."
    )
    pdf.ln(3)

    # Category breakdown table
    cat_rev = (
        delivered.groupby("category")["total_amount"]
        .sum().sort_values(ascending=False).reset_index()
    )
    total_cat = cat_rev["total_amount"].sum()

    pdf.set_fill_color(*MID_BLUE)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 9)
    for col, w, txt in [(10,80,"Category"),(90,50,"Revenue (INR)"),(140,40,"Share %")]:
        pdf.set_xy(col, pdf.get_y())
        pdf.cell(w - 10, 7, txt, fill=True, border=0)
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*BLACK)
    for i, row in cat_rev.iterrows():
        share = round(row["total_amount"] / total_cat * 100, 1)
        fill_c = LIGHT_GRAY if i % 2 == 0 else WHITE
        pdf.set_fill_color(*fill_c)
        pdf.set_xy(10, pdf.get_y())
        pdf.cell(70, 6, row["category"], fill=True)
        pdf.cell(50, 6, f"INR {row['total_amount']/1e6:.2f}M", fill=True)
        pdf.cell(40, 6, f"{share}%", fill=True)
        pdf.ln(6)

    pdf.ln(5)

    # ── SECTION 3: Key Insights ───────────────────────────────
    pdf.section_title("03. KEY INSIGHTS & OBSERVATIONS")
    pdf.ln(2)

    insights_good = [
        f"{top_cat} category shows strongest revenue performance - focus marketing spend here.",
        f"{top_reg} region leads in sales volume - expand distribution network.",
        f"Average Order Value of INR {aov:,.0f} indicates healthy per-transaction spending.",
    ]
    insights_warn = [
        f"Return rate at {ret_rate}% - monitor product quality in high-return categories.",
        f"{'Revenue growth positive' if mom_pct >= 0 else 'Revenue declined'} {mom_pct:+.1f}% MoM - {'maintain momentum.' if mom_pct >= 0 else 'immediate action needed.'}",
    ]

    for ins in insights_good:
        pdf.insight_bullet(ins, good=True)
    for ins in insights_warn:
        pdf.insight_bullet(ins, good=(mom_pct >= 0))

    pdf.ln(5)

    # ── SECTION 4: Recommendations ───────────────────────────
    pdf.section_title("04. RECOMMENDED ACTIONS")
    pdf.ln(2)
    actions = [
        "1. Increase inventory for top categories before peak season.",
        "2. Launch loyalty program targeting customers with 90+ days of inactivity.",
        "3. Investigate high return rate categories - conduct root cause analysis.",
        "4. Expand presence in underperforming regions with targeted campaigns.",
        "5. Review discount strategy - current avg discount may be compressing margins.",
    ]
    for a in actions:
        pdf.body_text(a, indent=4)

    # ── Save ─────────────────────────────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f"impact_report_{datetime.now().strftime('%b%Y')}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)
    pdf.output(filepath)
    print(f"✅ Impact Report saved: {filepath}")
    return filepath


if __name__ == "__main__":
    print("🚀 RevenueRadar - Impact Report Generator")
    print("=" * 55)
    path = generate_impact_report()
    print(f"\n📁 Open karo: {path}")
    print("➡️  Agla step: python 05_reports/prediction_report.py")