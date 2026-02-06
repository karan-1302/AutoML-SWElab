# Assignment 5: Deployment Plan
## Real Estate AutoML Prediction System

**Based on:** Lab 8 Local-First Architecture  
**Last Updated:** April 26, 2026  
**Strategy:** Run locally, save to cloud on demand

---

## I. What We Are Deploying

Lab 8 implements a local-first development strategy. All layers run on your local machine with optional cloud backups.

```
Layer 1: Presentation     →  localhost:3000 (React)
Layer 2: API/Router       →  localhost:8000 (FastAPI)
Layer 3: BLL              →  localhost:8000 (same process)
Layer 4: DAL              →  localhost:8000 (same process)
Layer 5: Storage          →  SQLite (local) + GitHub (code backup)
```

---

## II. Platform Assignments

### Layer 1 — Presentation (React Frontend) → localhost:3000

- React app runs locally on your machine.
- No build or deployment needed for development.
- Environment variable `REACT_APP_API_URL` points to `http://localhost:8000`.

**Why Local:** Instant feedback, no deployment delays, full debugging capabilities.

---

### Layers 2–4 — API + BLL + DAL (FastAPI Backend) → localhost:8000

- All three layers run together in a single Python process on your machine.
- The FastAPI app is the entry point; it calls BLL functions, which call DAL functions.
- No Docker, no cloud infrastructure needed.

**Why Local:** Simple setup, fast iteration, complete control over environment.

**Endpoints exposed:**
| Endpoint | Purpose |
|---|---|
| `POST /api/auth/login` | Login (Layer 2 → BLL AuthManager → D1) |
| `POST /api/ingest/upload` | Upload CSV (Layer 2 → BLL Dataset → D2) |
| `GET /api/ingest/preview` | Preview dataset (Layer 2 → BLL Dataset → D2) |
| `POST /api/train/start` | Start training (Layer 2 → BLL AutoMLTrainer → D2) |
| `GET /api/train/status` | Check training progress |
| `POST /api/predict` | Get prediction (Layer 2 → BLL MLModel → D2) |
| `GET /api/explain/latest` | Get SHAP explanation (Layer 2 → BLL Explainer → D2) |

---

### Layer 5 — Storage

#### D1: User Database → SQLite (local)

- Stores the `users`, `datasets`, `training_jobs`, `predictions` tables.
- File: `lab8/backend/automl.db`
- No network calls, instant access.

```sql
-- Tables (created automatically on startup)
users          (user_id, email, hashed_password, name, created_at)
datasets       (dataset_id, filename, user_id, columns_json, row_count, created_at)
training_jobs  (user_id, status, progress_json, scores_json, best_model_name, ...)
predictions    (user_id, predicted_price, model_used, confidence, input_features_json, ...)
```

#### D2: Dataset Storage → In-Memory Cache + SQLite

- Dataset metadata stored in SQLite.
- Raw pandas DataFrames kept in memory (`utils/store.py`) for ML operations.
- Cleared on restart (ephemeral).

#### D3: Model Registry → Local File System (Optional)

- Trained models saved as `.pkl` files locally.
- Optional: Push to DagsHub MLflow for backup.

---

## III. Step-by-Step Local Setup

### Step 1 — Backend Setup

```bash
# Navigate to backend
cd lab8/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (local only, never commit)
cat > .env << EOF
SECRET_KEY=dev-key-12345678901234567890
DATABASE_URL=sqlite:///automl.db
CORS_ORIGINS=http://localhost:3000
EOF

# Database initializes automatically on first run
python main.py
```

**Backend runs at:** `http://localhost:8000`  
**API Docs at:** `http://localhost:8000/docs`

### Step 2 — Frontend Setup

```bash
# Navigate to frontend (in new terminal)
cd lab8/frontend

# Install dependencies
npm install

# Create .env file
cat > .env << EOF
REACT_APP_API_URL=http://localhost:8000
EOF

# Run frontend
npm start
```

**Frontend runs at:** `http://localhost:3000`

### Step 3 — Verify Local Setup

```bash
# Test backend health
curl http://localhost:8000/

# Test login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@realestate.com","password":"password123"}'

# Open browser
open http://localhost:3000
```

### Step 4 — Run Tests

```bash
cd lab8/backend

# All tests
python -m pytest tests/ -v

# White box only
python -m pytest tests/test_whitebox.py -v

# Black box only
python -m pytest tests/test_blackbox.py -v
```

### Step 5 — Verify End-to-End

Test the full flow manually:
1. Open http://localhost:3000 in browser.
2. Log in with `demo@realestate.com` / `password123` → confirms Layer 1 → Layer 2 → BLL → D1 works.
3. Upload a CSV → confirms Layer 2 → BLL Dataset → D2 works.
4. Start training → confirms BLL AutoMLTrainer works.
5. Make a prediction → confirms BLL MLModel works.
6. View explanation → confirms BLL Explainer + SHAP works.

---

## IV. How the Layers Talk to Each Other

