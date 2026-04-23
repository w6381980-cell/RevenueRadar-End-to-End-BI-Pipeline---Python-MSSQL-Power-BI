# ============================================================
# config.py — RevenueRadar
# ============================================================
# YEH FILE KYA KARTI HAI:
#   Sari project ki settings ek jagah rakhi hain.
#   Baaki sari files yahan se import karengi.
#   Agar kuch change karna ho (server, db name) toh
#   sirf yahi ek file badalni padegi — baaki sab auto-update.
# ============================================================

# ── DATABASE SETTINGS ──────────────────────────────────────
# Tera actual SQL Server instance name
SERVER   = r"LAPTOP-LG4BEQ1J\SQLEXPRESS"

# Yeh database SSMS mein banayenge (Step 2 mein)
DATABASE = "RevenueRadarDB"

# Windows Authentication use kar rahe hain (password nahi chahiye)
# Agar SQL Server Login chahiye toh UID/PWD add karna
USE_WINDOWS_AUTH = True

# ── TABLE NAMES ─────────────────────────────────────────────
RAW_TABLE     = "raw_sales"       # Original generated data yahan jayegi
CLEANED_TABLE = "cleaned_sales"   # Cleaned data yahan jayegi
KPI_TABLE     = "kpi_summary"     # Calculated KPIs yahan jayenge
FORECAST_TABLE= "sales_forecast"  # Prediction results yahan

# ── FILE PATHS ───────────────────────────────────────────────
import os

# Root folder automatically detect hoga
ROOT_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OUTPUT_DIR  = os.path.join(ROOT_DIR, "08_output")   # Reports yahan save honge
DATA_DIR    = os.path.join(ROOT_DIR, "01_data_generation")

# ── REPORT SETTINGS ─────────────────────────────────────────
COMPANY_NAME  = "RevenueRadar Retail Pvt. Ltd."
REPORT_MONTH  = "April 2025"
EMAIL_ENABLED = False   # True karo jab email configure karo

# ── CONNECTION STRING (pyodbc format) ───────────────────────
def get_connection_string():
    """
    LOGIC:
      pyodbc ko ek string chahiye jisme sab info ho.
      Windows Auth mein Trusted_Connection=yes likhte hain —
      matlab SQL Server Windows ka login use karta hai,
      alag password nahi chahiye.
    """
    return (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"Trusted_Connection=yes;"
    )

# ── SQLALCHEMY ENGINE (pandas ke liye) ──────────────────────
from sqlalchemy import create_engine
import urllib

def get_engine():
    """
    LOGIC:
      pandas ka to_sql() function directly pyodbc nahi samajhta.
      SQLAlchemy ek wrapper hai jo pandas aur pyodbc ke beech
      kaam karta hai — 'engine' banata hai connection ka.
    """
    params = urllib.parse.quote_plus(get_connection_string())
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
    return engine

# ── TEST CONNECTION ──────────────────────────────────────────
def test_connection():
    """
    Run: python config/config.py
    Yeh batayega ki MSSQL se connection ho raha hai ya nahi.
    """
    import pyodbc
    try:
        conn = pyodbc.connect(get_connection_string())
        print("✅ MSSQL Connection SUCCESSFUL!")
        print(f"   Server  : {SERVER}")
        print(f"   Database: {DATABASE}")
        conn.close()
    except Exception as e:
        print(f"❌ Connection FAILED: {e}")
        print("\n🔧 Fix karo:")
        print("  1. SQL Server running hai? — Services mein check karo")
        print("  2. ODBC Driver 17 installed hai? — Microsoft site se download karo")
        print("  3. Database 'RevenueRadarDB' bana hai SSMS mein?")

if __name__ == "__main__":
    test_connection()