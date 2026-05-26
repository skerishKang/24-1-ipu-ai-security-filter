from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

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
    ProcessingLimitExceededError,
    SessionExpiredError,
    UnsupportedFileTypeError,
)
from app.services.manual_preview_service import ManualPreviewService

router = APIRouter(prefix="/mode", tags=["manual-mode"])

limiter = Limiter(key_func=get_remote_address)


def get_limiter(request: Request):
    return request.app.state.limiter


def get_manual_preview_service(request: Request) -> ManualPreviewService:
    return request.app.state.manual_preview_service



@router.post("/manual-preview", response_model=ManualPreviewResponse)
@limiter.limit("30/minute")
async def manual_preview(
    request: Request,
    payload: ManualPreviewRequest,
    manual_preview_service: Annotated[ManualPreviewService, Depends(get_manual_preview_service)],
) -> ManualPreviewResponse:
    return manual_preview_service.build_preview(payload)


@router.post("/manual-preview/file", response_model=ManualPreviewResponse)
@limiter.limit("10/minute")
async def manual_preview_file(
    request: Request,
    manual_preview_service: Annotated[ManualPreviewService, Depends(get_manual_preview_service)],
    file: UploadFile = File(...),
    policy: PolicyName = Form(default="default"),
) -> ManualPreviewResponse:
    try:
        return await manual_preview_service.build_file_preview(file=file, policy=policy)
    except ProcessingLimitExceededError as error:
        raise HTTPException(status_code=413, detail=str(error))
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
@limiter.limit("5/minute")
async def manual_preview_audio(
    request: Request,
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
@limiter.limit("60/minute")
async def manual_preview_restore(
    request: Request,
    payload: ManualRestoreRequest,
    manual_preview_service: Annotated[ManualPreviewService, Depends(get_manual_preview_service)],
) -> ManualRestoreResponse:
    return manual_preview_service.restore_preview(payload)
