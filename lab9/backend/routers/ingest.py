# lab8/backend/routers/ingest.py
# ─────────────────────────────────────────────────────────────
# Thin Router: Data Ingestion
# Updated for Lab 8: injects database session via DAL.
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from models.schemas   import IngestResponse
from utils.security   import get_current_user
from bll.ingest_bll   import validate_and_ingest
from dal.database     import get_db

router = APIRouter()


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Accept a CSV file upload.
    All validation, parsing, quality analysis, and storage are
    delegated to the BLL, which uses the DAL for persistence.
    """
    raw = await file.read()

    success, result = validate_and_ingest(
        filename=file.filename,
        file_bytes=raw,
        user_id=current_user["user_id"],
        db=db,
    )

    if not success:
        raise HTTPException(
            status_code=result.get("code", 400),
            detail=result["errors"],
        )

    return result
