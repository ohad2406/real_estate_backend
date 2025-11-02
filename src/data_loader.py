import pandas as pd

def load_transactions_csv(path: str) -> pd.DataFrame:
    """
    Fallback loader if a resource is only published as CSV (official).
    Expected/rename mapping can be adjusted here.
    """
    df = pd.read_csv(path)
    rename_map = {
        'תאריך עסקה': 'deal_date',
        'עיר': 'city',
        'שכונה': 'neighborhood',
        'כתובת': 'address',
        'מספר חדרים': 'rooms',
        'שטח': 'size_sqm',
        'מחיר': 'price_ils'
    }
    for k, v in rename_map.items():
        if k in df.columns and v not in df.columns:
            df = df.rename(columns={k: v})

    df['deal_date'] = pd.to_datetime(df['deal_date'], errors='coerce')
    for c in ['size_sqm', 'rooms', 'price_ils']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    df = df.dropna(subset=['deal_date', 'city', 'size_sqm', 'price_ils'])
    df = df[(df['size_sqm'] > 0) & (df['price_ils'] > 0)]

    df['price_per_sqm'] = df['price_ils'] / df['size_sqm']
    df['city_norm'] = df['city'].astype(str).str.lower().str.strip()
    df['neigh_norm'] = df.get('neighborhood', '').astype(str).str.lower().str.strip()
    return df
