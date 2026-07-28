"""Integrated pipeline endpoint — all four modules working together.

Each module's panel is sourced from that module's own output: Module 1 from its
real trained forecast, Module 3 from its mock CSV, Module 2 from the seasonal
planner and Module 4 from the recommender. Module 2 never carries another
module's data.
"""
import pandas as pd
from pydantic import BaseModel

from fastapi import APIRouter

from app.config import MONTH_NAMES
from app.schemas.module4_schemas import DestinationRecommendation, RecommendationRequest
from app.services import module2_service as m2
from app.services import module4_service as m4

router = APIRouter()


class Module1Output(BaseModel):
    destination: str
    predicted_arrivals: int
    predicted_foreign_visitors: int
    predicted_local_visitors: int
    estimated_revenue_lkr: int


class Module2Output(BaseModel):
    destination: str
    travel_suitability_score: float
    suitability_label: str
    season: str
    weather_verdict: str
    recommendation_summary: str
    season_reason: str


class Module3Output(BaseModel):
    destination: str
    crowd_risk_level: str
    crowd_score: float
    recommendation_action: str


class IntegratedResponse(BaseModel):
    travel_month: int
    month_name: str
    module1: list[Module1Output]   # Demand forecast (this system)
    module2: list[Module2Output]   # Seasonal planning (this system)
    module3: list[Module3Output]   # Crowd risk (mock)
    module4: list[DestinationRecommendation]  # Final recommendations (this system)


def _mock_row(df: pd.DataFrame, destination: str, year: int, month: int) -> pd.Series | None:
    """Look up a mock-output row, falling back to any year for that month."""
    match = df[
        (df["destination"] == destination)
        & (df["year"] == year)
        & (df["month"] == month)
    ]
    if match.empty:
        match = df[(df["destination"] == destination) & (df["month"] == month)]
    return None if match.empty else match.iloc[0]


@router.post("/recommend", response_model=IntegratedResponse)
def integrated_recommend(request: RecommendationRequest) -> IntegratedResponse:
    month = request.travel_month
    year = request.travel_year
    assets = m2._load_assets()
    destinations = sorted(assets["seasonal"]["destination"].unique())

    module1: list[Module1Output] = []
    module2: list[Module2Output] = []
    module3: list[Module3Output] = []

    for dest in destinations:
        # Module 1 — demand forecast, read from its real trained output
        m1_row = _mock_row(assets["mock_m1"], dest, year, month)
        module1.append(Module1Output(
            destination=dest,
            predicted_arrivals=int(m1_row["predicted_tourist_arrivals"]) if m1_row is not None else 0,
            predicted_foreign_visitors=int(m1_row["predicted_foreign_visitors"]) if m1_row is not None else 0,
            predicted_local_visitors=int(m1_row["predicted_local_visitors"]) if m1_row is not None else 0,
            estimated_revenue_lkr=int(m1_row["estimated_revenue_lkr"]) if m1_row is not None else 0,
        ))

        # Module 2 — seasonal planning, this system
        plan = m2.get_seasonal_plan(dest, year, month)
        module2.append(Module2Output(
            destination=dest,
            travel_suitability_score=plan.travel_suitability_score,
            suitability_label=plan.suitability_label,
            season=plan.season,
            weather_verdict=plan.weather_verdict,
            recommendation_summary=plan.recommendation_summary,
            season_reason=plan.season_reason,
        ))

        # Module 3 — crowd risk, read from its own mock output
        m3_row = _mock_row(assets["mock_m3"], dest, year, month)
        module3.append(Module3Output(
            destination=dest,
            crowd_risk_level=str(m3_row["crowd_risk_level"]) if m3_row is not None else "MEDIUM",
            crowd_score=float(m3_row["crowd_score_0_100"]) if m3_row is not None else 50.0,
            recommendation_action=str(m3_row["recommendation_action"]) if m3_row is not None else "monitor",
        ))

    module4 = m4.get_recommendations(request)

    return IntegratedResponse(
        travel_month=month,
        month_name=MONTH_NAMES[month - 1],
        module1=sorted(module1, key=lambda x: x.predicted_arrivals, reverse=True),
        module2=sorted(module2, key=lambda x: x.travel_suitability_score, reverse=True),
        module3=module3,
        module4=module4,
    )
