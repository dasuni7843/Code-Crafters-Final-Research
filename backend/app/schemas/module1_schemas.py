"""Module 1 — Destination Level Tourist Demand and Revenue Prediction schemas.

Demand is forecast with SARIMA (selected over ARIMA), revenue with Linear
Regression. All figures are precomputed in module1_output.csv; these models are
never re-run at request time.
"""
from pydantic import BaseModel, ConfigDict


class DemandForecastRequest(BaseModel):
    destination: str
    year: int = 2026  # 2026, 2027, 2028, 2029 or 2030
    month: int  # 1-12


class DemandForecastResponse(BaseModel):
    # model_used is a legitimate field name here; opt out of the "model_"
    # protected namespace so pydantic does not warn about it.
    model_config = ConfigDict(protected_namespaces=())

    destination: str
    year: int
    month: int
    month_name: str

    # Demand
    predicted_tourist_arrivals: int
    predicted_foreign_visitors: int
    predicted_local_visitors: int
    confidence_lower: int
    confidence_upper: int

    # Revenue
    estimated_revenue_lkr: int
    estimated_foreign_revenue_lkr: int
    estimated_local_revenue_lkr: int

    # Context
    national_arrivals: int
    model_used: str  # "SARIMA"
    mape_pct: float  # 6.78
    data_source: str  # always "forecast"
    forecast_horizon_years: int  # 1 to 5, drives confidence band width
    national_lower: int
    national_upper: int


class ModelComparisonResponse(BaseModel):
    arima_order: list[int]
    arima_mape: float
    arima_mae: float
    arima_rmse: float
    sarima_order: list[int]
    sarima_seasonal_order: list[int]
    sarima_mape: float
    sarima_mae: float
    sarima_rmse: float
    selected_model: str
    excluded_years: list[int]
    train_period: str
    train_months: int


class HistoricalRecord(BaseModel):
    """A real annual record for a destination, from official SLTDA sources."""
    year: int
    destination: str
    foreign_visitors: int
    local_visitors: int
    total_visitors: int
    foreign_income_lkr: int
    local_income_lkr: int
    total_revenue_lkr: int
