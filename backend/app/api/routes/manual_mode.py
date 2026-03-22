from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.schemas.manual_preview import (
    ManualRestoreRequest,
    ManualRestoreResponse,
    ManualPreviewRequest,
    ManualPreviewResponse,
    PolicyName,
)
from app.core.exceptions import (
    EmptyFileError,
    FileTooLargeError,
    InvalidEncodingError,
    SessionExpiredError,
    UnsupportedFileTypeError,
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
    except FileTooLargeError as error:
        raise HTTPException(status_code=413, detail=str(error))
    except EmptyFileError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except InvalidEncodingError as error:
        raise HTTPException(status_code=415, detail=str(error))
    except UnsupportedFileTypeError as error:
        raise HTTPException(status_code=415, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=415, detail=str(error))


@router.post("/manual-preview/audio", response_model=ManualPreviewResponse)
async def manual_preview_audio(
    manual_preview_service: Annotated[ManualPreviewService, Depends(get_manual_preview_service)],
    file: UploadFile = File(...),
    policy: PolicyName = Form(default="default"),
) -> ManualPreviewResponse:
    try:
        return await manual_preview_service.build_audio_preview(file=file, policy=policy)
    except NotImplementedError as error:
        raise HTTPException(status_code=501, detail=str(error))
    except FileTooLargeError as error:
        raise HTTPException(status_code=413, detail=str(error))
    except EmptyFileError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except UnsupportedFileTypeError as error:
        raise HTTPException(status_code=415, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=415, detail=str(error))


@router.post("/manual-preview/restore", response_model=ManualRestoreResponse)
async def manual_preview_restore(
    payload: ManualRestoreRequest,
    manual_preview_service: Annotated[ManualPreviewService, Depends(get_manual_preview_service)],
) -> ManualRestoreResponse:
    return manual_preview_service.restore_preview(payload)
