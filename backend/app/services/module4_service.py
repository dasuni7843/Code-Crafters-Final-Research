"""Module 4 — Personalization & Recommendation: model loading and inference."""
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler

from app.config import DATA_DIR, MODELS_DIR, MONTH_NAMES
# Seasonal suitability is Module 2's output, so the explanation of a suitability
# label lives there and is reused here rather than duplicated.
from app.services.module2_service import SCORE_COMPONENTS, season_reason

# Features used to build the content-based similarity matrix (matches training)
DEST_SIM_FEATURES = [
    "beach_score", "culture_score", "nature_score",
    "adventure_score", "avg_stay_days", "accessibility_score",
]
from app.schemas.module4_schemas import (
    DestinationProfile,
    DestinationRecommendation,
    RecommendationRequest,
    ScoreBreakdown,
    SimilarDestination,
)

M4_MODELS = MODELS_DIR / "module4"

CROWD_COMPAT = {
    "low": {"LOW": 1.0, "MEDIUM": 0.5, "HIGH": 0.1},
    "medium": {"LOW": 0.8, "MEDIUM": 1.0, "HIGH": 0.6},
    "high": {"LOW": 0.6, "MEDIUM": 0.8, "HIGH": 1.0},
}

PT_MAP = {"beach": 0, "cultural": 1, "nature": 2, "adventure": 3}
CT_MAP = {"low": 0, "medium": 1, "high": 2}
BUDGET_MAP = {"budget": 0, "mid": 1, "luxury": 2}
CROWD_MAP = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}


def _mode(s: pd.Series) -> str:
    """Most common value in a group, blank when the group is empty."""
    m = s.mode()
    return str(m.iloc[0]) if not m.empty else ""


