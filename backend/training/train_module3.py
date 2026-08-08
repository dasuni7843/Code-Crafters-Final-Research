"""
Module 3 — Crowd Risk — TRAINING
=================================
Predicts next-month tourist interest (a 0-100 "Destination Interest Index",
DII, fused from Google Trends search interest and Wikipedia page views) for
named places across Sri Lanka, then buckets the predicted month-over-month
change into LOW / MEDIUM / HIGH crowd risk using empirical terciles measured
during walk-forward evaluation.

Pipeline: adaptive DII fusion -> lag/rolling feature engineering -> signal
adequacy screening -> walk-forward LightGBM + RandomForest evaluation ->
inverse-MAPE ensemble -> tercile risk banding -> production RandomForest
refit on all history -> latest-snapshot predictions for the live app.

Coverage note: Module 3 tracks ~300 individual named attractions (finer
grain than the app's 20 core destinations). DEST_MAP below folds a handful
of sub-landmark keywords into the destination they belong to; everything
else keeps its own identity. module3_service flags which rows overlap the
app's 20 core destinations (app/config.py DESTINATIONS) when serving them.
"""
import warnings
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import lightgbm as lgb
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import classification_report, confusion_matrix, mean_absolute_error, mean_squared_error

warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
DATA_DIR = BASE_DIR / "data" / "module3"
MODELS_DIR = BASE_DIR / "models" / "module3"
RESULTS_DIR = BASE_DIR / "training" / "results" / "module3"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "#f8f9fa",
    "axes.grid": True, "grid.alpha": 0.4, "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
})
PAL = ["#2980b9", "#27ae60", "#e67e22", "#c0392b", "#8e44ad", "#16a085"]
RISK_LABELS = ["Low", "Medium", "High"]
RISK_ACTION = {"Low": "promote", "Medium": "monitor", "High": "redirect"}

FEATS = ["lag_1", "lag_2", "lag_3", "lag_6", "lag_12",
          "roll_mean_3", "roll_std_3", "pct_change", "month_num", "quarter"]

# A handful of sub-landmark Trends keywords fold into the destination they
# belong to; every other tracked place keeps its own name.
DEST_MAP = {
    "Sigiriya Rock Fortress": "Sigiriya", "Sigiriya Frescoes": "Sigiriya",
    "Sigiriya Museum": "Sigiriya", "Mirror Wall Sigiriya": "Sigiriya",
    "Sigiriya Lion Paw": "Sigiriya", "Sigiriya Water Gardens": "Sigiriya",
    "Nine Arch Bridge Ella": "Ella", "Ella Rock": "Ella", "Little Adam'S Peak Ella": "Ella",
    "Yala National Park Block 1 Entrance": "Yala", "Yala Safari Center": "Yala",
    "Mirissa Beach": "Mirissa", "Parrot Rock": "Mirissa",
    "Horton Plains National Park": "Horton Plains", "Horton Plains Visitor Centre": "Horton Plains",
    "Nilaveli Beach": "Nilaveli",
    "Bambarakiri Ella": "Bambarakanda",
}


def compute_mape(actual, pred) -> float:
    """Scale-independent MAPE, guarded against near-zero denominators."""
    a, p = np.array(actual), np.array(pred)
    mask = a > 1.0
    return float(np.mean(np.abs((a[mask] - p[mask]) / a[mask])) * 100) if mask.sum() else np.nan


def categorize_risk(value: float, low_t: float, high_t: float) -> str:
    if value <= low_t:
        return "Low"
    if value <= high_t:
        return "Medium"
    return "High"


def build_dii(trends_path: Path, wiki_path: Path) -> pd.DataFrame:
    """Fuse weekly Google Trends interest and monthly Wikipedia page views
    into a single monthly 0-100 Destination Interest Index (DII) per place.

    Trends-only destinations (no Wikipedia article) fall back to the
    normalized Trends signal alone rather than being dropped.
    """
    trends_df = pd.read_csv(trends_path, parse_dates=["date"])
    wiki_df = pd.read_csv(wiki_path, parse_dates=["date"])

    trends_df["canonical_destination"] = trends_df["destination"].map(DEST_MAP).fillna(trends_df["destination"])

    tr = trends_df[trends_df["geo"] == "LK"].groupby(["canonical_destination", "date"])["trend_index"].mean().reset_index()
    tr["month"] = tr["date"].dt.to_period("M").dt.to_timestamp()
    tr_m = tr.groupby(["canonical_destination", "month"])["trend_index"].mean().reset_index()
    tr_m.rename(columns={"canonical_destination": "destination"}, inplace=True)

    wiki_df["month"] = wiki_df["date"].dt.to_period("M").dt.to_timestamp()
    wk_m = wiki_df.groupby(["destination", "month"])["views"].mean().reset_index()

    fused = pd.merge(tr_m, wk_m, on=["destination", "month"], how="left")
    fused = fused.sort_values(["destination", "month"]).reset_index(drop=True)

    def min_max_norm(s: pd.Series) -> pd.Series:
        rng = s.max() - s.min()
        return (s - s.min()) / rng if rng > 0 else s * 0

    fused["g_norm"] = fused.groupby("destination")["trend_index"].transform(min_max_norm)
    fused["w_norm"] = fused.groupby("destination")["views"].transform(min_max_norm)
    fused["DII"] = np.where(
        fused["w_norm"].isna(),
        100 * fused["g_norm"],
        100 * (0.5 * fused["g_norm"] + 0.5 * fused["w_norm"]),
    )
    # Backward rolling mean only — no future lookahead leakage.
    fused["DII_smooth"] = fused.groupby("destination")["DII"].transform(
        lambda s: s.rolling(3, min_periods=1, center=False).mean()
    )
    return fused


