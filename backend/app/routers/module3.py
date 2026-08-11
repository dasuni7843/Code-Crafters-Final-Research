"""Module 3 — Crowd Risk endpoints."""
from fastapi import APIRouter, HTTPException

from app.schemas.module3_schemas import CrowdRiskPrediction, CrowdRiskSummary
from app.services import module3_service as service

router = APIRouter()


@router.get("/predictions", response_model=list[CrowdRiskPrediction])
def predictions(core_only: bool = False) -> list[CrowdRiskPrediction]:
    return service.list_predictions(core_only=core_only)


@router.get("/predictions/{destination}", response_model=CrowdRiskPrediction)
def prediction(destination: str) -> CrowdRiskPrediction:
    try:
        return service.get_prediction(destination)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"No crowd risk prediction tracked for '{destination}'.",
        )


@router.get("/summary", response_model=CrowdRiskSummary)
def summary() -> CrowdRiskSummary:
    return service.get_summary()