```
Browser (localhost:3000)
    │  HTTP
    ▼
FastAPI on localhost:8000  ← Layer 2: validates request, routes to BLL
    │  function call
    ▼
BLL (AuthManager / Dataset / AutoMLTrainer / Explainer)  ← Layer 3: does the work
    │  method call
    ▼
DAL (Repositories)  ← Layer 4: talks to storage
    │  SQL / file I/O
    ▼
SQLite (automl.db)  ← Layer 5: stores data locally
```

No layer skips another. The frontend never talks directly to the database.

---

## V. Security

| Concern | Solution |
|---|---|
| Passwords | Hashed with bcrypt, never stored in plaintext |
| API access | JWT token required on every request (8-hour expiry) |
| Secrets | Stored in `.env` file (never committed to git) |
| Database | SQLite with no network exposure |
| Transport | HTTP (local) - HTTPS not needed for localhost |
| CORS | Backend only accepts requests from `http://localhost:3000` |

---

## VI. Sequence Diagram — Prediction Flow (Local)

```
User (Browser)       Frontend          Backend API       SQLite
      │                  │                │                │
      │── open app ─────►│                │                │
      │                  │                │                │
      │── login ────────►│                │                │
      │                  │── POST /login ►│                │
      │                  │                │── query user ─►│
      │                  │                │◄── user row ───│
      │                  │◄── JWT token ──│                │
      │                  │                │                │
      │── enter details ►│                │                │
      │                  │── POST /predict + JWT ─────────►│
      │                  │                │── load model   │
      │                  │                │── run prediction
      │                  │◄── price ──────│                │
      │◄── show result ──│                │                │
```

---

## VII. Mapping Back to Lab 8

| Lab 8 Component | Where It Lives Locally |
|---|---|
| Presentation Layer (React) | localhost:3000 |
| API/Router Layer (FastAPI) | localhost:8000 |
| BLL (auth_bll, ingest_bll, train_bll, predict_bll, explain_bll) | localhost:8000 (same process) |
| DAL (repositories) | localhost:8000 (same process) |
| D1: User Database | SQLite (automl.db) |
| D2: Dataset Storage | SQLite + in-memory cache |
| D3: Model Registry | Local file system (optional: DagsHub) |

---

## VIII. Optional: Save to Cloud

When you want to backup your work:

### Save Code to GitHub

```bash
git add .
git commit -m "Lab 8: Local development with DAL"
git push origin main
```

### Save Database to Supabase (Optional)

```bash
# Export SQLite to SQL
sqlite3 lab8/backend/automl.db .dump > backup.sql

# Create Supabase project and restore
psql postgresql://user:pass@host:5432/db < backup.sql
```

### Save Models to DagsHub (Optional)

```bash
export MLFLOW_TRACKING_URI=https://dagshub.com/YOUR_USER/automl.mlflow
export DAGSHUB_USER_TOKEN=YOUR_TOKEN

python -c "
import mlflow
import joblib

mlflow.set_tracking_uri('https://dagshub.com/YOUR_USER/automl.mlflow')
with mlflow.start_run():
    model = joblib.load('best_model.pkl')
    mlflow.sklearn.log_model(model, 'model')
    mlflow.log_metric('r2', 0.92)
"
```

---

## IX. Troubleshooting

### Backend Issues

**Problem:** `sqlite3.OperationalError: no such table`
```bash
# Solution: Restart backend - tables created automatically
pkill -f "python main.py"
python main.py
```

**Problem:** `Address already in use` on port 8000
```bash
# Solution: Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

**Problem:** `ModuleNotFoundError: No module named 'fastapi'`
```bash
# Solution: Activate venv and reinstall
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Issues

**Problem:** `Cannot find module` errors
```bash
# Solution: Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Problem:** `CORS error` when calling backend
```bash
# Solution: Check CORS_ORIGINS in backend .env
# Should be: http://localhost:3000
```

**Problem:** `API_URL is undefined`
```bash
# Solution: Create .env file in frontend/
echo "REACT_APP_API_URL=http://localhost:8000" > .env
```

### Database Issues

**Problem:** Can't connect to SQLite
```bash
# Solution: Check file permissions
chmod 644 lab8/backend/automl.db
```

**Problem:** Database locked
```bash
# Solution: Close all connections and restart
pkill -f "python main.py"
python main.py
```

---

## X. Summary

**Local-First Strategy:**
- ✅ Run backend on `localhost:8000`
- ✅ Run frontend on `localhost:3000`
- ✅ Use SQLite for local database
- ✅ Keep runtime cache in memory
- ✅ Save code to GitHub (optional)
- ✅ Save models to DagsHub (optional)
- ✅ Save database to Supabase (optional)

**Benefits:**
- No cloud costs during development
- Full control over environment
- Faster iteration cycles
- Easy debugging
- Works offline (except for cloud saves)

**When to move to cloud:**
- Need 24/7 availability
- Multiple users accessing simultaneously
- Want automatic backups
- Need to scale beyond local machine
