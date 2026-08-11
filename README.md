# Sri Lanka Tourism AI System
## Tourism Forecasting and Personalized Destination Recommendation

Faculty of Information Technology | University of Moratuwa | Level 4
Group: Code Crafters

---

## System Description

Ceylon Tourism AI is a full-stack web application that helps travellers decide **when** and **where**
to visit in Sri Lanka. It brings together four machine learning modules into a single recommendation
pipeline. Given a traveller's preferences and a target month, the system estimates the best season to
travel to each of 20 destinations, predicts how well each destination matches the traveller, and ranks
them into a personalized shortlist with clear, human-readable reasons behind every recommendation.

This codebase implements **Module 1 (Destination Level Tourist Demand and Revenue Prediction)**,
**Module 2 (Seasonal Travel Planning)** and **Module 4 (Traveler Personalization and Destination
Recommendation)**. Only Module 3 (Crowd Risk) is built by another team member; its output is consumed
here through a mock CSV file in the format that module produces. The application exposes standalone demos
for Modules 1, 2 and 4, an integrated view that runs the complete four-module pipeline, and a gallery of
the training result charts.

## Architecture

The system follows a four-module pipeline:

```
Demand Forecast (M1)  →  Seasonal Planning (M2)  →  Crowd Risk (M3)  →  Recommendations (M4)
   this system            this system              external input        this system
```

- **Module 1 - Destination Level Tourist Demand and Revenue Prediction** (this system): demand is
  forecast with SARIMA(0,1,2)(0,1,1,12), selected over ARIMA(0,2,3), and revenue is estimated with
  Linear Regression split into foreign and local visitors. Trained on real SLTDA monthly arrival data,
  the forecast covers 2026 to 2030 for all 20 destinations and is precomputed in
  `backend/data/module1/module1_output.csv`. The models are never re-run at request time.
- **Module 2 - Seasonal Travel Planning** (this system): a RandomForest classifier assigns a
  BEST / GOOD / AVOID suitability label and an XGBoost regressor predicts a travel suitability score (TSS).
  Module 2 evaluates seasonal suitability using weather, seasonal attractiveness, tourism events, public
  holidays, and accessibility. It does not use crowd data - crowd risk is produced by Module 3 and
  consumed by Module 4.
- **Module 3 - Crowd Risk** (external): crowd risk level, score and a recommended action per destination
  and month, from an ensemble model. Consumed via `backend/data/**/mock_module3_output.csv`.
- **Module 4 - Personalization & Recommendation** (this system): a LightGBM model predicts a traveller's
  rating for each destination, a cosine content-similarity matrix measures how well a destination matches
  the preferred experience, and a weighted scorer combines rating, similarity, crowd compatibility and
  seasonal suitability into a final ranking.

## Tech Stack

- **Backend:** Python 3.12/3.13, FastAPI, scikit-learn, XGBoost, LightGBM, pandas, numpy, joblib
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Recharts, React Router, Axios, Lucide icons
- **ML Models:** SARIMA and ARIMA demand forecasting, Linear Regression revenue, RandomForest Classifier,
  XGBoost Regressor, LightGBM Rating Predictor, Cosine Similarity

## Project Structure

```
project_root/
├── backend/
│   ├── app/
│   │   ├── main.py                 FastAPI entry point (CORS, static, routers, error handling)
│   │   ├── config.py               paths and constants
│   │   ├── routers/                module1, module2, module4, integrated, results
│   │   ├── services/               module1_service, module2_service, module4_service (loading + inference)
│   │   └── schemas/                pydantic request/response models
│   ├── models/                     trained .pkl files (M1 + M2 + M4) - not retrained
│   ├── data/                       datasets, real Module 1 forecast + mock Module 3 output
│   ├── training/                   training scripts + result chart PNGs
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/                  Home, Module1, Module2, Module4, Integrated, TrainingResults
│   │   ├── components/             layout, ui, module2, module4, integrated
│   │   ├── context/                ThemeContext (dark/light)
│   │   ├── hooks/                  useApi
│   │   ├── services/api.ts         Axios client
│   │   ├── types/                  TypeScript interfaces
│   │   └── lib/                    constants and formatters
│   ├── package.json
│   ├── Dockerfile
│   └── vite.config.ts
├── docker-compose.yml
└── README.md
```

## Prerequisites

- Python 3.12.1
- Node.js 18+
- npm or yarn

