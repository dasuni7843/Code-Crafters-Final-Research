"""Module 2 — Seasonal Travel Planning endpoints."""
from fastapi import APIRouter, HTTPException

from app.schemas.module2_schemas import DestinationInfo, SeasonalPlanResponse
from app.services import module2_service as service

router = APIRouter()


@router.get("/destinations", response_model=list[DestinationInfo])
def list_destinations() -> list[DestinationInfo]:
    return service.get_all_destinations()


@router.get("/plan/{destination}/{year}/{month}", response_model=SeasonalPlanResponse)
def seasonal_plan(destination: str, year: int, month: int) -> SeasonalPlanResponse:
    if not 1 <= month <= 12:
        raise HTTPException(status_code=422, detail="Month must be between 1 and 12.")
    try:
        return service.get_seasonal_plan(destination, year, month)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Destination '{destination}' was not found. Please select from the dropdown.",
        )


@router.get("/monthly/{destination}/{year}", response_model=list[SeasonalPlanResponse])
def monthly_plan(destination: str, year: int) -> list[SeasonalPlanResponse]:
    try:
        return service.get_monthly_plan(destination, year)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Destination '{destination}' was not found. Please select from the dropdown.",
        )
