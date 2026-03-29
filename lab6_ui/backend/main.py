# backend/main.py
# Entry point for the Real Estate AutoML FastAPI backend.
# Mounts all routers and configures CORS for the React frontend.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, ingest, train, predict, explain

app = FastAPI(
    title="Real Estate AutoML API",
    description="Backend API for the Real Estate AutoML Prediction System (CS 331 Assignment 6)",
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────
# Allow the React dev server (port 3000) and production Vercel domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://real-estate-automl.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────
app.include_router(auth.router,    prefix="/api/auth",    tags=["Authentication"])
app.include_router(ingest.router,  prefix="/api/ingest",  tags=["Data Ingestion"])
app.include_router(train.router,   prefix="/api/train",   tags=["AutoML Training"])
app.include_router(predict.router, prefix="/api/predict", tags=["Prediction"])
app.include_router(explain.router, prefix="/api/explain", tags=["Explainability"])


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "Real Estate AutoML API v1.0"}


# ── Dev runner ────────────────────────────────────────────────
# Run with:  uvicorn main:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
