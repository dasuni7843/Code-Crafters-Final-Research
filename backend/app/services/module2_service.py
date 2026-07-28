"""Module 2 — Seasonal Travel Planning: model loading and inference.

Scoring inputs are weather, seasonality, tourism events, public holidays and
accessibility. Crowd is deliberately excluded from every feature and from the
suitability score — it is Module 3's output, surfaced here only as context.
"""
from functools import lru_cache

import pandas as pd

import joblib

from app.config import DATA_DIR, MODELS_DIR, MONTH_NAMES
from app.schemas.module2_schemas import (
    DestinationInfo,
    ScoreBreakdown,
    SeasonalPlanResponse,
)

M2_MODELS = MODELS_DIR / "module2"

CROWD_CONTEXT_NOTE = "Crowd data provided by the Crowd Risk module (Module 3)"

# Score components that make up the travel suitability score
SCORE_COMPONENTS = (
    "weather_component",
    "season_component",
    "event_component",
    "holiday_component",
    "access_component",
)

COMPONENT_REASONS = {
    "weather_component": "weaker weather than this destination's other months",
    "season_component": "falls outside the best travel window for this destination",
    "event_component": "fewer tourism events than usual",
    "holiday_component": "fewer public holidays than usual",
    "access_component": "reduced accessibility",
}

# Weather bands a traveller would feel directly, whatever the local baseline
POOR_WEATHER_VERDICTS = {"Poor", "Fair"}
HIGH_RAIN_RISKS = {"High", "Very High"}

# Minimum shortfall against a destination's own baseline before a component is
# worth reporting. Below this the difference is noise rather than a reason.
COMPONENT_DEFICIT_THRESHOLD = 0.03

# Dataset season codes to the wording used in the interface
SEASON_LABELS = {
    "dry_season": "Dry Season",
    "southwest_monsoon": "Southwest Monsoon",
    "northeast_monsoon": "Northeast Monsoon",
    "inter_monsoon": "Inter Monsoon",
}

# Years actually present in the seasonal dataset
DATA_YEAR_MIN = 2015
DATA_YEAR_MAX = 2024


@lru_cache(maxsize=1)
def _load_assets() -> dict:
    """Load models, encoders and datasets once."""
    classifier = joblib.load(M2_MODELS / "seasonal_classifier.pkl")
    regressor = joblib.load(M2_MODELS / "tss_regressor.pkl")
    label_encoder = joblib.load(M2_MODELS / "label_encoder.pkl")
    scaler = joblib.load(M2_MODELS / "feature_scaler.pkl")
    dest_encoder = joblib.load(M2_MODELS / "dest_encoder.pkl")
    climate_encoder = joblib.load(M2_MODELS / "climate_encoder.pkl")
    type_encoder = joblib.load(M2_MODELS / "type_encoder.pkl")
    feature_names = joblib.load(M2_MODELS / "feature_names.pkl")

    seasonal = pd.read_csv(DATA_DIR / "module2" / "module2_seasonal_travel_dataset.csv")
    # Module 1 is now the real trained model. Its production forecast is a
    # superset of the old mock schema, so this key is unchanged.
    mock_m1 = pd.read_csv(DATA_DIR / "module2" / "module1_output.csv")
    mock_m3 = pd.read_csv(DATA_DIR / "module2" / "mock_module3_output.csv")
    attrs = pd.read_csv(DATA_DIR / "raw" / "destination_attributes.csv")

    return {
        "classifier": classifier,
        "regressor": regressor,
        "label_encoder": label_encoder,
        "scaler": scaler,
        "dest_encoder": dest_encoder,
        "climate_encoder": climate_encoder,
        "type_encoder": type_encoder,
        "feature_names": feature_names,
        "seasonal": seasonal,
        "mock_m1": mock_m1,
        "mock_m3": mock_m3,
        "attrs": attrs,
    }


def models_loaded() -> bool:
    try:
        _load_assets()
        return True
    except Exception:
        return False


