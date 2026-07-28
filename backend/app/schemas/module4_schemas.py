"""Pydantic schemas for Module 4 — Personalization & Recommendation."""
from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    preferred_type: str = "beach"        # beach | cultural | nature | adventure
    crowd_tolerance: str = "medium"      # low | medium | high
    travel_month: int = Field(default=1, ge=1, le=12)
    travel_year: int = Field(default=2026, ge=2026, le=2030)  # drives Module 1 and 3 lookups
    trip_budget: str = "mid"             # budget | mid | luxury
    travel_party: str = "couple"         # solo | couple | family | group
    weather_preference: str = "any"      # hot | warm | cool | any
    activity_preference: str = "beach"   # heritage | beach | nature | adventure | wellness | food | photography
    top_n: int = Field(default=5, ge=1, le=20)


class ScoreBreakdown(BaseModel):
    predicted_rating: float
    content_similarity: float
    crowd_compatibility: float
    seasonal_suitability: float


class DestinationRecommendation(BaseModel):
    rank: int
    destination: str
    recommendation_score: float
    predicted_rating: float
    content_similarity_score: float
    crowd_risk_level: str        # from mock Module 3
    crowd_score: float
    predicted_arrivals: int      # from mock Module 1
    estimated_revenue_lkr: int
    avg_tss: float
    avg_wss: float
    weather_label: str
    season_suitability: str
    season_reason: str = ""      # why this month is not ideal, blank when BEST
    why_recommended: str
    activities: list[str]
    avg_stay_days: int
    best_months: list[str]
    dest_type: str
    district: str
    # Travel advisories sourced from mock Module 3
    is_off_season: bool = False   # not recommended for travel in this month
    crowd_event_note: str = ""    # e.g. "Esala Perahera festival", blank if none
    score_breakdown: ScoreBreakdown


class SimilarDestination(BaseModel):
    destination: str
    similarity_score: float
    dest_type: str
    district: str


class SimilarDestinationsRequest(BaseModel):
    destination: str
    top_n: int = 4


class DestinationProfile(BaseModel):
    destination: str
    dest_type: str
    district: str
    climate_zone: str
    beach_score: float
    culture_score: float
    nature_score: float
    adventure_score: float
    accessibility_score: float
    avg_stay_days: int
    best_months: list[str]
    activities: list[str]
    avg_cost_level: str
    family_friendly: bool
