# backend/routers/ingest.py
# Layer 2: Data Ingestion router
# POST /api/ingest/upload  →  BLL Dataset.loadFromCSV()  →  DAL saves to D2
# Maps to UC-02: Upload Dataset, UC-03: View Dataset  (Lab 4 Section V)

import hashlib
import io
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from models.schemas import IngestResponse
from utils.security import get_current_user
from utils.store    import set_dataset

router = APIRouter()

PREVIEW_ROWS = 10


@router.post("/upload", response_model=IngestResponse)
async def upload_csv(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a CSV dataset.

    Layer flow (Lab 4 Section II — "When a user uploads a CSV"):
      Layer 2 receives file
      → BLL Dataset.loadFromCSV() reads and validates it
      → BLL Dataset.preprocess() cleans it
      → DAL saves dataset info to D2 (Dataset Storage)
      → Layer 2 returns preview to React
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Only .csv files are accepted.")

    content = await file.read()

    try:
        df = pd.read_csv(io.StringIO(content.decode("utf-8")))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Could not parse CSV: {exc}")

    if df.empty:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Uploaded CSV is empty.")

    # BLL: generate a stable dataset ID from file content (MD5 hash)
    dataset_id = hashlib.md5(content).hexdigest()[:10]

    # DAL: save to D2 (in-memory store; swap for Supabase in production)
    set_dataset(dataset_id, {
        "filename":  file.filename,
        "columns":   df.columns.tolist(),
        "dataframe": df,
        "row_count": len(df),
        "user_id":   current_user["user_id"],
    })

    return IngestResponse(
        dataset_id=dataset_id,
        filename=file.filename,
        columns=df.columns.tolist(),
        row_count=len(df),
        preview=df.head(PREVIEW_ROWS).fillna("").to_dict(orient="records"),
    )