## Setup and Installation

### Backend Setup

```bash
cd backend
python -m venv venv

# Windows ( If Bash)
source venv/Scripts/activate

# If powershell Terminal
venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

python -m pip install --upgrade pip

python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API is served at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.
Verify it is healthy: `http://localhost:8000/api/health` returns `{"status":"ok","models_loaded":true}`.

### Frontend Setup

```bash
cd frontend
npm install
# optional: copy .env.example to .env to point at a non-default API URL
npm run dev
```

The app runs at `http://localhost:5173` and expects the backend at `http://localhost:8000`
(override with `VITE_API_URL`).

### Running with Docker

```bash
docker compose up --build
```

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

## How to Test Each Module

### Testing Module 1 - Demand Forecast

Navigate to **Demand forecast** in the sidebar. Select a destination, a forecast year (2026 through
2030) and a month, then click **Get demand forecast**. Expected outputs: the predicted arrivals as a
headline figure with its confidence range, the foreign and local visitor split, the estimated revenue
split into foreign and local with a revenue-per-visitor figure, and the model detail (SARIMA, 6.78
percent MAPE, national arrivals for context). Switch to **Full year** to see the 12-month arrivals line
with its confidence band, a monthly revenue bar chart and a summary strip with the peak and lowest
months. Expand **How this forecast was produced** to compare ARIMA against the selected SARIMA model.

Example test cases:
- Sigiriya, December 2026 → highest monthly arrivals, peak season
- Sigiriya, May 2026 → lowest monthly arrivals, monsoon trough
- Yala, any month → highest revenue per visitor among destinations

Forecasts for 2028 and later show a note that longer horizons carry wider uncertainty and are intended
for long range planning.

### Testing Module 2 - Seasonal Travel Planning

Navigate to **Seasonal planning** in the sidebar. Select a destination and month, then click
**Get seasonal plan**. Expected outputs: the suitability verdict and summary, a breakdown showing how
the score is composed, the weather detail grid, seasonal and festival context, and practical advice on
what to do, what to pack and what to note. Crowd level is shown separately as context from Module 3.
Switch to **Full year calendar** to see all 12 months at once, with best and avoid month chips; select
any month to open its full detail.

A year selector (2026 through 2030) keeps Module 2 aligned with the Module 1 forecast range. Seasonal
suitability follows climate patterns that repeat annually, so the dataset is climatology based; any year
outside its 2015 to 2024 source range falls back to the climatology row for that destination and month.

Example test cases:
- Mirissa, January → Best time to visit, Whale Watching Peak festival, sea calm and swimmable
- Ella, June → Avoid this period (southwest monsoon, high rain risk, rain jacket advised)
- Kandy, August → Best time to visit, Esala Perahera festival banner
- Sigiriya, March → Best time to visit (dry season, climbing activities listed)

### Testing Module 4 - Personalized Recommendations

Navigate to **Recommendations** in the sidebar. Fill in your preferences and click **Find my perfect
destinations**. Expected: a ranked list of destinations with match scores and reasons. Use **See similar**
on any card to explore related destinations.

Example test cases:
- Beach lover, prefer quiet, December → Mirissa or Unawatuna ranked first
- Culture explorer, moderate crowd, August → Dambulla or Sigiriya ranked first (Kandy drops during
  Esala Perahera, when crowds are at their heaviest)
- Nature seeker, lively is fine, April → Sigiriya or Yala near the top

### Testing the Full System

Navigate to **Full system** in the sidebar. Keep **Show pipeline steps** enabled to see how all four
modules contribute. Same inputs as Module 4 - the results show the Module 1 forecast, Module 2 seasonal
score, Module 3 crowd risk and the Module 4 final rank, with a score breakdown on every card.

## Model Performance

### Module 1 - Destination Level Tourist Demand and Revenue Prediction
- **Selected model: SARIMA(0,1,2)(0,1,1,12)** - MAPE 6.78%, MAE 13,784, RMSE 18,597
- ARIMA(0,2,3) comparison - MAPE 20.97%, MAE 35,305, RMSE 41,388
- Linear Regression revenue - R² 0.63 foreign, 0.76 local
- Trained on 108 months of real SLTDA data from 2010 to 2018. The years 2019 to 2022 are excluded due to
  the Easter Sunday attacks, the COVID-19 border closure and the economic crisis.

