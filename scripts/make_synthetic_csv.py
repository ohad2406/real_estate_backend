# scripts/make_synthetic_csv.py
# Generate a multi-city synthetic real-estate transactions CSV for testing:
# - Multiple cities and neighborhoods
# - Varying rooms (2/3/4) and sizes
# - Recent (last 2y) + long-term (~10y back, buckets ~ every 2y, 1-5 deals per bucket)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path

random.seed(7)
np.random.seed(7)

TODAY = datetime(2025, 10, 24)

CITIES = [
    ("Tel Aviv-Yafo", ["Old North", "Florentin", "Neve Tzedek"]),
    ("Jerusalem", ["Rehavia", "Katamon", "Talbiya"]),
    ("Haifa", ["Carmel Center", "Hadar", "German Colony"]),
    ("Rishon LeZion", ["West", "Neve Dekalim", "Ramat Eliyahu"]),
    ("Ramat Gan", ["Merom Nave", "Ramat Chen", "Borochov"]),
]
ROOMS = [2.0, 3.0, 4.0]
BASE_PPSQM = {
    "Tel Aviv-Yafo": 52000,
    "Jerusalem": 42000,
    "Haifa": 26000,
    "Rishon LeZion": 35000,
    "Ramat Gan": 38000,
}

def random_address():
    streets = ["Herzl", "Dizengoff", "Jabotinsky", "Ben Yehuda", "Bialik", "Hashalom", "Allenby"]
    return f"{np.random.choice(streets)} {np.random.randint(1, 251)}"

def gen_block(city, neighborhood, rooms,
              base_size=70, n_recent=20, years_back=10, bucket_span_days=720):
    """
    Build a block of transactions for (city, neighborhood, rooms).
    - Recent: n_recent deals in the last 2 years
    - Long-term: up to ~10 years back, buckets ~ every 2 years, 1–5 deals per bucket
    """
    rows = []
    base_ppsqm = BASE_PPSQM[city]

    # Adjust per-room price tendency (purely synthetic):
    # 2-room slightly cheaper per sqm, 4-room slightly higher per sqm.
    def room_factor(r):
        return 1.00 if r == 3.0 else (0.90 if r == 2.0 else 1.08)

    # Recent (within 2 years)
    for i in range(n_recent):
        d = TODAY - timedelta(days=int(np.random.randint(0, 2*365)))
        size = float(max(35, round(np.random.normal(base_size, 8), 1)))
        ppsqm = float(max(18000, round(np.random.normal(base_ppsqm * room_factor(rooms),
                                                        0.06 * base_ppsqm), 2)))
        price = int(round(ppsqm * size))
        rows.append(dict(
            tx_id=f"R_{city[:2]}_{neighborhood[:2]}_{rooms}_{i+1}",
            deal_date=d.strftime("%Y-%m-%d"),
            city=city,
            neighborhood=neighborhood,
            address=random_address(),
            size_sqm=size,
            rooms=float(rooms),
            floor=int(np.random.randint(0, 8)),
            year_built=int(np.random.randint(1950, 2020)),
            price_ils=price
        ))

    # Long-term (up to 10 years back), buckets ~ every 2 years
    bucket_end = TODAY - timedelta(days=2*365)  # start before recent window
    start_limit = TODAY - timedelta(days=years_back*365)
    while bucket_end > start_limit:
        bucket_start = bucket_end - timedelta(days=bucket_span_days)
        # 1..5 deals per bucket to avoid outlier reliance
        for _ in range(np.random.randint(1, 6)):
            d = bucket_start + timedelta(days=int(np.random.randint(0, bucket_span_days)))
            if d < start_limit or d >= TODAY - timedelta(days=2*365):
                continue
            years_ago = (TODAY - d).days / 365.25
            # ~1.6% annual appreciation forward → older deals slightly cheaper
            trend = (1 - 0.016) ** years_ago
            size = float(max(35, round(np.random.normal(base_size, 9), 1)))
            ppsqm = float(max(16000, round(np.random.normal(base_ppsqm * room_factor(rooms) * trend,
                                                            0.07 * base_ppsqm), 2)))
            price = int(round(ppsqm * size))
            rows.append(dict(
                tx_id=f"L_{city[:2]}_{neighborhood[:2]}_{rooms}_{int(d.timestamp())}",
                deal_date=d.strftime("%Y-%m-%d"),
                city=city,
                neighborhood=neighborhood,
                address=random_address(),
                size_sqm=size,
                rooms=float(rooms),
                floor=int(np.random.randint(0, 8)),
                year_built=int(np.random.randint(1945, 2015)),
                price_ils=price
            ))
        bucket_end = bucket_start

    return rows

def main():
    rows = []
    for city, n_list in CITIES:
        for nhood in n_list:
            for r in ROOMS:
                base_size = 70 if r == 3.0 else (60 if r == 2.0 else 85)
                rows.extend(gen_block(city, nhood, r,
                                      base_size=base_size,
                                      n_recent=20, years_back=10, bucket_span_days=720))
    df = pd.DataFrame(rows).sample(frac=1, random_state=7)\
                           .sort_values("deal_date", ascending=False)\
                           .reset_index(drop=True)

    out_dir = Path(__file__).resolve().parents[1] / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "transactions.csv"   # overwrite your current CSV
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} rows → {out_path}")

if __name__ == "__main__":
    main()