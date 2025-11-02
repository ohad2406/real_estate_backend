def norm(s: str) -> str:
    return (s or "").strip().lower()

def fmt_pct(x: float) -> str:
    return f"{x:.1f}%"

def fmt_ils(x: float) -> str:
    return f"{int(round(x)):,.0f} ₪".replace(",", "'")