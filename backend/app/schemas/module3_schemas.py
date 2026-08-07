"""Module 3 — Crowd Risk schemas.

Predicts next-month tourist interest (a 0-100 Destination Interest Index
fused from Google Trends and Wikipedia signal) one month ahead per tracked
place, and buckets the predicted change into a LOW/MEDIUM/HIGH crowd risk
band. All figures are precomputed in module3_predictions.csv; the trained
model is never re-run at request time.
"""
from pydantic import BaseModel, ConfigDict


class CrowdRiskPrediction(BaseModel):
    # model_used is a legitimate field name here; opt out of the "model_"
    # protected namespace so pydantic does not warn about it.
    model_config = ConfigDict(protected_namespaces=())

    destination: str
    is_core_destination: bool  # true if this also appears in app.config.DESTINATIONS
    last_known_month: str  # "2026-07"
    predicted_month: str  # "2026-08"
    latest_interest_index: float  # 0-100, last observed DII
    predicted_interest_index: float  # 0-100, predicted next-month DII
    predicted_change_pct: float  # % change vs one month before the latest observation
    crowd_risk_level: str  # "Low" | "Medium" | "High"
    crowd_score_0_100: float
    recommendation_action: str  # "promote" | "monitor" | "redirect"
    model_used: str


class CrowdRiskSummary(BaseModel):
    total_tracked: int
    core_destination_count: int
    low_count: int
    medium_count: int
    high_count: int
    naive_mape_pct: float
    ensemble_mape_pct: float
