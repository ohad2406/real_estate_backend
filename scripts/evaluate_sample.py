import os
from dotenv import load_dotenv
from pathlib import Path

# PYTHONPATH -> src
import sys
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
from gov_data_client import GovDataClient
from orchestrator import evaluate_listing

load_dotenv()
RESOURCE = os.getenv("DATA_GOV_RESOURCE_ID")
BASE = os.getenv("DATA_GOV_BASE", "https://data.gov.il/api/3/action").rstrip("/")

if not RESOURCE:
    raise SystemExit("Missing DATA_GOV_RESOURCE_ID in .env")

client = GovDataClient(base_url=BASE)

# שלב 1: בדוק קודם את הסכימה עם scripts/inspect_schema.py וקבל את שמות העמודות המדויקים.
# כאן שמתי שמות "לוגיים"; תצטרך להתאים אותם לשמות האמיתיים במשאב שלך.
SQL = """
SELECT deal_date, city, neighborhood, address, size_sqm, rooms, price_ils
FROM "table"
WHERE city = 'Tel Aviv-Yafo'
  AND rooms = 3
  AND deal_date >= '2023-01-01'
ORDER BY deal_date DESC
LIMIT 5000
"""

try:
    df = client.datastore_search_sql(RESOURCE, SQL)
except Exception as e:
    raise SystemExit(
        "Adjust SQL/table/columns to match the actual dataset. "
        f"Run scripts/inspect_schema.py first. Error: {e}"
    )

if df.empty:
    raise SystemExit("No records returned. Fix SQL/columns or filters.")

# טיפוסים וניקוי
if "deal_date" in df.columns:
    df["deal_date"] = pd.to_datetime(df["deal_date"], errors="coerce")
for c in ["size_sqm", "rooms", "price_ils"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

df = df.dropna(subset=["deal_date", "city", "size_sqm", "price_ils"])
df = df[(df["size_sqm"] > 0) & (df["price_ils"] > 0)]
df["price_per_sqm"] = df["price_ils"] / df["size_sqm"]
df["city_norm"] = df["city"].astype(str).str.lower().str.strip()
df["neigh_norm"] = df.get("neighborhood", "").astype(str).str.lower().str.strip()

# שלב 2: הערכת דירה לדוגמה (התאם עיר/שכונה/חדרים/מ"ר/מחיר)
res = evaluate_listing(
    transactions_df=df,
    city="Tel Aviv-Yafo",
    neighborhood="Old North",
    rooms=3.0,                 # התאמת חדרים מדויקת (exact)
    size_sqm=70,
    asking_price_ils=3_450_000
)

# תוצאה
import json
print(json.dumps(res, ensure_ascii=False, indent=2))
