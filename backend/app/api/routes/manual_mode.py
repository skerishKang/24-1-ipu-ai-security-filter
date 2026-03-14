from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.api.schemas.manual_preview import (
    ManualPreviewRequest,
    ManualPreviewResponse,
)
from app.services.manual_preview_service import ManualPreviewService

router = APIRouter(prefix="/mode", tags=["manual-mode"])
manual_preview_service = ManualPreviewService()


@router.post("/manual-preview", response_model=ManualPreviewResponse)
async def manual_preview(payload: ManualPreviewRequest) -> ManualPreviewResponse:
    return manual_preview_service.build_preview(payload)


@router.post("/manual-preview/file", response_model=ManualPreviewResponse)
async def manual_preview_file(
    file: UploadFile = File(...),
    policy: str = Form(default="default"),
) -> ManualPreviewResponse:
    try:
        return await manual_preview_service.build_file_preview(file=file, policy=policy)
    except ValueError as error:
        raise HTTPException(status_code=415, detail=str(error))
