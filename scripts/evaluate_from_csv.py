# scripts/evaluate_from_csv.py
import sys
from pathlib import Path

# ודא ש-PYTHONPATH כולל את src/
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from data_loader import load_transactions_csv
from orchestrator import evaluate_listing
import json

# 1) טען את קובץ העסקאות
df = load_transactions_csv(str(Path(__file__).resolve().parents[1] / "data" / "transactions.csv"))

# 2) הרצת הערכה לדירה לדוגמה (התאם ערכים אם תרצה)
res = evaluate_listing(
    transactions_df=df,
    city="Jerusalem",
    neighborhood="Rehavia",
    rooms=4.0,
    size_sqm=95,
    asking_price_ils=3_250_000
)

# 3) הדפס תוצאה יפה
print(json.dumps(res, ensure_ascii=False, indent=2, default=str))