from comps import recent_comps, longterm_buckets, longterm_bucket_summary
from pricing import summarize_recent_fair_ppsqm, decision_vs_asking
from growth import estimate_annual_appreciation
from stats import recent_two_years_stats, sales_counts_last5_years
from config import RECENT_YEARS, MARGIN_PCT

def evaluate_listing(transactions_df, city, neighborhood, rooms, size_sqm, asking_price_ils):
    """
    Orchestrate: recent comps → pricing decision → long-term trend → extra KPIs.
    Returns a single dict the frontend can consume.
    """
    messages = []

    # 1) recent comps (last 2y)
    rec = recent_comps(transactions_df, city, neighborhood, rooms, size_sqm)
    recent_summary = None
    decision = None

    if rec is None or len(rec) == 0:
        messages.append("No recent comps found with the given filters.")
    else:
        recent_summary = summarize_recent_fair_ppsqm(rec)
        if not recent_summary.get("ok"):
            messages.append("Not enough recent comps to compute a stable fair price.")
        else:
            decision = decision_vs_asking(
                fair_ppsqm=recent_summary["fair_ppsqm"],
                size_sqm=size_sqm,
                asking_price_ils=asking_price_ils,
                margin_pct=MARGIN_PCT,
            )

    # 2) long term (exclude last RECENT_YEARS by design in comps.longterm_buckets)
    lt = longterm_buckets(transactions_df, city, neighborhood, rooms, size_sqm)
    growth = estimate_annual_appreciation(lt)
    lt_summary = longterm_bucket_summary(lt)  # NEW: mean per bucket for charts

    # 3) extra KPIs on top of recent comps + area activity
    recent_kpis = recent_two_years_stats(rec)
    activity_5y = sales_counts_last5_years(transactions_df, city, neighborhood, rooms)

    return {
        "inputs": {
            "city": city,
            "neighborhood": neighborhood,
            "rooms": rooms,
            "size_sqm": size_sqm,
            "asking_price_ils": asking_price_ils,
        },
        "recent_comps": rec.to_dict(orient="records") if rec is not None else [],
        "recent_summary": recent_summary,
        "decision": decision,
        "recent_kpis": recent_kpis,                 # NEW (4,5,6)
        "longterm_buckets": lt.to_dict(orient="records") if lt is not None else [],
        "longterm_bucket_summary": lt_summary,      # NEW (3)
        "growth": growth,
        "sales_last5": activity_5y,                 # NEW (7)
        "messages": messages,
    }