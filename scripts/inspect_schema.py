import os
from dotenv import load_dotenv
from pathlib import Path

# ודא שה-PYTHONPATH מצביע ל-src
import sys
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from gov_data_client import GovDataClient

load_dotenv()
RESOURCE = os.getenv("DATA_GOV_RESOURCE_ID")

if not RESOURCE:
    raise SystemExit("Missing DATA_GOV_RESOURCE_ID in .env")

client = GovDataClient()
fields_df = client.get_fields(RESOURCE)
print(fields_df)
