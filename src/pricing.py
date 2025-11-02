import numpy as np
import pandas as pd
from config import MARGIN_PCT

def summarize_recent_fair_ppsqm(recent_df: pd.DataFrame) -> dict:
    """
    Fair ppsqm = median of recent comps (also return IQR & count).
    """
    if recent_df.empty:
        return dict(ok=False, fair_ppsqm=None, message="No recent comps.")
    s = recent_df['price_per_sqm'].dropna().astype(float)
    if s.empty:
        return dict(ok=False, fair_ppsqm=None, message="No valid ppsqm in comps.")
    fair = float(np.median(s))
    q1, q3 = float(np.percentile(s, 25)), float(np.percentile(s, 75))
    return dict(ok=True, fair_ppsqm=fair, q1=q1, q3=q3, iqr=q3-q1, n=len(s))

def price_range_from_fair_ppsqm(fair_ppsqm: float, size_sqm: float,
                                margin_pct: float = MARGIN_PCT) -> tuple[float, float]:
    base = fair_ppsqm * size_sqm
    return float(base*(1-margin_pct)), float(base*(1+margin_pct))

def decision_vs_asking(fair_ppsqm, size_sqm, asking_price_ils, margin_pct):
    """
    Decide if the asking price is cheap/fair/expensive relative to a fair range.
    asking_price_ils: integer price in ILS.
    """
    fair_price = fair_ppsqm * size_sqm
    low = fair_price * (1 - margin_pct)
    high = fair_price * (1 + margin_pct)

    label = "fair"
    if asking_price_ils < low:
        label = "cheap"
    elif asking_price_ils > high:
        label = "expensive"

    diff_pct = (asking_price_ils - fair_price) / fair_price * 100.0

    return {
        "label": label,
        "diff_pct": diff_pct,
        "fair_range": [low, high],
    }
