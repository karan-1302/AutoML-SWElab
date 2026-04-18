# lab8/backend/main.py
# ─────────────────────────────────────────────────────────────
# Entry point for the Real Estate AutoML FastAPI backend (Lab 8).
#
# Architecture (Lab 8 — DAL added):
#   Presentation Layer  →  Routers (thin HTTP layer)
#          ↓
#   Business Logic Layer  →  bll/ modules (core rules & validation)
#          ↓
#   Data Access Layer  →  dal/ (SQLAlchemy + SQLite)
#          ↓
#   Runtime Cache  →  utils/store.py (DataFrames & Pipelines)
#          +
#   ML Services  →  services/automl_trainer.py
#
# Changes from Lab 7:
#   - Added SQLAlchemy-based Data Access Layer (dal/)
#   - Database initialisation and seeding on startup
#   - BLL modules now persist data via DAL repositories
#   - In-memory store refactored to runtime cache only
# ─────────────────────────────────────────────────────────────

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dal.database import init_db, SessionLocal
from dal.seed import seed_database
from routers import auth, ingest, train, predict, explain


# ── Lifespan handler (startup / shutdown) ─────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise database and seed data on startup."""
    # Startup
    print("[startup] Initialising database...")
    init_db()

    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    print("[startup] Database ready.")
    yield
    # Shutdown (nothing to clean up)


app = FastAPI(
    title="Real Estate AutoML API (Lab 8 — DAL Architecture)",
    description=(
        "Backend API with an explicit Data Access Layer (DAL) using "
        "SQLAlchemy + SQLite, separating presentation, business logic, "
        "and data access. CS 331 Assignment 8."
    ),
    version="3.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://real-estate-automl.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers (Presentation Layer — thin) ──────────────────────
app.include_router(auth.router,    prefix="/api/auth",    tags=["Authentication"])
app.include_router(ingest.router,  prefix="/api/ingest",  tags=["Data Ingestion"])
app.include_router(train.router,   prefix="/api/train",   tags=["AutoML Training"])
app.include_router(predict.router, prefix="/api/predict",  tags=["Prediction"])
app.include_router(explain.router, prefix="/api/explain",  tags=["Explainability"])


@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "Real Estate AutoML API v3.0 (DAL Architecture)",
        "architecture": {
            "presentation_layer": "FastAPI routers (thin HTTP handlers)",
            "business_logic_layer": "bll/ package (auth, ingest, train, predict, explain)",
            "data_access_layer": "dal/ package (SQLAlchemy + SQLite)",
            "runtime_cache": "utils/store.py (DataFrames & Pipelines)",
            "ml_services": "services/automl_trainer.py",
        },
    }


# ── Dev runner ────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
