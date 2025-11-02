"""
Lightweight client for data.gov.il CKAN Datastore API.
- Use datastore_search for paging/filters.
- Use datastore_search_sql for server-side SQL filtering when available.
"""

from typing import Optional, Dict, Any, List
import os
import requests
import pandas as pd
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
