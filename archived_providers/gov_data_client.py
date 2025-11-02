"""
Lightweight client for data.gov.il CKAN Datastore API.
- Use datastore_search for paging/filters.
- Use datastore_search_sql for server-side SQL filtering when available.
"""

from typing import Optional, Dict, Any, List
import os
import requests
import pandas as pd
from requests.adapters import HTTPAdapter
from typing import Optional
from urllib3.util.retry import Retry  # NOTE: from urllib3.util.retry (not requests)
from dotenv import load_dotenv

load_dotenv()

DATA_GOV_BASE = os.getenv("DATA_GOV_BASE", "https://data.gov.il/api/3/action").rstrip("/")

class GovDataClient:
    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        self.base_url = (base_url or DATA_GOV_BASE).rstrip("/")
        self.timeout = timeout

    def datastore_search(self, resource_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/datastore_search"
        r = requests.get(url, params={"resource_id": resource_id, **params}, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        if not data.get("success"):
            raise RuntimeError(f"CKAN success=false. Payload: {data}")
        return data["result"]

    def datastore_search_sql(self, resource_id: str, sql: str, extra: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        url = f"{self.base_url}/datastore_search_sql"
        payload = {"resource_id": resource_id, "sql": sql}
        if extra:
            payload.update(extra)
        r = requests.get(url, params=payload, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        if not data.get("success"):
            raise RuntimeError(f"CKAN success=false. Payload: {data}")
        records = data["result"]["records"]
        df = pd.DataFrame.from_records(records) if records else pd.DataFrame()
        df.columns = [c.strip().lower() for c in df.columns]
        return df

    def get_fields(self, resource_id: str) -> pd.DataFrame:
        """Returns the schema (fields) without pulling rows."""
        result = self.datastore_search(resource_id, {"limit": 0})
        return pd.DataFrame(result.get("fields", []))

# --- shared HTTP session with retries (for govmap/cloudfront) ---
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Connection": "keep-alive",
}
TIMEOUT = 12  # seconds

def _session_gov() -> requests.Session:
    """Create a requests session with retries for GET calls to external gov endpoints."""
    s = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.headers.update(DEFAULT_HEADERS)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s

# --- GovMap autocomplete (free text search) ---
def search_address(query: str, limit: int = 10) -> dict:
    """Best-effort address search via GovMap. May fail if endpoint blocks server-side calls."""
    url = "https://apps.govmap.gov.il/wss/arcgis/rest/services/Search/MapServer/1/query"
    params = {
        "f": "json",
        "where": f"UPPER(NAME) LIKE UPPER('%{query}%')",
        "outFields": "*",
        "returnGeometry": "false",
        "resultRecordCount": limit,
    }
    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        if "application/json" not in r.headers.get("Content-Type", ""):
            print(f"[GovMap] Non-JSON response: {r.status_code} {r.text[:200]!r}")
            return None
        return r.json()
    except Exception as e:
        print(f"[GovMap] search_address error: {e}")
        if 'r' in locals():
            print(f"[GovMap] body preview: {r.text[:200]!r}")
        return None


# --- Nadlan.gov (CloudFront) indexes & pages ---
def list_neighborhood_index():
    url = "https://d3h795h5crxp9r.cloudfront.net/api/index/neigh.json"
    try:
        with _session_gov() as s:
            r = s.get(url, timeout=TIMEOUT)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        print(f"[Nadlan] neighborhood_index error: {e}")
        return None

def get_settlement_page(settlement_id: str | int) -> dict:
    url = f"https://d3h795h5crxp9r.cloudfront.net/api/pages/settlement/buy/{settlement_id}.json"
    try:
        with _session_gov() as s:
            r = s.get(url, timeout=TIMEOUT)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        print(f"[Nadlan] settlement {settlement_id} error: {e}")
        return None

def get_neighborhood_page(neighborhood_id: str | int) -> dict:
    url = f"https://d3h795h5crxp9r.cloudfront.net/api/pages/neighborhood/buy/{neighborhood_id}.json"
    try:
        with _session_gov() as s:
            r = s.get(url, timeout=TIMEOUT)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        print(f"[Nadlan] neighborhood {neighborhood_id} error: {e}")
        return None
    
# --- (Optional) Deals page as HTML, if you know a stable absolute URL ---
def get_deals_html(absolute_url: str) -> str:
    """
    Fetch a deals page (HTML) as-is. Parsing should be done by a separate parser.
    """
    headers = DEFAULT_HEADERS | {"Accept": "text/html, */*"}
    with _session_gov() as s:
        r = s.get(absolute_url, timeout=TIMEOUT, headers=headers)
        r.raise_for_status()
        return r.text



