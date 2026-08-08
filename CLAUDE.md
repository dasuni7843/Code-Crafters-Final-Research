# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## System Description

Ceylon Tourism AI — a full-stack app (FastAPI + React/TypeScript) that recommends when and where to
travel in Sri Lanka. It chains four ML modules into one pipeline:

```
Demand Forecast (M1)  →  Seasonal Planning (M2)  →  Crowd Risk (M3)  →  Recommendations (M4)
   this system            this system              external mock         this system
```

- **Module 1** (`app/services/module1_service.py`) — SARIMA(0,1,2)(0,1,1,12) demand forecast + Linear
  Regression revenue (foreign/local split). Precomputed for 2026–2030 in
  `backend/data/module1/module1_output.csv`; **models are never re-run at request time**, the service
  only reads this CSV.
- **Module 2** (`app/services/module2_service.py`) — RandomForest suitability label (BEST/GOOD/AVOID) +
  XGBoost travel suitability score (TSS), from weather/season/events/holidays/accessibility.
  **Crowd is deliberately excluded** from every M2 feature and score — crowd is Module 3's concern and
  is only ever surfaced as context.
- **Module 3** — crowd risk. Two parallel things exist under this name:
  - The **mock pipeline** M2/M4/Integrated actually consume: `crowd_risk_level`/`crowd_score`/
    `recommendation_action` read via `backend/data/**/mock_module3_output.csv`, giving full
    20-destination × year × month coverage. `module4_service.py` and `routers/integrated.py` are
    unaffected by the real module below — swapping the mock CSV for a real one with matching columns
    and full coverage is still the intended upgrade path.
  - The **real, trained Module 3** (`app/services/module3_service.py`, router at `/api/module3`,
    frontend page at `/module3`) — a RandomForest/LightGBM ensemble trained in
    `backend/training/train_module3.py` on Google Trends + Wikipedia signal
    (`backend/data/module3/`), predicting a 0-100 Destination Interest Index one month ahead and
    banding the predicted change into LOW/MEDIUM/HIGH via empirical terciles. It tracks ~300
    individually named attractions (finer grain than the app's 20 core destinations), of which only
    a handful overlap `config.DESTINATIONS` (flagged via `is_core_destination`). Because coverage is
    partial and inference needs a recent real-world data point rather than an arbitrary future
    year/month, it is **not** wired into the M2/M4/Integrated pipeline — it's a standalone
    module with its own precomputed `module3_predictions.csv` (same "never re-run at request time"
    convention as Module 1).
- **Module 4** (`app/services/module4_service.py`) — LightGBM rating prediction + cosine content
  similarity + a weighted scorer (`rating*0.35 + content_sim*0.30 + crowd_compat*0.25 + avg_tss*0.10`)
  combining M1/M2 + the mock M3 pipeline into a final ranked recommendation.

## Commands

### Backend (from `backend/`)

```bash
python -m venv venv
venv\Scripts\activate            # PowerShell
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- API: `http://localhost:8000`, interactive docs: `http://localhost:8000/docs`
- Health check: `GET /api/health` → `{"status":"ok","models_loaded":true}`
- There is no automated test suite or lint config in this repo — verify backend changes via the
  `/docs` Swagger UI or direct requests to the running server.

### Frontend (from `frontend/`)

```bash
npm install
npm run dev        # dev server at http://localhost:5173, expects backend at :8000
npm run build       # tsc -b && vite build
npm run preview
```

No frontend test suite exists either. `npm run build` (via `tsc -b`) is the closest thing to a
correctness check — run it after non-trivial TypeScript changes.

### Docker

```bash
docker compose up --build   # frontend :5173, backend :8000
```

### Retraining models (rarely needed)

Scripts in `backend/training/` (`train_module1.py`, `train_module2.py`, `train_module4.py`,
`build_module1_dataset.py`, `forecast_2026_2030.py`) regenerate the `.pkl` files in `backend/models/`
and the chart PNGs in `backend/training/results/`. Do not run these casually — the app is designed to
serve precomputed models/CSVs, not retrain on request.

## Architecture Notes

**Backend layering**: `routers/` (HTTP layer, thin) → `services/` (model loading + inference logic,
one file per module) → `schemas/` (pydantic request/response models). `app/config.py` holds paths
(`MODELS_DIR`, `DATA_DIR`, `RESULTS_DIR`) and the canonical lists of `DESTINATIONS` (20, order matches
the trained encoders — don't reorder) and `MONTH_NAMES`.

**Model loading**: each service module has an `_load_assets()` cached with `@lru_cache(maxsize=1)` that
loads `.pkl` models + CSVs once; `main.py`'s startup hook calls `models_loaded()` on all three services
to warm the cache before the first request.

**Cross-module data flow** (important when touching `module4_service.py` or `routers/integrated.py`):
- M4 does **not** duplicate M2's suitability logic — it imports `SCORE_COMPONENTS` and `season_reason`
  from `module2_service` and reuses M2's own label (`m2_label`) as the season verdict, falling back to
  a local banding (`_season_suitability`) only when a destination/month is missing from the M2 dataset.
  This guarantees a destination+month never shows a different seasonal verdict on the Recommendations
  page than on the Seasonal Planning page.
- Lookups against mock/forecast CSVs (`_mock_m1`, `_mock_m3` in module4_service, `_mock_row` in
  integrated.py) filter by exact year first, then fall back to matching on destination+month only
  (ignoring year) so a lookup never 404s just because the requested year is outside the source data's
  range.
- `module4_service._build_similarity()` **rebuilds** the cosine similarity matrix from
  `destination_features.csv` at load time rather than unpickling the pandas-pickled matrix in
  `models/module4/` — cross-pandas-version unpickling of those matrices is unreliable.

**Versioning gotcha**: `requirements.txt` pins `xgboost==3.1.1` specifically because it's required to
correctly unpickle `module2/tss_regressor.pkl` with its learned `base_score` intact (3.0.x silently
resets it, degrading R² from ~0.98 to 0.78; 3.3.x can't read the file at all). Don't bump this without
retraining.

**Frontend structure**: `pages/` (one per module + Home + Integrated + TrainingResults) compose
`components/<module>/` pieces; shared primitives live in `components/ui/`. `services/api.ts` is the
single Axios client; `hooks/useApi.ts` wraps request/loading/error state. `lib/constants.ts` and
`lib/destinationImages.ts` hold static lookup data. Base API URL comes from `VITE_API_URL`
(`frontend/.env.example`), default `http://localhost:8000`.

**Error handling convention** (`app/main.py`): all errors (validation, HTTP, unhandled) are normalized
to `{"error": true, "message": "<user-friendly>", "detail": "<raw>"}` via global exception handlers —
follow this shape if adding new error paths rather than letting FastAPI's default error format leak
through.

## Data Provenance

Module 1 is trained on real SLTDA (Sri Lanka Tourism Development Authority) monthly arrival data,
2010–2018 (2019–2022 excluded due to the Easter attacks, COVID border closure, and the economic
crisis), plus Central Cultural Fund, Department of Wildlife Conservation, and Department of Forest
Conservation site records. Module 2's dataset is climatology-based, sourced from 2015–2024
(`DATA_YEAR_MIN`/`DATA_YEAR_MAX` in `module2_service.py`); any requested year outside that range falls
back to the climatology row for that destination/month, since seasonal patterns repeat annually.
