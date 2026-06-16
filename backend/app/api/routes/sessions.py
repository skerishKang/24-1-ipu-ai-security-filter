from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.schemas.sessions import (
    MappingItem,
    SessionMappingsResponse,
    SessionMetadata,
    SessionSummary,
)
from app.core.auth import optional_auth_owner_hash
from app.services.session_service import (
    SessionHistoryUnavailableError,
    SessionOwnershipError,
    SessionService,
)

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
    # The session history API is gated by the same optional-auth dependency
    # that protects the manual-preview endpoints. Without this, any caller
    # could enumerate every session and read the original PII that lives
    # in the session mapping table.
    dependencies=[Depends(optional_auth_owner_hash)],
)


def _get_service() -> SessionService:
    try:
        return SessionService()
    except SessionHistoryUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("", response_model=list[SessionSummary])
async def list_sessions(
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    owner_hash: Annotated[str, Depends(optional_auth_owner_hash)] = "dev-local",
) -> list[SessionSummary]:
    service = _get_service()
    sessions = service.list_sessions(limit=limit, owner_hash=owner_hash)
    return [SessionSummary(session_id=s["session_id"], expires_at=s["expires_at"]) for s in sessions]


@router.get("/{session_id}", response_model=SessionMetadata)
async def get_session(
    session_id: str,
    owner_hash: Annotated[str, Depends(optional_auth_owner_hash)] = "dev-local",
) -> SessionMetadata:
    service = _get_service()
    metadata = service.get_session_metadata(session_id, owner_hash=owner_hash)
    if metadata is None:
        # 404 covers both "no such session" and "session owned by someone else"
        # so we do not leak existence to non-owners.
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionMetadata(**metadata)


@router.get("/{session_id}/mappings", response_model=SessionMappingsResponse)
async def get_session_mappings(
    session_id: str,
    owner_hash: Annotated[str, Depends(optional_auth_owner_hash)] = "dev-local",
) -> SessionMappingsResponse:
    service = _get_service()
    metadata = service.get_session_metadata(session_id, owner_hash=owner_hash)
    if metadata is None:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        mappings = service.get_mappings(session_id, owner_hash=owner_hash)
    except SessionOwnershipError:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionMappingsResponse(
        session_id=session_id,
        mapping_count=metadata["mapping_count"],
        mappings=[
            MappingItem(type=m.type, replaced=m.replaced)
            for m in mappings
        ],
    )