def add_features(fused: pd.DataFrame) -> pd.DataFrame:
    g = fused.groupby("destination")["DII_smooth"]
    for lag in (1, 2, 3, 6, 12):
        fused[f"lag_{lag}"] = g.shift(lag)
    fused["roll_mean_3"] = g.transform(lambda s: s.shift(1).rolling(3).mean())
    fused["roll_std_3"] = g.transform(lambda s: s.shift(1).rolling(3).std())
    pct = g.shift(1).pct_change()
    fused["pct_change"] = pct.replace([np.inf, -np.inf], np.nan).fillna(0)
    fused["month_num"] = fused["month"].dt.month
    fused["quarter"] = fused["month"].dt.quarter
    fused["target"] = g.shift(-1)  # next month's DII_smooth
    return fused


def screen_active_destinations(fused: pd.DataFrame) -> list[str]:
    """Drop places whose Trends signal is zero more than half the time —
    too sparse for a lag/rolling model to learn anything from."""
    zero_frac = fused.groupby("destination")["DII_smooth"].apply(lambda s: (s == 0).mean())
    return zero_frac[zero_frac < 0.50].index.tolist()


def walk_forward_eval(model_ready: pd.DataFrame) -> pd.DataFrame:
    months = sorted(model_ready["month"].unique())
    split_start = int(len(months) * 0.7)  # 70/30 train/test split
    eval_months = months[split_start:]

    records = []
    for cut in eval_months:
        train = model_ready[model_ready["month"] < cut].copy()
        test = model_ready[model_ready["month"] == cut].copy()
        if len(train) < 20 or test.empty:
            continue

        X_train = train[FEATS].replace([np.inf, -np.inf], np.nan).fillna(0)
        X_test = test[FEATS].replace([np.inf, -np.inf], np.nan).fillna(0)
        y_train = train["target"]

        train["dest_cat"] = train["destination"].astype("category")
        test["dest_cat"] = test["destination"].astype("category")
        m_lgb = lgb.LGBMRegressor(
            n_estimators=150, learning_rate=0.05, num_leaves=15,
            min_child_samples=3, verbose=-1, random_state=42,
        )
        m_lgb.fit(train[FEATS + ["dest_cat"]], y_train, categorical_feature=["dest_cat"])

        rf = RandomForestRegressor(n_estimators=100, n_jobs=-1, random_state=42)
        rf.fit(X_train, y_train)

        test_sub = test.copy()
        test_sub["pred_lgbm"] = m_lgb.predict(test[FEATS + ["dest_cat"]])
        test_sub["pred_rf"] = rf.predict(X_test)
        test_sub["pred_naive"] = test_sub["lag_12"]
        records.append(test_sub)

    return pd.concat(records, ignore_index=True)


