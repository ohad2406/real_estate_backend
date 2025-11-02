import numpy as np
import pandas as pd
from config import LONGTERM_MIN

def estimate_annual_appreciation(longterm_df: pd.DataFrame) -> dict:
    """
    Estimate annual appreciation rate (CAGR approx) from long-term comps:
      - Regress log(price_per_sqm) on time (years since first point).
    Returns dict with ok flag, annual_pct, n_points, and a message.
    """
    n = len(longterm_df)
    if n < LONGTERM_MIN:
        return dict(ok=False, annual_pct=None, n_points=n,
                    message=f"Not enough long-term comps (need >= {LONGTERM_MIN}).")

    df = longterm_df.dropna(subset=['deal_date', 'price_per_sqm']).copy()
    if df.empty or df['price_per_sqm'].le(0).any():
        return dict(ok=False, annual_pct=None, n_points=n, message="Invalid ppsqm values.")

    t0 = df['deal_date'].min()
    df['t_years'] = (df['deal_date'] - t0).dt.days / 365.25
    if (df['t_years'].max() - df['t_years'].min()) < 0.5:
        return dict(ok=False, annual_pct=None, n_points=n, message="Time span too narrow.")

    y = np.log(df['price_per_sqm'].to_numpy())
    x = df['t_years'].to_numpy()
    A = np.vstack([x, np.ones_like(x)]).T
    slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]

    annual_pct = (np.exp(slope) - 1.0) * 100.0
    return dict(ok=True, annual_pct=float(annual_pct), n_points=int(n), message="ok")
