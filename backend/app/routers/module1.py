"""Module 1 — Destination Level Tourist Demand and Revenue Prediction endpoints."""
from fastapi import APIRouter, HTTPException

from app.schemas.module1_schemas import (
    DemandForecastResponse,
    HistoricalRecord,
    ModelComparisonResponse,
)
from app.services import module1_service as service

router = APIRouter()

FORECAST_YEAR_MIN = 2026
FORECAST_YEAR_MAX = 2030


def _check_year(year: int) -> None:
    if not FORECAST_YEAR_MIN <= year <= FORECAST_YEAR_MAX:
        raise HTTPException(
            status_code=422,
            detail=f"Year must be between {FORECAST_YEAR_MIN} and {FORECAST_YEAR_MAX}.",
        )


@router.get("/forecast/{destination}/{year}/{month}", response_model=DemandForecastResponse)
def forecast(destination: str, year: int, month: int) -> DemandForecastResponse:
    if not 1 <= month <= 12:
        raise HTTPException(status_code=422, detail="Month must be between 1 and 12.")
    _check_year(year)
    try:
        return service.get_forecast(destination, year, month)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"No forecast found for '{destination}'. Please select from the dropdown.",
        )


@router.get("/yearly/{destination}/{year}", response_model=list[DemandForecastResponse])
def yearly(destination: str, year: int) -> list[DemandForecastResponse]:
    _check_year(year)
    try:
        return service.get_yearly_forecast(destination, year)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"No forecast found for '{destination}'. Please select from the dropdown.",
        )


@router.get("/comparison", response_model=ModelComparisonResponse)
def comparison() -> ModelComparisonResponse:
    return service.get_model_comparison()


@router.get("/all/{year}/{month}", response_model=list[DemandForecastResponse])
def all_destinations(year: int, month: int) -> list[DemandForecastResponse]:
    if not 1 <= month <= 12:
        raise HTTPException(status_code=422, detail="Month must be between 1 and 12.")
    _check_year(year)
    try:
        return service.get_all_destinations_forecast(year, month)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="No forecast found for the requested period.",
        )


@router.get("/historical/{destination}", response_model=list[HistoricalRecord])
def historical(destination: str) -> list[HistoricalRecord]:
    return service.get_real_historical(destination)
