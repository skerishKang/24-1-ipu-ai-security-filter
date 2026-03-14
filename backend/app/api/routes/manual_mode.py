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
        raise HTTPException(status_code=415, detail=str(error))
