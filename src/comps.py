from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict
from config import (
    SIZE_TOL, RECENT_YEARS, RECENT_MIN, RECENT_MAX,
    BUCKET_SPAN_DAYS, REQUIRE_SAME_NEIGHBORHOOD,
    ROOMS_MATCH_MODE, ROOMS_TOL,
    LONGTERM_YEARS, BUCKET_SAMPLES_PER_BUCKET
)

def _apply_match_filters(df: pd.DataFrame, city: str, neighborhood: str,
                         rooms: float, size_sqm: float) -> pd.DataFrame:
    """
    Core comparable filters:
      - City: must match (normalized)
      - Neighborhood: keep if configured and available (fallback to city if none)
      - Size within ±SIZE_TOL
      - Rooms: **EXACT** (per requirement), unless config changed
    """
    city_norm = str(city).lower().strip()
    neigh_norm = str(neighborhood).lower().strip()

    base = df[df['city_norm'] == city_norm].copy()
    if REQUIRE_SAME_NEIGHBORHOOD and 'neigh_norm' in base.columns:
        sub = base[base['neigh_norm'] == neigh_norm]
        if len(sub) >= 1:
            base = sub

    size_low, size_high = size_sqm * (1 - SIZE_TOL), size_sqm * (1 + SIZE_TOL)
    base = base[(base['size_sqm'] >= size_low) & (base['size_sqm'] <= size_high)]

    if ROOMS_MATCH_MODE == "exact":
        base = base[base['rooms'] == rooms]
    else:
        base = base[base['rooms'].between(rooms - ROOMS_TOL, rooms + ROOMS_TOL, inclusive='both')]

    return base

def recent_comps(df: pd.DataFrame, city: str, neighborhood: str,
                 rooms: float, size_sqm: float, today: datetime | None = None) -> pd.DataFrame:
    """
    Return up to RECENT_MAX (12) most recent comps from the last RECENT_YEARS,
    newest first. Requires exact rooms and ±size tolerance (handled upstream).    """
    today = today or datetime.utcnow()
    cutoff = today - timedelta(days=RECENT_YEARS * 365)

    cand = _apply_match_filters(df, city, neighborhood, rooms, size_sqm)
    cand = cand[cand['deal_date'] >= cutoff].sort_values('deal_date', ascending=False)

    if len(cand) >= RECENT_MAX:
        return cand.head(RECENT_MAX).reset_index(drop=True)
    if len(cand) >= RECENT_MIN:
        return cand.head(RECENT_MIN).reset_index(drop=True)
    return cand.reset_index(drop=True)

def longterm_buckets(df: pd.DataFrame, city: str, neighborhood: str,
                     rooms: float, size_sqm: float, today: datetime | None = None) -> pd.DataFrame:
    """
    Build long-term comparables over the last LONGTERM_YEARS.
    For each ~BUCKET_SPAN_DAYS (~2 years) window going backward,
    pick up to BUCKET_SAMPLES_PER_BUCKET most recent deals in that window.
    Returns a concatenated DataFrame, newest → oldest.
    """
    today = today or datetime.utcnow()
    cutoff_longterm = today - timedelta(days=LONGTERM_YEARS * 365)

    # Apply core filters (city/neighborhood/size tolerance/rooms exact)
    cand = _apply_match_filters(df, city, neighborhood, rooms, size_sqm).copy()
    if cand.empty:
        return pd.DataFrame(columns=df.columns)

    cand = cand.dropna(subset=['deal_date']).sort_values('deal_date', ascending=False)
    cand = cand[cand['deal_date'] >= cutoff_longterm]
    if cand.empty:
        return pd.DataFrame(columns=df.columns)

    all_rows = []
    bucket_end = today
    span = timedelta(days=BUCKET_SPAN_DAYS)

    while bucket_end > cutoff_longterm:
        bucket_start = bucket_end - span
        in_bucket = cand[(cand['deal_date'] <= bucket_end) & (cand['deal_date'] > bucket_start)]
        if len(in_bucket) > 0:
            picks = in_bucket.sort_values('deal_date', ascending=False).head(BUCKET_SAMPLES_PER_BUCKET)
            all_rows.append(picks)
        bucket_end = bucket_start

    if not all_rows:
        return pd.DataFrame(columns=df.columns)

    out = pd.concat(all_rows, ignore_index=True)
    out = out.sort_values('deal_date', ascending=False).reset_index(drop=True)
    return out

def longterm_bucket_summary(
    df_longterm: pd.DataFrame,
    today: datetime | None = None,
    bucket_span_days: int = BUCKET_SPAN_DAYS,
) -> List[Dict]:
    """
    Summarize long-term buckets by averaging per ~bucket_span_days window.
    Input df_longterm is expected to already be filtered (city/neighborhood/rooms/size)
    and cover up to LONGTERM_YEARS, EXCLUDING the last RECENT_YEARS if your pipeline does so.
    Returns a list of dicts sorted newest → oldest:
      - bucket_start, bucket_end, center_date
      - years_ago (float, from today to center_date)
      - n (count in bucket)
      - mean_ppsqm, mean_price_ils
    """
    if df_longterm.empty:
        return []

    today = today or datetime.utcnow()
    df = df_longterm.copy()
    df = df.dropna(subset=["deal_date"]).sort_values("deal_date", ascending=False)

    # Build contiguous rolling windows backward from `today - RECENT_YEARS`
    out = []
    bucket_end = df["deal_date"].max() + timedelta(seconds=1)  # make the max inclusive
    span = timedelta(days=bucket_span_days)
    cutoff_oldest = today - timedelta(days=LONGTERM_YEARS * 365)

    while bucket_end > cutoff_oldest:
        bucket_start = bucket_end - span
        in_bucket = df[(df["deal_date"] <= bucket_end) & (df["deal_date"] > bucket_start)]
        if len(in_bucket) > 0:
            mean_ppsqm = float(in_bucket["price_per_sqm"].mean())
            mean_price = float(in_bucket["price_ils"].mean())
            center = bucket_start + (span / 2)
            years_ago = (today - center).days / 365.25
            out.append(dict(
                bucket_start=bucket_start,
                bucket_end=bucket_end,
                center_date=center,
                years_ago=years_ago,
                n=int(len(in_bucket)),
                mean_ppsqm=mean_ppsqm,
                mean_price_ils=mean_price,
            ))
        bucket_end = bucket_start

    # newest → oldest (already so), convert datetimes to str so it's JSON-friendly (or let caller json.dumps(..., default=str))
    for b in out:
        b["bucket_start"] = b["bucket_start"].strftime("%Y-%m-%d")
        b["bucket_end"] = b["bucket_end"].strftime("%Y-%m-%d")
        b["center_date"] = b["center_date"].strftime("%Y-%m-%d")

    return out