def main() -> None:
    print("=" * 70)
    print("  MODULE 3 — CROWD RISK (DESTINATION INTEREST INDEX) — TRAINING")
    print("=" * 70)

    print("\n[1/6] Building adaptive DII from Trends + Wikipedia signals...")
    fused = build_dii(DATA_DIR / "trends_master.csv", DATA_DIR / "wiki_master.csv")
    fused = add_features(fused)
    active = screen_active_destinations(fused)
    print(f"  Tracked places: {fused['destination'].nunique()} | Signal-adequate: {len(active)}")

    model_ready = fused[fused["destination"].isin(active)].dropna(subset=["lag_12", "target"]).copy()
    model_ready[FEATS] = model_ready[FEATS].replace([np.inf, -np.inf], np.nan).fillna(0)
    print(f"  Model-ready rows: {len(model_ready)}")

    print("\n[2/6] Walk-forward evaluation (LightGBM + RandomForest per fold)...")
    wf_results = walk_forward_eval(model_ready)
    naive_mape = compute_mape(wf_results["target"], wf_results["pred_naive"])
    rf_mape = compute_mape(wf_results["target"], wf_results["pred_rf"])
    lgb_mape = compute_mape(wf_results["target"], wf_results["pred_lgbm"])
    print(f"  Seasonal Naive MAPE: {naive_mape:.2f}%  |  RF MAPE: {rf_mape:.2f}%  |  LightGBM MAPE: {lgb_mape:.2f}%")

    print("\n[3/6] Inverse-MAPE per-destination ensemble + tercile risk banding...")
    dest_mape = wf_results.groupby("destination").apply(lambda g: pd.Series({
        "mape_lgbm": compute_mape(g["target"], g["pred_lgbm"]),
        "mape_rf": compute_mape(g["target"], g["pred_rf"]),
    }))
    dest_mape["w_lgbm"] = (1 / dest_mape["mape_lgbm"]) / ((1 / dest_mape["mape_lgbm"]) + (1 / dest_mape["mape_rf"]))
    dest_mape["w_rf"] = 1.0 - dest_mape["w_lgbm"]
    wf_results = wf_results.merge(dest_mape[["w_lgbm", "w_rf"]], on="destination")
    wf_results["pred_ensemble"] = wf_results["w_lgbm"] * wf_results["pred_lgbm"] + wf_results["w_rf"] * wf_results["pred_rf"]
    ensemble_mape = compute_mape(wf_results["target"], wf_results["pred_ensemble"])
    print(f"  Inverse-MAPE ensemble MAPE: {ensemble_mape:.2f}%")

    wf_results["actual_change"] = ((wf_results["target"] - wf_results["lag_1"]) / wf_results["lag_1"]).replace([np.inf, -np.inf], np.nan).fillna(0)
    wf_results["pred_change"] = ((wf_results["pred_ensemble"] - wf_results["lag_1"]) / wf_results["lag_1"]).replace([np.inf, -np.inf], np.nan).fillna(0)
    low_t, high_t = np.percentile(wf_results["pred_change"], [33.3, 66.7])
    wf_results["actual_risk"] = wf_results["actual_change"].apply(lambda v: categorize_risk(v, low_t, high_t))
    wf_results["predicted_risk"] = wf_results["pred_change"].apply(lambda v: categorize_risk(v, low_t, high_t))
    print(f"  Risk thresholds (month-over-month change): Low <= {low_t:.3f} <= Medium <= {high_t:.3f} <= High")
    print(classification_report(wf_results["actual_risk"], wf_results["predicted_risk"], labels=RISK_LABELS, target_names=RISK_LABELS, zero_division=0))

    print("[4/6] Fitting production RandomForest on all available history...")
    X_all = model_ready[FEATS].replace([np.inf, -np.inf], np.nan).fillna(0)
    y_all = model_ready["target"]
    final_rf = RandomForestRegressor(n_estimators=100, random_state=42)
    final_rf.fit(X_all, y_all)

    joblib.dump(final_rf, MODELS_DIR / "final_rf_crowd_model.joblib")
    joblib.dump(dest_mape[["w_lgbm", "w_rf"]], MODELS_DIR / "destination_ensemble_weights.joblib")
    joblib.dump({"low": float(low_t), "high": float(high_t)}, MODELS_DIR / "risk_thresholds.joblib")
    print(f"  Saved model + ensemble weights + risk thresholds to {MODELS_DIR}")

    print("\n[5/6] Charts + metrics summary...")
    summary_rows = []
    for name, col in [("Seasonal Naive", "pred_naive"), ("Random Forest", "pred_rf"),
                       ("Pooled LightGBM", "pred_lgbm"), ("Inverse-MAPE Ensemble", "pred_ensemble")]:
        summary_rows.append({
            "Model": name,
            "MAPE (%)": compute_mape(wf_results["target"], wf_results[col]),
            "MAE": mean_absolute_error(wf_results["target"], wf_results[col]),
            "RMSE": np.sqrt(mean_squared_error(wf_results["target"], wf_results[col])),
        })
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(RESULTS_DIR / "model_metrics_summary.csv", index=False)
    print(summary_df.to_string(index=False))

    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    sns.barplot(data=summary_df, x="Model", y="MAPE (%)", ax=axes[0, 0], palette="crest")
    axes[0, 0].set_title("Overall Forecast Error (MAPE %)", fontsize=13, fontweight="bold")
    axes[0, 0].tick_params(axis="x", rotation=15)
    for p in axes[0, 0].patches:
        axes[0, 0].annotate(f"{p.get_height():.2f}%", (p.get_x() + p.get_width() / 2, p.get_height()),
                             ha="center", va="center", xytext=(0, 5), textcoords="offset points", fontweight="bold")

    axes[0, 1].scatter(wf_results["target"], wf_results["pred_ensemble"], alpha=0.75, color="#2b5c8f", edgecolor="k")
    lims = [wf_results["target"].min(), wf_results["target"].max()]
    axes[0, 1].plot(lims, lims, "r--", lw=2, label="Ideal 1:1 Reference")
    axes[0, 1].set_title("Ensemble Forecast vs Actual Destination Interest Index", fontsize=13, fontweight="bold")
    axes[0, 1].set_xlabel("Actual DII"); axes[0, 1].set_ylabel("Predicted DII"); axes[0, 1].legend()

    sig_df = wf_results[wf_results["destination"] == "Sigiriya"].sort_values("month")
    if not sig_df.empty:
        axes[1, 0].plot(sig_df["month"], sig_df["target"], marker="o", label="Actual DII", color="black", linewidth=2.5)
        axes[1, 0].plot(sig_df["month"], sig_df["pred_ensemble"], marker="s", label="Ensemble Forecast", color="#2e7d32", linestyle="--")
        axes[1, 0].plot(sig_df["month"], sig_df["pred_naive"], marker="^", label="Seasonal Naive Baseline", color="gray", linestyle=":")
        axes[1, 0].set_title("Walk-Forward Tracking: Sigiriya", fontsize=13, fontweight="bold")
        axes[1, 0].tick_params(axis="x", rotation=30); axes[1, 0].legend()

    cm = confusion_matrix(wf_results["actual_risk"], wf_results["predicted_risk"], labels=RISK_LABELS)
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=RISK_LABELS, yticklabels=RISK_LABELS, ax=axes[1, 1])
    axes[1, 1].set_title("Crowd Risk Band Confusion Matrix (Tercile Classes)", fontsize=13, fontweight="bold")
    axes[1, 1].set_xlabel("Predicted Risk Band"); axes[1, 1].set_ylabel("Actual Risk Band")

    plt.tight_layout()
    plt.savefig(RESULTS_DIR / "model_evaluation_charts.png", dpi=300, bbox_inches="tight")
    plt.close()
    print(f"  Saved charts + metrics to {RESULTS_DIR}")

    print("\n[6/6] Latest-snapshot predictions for the live app...")
    # The most recent row per destination has lag features but no target yet
    # (there is no "next month" in the data) — that's exactly the row that
    # answers "what happens next" for a currently-running app.
    latest = (
        fused[fused["destination"].isin(active)]
        .dropna(subset=["lag_12"])
        .sort_values("month")
        .groupby("destination")
        .tail(1)
        .copy()
    )
    X_latest = latest[FEATS].replace([np.inf, -np.inf], np.nan).fillna(0)
    latest["predicted_dii"] = final_rf.predict(X_latest).clip(0, 100)
    latest["predicted_change_ratio"] = (
        (latest["predicted_dii"] - latest["lag_1"]) / latest["lag_1"]
    ).replace([np.inf, -np.inf], np.nan).fillna(0)
    latest["crowd_risk_level"] = latest["predicted_change_ratio"].apply(lambda v: categorize_risk(v, low_t, high_t))
    latest["crowd_score_0_100"] = latest["predicted_dii"].round(1)
    latest["recommendation_action"] = latest["crowd_risk_level"].map(RISK_ACTION)
    latest["last_known_month"] = latest["month"].dt.strftime("%Y-%m")
    latest["predicted_month"] = (latest["month"] + pd.DateOffset(months=1)).dt.strftime("%Y-%m")
    latest["latest_interest_index"] = latest["DII_smooth"].round(1)
    latest["predicted_change_pct"] = (latest["predicted_change_ratio"] * 100).round(1)
    latest["model_used"] = "RF_DII_WalkForward_Ensemble"

    out_cols = [
        "destination", "last_known_month", "predicted_month", "latest_interest_index",
        "predicted_dii", "predicted_change_pct", "crowd_risk_level", "crowd_score_0_100",
        "recommendation_action", "model_used",
    ]
    predictions = latest[out_cols].sort_values("crowd_score_0_100", ascending=False).reset_index(drop=True)
    predictions.to_csv(DATA_DIR / "module3_predictions.csv", index=False)
    print(f"  Saved {len(predictions)} destination predictions to {DATA_DIR / 'module3_predictions.csv'}")

    print("\n" + "=" * 70)
    print(f"  Naive={naive_mape:.2f}%  RF={rf_mape:.2f}%  LightGBM={lgb_mape:.2f}%  Ensemble={ensemble_mape:.2f}%")
    print("=" * 70)


if __name__ == "__main__":
    main()
