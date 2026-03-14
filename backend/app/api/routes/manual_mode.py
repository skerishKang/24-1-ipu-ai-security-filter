from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.schemas.manual_preview import (
    ManualPreviewRequest,
    ManualPreviewResponse,
    PolicyName,
)
from app.services.manual_preview_service import ManualPreviewService

router = APIRouter(prefix="/mode", tags=["manual-mode"])


@lru_cache(maxsize=1)
def get_manual_preview_service() -> ManualPreviewService:
    return ManualPreviewService()


@router.post("/manual-preview", response_model=ManualPreviewResponse)
async def manual_preview(
    payload: ManualPreviewRequest,
    manual_preview_service: Annotated[ManualPreviewService, Depends(get_manual_preview_service)],
) -> ManualPreviewResponse:
    return manual_preview_service.build_preview(payload)


@router.post("/manual-preview/file", response_model=ManualPreviewResponse)
async def manual_preview_file(
    manual_preview_service: Annotated[ManualPreviewService, Depends(get_manual_preview_service)],
    file: UploadFile = File(...),
    policy: PolicyName = Form(default="default"),
) -> ManualPreviewResponse:
    try:
        return await manual_preview_service.build_file_preview(file=file, policy=policy)
    except ValueError as error:
        message = str(error)
        if "1MB" in message:
            raise HTTPException(status_code=413, detail=message)
        if "비어 있는" in message:
            raise HTTPException(status_code=400, detail=message)
        if "UTF-8" in message:
            raise HTTPException(status_code=415, detail=message)
        raise HTTPException(status_code=415, detail=message)
