"""Module 1 — Destination Level Tourist Demand and Revenue Prediction.

Demand is forecast with SARIMA(0,1,2)(0,1,1,12), chosen over ARIMA(0,2,3) for its
handling of Sri Lanka's strong annual seasonality. Revenue is estimated with
Linear Regression, split into foreign and local visitors.

The forecast for 2026 through 2030 is precomputed in module1_output.csv. The
ARIMA and SARIMA models are never re-run at request time; the .pkl files are kept
for reference and retraining only.
"""
import json
from functools import lru_cache

import pandas as pd

from app.config import DATA_DIR, MODELS_DIR, MONTH_NAMES
from app.schemas.module1_schemas import (
    DemandForecastResponse,
    HistoricalRecord,
    ModelComparisonResponse,
)

M1_DATA = DATA_DIR / "module1"
M1_MODELS = MODELS_DIR / "module1"


@lru_cache(maxsize=1)
def _load_assets() -> dict:
    """Load the precomputed forecast, model metadata and real historical data once."""
    forecast = pd.read_csv(M1_DATA / "module1_output.csv")
    with open(M1_MODELS / "model_metadata.json", encoding="utf-8") as f:
        metadata = json.load(f)
    real_annual = pd.read_csv(M1_DATA / "module1_real_annual_destination.csv")
    return {
        "forecast": forecast,
        "metadata": metadata,
        "real_annual": real_annual,
    }


def models_loaded() -> bool:
    try:
        _load_assets()
        return True
    except Exception:
        return False


def _to_response(row: pd.Series) -> DemandForecastResponse:
    month = int(row["month"])
    return DemandForecastResponse(
        destination=str(row["destination"]),
        year=int(row["year"]),
        month=month,
        month_name=MONTH_NAMES[month - 1],
        predicted_tourist_arrivals=int(row["predicted_tourist_arrivals"]),
        predicted_foreign_visitors=int(row["predicted_foreign_visitors"]),
        predicted_local_visitors=int(row["predicted_local_visitors"]),
        confidence_lower=int(row["confidence_lower"]),
        confidence_upper=int(row["confidence_upper"]),
        estimated_revenue_lkr=int(row["estimated_revenue_lkr"]),
        estimated_foreign_revenue_lkr=int(row["estimated_foreign_revenue_lkr"]),
        estimated_local_revenue_lkr=int(row["estimated_local_revenue_lkr"]),
        national_arrivals=int(row["national_arrivals"]),
        model_used=str(row["model_used"]),
        mape_pct=round(float(row["mape_pct"]), 2),
        data_source=str(row["data_source"]),
        forecast_horizon_years=int(row["forecast_horizon_years"]),
        national_lower=int(row["national_lower"]),
        national_upper=int(row["national_upper"]),
    )


def get_forecast(destination: str, year: int, month: int) -> DemandForecastResponse:
    """Look up the precomputed forecast row for a destination, year and month."""
    forecast = _load_assets()["forecast"]
    match = forecast[
        (forecast["destination"] == destination)
        & (forecast["year"] == year)
        & (forecast["month"] == month)
    ]
    if match.empty:
        raise KeyError(destination)
    return _to_response(match.iloc[0])


def get_yearly_forecast(destination: str, year: int) -> list[DemandForecastResponse]:
    """All twelve months of the forecast for a destination and year."""
    forecast = _load_assets()["forecast"]
    match = forecast[
        (forecast["destination"] == destination) & (forecast["year"] == year)
    ].sort_values("month")
    if match.empty:
        raise KeyError(destination)
    return [_to_response(r) for _, r in match.iterrows()]


def get_all_destinations_forecast(
    year: int, month: int
) -> list[DemandForecastResponse]:
    """Every destination's forecast for one month, ranked by predicted arrivals."""
    forecast = _load_assets()["forecast"]
    match = forecast[
        (forecast["year"] == year) & (forecast["month"] == month)
    ].sort_values("predicted_tourist_arrivals", ascending=False)
    if match.empty:
        raise KeyError(f"{year}-{month}")
    return [_to_response(r) for _, r in match.iterrows()]


def get_model_comparison() -> ModelComparisonResponse:
    """ARIMA vs SARIMA metrics, drawn from the training metadata."""
    m = _load_assets()["metadata"]
    return ModelComparisonResponse(
        arima_order=list(m["arima_order"]),
        arima_mape=round(float(m["arima_mape"]), 2),
        arima_mae=round(float(m["arima_mae"]), 0),
        arima_rmse=round(float(m["arima_rmse"]), 0),
        sarima_order=list(m["sarima_order"]),
        sarima_seasonal_order=list(m["sarima_seasonal_order"]),
        sarima_mape=round(float(m["sarima_mape"]), 2),
        sarima_mae=round(float(m["sarima_mae"]), 0),
        sarima_rmse=round(float(m["sarima_rmse"]), 0),
        selected_model=str(m["selected_model"]),
        excluded_years=list(m["excluded_years"]),
        train_period=str(m["train_period"]),
        train_months=int(m["train_months"]),
    )


def get_real_historical(destination: str) -> list[HistoricalRecord]:
    """Real annual visitor and revenue records for a destination.

    Not every destination has official records; those without any return an
    empty list rather than an error.
    """
    real = _load_assets()["real_annual"]
    match = real[real["destination"] == destination].sort_values("year")
    return [
        HistoricalRecord(
            year=int(r["year"]),
            destination=str(r["destination"]),
            foreign_visitors=int(r["foreign_visitors"]),
            local_visitors=int(r["local_visitors"]),
            total_visitors=int(r["total_visitors"]),
            foreign_income_lkr=int(round(float(r["foreign_income_lkr"]))),
            local_income_lkr=int(round(float(r["local_income_lkr"]))),
            total_revenue_lkr=int(round(float(r["total_revenue_lkr"]))),
        )
        for _, r in match.iterrows()
    ]
