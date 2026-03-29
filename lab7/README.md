# Real Estate AutoML Prediction System — Lab 7
## CS 331 Software Engineering Lab — Assignment 7: Business Logic Layer (BLL)

---

## Architecture Overview

This assignment refactors the Lab 6 application to introduce an **explicit Business Logic Layer (BLL)** that mediates between the Presentation Layer and the Data Access Layer.

```
┌──────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                            │
│                                                                  │
│   React Frontend (Pages)          FastAPI Routers (Thin HTTP)    │
│   ├── LoginPage.js                ├── routers/auth.py            │
│   ├── UploadPage.js               ├── routers/ingest.py          │
│   ├── TrainPage.js                ├── routers/train.py           │
│   ├── PredictPage.js              ├── routers/predict.py         │
│   └── ExplainPage.js              └── routers/explain.py         │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                  BUSINESS LOGIC LAYER (BLL)                      │
│                                                                  │
│   bll/auth_bll.py      — Credential validation, JWT generation   │
│   bll/ingest_bll.py    — File validation, data quality scoring   │
│   bll/train_bll.py     — Target validation, training orchestration│
│   bll/predict_bll.py   — Feature validation, confidence scoring  │
│   bll/explain_bll.py   — SHAP computation, recommendation engine │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                    DATA ACCESS LAYER                             │
│                                                                  │
│   utils/store.py           — In-memory data store (users,        │
│                              datasets, training jobs, predictions)│
│   utils/security.py        — JWT + bcrypt helpers                │
│   services/automl_trainer.py — sklearn + XGBoost ML pipeline     │
│   models/schemas.py        — Pydantic request/response schemas   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
lab7/
├── Q2_documentation.md          # Q2 answers (Business Rules, Validation, Data Transformation)
├── README.md                    # This file
├── backend/
│   ├── main.py                  # FastAPI entry point (v2.0 BLL architecture)
│   ├── requirements.txt
│   ├── .env
│   ├── bll/                     # ★ BUSINESS LOGIC LAYER (NEW in Lab 7)
│   │   ├── __init__.py
│   │   ├── auth_bll.py          # Authentication business rules
│   │   ├── ingest_bll.py        # Data ingestion business rules
│   │   ├── train_bll.py         # Training business rules
│   │   ├── predict_bll.py       # Prediction business rules
│   │   └── explain_bll.py       # Explainability business rules
│   ├── routers/                 # Thin HTTP handlers (delegate to BLL)
│   │   ├── auth.py
│   │   ├── ingest.py
│   │   ├── train.py
│   │   ├── predict.py
│   │   └── explain.py
│   ├── models/
│   │   └── schemas.py           # Pydantic schemas (validation)
│   ├── services/
│   │   └── automl_trainer.py    # ML training engine
│   └── utils/
│       ├── security.py          # JWT + bcrypt
│       └── store.py             # In-memory data store
└── frontend/
    ├── package.json
    └── src/
        ├── App.js
        ├── context/
        │   ├── AuthContext.js
        │   └── AppContext.js
        ├── components/
        │   ├── Sidebar.js
        │   ├── DataGrid.js
        │   └── ProgressBar.js
        └── pages/               # Enhanced with BLL validation feedback
            ├── LoginPage.js     # Real-time email/password validation
            ├── UploadPage.js    # Data quality report display
            ├── TrainPage.js     # Target column validation
            ├── PredictPage.js   # Per-field range validation
            └── ExplainPage.js   # BLL pipeline visualisation
```

---

## What Changed from Lab 6

| Aspect            | Lab 6                              | Lab 7                                    |
|-------------------|------------------------------------|------------------------------------------|
| Business Logic    | Mixed into routers                 | Extracted into `bll/` package            |
| Routers           | Fat (contain logic + HTTP)         | Thin (only HTTP, delegate to BLL)        |
| Validation        | Pydantic only                      | 3-tier: Client + Pydantic + BLL          |
| Data Quality      | Not reported                       | Quality score, missing data analysis     |
| Error Messages    | Single string                      | Array of specific validation errors      |
| Frontend Feedback | Basic error alerts                 | Per-field validation, quality reports     |

---

## Setup & Running

### Backend

```bash
cd lab7/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

API at `http://localhost:8000` · Docs at `http://localhost:8000/docs`

### Frontend

```bash
cd lab7/frontend
npm install
npm start
```

Dashboard at `http://localhost:3000`

---

## Demo Credentials

| Field    | Value               |
|----------|---------------------|
| Email    | demo@realestate.com |
| Password | password123         |

---

## BLL Module Summary

| Module         | Business Rules | Key Validations                          |
|----------------|---------------|------------------------------------------|
| `auth_bll`     | 7 rules       | Email format, password length, hash match|
| `ingest_bll`   | 9 rules       | Extension, size, quality scoring         |
| `train_bll`    | 7 rules       | Numeric target, min rows, no concurrent  |
| `predict_bll`  | 9 rules       | Field ranges, trained model required     |
| `explain_bll`  | 8 rules       | Prediction required, SHAP + fallback     |
| **Total**      | **40 rules**  |                                          |
