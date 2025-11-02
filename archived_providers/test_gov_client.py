# scripts/test_gov_client.py
from __future__ import annotations

import json
import argparse
from pathlib import Path
from typing import Any, Dict, List, Union

from src.gov_data_client import (
    search_address,
    list_neighborhood_index,
    get_settlement_page,
    get_neighborhood_page,
    # get_deals_html,  # לא בשימוש בשלב זה
)

OUTDIR = Path("output")
OUTDIR.mkdir(exist_ok=True)

def dump_json(obj: Any, path: Path) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2))
    print(f"saved → {path}")

def preview(obj: Any, max_len: int = 3) -> None:
    """Print a tiny preview to the console so you know what you got."""
    if isinstance(obj, dict):
        keys = list(obj.keys())
        print(f"[dict] keys: {keys[:10]}")
    elif isinstance(obj, list):
        print(f"[list] len={len(obj)}; showing first {max_len} items")
        for i, it in enumerate(obj[:max_len], 1):
            if isinstance(it, dict):
                print(f"  {i}) keys: {list(it.keys())[:10]}")
            else:
                print(f"  {i}) type={type(it).__name__}")
    else:
        print(f"[{type(obj).__name__}]")

def main() -> None:
    ap = argparse.ArgumentParser(description="Smoke-test gov data client (RAW GETs).")
    ap.add_argument("--query", default="דיזנגוף תל אביב", help="GovMap free-text search query")
    ap.add_argument("--settlement-id", type=str, default=None, help="Settlement id for buy page")
    ap.add_argument("--neigh-id", type=str, default=None, help="Neighborhood id for buy page")
    args = ap.parse_args()

    # 1) GovMap search
    print("\n=== GovMap search ===")
    srch = search_address(args.query)
    if srch is not None:
        dump_json(srch, OUTDIR / "govmap_search.json")
        preview(srch)
    else:
        print("[GovMap] search returned None (likely blocked). Skipping.")

    # 2) Neighborhood index (CloudFront)
    print("\n=== Neighborhood index ===")
    neigh_index = list_neighborhood_index()
    if neigh_index is not None:
        dump_json(neigh_index, OUTDIR / "neighborhood_index.json")
        preview(neigh_index)
    else:
        print("[Nadlan] neighborhood index unavailable (DNS/block). Skipping.")

    # 3) Settlement page (if provided)
    if args.settlement_id:
        print(f"\n=== Settlement page: {args.settlement_id} ===")
        settlement = get_settlement_page(args.settlement_id)
        if neigh_index is not None:
            dump_json(neigh_index, OUTDIR / "neighborhood_index.json")
            preview(neigh_index)
        else:
            print("[Nadlan] neighborhood index unavailable (DNS/block). Skipping.")

    # 4) Neighborhood page (if provided)
    if args.neigh_id:
        print(f"\n=== Neighborhood page: {args.neigh_id} ===")
        neigh = get_neighborhood_page(args.neigh_id)
        if neigh_index is not None:
            dump_json(neigh_index, OUTDIR / "neighborhood_index.json")
            preview(neigh_index)
        else:
            print("[Nadlan] neighborhood index unavailable (DNS/block). Skipping.")


    print("\nDone.")

if __name__ == "__main__":
    main()
