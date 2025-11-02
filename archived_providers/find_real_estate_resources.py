import requests
import pandas as pd

BASE = "https://data.gov.il/api/3/action"

# מילות חיפוש נפוצות (תוכל לשנות/להוסיף):
QUERIES = [
    "מקרקעין",
    "עסקאות",
    "מיסוי מקרקעין",
    "נדלן",
    "נדל\"ן",
    "דירות",
    "real estate",
    "property",
]

# מזהה ארגון רשות המסים בישראל (נשתמש כסינון אופציונלי)
TAX_AUTH_ORG_ID = "16d42d07-7d0d-4d65-a405-4071e2369cb9"

def package_search(q: str, org_id: str | None = None, rows: int = 50):
    params = {"q": q, "rows": rows}
    if org_id:
        params["fq"] = f"organization:{org_id}"
    r = requests.get(f"{BASE}/package_search", params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        return []
    return data["result"]["results"]

def package_show(dataset_id: str):
    r = requests.get(f"{BASE}/package_show", params={"id": dataset_id}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        return None
    return data["result"]

def datastore_fields(resource_id: str):
    r = requests.get(f"{BASE}/datastore_search", params={"resource_id": resource_id, "limit": 0}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        return None
    return pd.DataFrame(data["result"]["fields"])

def preview_rows(resource_id: str, limit: int = 5):
    r = requests.get(f"{BASE}/datastore_search", params={"resource_id": resource_id, "limit": limit}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        return None
    recs = data["result"]["records"]
    return pd.DataFrame(recs)

def main():
    seen_ds = set()
    print("=== Searching datasets (broad) ===\n")
    for q in QUERIES:
        results = package_search(q)
        print(f'Query: "{q}" → {len(results)} datasets')
        for ds in results:
            if ds["id"] in seen_ds:
                continue
            seen_ds.add(ds["id"])
            print(f'  • {ds.get("title")} | ID: {ds["id"]} | ORG: {ds.get("organization", {}).get("title")}')
        print()

    print("\n=== Searching by organization: Israel Tax Authority ===\n")
    results = package_search("", org_id=TAX_AUTH_ORG_ID, rows=100)
    print(f"Found {len(results)} datasets under Tax Authority\n")
    for ds in results:
        print(f'→ DATASET: {ds.get("title")} | ID: {ds["id"]}')
        pkg = package_show(ds["id"])
        if not pkg:
            continue
        resources = pkg.get("resources", [])
        for res in resources:
            print(f'   - RES: {res.get("name")}')
            print(f'     ID: {res.get("id")}')
            print(f'     FORMAT: {res.get("format")} | DATASTORE: {res.get("datastore_active")}')
            print(f'     URL: {res.get("url")}')
        print("-" * 70)

    print("""
Next steps:
1) Pick a RESOURCE_ID with DATASTORE=True from the list above.
2) Call datastore_fields(RESOURCE_ID) and preview_rows(RESOURCE_ID) below by uncommenting.
    """)

    # ── דוגמה ידנית (אחרי שבחרת RESOURCE_ID) ──
    # RESOURCE_ID = "PUT_RESOURCE_ID_HERE"
    # print("\\n=== Fields ===")
    # print(datastore_fields(RESOURCE_ID))
    # print("\\n=== Sample rows ===")
    # print(preview_rows(RESOURCE_ID, limit=5))

if __name__ == "__main__":
    main()