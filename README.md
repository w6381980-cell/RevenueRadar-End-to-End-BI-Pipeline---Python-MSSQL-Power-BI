# 🚀 RevenueRadar — AI-Powered Business Intelligence System

An end-to-end Data Analytics & Business Intelligence project that transforms raw data into actionable insights using Python, SQL Server, and Power BI.

---

## 📊 Project Overview

RevenueRadar is a complete analytics pipeline that:

- Generates realistic business data (50,000+ rows)
- Cleans and processes raw data
- Stores data in MSSQL
- Performs KPI analysis
- Forecasts future revenue trends
- Generates automated reports (PDF + Excel)
- Visualizes insights using Power BI Dashboard

---

## 🧠 Key Features

✅ Automated Data Pipeline  
✅ Data Cleaning & Quality Improvement  
✅ MSSQL Database Integration  
✅ KPI & Business Metrics Calculation  
✅ Revenue Forecasting (Prophet)  
✅ PDF Reports (Impact, Prediction, Coach)  
✅ Excel MIS Report  
✅ Interactive Power BI Dashboard  

---

## 🛠️ Tech Stack

- **Python** (Pandas, NumPy, Faker, Prophet)
- **SQL Server (MSSQL)**
- **Power BI**
- **Matplotlib / Seaborn**
- **FPDF (PDF Reports)**
- **SQLAlchemy / PyODBC**

---

## ⚙️ Project Architecture
## 📂 Project Structure


revenue-radar-bi/
│
├── 01_data_generation/
├── 02_data_cleaning/
├── 03_kpi_analysis/
├── 04_forecasting/
├── 05_reports/
├── 06_scheduler/
├── 08_output/
├── config/
├── requirements.txt
└── README.md


---

## 🚀 How to Run

### 1. Install dependencies

pip install -r requirements.txt


### 2. Setup Database
- Create MSSQL database: `RevenueRadarDB`

### 3. Run Full Pipeline

python 06_scheduler/run_pipeline.py


### 4. Generate Reports

python 05_reports/impact_report.py
python 05_reports/prediction_report.py
python 05_reports/coach_report.py


---

## 📊 Power BI Dashboard

Connect Power BI to MSSQL and load:
- `cleaned_sales` table

Create visuals:
- KPI Cards
- Line Chart (Revenue Trend)
- Bar Charts (Category, Region)
- Donut Chart (Order Status)

---

## 📌 Future Improvements

- Real-time data streaming
- Deployment on cloud (Azure / AWS)
- API integration
- Web dashboard (Streamlit / Flask)

---

## 🤝 Connect With Me

If you like this project, feel free to connect and collaborate!

