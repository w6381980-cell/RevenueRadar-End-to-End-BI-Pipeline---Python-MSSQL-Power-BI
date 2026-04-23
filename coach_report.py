# ============================================================
# coach_report.py - RevenueRadar
# ============================================================
# YEH FILE KYA KARTI HAI:
#   Data dekh ke actionable coaching tips generate karta hai.
#   "Kya problem hai -> kya karna chahiye" format mein.
#   Sales team aur management dono ke liye useful.
#
# RUN: python 05_reports/coach_report.py
# OUTPUT: 08_output/coach_report_MMYYYY.pdf
# ============================================================

from fpdf import FPDF
import pandas as pd
import sys, os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.config import (get_engine, CLEANED_TABLE,
                            OUTPUT_DIR, COMPANY_NAME)

DARK_BLUE  = (26,  60, 107)
TEAL       = (15, 110, 86)
ORANGE     = (216, 90, 48)
AMBER      = (186, 117, 23)
LIGHT_GRAY = (245, 245, 245)
WHITE      = (255, 255, 255)
BLACK      = (30,  30,  30)
RED_C      = (178, 34,  34)
GREEN_C    = (29, 122,  74)

class CoachReport(FPDF):
    def __init__(self):
        super().__init__()
        self.set_doc_option('core_fonts_encoding', 'windows-1252')
    def header(self):
        self.set_fill_color(*TEAL)
        self.rect(0, 0, 210, 18, "F")
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*WHITE)
        self.set_xy(10, 4)
        self.cell(0, 10, "REVENUERADAR - DATA COACH REPORT")
        self.set_xy(0, 4)
        self.cell(200, 10, datetime.now().strftime("%B %Y"), align="R")
        self.ln(14)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 6,
                  f"RevenueRadar Coach | Page {self.page_no()}",
                  align="C")

    def section_title(self, title, color=None):
        c = color or TEAL
        self.set_fill_color(*c)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 8, f"  {title}", fill=True, ln=True)
        self.ln(3)
        self.set_text_color(*BLACK)

    def coach_card(self, priority, title, observation, action, impact):
        """
        Coach card: Ek problem + solution card.
        priority: HIGH / MEDIUM / LOW
        """
        color_map = {"HIGH": RED_C, "MEDIUM": AMBER, "LOW": GREEN_C}
        color     = color_map.get(priority, TEAL)

        y_start = self.get_y()
        # Priority badge
        self.set_fill_color(*color)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 8)
        self.set_x(10)
        self.cell(25, 6, f" {priority}", fill=True)
        self.set_x(37)
        self.set_fill_color(*LIGHT_GRAY)
        self.set_text_color(*BLACK)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 6, f" {title}", fill=True, ln=True)
        self.ln(1)

        # Observation
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(80, 80, 80)
        self.set_x(12)
        self.cell(25, 5, "OBSERVED:")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*BLACK)
        self.multi_cell(0, 5, observation)

        # Action
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(80, 80, 80)
        self.set_x(12)
        self.cell(25, 5, "ACTION:")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*BLACK)
        self.multi_cell(0, 5, action)

        # Impact
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*TEAL)
        self.set_x(12)
        self.cell(25, 5, "IMPACT:")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*BLACK)
        self.multi_cell(0, 5, impact)

        self.ln(5)

    def body_text(self, text):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*BLACK)
        self.set_x(10)
        self.multi_cell(0, 5, text)
        self.ln(2)


