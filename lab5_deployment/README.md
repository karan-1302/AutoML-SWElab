# Lab 5: Deployment & Interaction Architecture

**Assignment:** Assignment 5 — Deployment Plan + Implementation of Two Key Modules  
**Status:** ✅ COMPLETE  
**Date:** April 26, 2026

---

## Overview

Lab 5 implements the deployment strategy for the Real Estate AutoML system defined in Lab 4's layered architecture. It consists of two parts:

1. **Deployment Plan** (`Deployment.md`) — Maps the 5-layer architecture to cloud platforms
2. **Backend Implementation** (`backend/`) — Two key modules demonstrating the architecture in action

---

## Part 1: Deployment Plan

**File:** `Deployment.md`

A practical, non-overcomplicated deployment strategy that:

- Maps each layer to a specific hosting platform:
  - **Layer 1 (Presentation)** → Vercel (React frontend)
  - **Layers 2–4 (API + BLL + DAL)** → Render (FastAPI backend)
  - **Layer 5 (Storage)** → Supabase (D1, D2) + DagsHub MLflow (D3)

- Provides 6 concrete deployment steps
- Includes security measures and sequence diagrams
- Shows how to swap in-memory stores for production databases

---

## Part 2: Backend Implementation

**Directory:** `backend/`

A working FastAPI backend that demonstrates the layered architecture with two key modules:

### Module 1: AutoML Trainer (Layer 3 — Business Logic Layer)

**File:** `backend/services/automl_trainer.py`

Implements the `AutoMLTrainer` component from Lab 4:

```python
def run_automl(user_id: str, df: pd.DataFrame, target_column: str):
    """
    Train LinearRegression, RandomForest, and XGBoost.
    Evaluate each model on a held-out test set.
    Select the best model by R² score.
    Persist the winning pipeline to D3 (Model Registry).
    """
```

**Features:**
- Trains 3 candidate algorithms in sequence
- Computes RMSE, MAE, and R² metrics
- Live progress tracking (0–100% per algorithm)
- Runs in a background thread (called by `/api/train/start`)
- Properly handles preprocessing (numeric + categorical columns)

**Maps to:** DFD Process 3.0 (AutoML Training & Registry)

---

### Module 2: Prediction Router (Layer 2 — API/Router Layer)

**File:** `backend/routers/predict.py`

Implements the full prediction flow from Lab 4:

```python
@router.post("", response_model=PredictResponse)
def predict_price(
    body: PredictRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate a property price prediction.
    
    Layer flow:
      Layer 2 (this router) validates JWT
      → Layer 3 (BLL) via sklearn Pipeline
      → Layer 4 (DAL) loads model from D3
      → Returns prediction to React
    """
```

**Features:**
- Accepts property features as JSON
- Requires JWT authentication
- Loads trained model from D3 (Model Registry)
- Runs inference via sklearn Pipeline
- Calculates confidence (heuristic: R² → 50–99%)
- Caches result for Explain endpoint

**Maps to:** Use Case UC-09 (Generate Prediction)

---

## Backend Structure

```
backend/
├── main.py                          # FastAPI entry point (Layer 2)
├── models/
│   └── schemas.py                   # Pydantic request/response schemas
├── routers/
│   ├── auth.py                      # POST /api/auth/login
│   ├── ingest.py                    # POST /api/ingest/upload
│   ├── train.py                     # POST /api/train/start, GET /api/train/status
│   ├── predict.py                   # ⭐ POST /api/predict (KEY MODULE 2)
│   └── explain.py                   # GET /api/explain/latest
├── services/
│   └── automl_trainer.py            # ⭐ run_automl() (KEY MODULE 1)
├── utils/
│   ├── security.py                  # JWT + password hashing
│   └── store.py                     # In-memory DAL (D1, D2, D3 placeholders)
├── requirements.txt                 # Python dependencies
└── .env.example                     # Environment variables template
```

---

## How to Run Locally

### 1. Install Dependencies

```bash
cd lab5_deployment/backend
pip install -r requirements.txt
```

### 2. Start the Backend

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### 3. Test the Endpoints

**Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@realestate.com","password":"password123"}'
```

Returns a JWT token. Use it for subsequent requests:

```bash
TOKEN="<jwt-from-login>"

# Upload a CSV
curl -X POST http://localhost:8000/api/ingest/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@data.csv"

# Start training
curl -X POST http://localhost:8000/api/train/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"dataset_id":"abc123","target_column":"price"}'

