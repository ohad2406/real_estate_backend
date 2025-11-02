# 🏠 Real Estate Valuation API (CSV-based)

Small FastAPI backend that evaluates an apartment's asking price using recent comparable sales and long-term trends.  
**Data source (for now):** a local CSV at `data/transactions.csv` (synthetic/dev).

## ✨ What it does
- Filters comparable sales in the same **city + neighborhood**, **exact rooms**, and **±8%** size tolerance.
- Computes a fair price per sqm from the last **2 years** and classifies asking price as _cheap / fair / expensive_ with a **±4%** band.
- Returns recent KPIs (avg/min/max), long-term bucketed means (~2-year windows across ~10 years), and sales volume of the last 5 years.

## 🗂 Project layout

## 🧰 Prerequisites
- Python 3.10+ (tested on macOS)
- CSV at `data/transactions.csv` (already provided)

## 📦 Install
```bash
python3 -m pip install -r requirements.txt