def _lookup_row(seasonal: pd.DataFrame, destination: str, year: int, month: int) -> pd.Series:
    """Find the seasonal-dataset row. Falls back to the latest year available."""
    data_year = year if DATA_YEAR_MIN <= year <= DATA_YEAR_MAX else DATA_YEAR_MAX
    match = seasonal[
        (seasonal["destination"] == destination)
        & (seasonal["year"] == data_year)
        & (seasonal["month"] == month)
    ]
    if match.empty:
        # fall back to any year for that destination + month
        match = seasonal[
            (seasonal["destination"] == destination) & (seasonal["month"] == month)
        ]
    if match.empty:
        raise KeyError(destination)
    return match.iloc[0]


def _crowd_context(
    mock_m3: pd.DataFrame, destination: str, year: int, month: int
) -> tuple[str, str, bool]:
    """Crowd level, event note and off-season flag for display only.

    All three come from Module 3's mock output, never from Module 2's scoring.
    """
    row = mock_m3[
        (mock_m3["destination"] == destination)
        & (mock_m3["year"] == year)
        & (mock_m3["month"] == month)
    ]
    if row.empty:
        row = mock_m3[(mock_m3["destination"] == destination) & (mock_m3["month"] == month)]
    if row.empty:
        return "MEDIUM", "", False
    r = row.iloc[0]
    return (
        str(r["crowd_risk_level"]),
        _event_note(r.get("event_note")),
        bool(int(r.get("is_off_season", 0))),
    )


def _event_note(value: object) -> str:
    """Event note for display. The source data joins clauses with a hyphen,
    which the interface never uses as decoration, so it becomes a comma."""
    note = _text(value)
    return note.replace(" - ", ", ")


def _split_list(value: object) -> list[str]:
    """Pipe-delimited dataset string to a clean list."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    return [part.strip() for part in str(value).split("|") if part.strip()]


def _text(value: object) -> str:
    """Dataset cell to a plain string, blank when missing."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def season_reason(
    verdict: str,
    rain_risk: str,
    components: dict[str, float],
    baseline: dict[str, float],
) -> str:
    """Explain why a month scores the way it does, entirely from dataset values.

    Two signals are combined because neither alone is sufficient:

    * A *relative* deficit against the destination's own 12-month baseline
      isolates what makes this month worse than the rest of the year there.
      On its own it misses destinations whose weather is uniformly mediocre,
      where every month looks equally bad and the deficit is zero.
    * The *absolute* weather verdict and rain risk describe conditions a
      traveller would feel regardless of how the other months compare. On its
      own it surfaces factors that are equally true of the best months.

    Shared with Module 4 so a suitability label is explained the same way
    wherever it appears.
    """
    reasons: list[str] = []

    if verdict in POOR_WEATHER_VERDICTS and rain_risk in HIGH_RAIN_RISKS:
        reasons.append(f"{verdict.lower()} weather with {rain_risk.lower()} rain risk")

    deficits = sorted(
        ((baseline.get(c, 0.0) - components.get(c, 0.0), c) for c in SCORE_COMPONENTS),
        reverse=True,
    )
    for deficit, component in deficits:
        if len(reasons) >= 2:
            break
        if deficit < COMPONENT_DEFICIT_THRESHOLD:
            break
        if component == "weather_component" and reasons:
            continue  # already stated in absolute terms
        reasons.append(COMPONENT_REASONS[component])

    return "; ".join(reasons[:2])


@lru_cache(maxsize=1)
def _component_baselines() -> dict[str, dict[str, float]]:
    """Each destination's own 12-month average per score component."""
    seasonal = _load_assets()["seasonal"]
    monthly = seasonal.groupby(["destination", "month"])[list(SCORE_COMPONENTS)].mean()
    return monthly.groupby("destination").mean().to_dict("index")


def _season_label(value: object) -> str:
    """Season code to display wording, e.g. dry_season to Dry Season."""
    raw = _text(value)
    if not raw:
        return ""
    return SEASON_LABELS.get(raw, raw.replace("_", " ").title())