def generate_coach_report():
    print("📄 Coach Report generate ho rahi hai (PDF)...")

    # Data load karo
    engine    = get_engine()
    df        = pd.read_sql(f"SELECT * FROM {CLEANED_TABLE}", engine)
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    delivered = df[df["order_status"] == "Delivered"]
    returned  = df[df["order_status"] == "Returned"]

    # Stats compute karo
    ret_rate      = round(len(returned) / len(df) * 100, 2)
    avg_discount  = round(df["discount_pct"].mean(), 2)
    total_rev     = delivered["total_amount"].sum()
    total_disc    = df["discount_amt"].sum()
    disc_pct_rev  = round(total_disc / total_rev * 100, 2)

    # Monthly trend
    monthly = (
        delivered.groupby(["year","month"])["total_amount"]
        .sum().reset_index().sort_values(["year","month"])
    )
    if len(monthly) >= 2:
        growth = ((monthly.iloc[-1]["total_amount"] -
                   monthly.iloc[-2]["total_amount"]) /
                  monthly.iloc[-2]["total_amount"] * 100)
    else:
        growth = 0

    # Churn
    today   = df["sale_date"].max()
    cust_ag = delivered.groupby("customer_email")["sale_date"].max()
    churned = (cust_ag < today - pd.Timedelta(days=90)).sum()
    tot_c   = len(cust_ag)
    ch_rate = round(churned / tot_c * 100, 1) if tot_c else 0

    # Category performance
    cat_rev   = delivered.groupby("category")["total_amount"].sum()
    top_cat   = cat_rev.idxmax()
    low_cat   = cat_rev.idxmin()

    # Region analysis
    reg_rev   = delivered.groupby("region")["total_amount"].sum()
    top_reg   = reg_rev.idxmax()
    low_reg   = reg_rev.idxmin()

    # Weekend vs Weekday
    wk_rev    = delivered.groupby("is_weekend")["total_amount"].sum()

    # Build PDF
    pdf = CoachReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*TEAL)
    pdf.cell(0, 10, "Data Coach Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"{COMPANY_NAME} | AI-Generated Coaching Insights",
             ln=True, align="C")
    pdf.ln(8)

    # ── SECTION 1: Revenue Coaching ───────────────────────────
    pdf.section_title("01. REVENUE COACHING CARDS")
    pdf.ln(2)

    if growth < 0:
        pdf.coach_card(
            priority    = "HIGH",
            title       = "Revenue Decline Detected",
            observation = f"Revenue dropped {growth:.1f}% this month vs last month.",
            action      = ("1. Identify which category dropped most.\n"
                           "2. Run targeted discount campaign this week.\n"
                           "3. Check if any supply/inventory issue."),
            impact      = "Potential recovery of INR 2-5L with quick promotions."
        )
    else:
        pdf.coach_card(
            priority    = "LOW",
            title       = "Revenue Growth on Track",
            observation = f"Revenue grew {growth:.1f}% this month.",
            action      = ("1. Maintain current marketing spend.\n"
                           "2. Scale up best-performing category.\n"
                           "3. Cross-sell to existing customers."),
            impact      = "Compounding growth if momentum maintained."
        )

    # ── SECTION 2: Discount Coaching ─────────────────────────
    pdf.section_title("02. DISCOUNT STRATEGY COACHING")
    pdf.ln(2)

    disc_priority = "HIGH" if avg_discount > 20 else "MEDIUM" if avg_discount > 10 else "LOW"
    pdf.coach_card(
        priority    = disc_priority,
        title       = f"Average Discount at {avg_discount}%",
        observation = (f"Discounts are consuming {disc_pct_rev}% of revenue. "
                       f"Total discounts given: INR {total_disc/1e6:.2f}M."),
        action      = ("1. Cap discounts at 15% for Electronics/Appliances.\n"
                       "2. Offer discounts only to inactive customers.\n"
                       "3. A/B test: 10% vs 20% discount response rate."),
        impact      = f"Reducing avg discount by 5% saves INR {total_disc*0.05/1e6:.2f}M annually."
    )

    # ── SECTION 3: Churn Coaching ────────────────────────────
    pdf.section_title("03. CUSTOMER RETENTION COACHING")
    pdf.ln(2)

    ch_priority = "HIGH" if ch_rate > 30 else "MEDIUM" if ch_rate > 15 else "LOW"
    pdf.coach_card(
        priority    = ch_priority,
        title       = f"Customer Churn Rate: {ch_rate}%",
        observation = (f"{churned:,} customers inactive for 90+ days "
                       f"({ch_rate}% of {tot_c:,} total customers)."),
        action      = ("1. Send WIN-BACK email to all inactive customers.\n"
                       "2. Offer 20% discount valid for 7 days only.\n"
                       "3. Segment by last category -> personalize offer.\n"
                       "4. Set up automated 60-day inactivity trigger."),
        impact      = f"Recovering 25% of churned customers = INR {churned*0.25*delivered['total_amount'].mean()/1e6:.2f}M additional revenue."
    )

    # ── SECTION 4: Category Coaching ─────────────────────────
    pdf.section_title("04. CATEGORY COACHING")
    pdf.ln(2)

    pdf.coach_card(
        priority    = "LOW",
        title       = f"Double Down on '{top_cat}'",
        observation = f"'{top_cat}' is the #1 revenue category.",
        action      = ("1. Increase inventory 20% before next month.\n"
                       "2. Bundle products from this category.\n"
                       "3. Feature on homepage/top banner."),
        impact      = "20% inventory increase could yield 15% more revenue from this category."
    )

    pdf.coach_card(
        priority    = "MEDIUM",
        title       = f"Revive '{low_cat}' Category",
        observation = f"'{low_cat}' has the lowest revenue contribution.",
        action      = ("1. Review pricing - may be overpriced vs market.\n"
                       "2. Create combo offers with top category.\n"
                       "3. If consistently low for 3 months - consider dropping."),
        impact      = "Bundle strategy can increase attach rate by 10-20%."
    )

    # ── SECTION 5: Return Rate Coaching ──────────────────────
    pdf.section_title("05. RETURN RATE COACHING")
    pdf.ln(2)

    ret_priority = "HIGH" if ret_rate > 15 else "MEDIUM" if ret_rate > 10 else "LOW"
    pdf.coach_card(
        priority    = ret_priority,
        title       = f"Return Rate at {ret_rate}%",
        observation = (f"{len(returned):,} orders returned out of {len(df):,} total "
                       f"({ret_rate}% return rate)."),
        action      = ("1. Identify which products have highest return rates.\n"
                       "2. Improve product descriptions and images.\n"
                       "3. Add size guides for Fashion category.\n"
                       "4. Introduce 'exchange instead of return' policy."),
        impact      = f"Reducing return rate by 3% saves INR {len(returned)*0.03*delivered['total_amount'].mean()/1e6:.2f}M in reverse logistics."
    )

    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f"coach_report_{datetime.now().strftime('%b%Y')}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)
    pdf.output(filepath)
    print(f"✅ Coach Report saved: {filepath}")
    return filepath


if __name__ == "__main__":
    print("🚀 RevenueRadar - Coach Report Generator")
    print("=" * 55)
    path = generate_coach_report()
    print(f"\n📁 Open karo: {path}")
    print("➡️  Agla step: python 05_reports/email_sender.py")