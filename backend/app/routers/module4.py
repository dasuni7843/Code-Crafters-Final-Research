"""Module 4 — Personalization & Recommendation endpoints."""
from fastapi import APIRouter, HTTPException

from app.schemas.module4_schemas import (
    DestinationProfile,
    DestinationRecommendation,
    RecommendationRequest,
    SimilarDestination,
)
from app.services import module4_service as service

router = APIRouter()


@router.get("/destinations", response_model=list[DestinationProfile])
def list_destinations() -> list[DestinationProfile]:
    return service.list_destinations()


@router.post("/recommend", response_model=list[DestinationRecommendation])
def recommend(request: RecommendationRequest) -> list[DestinationRecommendation]:
    return service.get_recommendations(request)


@router.get("/similar/{destination}", response_model=list[SimilarDestination])
def similar(destination: str, top_n: int = 4) -> list[SimilarDestination]:
    try:
        return service.get_similar_destinations(destination, top_n)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Destination '{destination}' was not found. Please select from the dropdown.",
        )


@router.get("/destination/{name}", response_model=DestinationProfile)
def destination_profile(name: str) -> DestinationProfile:
    try:
        return service.get_destination_profile(name)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Destination '{name}' was not found. Please select from the dropdown.",
        )
