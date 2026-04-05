# lab7/backend/main.py
# ─────────────────────────────────────────────────────────────
# Entry point for the Real Estate AutoML FastAPI backend (Lab 7).
#
# Architecture:
#   Presentation Layer  →  Routers (thin HTTP layer)
#          ↓
#   Business Logic Layer  →  bll/ modules (core rules & validation)
#          ↓
#   Data Access Layer  →  utils/store.py (in-memory) + services/ (ML engine)
#
# The routers are thin — they only handle HTTP concerns (request
# parsing, status codes, headers). All business logic, validation,
# data transformation, and domain rules live in the bll/ package.
# ─────────────────────────────────────────────────────────────

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, ingest, train, predict, explain

app = FastAPI(
    title="Real Estate AutoML API (Lab 7 — BLL Architecture)",
    description=(
        "Backend API with an explicit Business Logic Layer (BLL) "
        "separating presentation, business rules, and data access. "
        "CS 331 Assignment 7."
    ),
    version="2.0.0",
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
        "service": "Real Estate AutoML API v2.0 (BLL Architecture)",
        "architecture": {
            "presentation_layer": "FastAPI routers (thin HTTP handlers)",
            "business_logic_layer": "bll/ package (auth, ingest, train, predict, explain)",
            "data_access_layer": "utils/store.py (in-memory) + services/automl_trainer.py",
        },
    }


# ── Dev runner ────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
