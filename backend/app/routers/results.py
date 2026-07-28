"""Training result image metadata endpoints."""
from pydantic import BaseModel

from fastapi import APIRouter

router = APIRouter()


class ResultImage(BaseModel):
    filename: str
    title: str
    description: str
    url: str


MODULE1_RESULTS = [
    ("m1_01_series_and_exclusions.png", "Series and Exclusions", "Monthly arrivals 1971 to 2025 showing excluded pandemic years"),
    ("m1_02_stationarity.png", "Stationarity Tests", "Augmented Dickey Fuller results before and after differencing"),
    ("m1_03_acf_pacf.png", "ACF and PACF", "Autocorrelation plots used to identify model parameters"),
    ("m1_04_arima_vs_sarima.png", "ARIMA vs SARIMA", "Hold out forecast comparison on the last twelve months"),
    ("m1_05_metric_comparison.png", "Metric Comparison", "MAPE, MAE and RMSE for both forecasting models"),
    ("m1_06_revenue_regression.png", "Revenue Regression", "Linear regression fit from visitors to revenue"),
    ("m1_07_seasonality.png", "Seasonality Profile", "Average monthly arrivals across the clean training period"),
    ("m1_08_destination_visitors.png", "Destination Visitors", "Real visitor counts by destination from official sources"),
    ("m1_09_destination_revenue.png", "Destination Revenue", "Real tourism revenue by destination"),
    ("m1_10_performance_summary.png", "Performance Summary", "Combined model metrics and selected model"),
    ("m1_11_five_year_forecast.png", "Five Year Forecast", "Monthly forecast to 2030 with confidence intervals"),
    ("m1_12_annual_forecast.png", "Annual Forecast", "Annual arrivals, real history against forecast to 2030"),
    ("m1_13_destination_forecast.png", "Destination Forecast", "Predicted visitors per destination across all forecast years"),
]

MODULE2_RESULTS = [
    ("m2_01_confusion_matrix.png", "Confusion Matrix", "Classification accuracy of BEST/GOOD/AVOID labels"),
    ("m2_02_feature_importance.png", "Feature Importance", "Top 15 features driving seasonal suitability prediction"),
    ("m2_03_cross_validation.png", "Cross Validation", "5-fold CV showing model stability across data splits"),
    ("m2_04_tss_regression.png", "TSS Regression", "XGBoost predicted vs actual travel suitability scores"),
    ("m2_05_suitability_heatmap.png", "Suitability Heatmap", "Travel suitability score per destination and month"),
    ("m2_06_label_distribution.png", "Label Distribution", "BEST/GOOD/AVOID count per destination"),
    ("m2_07_monthly_tss_trend.png", "Monthly TSS Trend", "Average suitability score across all destinations by month"),
    ("m2_08_performance_summary.png", "Performance Summary", "Combined accuracy, F1, RMSE, R² overview"),
    ("m2_09_destination_by_season.png", "Destination by Season", "Best destinations for each Sri Lanka season"),
    ("m2_10_weather_vs_tss.png", "Weather vs TSS", "Correlation between weather factors and suitability"),
]

MODULE4_RESULTS = [
    ("m4_01_feature_importance.png", "Feature Importance", "LightGBM gain-based feature importance for rating prediction"),
    ("m4_02_rating_prediction.png", "Rating Prediction", "Predicted vs actual ratings and confusion matrix"),
    ("m4_03_similarity_matrix.png", "Similarity Matrix", "Cosine similarity between all 20 destinations"),
    ("m4_04_ndcg_per_destination.png", "NDCG per Destination", "Ranking quality score per destination"),
    ("m4_05_rating_distribution.png", "Rating Distribution", "Distribution of real Kaggle and synthetic ratings"),
    ("m4_06_avg_rating_per_destination.png", "Average Rating", "Mean rating with standard deviation per destination"),
    ("m4_07_recommendation_demo.png", "Recommendation Demo", "Sample scores for 3 different traveler profiles"),
    ("m4_08_performance_summary.png", "Performance Summary", "RMSE, MAE, R², exact match accuracy overview"),
    ("m4_09_rating_by_month_heatmap.png", "Rating by Month Heatmap", "User ratings across destinations and travel months"),
    ("m4_10_destination_radar.png", "Destination Radar", "Feature profile radar charts for 6 key destinations"),
]


def _build(module: str, entries: list[tuple[str, str, str]]) -> list[ResultImage]:
    return [
        ResultImage(
            filename=fn,
            title=title,
            description=desc,
            url=f"/results/{module}/{fn}",
        )
        for fn, title, desc in entries
    ]


@router.get("/module1", response_model=list[ResultImage])
def module1_results() -> list[ResultImage]:
    return _build("module1", MODULE1_RESULTS)


@router.get("/module2", response_model=list[ResultImage])
def module2_results() -> list[ResultImage]:
    return _build("module2", MODULE2_RESULTS)


@router.get("/module4", response_model=list[ResultImage])
def module4_results() -> list[ResultImage]:
    return _build("module4", MODULE4_RESULTS)
