from pathlib import Path
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Make src importable
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from data_loader import load_transactions_csv
from orchestrator import evaluate_listing

app = FastAPI(title="Real Estate Valuation API", version="0.1.0")

# CORS: allow local frontends (edit origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React/Vite dev
        "http://127.0.0.1:3000",
        "http://localhost:8501",  # Streamlit dev
        "http://127.0.0.1:8501",
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load data once on startup (CSV for now)
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "transactions.csv"
DF = load_transactions_csv(str(DATA_PATH))

class EvaluateInput(BaseModel):
    city: str
    neighborhood: str
    rooms: float
    size_sqm: float
    asking_price_ils: int

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/evaluate")
def evaluate(payload: EvaluateInput):
    """
    Main endpoint: receive listing attributes, return all computed metrics.
    """
    result = evaluate_listing(
        transactions_df=DF,
        city=payload.city,
        neighborhood=payload.neighborhood,
        rooms=payload.rooms,
        size_sqm=payload.size_sqm,
        asking_price_ils=payload.asking_price_ils,
    )
    return result