def _build_similarity(features: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Rebuild the content-based similarity and feature matrices from the
    destination features CSV.

    This reproduces the exact computation used during training (MinMax scaling
    of the destination features followed by cosine similarity). Rebuilding here
    avoids depending on the pandas-pickled matrices, which fail to unpickle
    across pandas versions.
    """
    dest_matrix = features.set_index("destination")[DEST_SIM_FEATURES].fillna(0).astype(float)
    scaler = MinMaxScaler()
    feat_matrix = pd.DataFrame(
        scaler.fit_transform(dest_matrix),
        index=dest_matrix.index,
        columns=dest_matrix.columns,
    )
    sim_matrix = pd.DataFrame(
        cosine_similarity(feat_matrix),
        index=dest_matrix.index,
        columns=dest_matrix.index,
    )
    return sim_matrix, feat_matrix


@lru_cache(maxsize=1)
def _load_assets() -> dict:
    lgbm = joblib.load(M4_MODELS / "lgbm_rating_model.pkl")
    encoders = joblib.load(M4_MODELS / "encoders.pkl")
    feature_names = joblib.load(M4_MODELS / "feature_names.pkl")

    features = pd.read_csv(DATA_DIR / "module4" / "destination_features.csv")
    sim_matrix, feat_matrix = _build_similarity(features)
    # Module 1 is now the real trained model. Its production forecast is a
    # superset of the old mock schema, so this key is unchanged.
    mock_m1 = pd.read_csv(DATA_DIR / "module4" / "module1_output.csv")
    mock_m3 = pd.read_csv(DATA_DIR / "module4" / "mock_module3_output.csv")
    attrs = pd.read_csv(DATA_DIR / "raw" / "destination_attributes.csv")
    seasonal = pd.read_csv(DATA_DIR / "module2" / "module2_seasonal_travel_dataset.csv")

    # Per destination + month aggregates from the Module 2 dataset. The crowd
    # columns there are named ref_* because Module 2 does not score on crowd;
    # the values are unchanged from the columns this previously read.
    agg = (
        seasonal.groupby(["destination", "month"])
        .agg(
            avg_tss=("travel_suitability_score", "mean"),
            avg_wss=("weather_suitability_score", "mean"),
            avg_crowd_ratio=("ref_crowd_ratio", "mean"),
            weather_verdict=("weather_verdict", _mode),
            rain_risk=("rain_risk", _mode),
            suitability_label=("suitability_label", _mode),
            **{c: (c, "mean") for c in SCORE_COMPONENTS},
        )
        .reset_index()
    )
    # Each destination's own 12-month average per component. Comparing a month
    # against this baseline is what isolates why that month scores worse than
    # the rest of the year for the same destination.
    component_baseline = (
        agg.groupby("destination")[list(SCORE_COMPONENTS)].mean().to_dict("index")
    )
    dominant_crowd = (
        seasonal.groupby(["destination", "month"])["ref_crowd_level"]
        .agg(lambda s: s.mode().iloc[0])
        .reset_index()
        .rename(columns={"ref_crowd_level": "dominant_crowd"})
    )

    return {
        "lgbm": lgbm,
        "sim_matrix": sim_matrix,
        "feat_matrix": feat_matrix,
        "encoders": encoders,
        "feature_names": feature_names,
        "features": features.set_index("destination"),
        "mock_m1": mock_m1,
        "mock_m3": mock_m3,
        "component_baseline": component_baseline,
        "attrs": attrs.set_index("destination"),
        "agg": agg,
        "dominant_crowd": dominant_crowd,
    }


def models_loaded() -> bool:
    try:
        _load_assets()
        return True
    except Exception:
        return False


def _agg_for(
    assets: dict, destination: str, month: int
) -> tuple[float, float, float, str, str, str, str]:
    """Seasonal aggregates for a destination and month, plus Module 2's weather
    verdict and the reason text explaining why that month scores as it does.

    The verdict is taken from Module 2 rather than re-derived from avg_wss.
    Module 2 judges weather on rainfall as well as the suitability score, so a
    month with pleasant temperatures but very high rain risk reads as Poor.
    Deriving a second label here from the score alone contradicted that.
    """
    agg = assets["agg"]
    row = agg[(agg["destination"] == destination) & (agg["month"] == month)]
    dc = assets["dominant_crowd"]
    dcr = dc[(dc["destination"] == destination) & (dc["month"] == month)]
    crowd = str(dcr.iloc[0]["dominant_crowd"]) if not dcr.empty else "MEDIUM"
    if row.empty:
        return 0.5, 0.5, 0.5, crowd, "", "", ""
    r = row.iloc[0]
    verdict = str(r["weather_verdict"])
    reason = season_reason(
        verdict,
        str(r["rain_risk"]),
        {c: float(r[c]) for c in SCORE_COMPONENTS},
        assets["component_baseline"].get(destination, {}),
    )
    return (
        float(r["avg_tss"]),
        float(r["avg_wss"]),
        float(r["avg_crowd_ratio"]),
        crowd,
        verdict,
        reason,
        str(r["suitability_label"]),
    )


def _mock_m1(assets: dict, destination: str, year: int, month: int) -> tuple[int, int]:
    """Predicted arrivals and revenue from Module 1's real forecast.

    Filters by year first; falls back to any year for that destination and month
    so a lookup never fails even if the requested year is outside the forecast.
    """
    m1 = assets["mock_m1"]
    row = m1[(m1["destination"] == destination) & (m1["year"] == year) & (m1["month"] == month)]
    if row.empty:
        row = m1[(m1["destination"] == destination) & (m1["month"] == month)]
    if row.empty:
        return 0, 0
    r = row.iloc[0]
    return int(r["predicted_tourist_arrivals"]), int(r["estimated_revenue_lkr"])


def _mock_m3(assets: dict, destination: str, year: int, month: int) -> tuple[str, float, bool, str]:
    """Crowd risk, score, off-season flag and event note from Module 3's output."""
    m3 = assets["mock_m3"]
    row = m3[(m3["destination"] == destination) & (m3["year"] == year) & (m3["month"] == month)]
    if row.empty:
        row = m3[(m3["destination"] == destination) & (m3["month"] == month)]
    if row.empty:
        return "MEDIUM", 50.0, False, ""
    r = row.iloc[0]
    note = r.get("event_note")
    # The source data joins clauses with a hyphen; the interface never uses a
    # hyphen as decoration, so it becomes a comma.
    note = "" if note is None or pd.isna(note) else str(note).strip().replace(" - ", ", ")
    return (
        str(r["crowd_risk_level"]),
        float(r["crowd_score_0_100"]),
        bool(int(r.get("is_off_season", 0))),
        note,
    )


def _content_similarity(assets: dict, destination: str, preferred_type: str) -> float:
    """Average similarity of a destination to all destinations matching the user's type."""
    sim = assets["sim_matrix"]
    features = assets["features"]
    matching = [
        d for d in sim.index
        if str(features.loc[d]["type"]).lower() == preferred_type.lower() and d != destination
    ]
    if matching:
        return float(sim.loc[destination, matching].mean())
    # Fallback: the destination's own attribute score for the requested type
    attr_col = {
        "beach": "beach_score",
        "cultural": "culture_score",
        "nature": "nature_score",
        "adventure": "adventure_score",
    }.get(preferred_type.lower(), "culture_score")
    return float(features.loc[destination][attr_col])


def _season_suitability(avg_tss: float) -> str:
    """Fallback banding, used only when a destination and month is missing from
    the Module 2 dataset. Otherwise Module 2's own label is used, so the two
    modules never disagree about the same destination and month."""
    if avg_tss >= 0.65:
        return "BEST"
    if avg_tss >= 0.5:
        return "GOOD"
    return "AVOID"


def _why(destination: str, dest_type: str, req: RecommendationRequest,
         crowd_risk: str, season_fit: str, rating: float) -> str:
    reasons = []
    if season_fit == "BEST":
        reasons.append(f"{MONTH_NAMES[req.travel_month - 1]} is an ideal month to visit")
    elif season_fit == "GOOD":
        reasons.append(f"conditions in {MONTH_NAMES[req.travel_month - 1]} are favourable")
    if dest_type.lower() == req.preferred_type.lower():
        reasons.append(f"it matches your interest in {req.preferred_type} experiences")
    compat = CROWD_COMPAT.get(req.crowd_tolerance, {}).get(crowd_risk, 0.5)
    if compat >= 0.8:
        reasons.append(f"the {crowd_risk.lower()} crowd level suits your comfort")
    if rating >= 4.0:
        reasons.append(f"travellers rate it highly ({rating:.1f} of 5)")
    if not reasons:
        reasons.append("it offers a well-rounded experience for your preferences")
    text = ", and ".join([", ".join(reasons[:-1]), reasons[-1]]) if len(reasons) > 1 else reasons[0]
    return f"{destination} stands out because {text}."


def _predict_rating(assets: dict, destination: str, dest_type: str, cost_level: str,
                    crowd: str, req: RecommendationRequest,
                    avg_tss: float, avg_wss: float, avg_crowd_ratio: float,
                    features_row: pd.Series) -> float:
    enc = assets["encoders"]
    type_match = 1 if dest_type.lower() == req.preferred_type.lower() else 0
    alignment = 1.0 if type_match else 0.5

    vec = {
        "dest_enc": int(enc["le_dest"].transform([destination])[0]),
        "type_enc": int(enc["le_type"].transform([dest_type])[0]),
        "cost_enc": int(enc["le_cost"].transform([cost_level])[0]),
        "crowd_enc": CROWD_MAP.get(crowd, 1),
        "ct_enc": CT_MAP.get(req.crowd_tolerance, 1),
        "pt_enc": PT_MAP.get(req.preferred_type, 1),
        "budget_enc": BUDGET_MAP.get(req.trip_budget, 1),
        "type_match": type_match,
        "beach_score": float(features_row["beach_score"]),
        "culture_score": float(features_row["culture_score"]),
        "nature_score": float(features_row["nature_score"]),
        "adventure_score": float(features_row["adventure_score"]),
        "avg_stay_days": float(features_row["avg_stay_days"]),
        "accessibility_score": float(features_row["accessibility_score"]),
        "avg_tss": avg_tss,
        "avg_wss": avg_wss,
        "avg_crowd_ratio": avg_crowd_ratio,
        "travel_month": req.travel_month,
        "preference_alignment_score": alignment,
    }
    X = np.array([[vec[f] for f in assets["feature_names"]]], dtype=float)
    pred = float(assets["lgbm"].predict(X)[0])
    return max(1.0, min(5.0, pred))


def get_recommendations(req: RecommendationRequest) -> list[DestinationRecommendation]:
    assets = _load_assets()
    features = assets["features"]

    scored: list[dict] = []
    for destination in assets["sim_matrix"].index:
        frow = features.loc[destination]
        dest_type = str(frow["type"])
        cost_level = str(frow["avg_cost_level"])

        (
            avg_tss, avg_wss, avg_crowd_ratio, crowd,
            weather_verdict, season_reason, m2_label,
        ) = _agg_for(assets, destination, req.travel_month)
        crowd_risk, crowd_score, is_off_season, crowd_event_note = _mock_m3(
            assets, destination, req.travel_year, req.travel_month
        )
        arrivals, revenue = _mock_m1(assets, destination, req.travel_year, req.travel_month)

        rating = _predict_rating(
            assets, destination, dest_type, cost_level, crowd, req,
            avg_tss, avg_wss, avg_crowd_ratio, frow,
        )
        content_sim = _content_similarity(assets, destination, req.preferred_type)
        crowd_compat = CROWD_COMPAT.get(req.crowd_tolerance, {}).get(crowd_risk, 0.5)

        score = (
            (rating / 5.0) * 0.35
            + content_sim * 0.30
            + crowd_compat * 0.25
            + avg_tss * 0.10
        )

        # Module 2's own label, so a destination and month never carries a
        # different verdict here than it does on the seasonal planning page.
        season_fit = m2_label or _season_suitability(avg_tss)
        scored.append({
            "destination": destination,
            "score": score,
            "rating": rating,
            "content_sim": content_sim,
            "crowd_risk": crowd_risk,
            "crowd_score": crowd_score,
            "crowd_compat": crowd_compat,
            "is_off_season": is_off_season,
            "crowd_event_note": crowd_event_note,
            "arrivals": arrivals,
            "revenue": revenue,
            "avg_tss": avg_tss,
            "avg_wss": avg_wss,
            "season_fit": season_fit,
            "season_reason": season_reason,
            "weather_verdict": weather_verdict,
            "dest_type": dest_type,
            "frow": frow,
        })

    scored.sort(key=lambda d: d["score"], reverse=True)
    top = scored[: req.top_n]

    results: list[DestinationRecommendation] = []
    for i, d in enumerate(top, start=1):
        frow = d["frow"]
        best_months = [m.strip() for m in str(frow["best_months"]).split(",") if m.strip()]
        activities = [a.strip() for a in str(frow["activities"]).split(",") if a.strip()]
        results.append(
            DestinationRecommendation(
                rank=i,
                destination=d["destination"],
                recommendation_score=round(d["score"], 4),
                predicted_rating=round(d["rating"], 2),
                content_similarity_score=round(d["content_sim"], 4),
                crowd_risk_level=d["crowd_risk"],
                crowd_score=round(d["crowd_score"], 1),
                predicted_arrivals=d["arrivals"],
                estimated_revenue_lkr=d["revenue"],
                avg_tss=round(d["avg_tss"], 4),
                avg_wss=round(d["avg_wss"], 4),
                weather_label=d["weather_verdict"],
                season_suitability=d["season_fit"],
                # Only worth showing when the label is something to explain
                season_reason=d["season_reason"] if d["season_fit"] != "BEST" else "",
                why_recommended=_why(
                    d["destination"], d["dest_type"], req,
                    d["crowd_risk"], d["season_fit"], d["rating"],
                ),
                activities=activities,
                avg_stay_days=int(frow["avg_stay_days"]),
                best_months=best_months,
                dest_type=d["dest_type"],
                district=str(frow["district"]),
                is_off_season=d["is_off_season"],
                crowd_event_note=d["crowd_event_note"],
                score_breakdown=ScoreBreakdown(
                    predicted_rating=round((d["rating"] / 5.0) * 0.35, 4),
                    content_similarity=round(d["content_sim"] * 0.30, 4),
                    crowd_compatibility=round(d["crowd_compat"] * 0.25, 4),
                    seasonal_suitability=round(d["avg_tss"] * 0.10, 4),
                ),
            )
        )
    return results


def get_similar_destinations(destination: str, top_n: int = 4) -> list[SimilarDestination]:
    assets = _load_assets()
    sim = assets["sim_matrix"]
    if destination not in sim.index:
        raise KeyError(destination)
    features = assets["features"]
    series = sim.loc[destination].drop(labels=[destination]).sort_values(ascending=False)
    result: list[SimilarDestination] = []
    for dest, val in series.head(top_n).items():
        frow = features.loc[dest]
        result.append(
            SimilarDestination(
                destination=str(dest),
                similarity_score=round(float(val), 4),
                dest_type=str(frow["type"]),
                district=str(frow["district"]),
            )
        )
    return result


def get_destination_profile(destination: str) -> DestinationProfile:
    assets = _load_assets()
    features = assets["features"]
    if destination not in features.index:
        raise KeyError(destination)
    frow = features.loc[destination]
    best_months = [m.strip() for m in str(frow["best_months"]).split(",") if m.strip()]
    activities = [a.strip() for a in str(frow["activities"]).split(",") if a.strip()]
    return DestinationProfile(
        destination=destination,
        dest_type=str(frow["type"]),
        district=str(frow["district"]),
        climate_zone=str(frow["climate_zone"]),
        beach_score=float(frow["beach_score"]),
        culture_score=float(frow["culture_score"]),
        nature_score=float(frow["nature_score"]),
        adventure_score=float(frow["adventure_score"]),
        accessibility_score=float(frow["accessibility_score"]),
        avg_stay_days=int(frow["avg_stay_days"]),
        best_months=best_months,
        activities=activities,
        avg_cost_level=str(frow["avg_cost_level"]),
        family_friendly=bool(int(frow["family_friendly"])),
    )


def list_destinations() -> list[DestinationProfile]:
    assets = _load_assets()
    return [get_destination_profile(d) for d in sorted(assets["features"].index)]
