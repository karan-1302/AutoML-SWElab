# Real Estate AutoML Prediction System
## CS 331 Software Engineering Lab — Assignment 6

A full-stack Direct Manipulation Interface (DMI) for the Real Estate AutoML Prediction System.

---

## Project Structure

```
assignment6/
├── frontend/                   # React.js web dashboard
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── context/
│   │   │   ├── AuthContext.js  # JWT auth state
│   │   │   └── AppContext.js   # Shared dataset/model state
│   │   ├── components/
│   │   │   ├── Sidebar.js      # Navigation sidebar
│   │   │   ├── DataGrid.js     # Paginated data preview table
│   │   │   └── ProgressBar.js  # Algorithm training progress
│   │   ├── pages/
│   │   │   ├── LoginPage.js    # UC: Authentication
│   │   │   ├── UploadPage.js   # UC-01, UC-02
│   │   │   ├── TrainPage.js    # UC-04 to UC-08
│   │   │   ├── PredictPage.js  # UC-09, UC-10
│   │   │   └── ExplainPage.js  # UC-11, UC-12
│   │   ├── App.js              # Router + layout
│   │   ├── index.js
│   │   └── index.css           # Global design system
│   └── package.json
│
└── backend/                    # FastAPI Python microservice
    ├── main.py                 # App factory + CORS
    ├── requirements.txt
    ├── .env                    # Environment variables
    ├── models/
    │   └── schemas.py          # Pydantic request/response models
    ├── routers/
    │   ├── auth.py             # POST /api/auth/login
    │   ├── ingest.py           # POST /api/ingest/upload
    │   ├── train.py            # POST /api/train/start  GET /api/train/status
    │   ├── predict.py          # POST /api/predict
    │   └── explain.py          # GET  /api/explain/latest
    ├── services/
    │   └── automl_trainer.py   # Core AutoML engine (sklearn + XGBoost)
    └── utils/
        ├── security.py         # JWT helpers + bcrypt
        └── store.py            # In-memory dataset / model store
```

---

## Setup & Running

### Prerequisites
- Node.js 18+
- Python 3.10+

---

### 1. Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.
Interactive docs (Swagger UI) at `http://localhost:8000/docs`.

---

### 2. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the React dev server
npm start
```

The dashboard will open at `http://localhost:3000`.

---

## Demo Credentials

| Field    | Value                    |
|----------|--------------------------|
| Email    | demo@realestate.com      |
| Password | password123              |

---

## API Endpoints

| Method | Endpoint               | Description                          | Auth |
|--------|------------------------|--------------------------------------|------|
| POST   | /api/auth/login        | Login → returns JWT                  | No   |
| POST   | /api/ingest/upload     | Upload CSV dataset                   | Yes  |
| POST   | /api/train/start       | Start AutoML training                | Yes  |
| GET    | /api/train/status      | Poll training progress               | Yes  |
| POST   | /api/predict           | Get property price prediction        | Yes  |
| GET    | /api/explain/latest    | Get SHAP values + recommendations    | Yes  |

---

## UI Screens & Use Case Mapping

| Screen    | Route      | Use Cases Covered         |
|-----------|------------|---------------------------|
| Login     | /login     | Authentication (JWT)      |
| Upload    | /upload    | UC-01, UC-02              |
| Train     | /train     | UC-04, UC-05, UC-06–08   |
| Predict   | /predict   | UC-09, UC-10              |
| Explain   | /explain   | UC-11, UC-12              |

---

## Technology Stack

| Layer       | Technology                             |
|-------------|----------------------------------------|
| Frontend    | React.js 18, React Router v6, Recharts |
| Backend     | FastAPI, Python 3.10+                  |
| ML Engine   | scikit-learn, XGBoost, SHAP            |
| Auth        | JWT (python-jose), bcrypt (passlib)    |
| Data        | pandas, numpy                          |
| Deployment  | Vercel (frontend), Render (backend)    |
| Model Store | DagsHub MLflow (production)            |
| Database    | Supabase PostgreSQL (production)       |
