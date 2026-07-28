"""Pydantic schemas for Module 2 — Seasonal Travel Planning.

Module 2 scores seasonal suitability from weather, seasonality, tourism events,
public holidays and accessibility only. Crowd risk is Module 3's output and is
carried here purely as labelled external context.
"""
from pydantic import BaseModel, Field


class SeasonalPlanRequest(BaseModel):
    destination: str
    year: int = 2025
    month: int = Field(ge=1, le=12)


class MonthlyPlanRequest(BaseModel):
    destination: str
    year: int = 2025


class DestinationInfo(BaseModel):
    destination: str
    dest_type: str
    district: str
    climate_zone: str
    elevation_m: int


class ScoreBreakdown(BaseModel):
    """Weighted contributions that make up the travel suitability score."""
    weather_component: float
    season_component: float
    event_component: float
    holiday_component: float
    accessibility_component: float


class SeasonalPlanResponse(BaseModel):
    destination: str
    year: int
    month: int
    month_name: str

    # Core output
    suitability_label: str              # BEST / GOOD / AVOID
    travel_suitability_score: float     # 0-1
    recommendation_summary: str
    season_reason: str                  # why this month is not ideal, blank when BEST

    # Score breakdown (explains why the score is what it is)
    score_breakdown: ScoreBreakdown

    # Weather detail
    weather_suitability_score: float
    weather_verdict: str                # Excellent / Good / Fair / Poor
    avg_temp_c: float
    total_rainfall_mm: float
    rain_risk: str                      # Low / Moderate / High / Very High
    rainy_days: int
    avg_humidity_pct: float
    sunshine_hours: float
    comfort_index: float                # 0-100

    # Seasonal context
    season: str
    is_peak_national: bool
    is_best_period: bool
    festival_name: str                  # empty string when there is none
    tourism_event_score: int
    holiday_count: int

    # Practical planning
    best_activities: list[str]
    packing_advice: list[str]
    things_to_note: list[str]
    sea_condition: str

    # Destination meta
    dest_type: str
    climate_zone: str
    avg_stay_days: int

    # Crowd context — produced by Module 3, shown as external information only
    crowd_context_level: str            # LOW / MEDIUM / HIGH
    crowd_context_note: str
    crowd_event_note: str               # e.g. "Poson Poya, peak pilgrimage", blank if none
    is_off_season: bool                 # destination not recommended for travel this month
