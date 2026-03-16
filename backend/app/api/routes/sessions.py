from fastapi import APIRouter, HTTPException

from app.api.schemas.sessions import (
    MappingItem,
    SessionMappingsResponse,
    SessionMetadata,
    SessionSummary,
)
from app.services.session_service import SessionHistoryUnavailableError, SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _get_service() -> SessionService:
    try:
        return SessionService()
    except SessionHistoryUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("", response_model=list[SessionSummary])
async def list_sessions(limit: int = 50) -> list[SessionSummary]:
    service = _get_service()
    sessions = service.list_sessions(limit=limit)
    return [SessionSummary(session_id=s["session_id"], expires_at=s["expires_at"]) for s in sessions]


@router.get("/{session_id}", response_model=SessionMetadata)
async def get_session(session_id: str) -> SessionMetadata:
    service = _get_service()
    metadata = service.get_session_metadata(session_id)
    if metadata is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionMetadata(**metadata)


@router.get("/{session_id}/mappings", response_model=SessionMappingsResponse)
async def get_session_mappings(session_id: str) -> SessionMappingsResponse:
    service = _get_service()
    metadata = service.get_session_metadata(session_id)
    if metadata is None:
        raise HTTPException(status_code=404, detail="Session not found")
    mappings = service.get_mappings(session_id)
    return SessionMappingsResponse(
        session_id=session_id,
        mapping_count=metadata["mapping_count"],
        mappings=[
            MappingItem(type=m.type, replaced=m.replaced)
            for m in mappings
        ],
    )
