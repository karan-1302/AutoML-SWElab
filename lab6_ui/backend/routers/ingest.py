# backend/routers/ingest.py
# UC-01: Upload Dataset  |  UC-02: Preview Dataset
# POST /api/ingest/upload  → validates CSV → stores in memory → returns column list + preview rows

import io
import uuid

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from models.schemas  import IngestResponse
from utils.security  import get_current_user
from utils.store     import DATASETS

router = APIRouter()

PREVIEW_ROWS   = 10
MAX_FILE_MB    = 50
ALLOWED_SUFFIX = ".csv"


@router.post("/upload", response_model=IngestResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Accept a CSV file upload from the user.
    Validates the file, parses it with pandas, stores the DataFrame in
    the in-memory DATASETS store, and returns a preview of the first rows.
    """
    # ── 1. Validate file extension ─────────────────────────────
    if not file.filename.lower().endswith(ALLOWED_SUFFIX):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {ALLOWED_SUFFIX} files are accepted.",
        )

    # ── 2. Read bytes and check size ───────────────────────────
    raw = await file.read()
    if len(raw) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {MAX_FILE_MB} MB limit.",
        )

    # ── 3. Parse with pandas ───────────────────────────────────
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not parse CSV: {exc}",
        )

    if df.empty:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded CSV file is empty.",
        )

    # ── 4. Store in memory ────────────────────────────────────
    dataset_id = str(uuid.uuid4())
    DATASETS[dataset_id] = {
        "dataset_id":  dataset_id,
        "filename":    file.filename,
        "user_id":     current_user["user_id"],
        "dataframe":   df,
        "row_count":   len(df),
        "columns":     list(df.columns),
    }

    # ── 5. Build preview (replace NaN with None for JSON safety) ─
    preview_df = df.head(PREVIEW_ROWS).where(pd.notnull(df.head(PREVIEW_ROWS)), None)
    preview    = preview_df.to_dict(orient="records")

    return IngestResponse(
        dataset_id=dataset_id,
        filename=file.filename,
        columns=list(df.columns),
        row_count=len(df),
        preview=preview,
    )
