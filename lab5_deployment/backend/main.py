# backend/main.py
# Layer 2: API / Router Layer
# FastAPI entry point for the Real Estate AutoML Prediction System.
# Implements the deployment architecture defined in Lab 4 / Assignment 5.
#
# Layers running in this container (Render):
#   Layer 2 — API/Router  : this file + routers/
#   Layer 3 — BLL         : services/automl_trainer.py
#   Layer 4 — DAL         : utils/store.py  (in-memory; swap for Supabase in prod)
#   Layer 5 — Storage     : in-memory store (D1/D2) + DagsHub MLflow (D3)

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, ingest, train, predict, explain

app = FastAPI(
    title="Real Estate AutoML API",
    description=(
        "Deployment implementation for Assignment 5. "
        "Follows the 5-layer architecture defined in Lab 4."
    ),
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────
# Allow the React dev server locally and the Vercel production domain.
# In production, set CORS_ORIGINS env var to the actual Vercel URL.
_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,https://real-estate-automl.vercel.app",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers (Layer 2: API/Router Layer) ───────────────────────
app.include_router(auth.router,    prefix="/api/auth",    tags=["Authentication"])
app.include_router(ingest.router,  prefix="/api/ingest",  tags=["Data Ingestion"])
app.include_router(train.router,   prefix="/api/train",   tags=["AutoML Training"])
app.include_router(predict.router, prefix="/api/predict", tags=["Prediction"])
app.include_router(explain.router, prefix="/api/explain", tags=["Explainability"])


@app.get("/", tags=["Health"])
def root():
    """Health check — confirms the API/Router layer is running."""
    return {
        "status": "ok",
        "service": "Real Estate AutoML API",
        "layer": "API/Router (Layer 2)",
        "deployment": "Render",
    }


# ── Dev runner ────────────────────────────────────────────────
# Start locally:  uvicorn main:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
