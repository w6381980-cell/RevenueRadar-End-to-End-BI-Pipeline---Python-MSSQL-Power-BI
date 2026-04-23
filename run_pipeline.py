# ============================================================
# run_pipeline.py — RevenueRadar MASTER FILE
# ============================================================
# YEH FILE KYA KARTI HAI:
#   Puri pipeline ek baar mein chalata hai — sequence mein.
#   Yeh file sabse important hai. Sirf yahi chalao:
#
#   python 06_scheduler/run_pipeline.py
#
# SEQUENCE:
#   1. Data generate karo
#   2. MSSQL mein load karo
#   3. Clean karo
#   4. Cleaned data MSSQL mein save karo
#   5. KPIs calculate karo
#   6. Forecast chalao
#   7. Excel MIS report banao
#   8. Done!
# ============================================================

import sys, os
import time
from datetime import datetime

# Root path fix
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

def print_step(num, msg):
    """Step header print karo."""
    print(f"\n{'='*60}")
    print(f"  STEP {num}: {msg}")
    print(f"{'='*60}")

def run_pipeline():
    start_time = time.time()

    print("\n" + "🎯"*30)
    print(f"  REVENUERADAR — FULL PIPELINE")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯"*30)

    # ── STEP 1: Data Generation ──────────────────────────────
    print_step(1, "DATA GENERATION (Faker)")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "gen", os.path.join(ROOT, "01_data_generation/generate_fake_data.py")
        )
        # Direct import karne ki bajaye subprocess use karo
        import subprocess
        result = subprocess.run(
            [sys.executable,
             os.path.join(ROOT, "01_data_generation/generate_fake_data.py")],
            capture_output=False
        )
        if result.returncode != 0:
            raise Exception("Data generation failed")
        print("  ✅ STEP 1 COMPLETE")
    except Exception as e:
        print(f"  ❌ STEP 1 FAILED: {e}")
        sys.exit(1)

    # ── STEP 2: Load to MSSQL ────────────────────────────────
    print_step(2, "LOAD TO MSSQL (raw_sales)")
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable,
             os.path.join(ROOT, "01_data_generation/load_to_mssql.py")],
            capture_output=False
        )
        if result.returncode != 0:
            raise Exception("MSSQL load failed")
        print("  ✅ STEP 2 COMPLETE")
    except Exception as e:
        print(f"  ❌ STEP 2 FAILED: {e}")
        sys.exit(1)

    # ── STEP 3: Clean + Save to MSSQL ───────────────────────
    print_step(3, "DATA CLEANING + SAVE TO MSSQL (cleaned_sales)")
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable,
             os.path.join(ROOT, "02_data_cleaning/save_cleaned_to_mssql.py")],
            capture_output=False
        )
        if result.returncode != 0:
            raise Exception("Cleaning failed")
        print("  ✅ STEP 3 COMPLETE")
    except Exception as e:
        print(f"  ❌ STEP 3 FAILED: {e}")
        sys.exit(1)

    # ── STEP 4: KPI Engine ───────────────────────────────────
    print_step(4, "KPI CALCULATION")
    try:
        sys.path.insert(0, os.path.join(ROOT, "03_analytics"))
        from kpi_engine import load_clean_data, calculate_kpis
        df   = load_clean_data()
        kpis = calculate_kpis(df)
        print("  ✅ STEP 4 COMPLETE")
    except Exception as e:
        print(f"  ❌ STEP 4 FAILED: {e}")
        # Non-fatal — continue karo

    # ── STEP 5: Sales Forecast ───────────────────────────────
    print_step(5, "SALES FORECAST (Prophet ML)")
    try:
        sys.path.insert(0, os.path.join(ROOT, "04_prediction"))
        from sales_forecast import run_forecast
        from config.config import get_engine, CLEANED_TABLE
        import pandas as pd
        engine = get_engine()
        df_f   = pd.read_sql(f"SELECT * FROM {CLEANED_TABLE}", engine)
        df_f["sale_date"] = pd.to_datetime(df_f["sale_date"])
        run_forecast(df_f, forecast_days=90)
        print("  ✅ STEP 5 COMPLETE")
    except Exception as e:
        print(f"  ⚠️  STEP 5 SKIPPED (Prophet issue): {e}")
        # Non-fatal

    # ── STEP 6: Excel MIS Report ─────────────────────────────
    print_step(6, "EXCEL MIS REPORT GENERATION")
    try:
        sys.path.insert(0, os.path.join(ROOT, "05_reports"))
        from excel_mis_report import generate_mis_report
        mis_path = generate_mis_report()
        print(f"  📁 Report: {mis_path}")
        print("  ✅ STEP 6 COMPLETE")
    except Exception as e:
        print(f"  ❌ STEP 6 FAILED: {e}")

    # ── DONE ─────────────────────────────────────────────────
    elapsed = round(time.time() - start_time, 1)
    print("\n" + "✅"*30)
    print(f"\n  🎉 REVENUERADAR PIPELINE COMPLETE!")
    print(f"  ⏱️  Total time: {elapsed} seconds")
    print(f"  📁 Reports saved in: {os.path.join(ROOT, '08_output')}")
    print(f"  🕐 Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "✅"*30)


if __name__ == "__main__":
    run_pipeline()