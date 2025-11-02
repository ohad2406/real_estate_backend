import sys, requests
from urllib.parse import urlencode

BASE = "https://data.gov.il/api/3/action/package_search"

q = sys.argv[1] if len(sys.argv) > 1 else "נדל\"ן"
params = {"q": q, "rows": 20}  # הגדל rows אם צריך
r = requests.get(BASE, params=params, timeout=30)
r.raise_for_status()
data = r.json()
if not data.get("success"):
    raise SystemExit("package_search failed")

results = data["result"]["results"]
print(f"Found {len(results)} datasets for query: {q}\n")
for ds in results:
    print("DATASET TITLE:", ds.get("title"))
    print("DATASET ID:", ds.get("id"))
    print("NUM RESOURCES:", len(ds.get("resources", [])))
    print("-"*60)