def get_seasonal_plan(destination: str, year: int, month: int) -> SeasonalPlanResponse:
    assets = _load_assets()
    row = _lookup_row(assets["seasonal"], destination, year, month)
    crowd_level, crowd_event_note, crowd_off_season = _crowd_context(
        assets["mock_m3"], destination, year, month
    )

    # Build the feature vector strictly in the trained order. feature_names.pkl
    # no longer contains any crowd field, so none is injected here.
    df_one = pd.DataFrame([row])
    df_one["dest_enc"] = assets["dest_encoder"].transform([destination])[0]
    df_one["clim_enc"] = assets["climate_encoder"].transform([row["climate_zone"]])[0]
    df_one["type_enc"] = assets["type_encoder"].transform([row["dest_type"]])[0]

    X = df_one[assets["feature_names"]].astype(float).values
    X_scaled = assets["scaler"].transform(X)

    pred_label_enc = int(assets["classifier"].predict(X_scaled)[0])
    suitability_label = str(assets["label_encoder"].inverse_transform([pred_label_enc])[0])

    tss_pred = float(assets["regressor"].predict(X_scaled)[0])
    tss_pred = max(0.0, min(1.0, tss_pred))

    breakdown = ScoreBreakdown(
        weather_component=round(float(row["weather_component"]), 4),
        season_component=round(float(row["season_component"]), 4),
        event_component=round(float(row["event_component"]), 4),
        holiday_component=round(float(row["holiday_component"]), 4),
        accessibility_component=round(float(row["access_component"]), 4),
    )

    return SeasonalPlanResponse(
        destination=destination,
        year=year,
        month=month,
        month_name=MONTH_NAMES[month - 1],
        suitability_label=suitability_label,
        travel_suitability_score=round(tss_pred, 4),
        recommendation_summary=_text(row["recommendation_summary"]),
        season_reason=(
            ""
            if suitability_label == "BEST"
            else season_reason(
                _text(row["weather_verdict"]),
                _text(row["rain_risk"]),
                {c: float(row[c]) for c in SCORE_COMPONENTS},
                _component_baselines().get(destination, {}),
            )
        ),
        score_breakdown=breakdown,
        weather_suitability_score=round(float(row["weather_suitability_score"]), 4),
        weather_verdict=_text(row["weather_verdict"]),
        avg_temp_c=round(float(row["avg_temp_c"]), 1),
        total_rainfall_mm=round(float(row["total_rainfall_mm"]), 1),
        rain_risk=_text(row["rain_risk"]),
        rainy_days=int(row["rainy_days"]),
        avg_humidity_pct=round(float(row["avg_humidity_pct"]), 1),
        sunshine_hours=round(float(row["sunshine_hours"]), 1),
        comfort_index=round(float(row["comfort_index"]), 1),
        season=_season_label(row["season"]),
        is_peak_national=bool(int(row["is_peak_national"])),
        is_best_period=bool(int(row["is_best_period_for_dest"])),
        festival_name=_text(row["festival_name"]),
        tourism_event_score=int(row["tourism_event_score"]),
        holiday_count=int(row["holiday_count"]),
        best_activities=_split_list(row["best_activities"]),
        packing_advice=_split_list(row["packing_advice"]),
        things_to_note=_split_list(row["things_to_note"]),
        sea_condition=_text(row["sea_condition"]),
        dest_type=_text(row["dest_type"]),
        climate_zone=_text(row["climate_zone"]),
        avg_stay_days=int(row["avg_stay_days"]),
        crowd_context_level=crowd_level,
        crowd_context_note=CROWD_CONTEXT_NOTE,
        crowd_event_note=crowd_event_note,
        is_off_season=crowd_off_season,
    )


def get_monthly_plan(destination: str, year: int) -> list[SeasonalPlanResponse]:
    return [get_seasonal_plan(destination, year, m) for m in range(1, 13)]


def get_all_destinations() -> list[DestinationInfo]:
    assets = _load_assets()
    attrs = assets["attrs"]
    result: list[DestinationInfo] = []
    for _, r in attrs.sort_values("destination").iterrows():
        result.append(
            DestinationInfo(
                destination=str(r["destination"]),
                dest_type=str(r["type"]),
                district=str(r["district"]),
                climate_zone=str(r["climate_zone"]),
                elevation_m=int(r["elevation_m"]),
            )
        )
    return result
