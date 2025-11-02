"""
Project configuration and matching thresholds.
Adjust here without touching the core logic.
"""

# --- matching tolerances ---
SIZE_TOL = 0.08
ROOMS_MATCH_MODE = "exact"
ROOMS_TOL = 0.0
REQUIRE_SAME_NEIGHBORHOOD = True

# --- recent window (last 2 years) ---
RECENT_YEARS = 2
RECENT_MIN = 10
RECENT_MAX = 12

# --- long-term window (~10 years total) ---
LONGTERM_YEARS = 10
BUCKET_SPAN_DAYS = 720
BUCKET_SAMPLES_PER_BUCKET = 5
LONGTERM_MIN = 3  # <-- חשוב! מינימום נקודות למגמה

# --- pricing margin for 'fair range' ---
MARGIN_PCT = 0.04
