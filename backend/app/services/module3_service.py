"""Module 3 — Crowd Risk: precomputed prediction lookups.

Predicts a Destination Interest Index (DII, 0-100) one month ahead from
fused Google Trends + Wikipedia signal, per tracked place, and buckets the
predicted change into a LOW/MEDIUM/HIGH crowd risk band using terciles
measured during walk-forward evaluation (see backend/training/train_module3.py).
Predictions are precomputed in module3_predictions.csv; the trained
RandomForest is never re-run at request time, the same convention Module 1
uses for its forecast.

Module 3 tracks ~300 individual named attractions — a finer grain than the
app's 20 core destinations (app.config.DESTINATIONS). Most tracked places
therefore don't appear in Modules 1, 2 or 4; is_core_destination flags the
ones that do, so the frontend can filter down to just the app's own
destination list.
"""
from functools import lru_cache

import pandas as pd

from app.config import DATA_DIR, DESTINATIONS, RESULTS_DIR
from app.schemas.module3_schemas import CrowdRiskPrediction, CrowdRiskSummary

M3_DATA = DATA_DIR / "module3"
M3_RESULTS = RESULTS_DIR / "module3"


@lru_cache(maxsize=1)
def _load_assets() -> dict:
    predictions = pd.read_csv(M3_DATA / "module3_predictions.csv")
    predictions["is_core_destination"] = predictions["destination"].isin(set(DESTINATIONS))
    metrics = pd.read_csv(M3_RESULTS / "model_metrics_summary.csv").set_index("Model")
    return {"predictions": predictions, "metrics": metrics}


def models_loaded() -> bool:
    try:
        _load_assets()
        return True
    except Exception:
        return False


def _to_response(row: pd.Series) -> CrowdRiskPrediction:
    return CrowdRiskPrediction(
        destination=str(row["destination"]),
        is_core_destination=bool(row["is_core_destination"]),
        last_known_month=str(row["last_known_month"]),
        predicted_month=str(row["predicted_month"]),
        latest_interest_index=round(float(row["latest_interest_index"]), 1),
        predicted_interest_index=round(float(row["predicted_dii"]), 1),
        predicted_change_pct=round(float(row["predicted_change_pct"]), 1),
        crowd_risk_level=str(row["crowd_risk_level"]),
        crowd_score_0_100=round(float(row["crowd_score_0_100"]), 1),
        recommendation_action=str(row["recommendation_action"]),
        model_used=str(row["model_used"]),
    )


def list_predictions(core_only: bool = False) -> list[CrowdRiskPrediction]:
    """All tracked places, ranked by current crowd interest. Pass core_only
    to restrict the list to the app's 20 core destinations."""
    df = _load_assets()["predictions"]
    if core_only:
        df = df[df["is_core_destination"]]
    df = df.sort_values("crowd_score_0_100", ascending=False)
    return [_to_response(r) for _, r in df.iterrows()]


def get_prediction(destination: str) -> CrowdRiskPrediction:
    df = _load_assets()["predictions"]
    match = df[df["destination"].str.lower() == destination.lower()]
    if match.empty:
        raise KeyError(destination)
    return _to_response(match.iloc[0])


def get_summary() -> CrowdRiskSummary:
    assets = _load_assets()
    df = assets["predictions"]
    metrics = assets["metrics"]
    counts = df["crowd_risk_level"].value_counts()
    return CrowdRiskSummary(
        total_tracked=len(df),
        core_destination_count=int(df["is_core_destination"].sum()),
        low_count=int(counts.get("Low", 0)),
        medium_count=int(counts.get("Medium", 0)),
        high_count=int(counts.get("High", 0)),
        naive_mape_pct=round(float(metrics.loc["Seasonal Naive", "MAPE (%)"]), 2),
        ensemble_mape_pct=round(float(metrics.loc["Inverse-MAPE Ensemble", "MAPE (%)"]), 2),
    )