# Check training status
curl -X GET http://localhost:8000/api/train/status \
  -H "Authorization: Bearer $TOKEN"

# Make a prediction
curl -X POST http://localhost:8000/api/predict \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"features":{"bedrooms":3,"sqft_living":1800,"zipcode":"98001"}}'

# Get explanation
curl -X GET http://localhost:8000/api/explain/latest \
  -H "Authorization: Bearer $TOKEN"
```

---

## Deployment to Production

### Step 1: Set Up Storage

1. Create a Supabase project → copy `DATABASE_URL`
2. Create a DagsHub repository → enable MLflow → copy token and tracking URI
3. Run the SQL schema from Lab 4 Section VII to create tables

### Step 2: Configure Environment

Copy `.env.example` to `.env` and fill in:
- `SECRET_KEY` (random 32-char string)
- `DATABASE_URL` (Supabase)
- `DAGSHUB_USER_TOKEN` (DagsHub)
- `MLFLOW_TRACKING_URI` (DagsHub)
- `CORS_ORIGINS` (Vercel domain)

### Step 3: Deploy Backend to Render

1. Push code to GitHub
2. Create a new Web Service on Render
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn main:app --host 0.0.0.0 --port 8000`
5. Add environment variables from `.env`
6. Deploy

### Step 4: Deploy Frontend to Vercel

1. Push React code to GitHub
2. Import repo in Vercel
3. Set `REACT_APP_API_URL` to the Render backend URL
4. Deploy

---

## Architecture Mapping

| Lab 4 Component | Implementation | File |
|---|---|---|
| Layer 2: API/Router | FastAPI + 5 routers | `main.py` + `routers/` |
| Layer 3: BLL — AutoMLTrainer | `run_automl()` | `services/automl_trainer.py` |
| Layer 3: BLL — Explainer | `_compute_feature_contributions()` | `routers/explain.py` |
| Layer 4: DAL — ModelRegistry | `get_training_job()` | `utils/store.py` |
| Layer 5: D1 — User Database | `USERS` dict | `utils/store.py` |
| Layer 5: D2 — Dataset Storage | `DATASETS` dict | `utils/store.py` |
| Layer 5: D3 — Model Registry | `TRAINING_JOBS` dict | `utils/store.py` |

---

## Key Design Decisions

1. **In-Memory Store:** For simplicity, the DAL uses Python dicts. In production, swap for Supabase + DagsHub.

2. **Background Training:** The `/api/train/start` endpoint spawns a daemon thread so the HTTP response returns immediately. The frontend polls `/api/train/status` for progress.

3. **Confidence Heuristic:** Prediction confidence is calculated as `50 + R² * 49`, mapping model R² (0–1) to confidence (50–99%).

4. **Feature Contributions:** The Explain endpoint uses feature importances (tree-based) or coefficients (linear) instead of full SHAP for simplicity. In production, use `shap.TreeExplainer`.

5. **No Database Migrations:** The in-memory store doesn't require migrations. When deploying to Supabase, use Alembic for schema management.

---

## Verification

✅ **Module 1 (AutoML Trainer):**
- Trains all 3 algorithms
- Computes metrics correctly
- Selects best model by R²
- Stores pipeline in D3

✅ **Module 2 (Prediction Router):**
- Loads model from D3
- Preprocesses input features
- Runs inference
- Caches result for Explain endpoint

✅ **End-to-End:**
- Synthetic data training: ✅
- Prediction generation: ✅
- Confidence calculation: ✅

---

## Files Included

- `Deployment.md` — Detailed deployment plan
- `COMPLETION_REPORT.md` — Assignment completion summary
- `backend/main.py` — FastAPI entry point
- `backend/models/schemas.py` — Pydantic schemas
- `backend/routers/` — 5 routers (auth, ingest, train, predict, explain)
- `backend/services/automl_trainer.py` — AutoML Trainer (KEY MODULE 1)
- `backend/utils/security.py` — JWT + password hashing
- `backend/utils/store.py` — In-memory DAL
- `backend/requirements.txt` — Python dependencies
- `backend/.env.example` — Environment variables template

---

## Summary

Lab 5 is **complete** with:

1. ✅ **Deployment Plan** — Practical, non-overcomplicated, production-ready
2. ✅ **Two Key Modules** — AutoML Trainer (BLL) + Prediction Router (API/Router)

Both modules are fully implemented, documented, verified, and ready for deployment to Render + Supabase.
