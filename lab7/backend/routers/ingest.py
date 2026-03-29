# lab7/backend/routers/ingest.py
# ─────────────────────────────────────────────────────────────
# Thin Router: Data Ingestion
# Delegates all business logic to bll/ingest_bll.py
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from models.schemas   import IngestResponse
from utils.security   import get_current_user
from bll.ingest_bll   import validate_and_ingest

router = APIRouter()


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Accept a CSV file upload.
    The router only handles HTTP concerns (reading the upload).
    All validation, parsing, quality analysis, and storage are
    delegated to the Business Logic Layer (ingest_bll).
    """
    raw = await file.read()

    success, result = validate_and_ingest(
        filename=file.filename,
        file_bytes=raw,
        user_id=current_user["user_id"],
    )

    if not success:
        raise HTTPException(
            status_code=result.get("code", 400),
            detail=result["errors"],
        )

    # Return the full result including quality_report
    return result
