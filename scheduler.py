# ============================================================
# scheduler.py — RevenueRadar
# ============================================================
# YEH FILE KYA KARTI HAI:
#   Har roz ek fixed time pe automatically puri pipeline
#   chalata hai. Python terminal khula rakhna padega.
#
# LOGIC:
#   'schedule' library ek simple cron-like scheduler hai.
#   .every().day.at("09:00") matlab roz 9 baje chalao.
#   while True loop continuously check karta rehta hai.
#
# RUN: python 06_scheduler/scheduler.py
# NOTE: Terminal band mat karna — ya Windows Task Scheduler use karo
# ============================================================

import schedule
import time
import subprocess
import sys
import os
from datetime import datetime

# Root path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_full_pipeline():
    """
    Puri pipeline ek baar chalata hai.
    Scheduler yahi function call karega daily.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*50}")
    print(f"🕐 SCHEDULED RUN — {now}")
    print(f"{'='*50}")

    try:
        result = subprocess.run(
            [sys.executable,
             os.path.join(ROOT, "06_scheduler", "run_pipeline.py")],
            capture_output = False,
            text           = True
        )
        if result.returncode == 0:
            print(f"✅ Pipeline successful — {now}")
        else:
            print(f"❌ Pipeline failed — check errors above")
    except Exception as e:
        print(f"❌ Scheduler error: {e}")


def start_scheduler(run_time="09:00"):
    """
    LOGIC:
      schedule.every().day.at("09:00") → roz 9 baje
      schedule.run_pending() → check karo koi job pending hai?
      time.sleep(60) → 60 seconds wait karo phir dobara check
    """
    print("🚀 RevenueRadar — Automated Scheduler")
    print("=" * 55)
    print(f"  Daily run time: {run_time}")
    print(f"  Server time   : {datetime.now().strftime('%H:%M:%S')}")
    print(f"  Press Ctrl+C to stop\n")

    # Schedule set karo
    schedule.every().day.at(run_time).do(run_full_pipeline)

    # Optional: Test ke liye abhi bhi ek baar chalao
    # schedule.every(1).minutes.do(run_full_pipeline)  # ← test mode

    print(f"⏰ Next run scheduled at: {run_time} daily")
    print("  (Terminal band mat karna!)\n")

    # ── Infinite loop — scheduler run karta rehta hai ────────
    while True:
        schedule.run_pending()
        time.sleep(60)   # Har 60 seconds mein check


if __name__ == "__main__":
    # Default 9 AM — change karo agar alag time chahiye
    RUN_AT = "09:00"

    # Command line se time pass kar sakte ho:
    # python scheduler.py 14:30
    if len(sys.argv) > 1:
        RUN_AT = sys.argv[1]

    try:
        start_scheduler(run_time=RUN_AT)
    except KeyboardInterrupt:
        print("\n\n⛔ Scheduler stopped by user.")
        print("   Dobara chalane ke liye:")
        print("   python 06_scheduler/scheduler.py")