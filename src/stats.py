from __future__ import annotations
import pandas as pd
from datetime import datetime, timedelta

def recent_two_years_stats(recent_df: pd.DataFrame) -> dict:
    """
    Compute stats over the recent comps (last 2 years, already filtered).
    Returns:
      - avg_price_recent
      - min_price_recent
      - max_price_recent
      - count_above_avg_recent
    """
    out = {
        "avg_price_recent": None,
        "min_price_recent": None,
        "max_price_recent": None,
        "count_above_avg_recent": 0,
        "n": 0,
    }
    if recent_df is None or len(recent_df) == 0:
        return out

    df = recent_df.copy()
    df = df.dropna(subset=["price_ils"])
    if len(df) == 0:
        return out

    out["n"] = int(len(df))
    out["avg_price_recent"] = float(df["price_ils"].mean())
    out["min_price_recent"] = int(df["price_ils"].min())
    out["max_price_recent"] = int(df["price_ils"].max())
    out["count_above_avg_recent"] = int((df["price_ils"] > out["avg_price_recent"]).sum())
    return out

def sales_counts_last5_years(
    df_all: pd.DataFrame,
    city: str,
    neighborhood: str,
    rooms: float,
    today: datetime | None = None,
) -> dict:
    """
    Count how many sales happened in the last 5 years (same city, neighborhood, and rooms).
    Also return per-year counts for a pie/bar chart.
    """
    today = today or datetime.utcnow()
    cutoff = today - timedelta(days=5 * 365)

    # filter to same area and exact rooms (keeps consistency with comps logic)
    df = df_all.copy()
    df = df.dropna(subset=["deal_date"])
    df = df[
        (df["city_norm"] == city.strip().lower())
        & (df["neigh_norm"] == neighborhood.strip().lower())
        & (df["rooms"] == float(rooms))
        & (df["deal_date"] >= cutoff)
    ]

    if df.empty:
        return {"total": 0, "per_year": []}

    df["year"] = df["deal_date"].dt.year
    counts = df.groupby("year")["tx_id"].count().reset_index(name="count")
    # ensure latest first for pretty output
    counts = counts.sort_values("year", ascending=False)

    return {
        "total": int(counts["count"].sum()),
        "per_year": [{"year": int(r.year), "count": int(r["count"])} for _, r in counts.iterrows()],
    }