SARIMA was selected over ARIMA because it captures Sri Lanka's strong annual seasonality. Demand is
forecast at the national level and calibrated down to each of the 20 destinations; revenue is derived
from the foreign and local visitor split.

### Module 2 - Seasonal Travel Planning
- RandomForest Accuracy: 96.88%
- 5-Fold CV Accuracy: 97.21%
- XGBoost R²: 0.9984
- XGBoost RMSE: 0.0061

Scored from weather, seasonal attractiveness, tourism events, public holidays and accessibility.
Crowd is not a Module 2 feature.

### Module 4 - Recommendations
- LightGBM RMSE: 0.1385
- Exact Match Accuracy: 97.57%
- Mean NDCG@10: 0.9885

## Data Provenance

Module 1 is trained and calibrated entirely on real, official Sri Lankan tourism data:

- **SLTDA Annual Statistical Reports 2010 to 2025** - national monthly arrival series and annual totals
- **Central Cultural Fund site records** - visitor counts for cultural triangle sites
- **Department of Wildlife Conservation park records** - national park visitor counts
- **Department of Forest Conservation records** - forest and nature reserve visitor counts

## API Reference

| Method | Path | Description | Request body |
| --- | --- | --- | --- |
| GET | `/api/health` | Health check and model status | - |
| GET | `/api/module1/forecast/{destination}/{year}/{month}` | Demand and revenue forecast for one month | - |
| GET | `/api/module1/yearly/{destination}/{year}` | Forecast for all 12 months | - |
| GET | `/api/module1/comparison` | ARIMA vs SARIMA metrics and selected model | - |
| GET | `/api/module1/all/{year}/{month}` | Every destination for one month, ranked by arrivals | - |
| GET | `/api/module1/historical/{destination}` | Real SLTDA annual records for a destination | - |
| GET | `/api/module2/destinations` | All 20 destinations with type, district, climate | - |
| GET | `/api/module2/plan/{destination}/{year}/{month}` | Seasonal plan for one month | - |
| GET | `/api/module2/monthly/{destination}/{year}` | Seasonal plan for all 12 months | - |
| GET | `/api/module4/destinations` | All destinations with feature profiles | - |
| POST | `/api/module4/recommend` | Ranked recommendations | `RecommendationRequest` |
| GET | `/api/module4/similar/{destination}` | Most similar destinations | query: `top_n` |
| GET | `/api/module4/destination/{name}` | Full destination profile | - |
| POST | `/api/integrated/recommend` | Full four-module pipeline result | `RecommendationRequest` |
| GET | `/api/results/module1` | Module 1 chart metadata | - |
| GET | `/api/results/module2` | Module 2 chart metadata | - |
| GET | `/api/results/module4` | Module 4 chart metadata | - |
| GET | `/results/{module}/{file}.png` | Static result chart images | - |

`RecommendationRequest`:

```json
{
  "preferred_type": "beach",
  "crowd_tolerance": "low",
  "travel_month": 12,
  "travel_year": 2026,
  "trip_budget": "mid",
  "travel_party": "couple",
  "weather_preference": "any",
  "activity_preference": "beach",
  "top_n": 5
}
```

## Environment Variables

| Variable | Where | Default | Description |
| --- | --- | --- | --- |
| `BACKEND_HOST` | backend | `0.0.0.0` | Host the API binds to |
| `BACKEND_PORT` | backend | `8000` | Port the API binds to |
| `CORS_ORIGINS` | backend | `http://localhost:5173,http://localhost:3000` | Allowed frontend origins |
| `VITE_API_URL` | frontend | `http://localhost:8000` | Base URL of the backend API |

## Notes on Module 3

Module 1 (Demand Forecasting) is now implemented and trained on real SLTDA data; its production forecast
lives in one place, `backend/data/module1/module1_output.csv`, and is read from there by Module 4 and the
integrated pipeline. Module 2 does not consume it - Module 2 scores seasonal suitability on weather,
seasonality, events, holidays and accessibility only. **Only Module 3 (Crowd Risk)
remains mocked** - it is built by another team member and is consumed via
`backend/data/**/mock_module3_output.csv`, which covers 2024 to 2030 so crowd lookups resolve for every
selectable forecast year. When Module 3 integration is complete, replace its mock CSV with the real output
- no code changes are needed, as the service layer reads the same columns the real module produces.
