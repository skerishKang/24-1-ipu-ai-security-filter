
from pydantic import BaseModel


class SessionSummary(BaseModel):
    session_id: str
    expires_at: float


class SessionMetadata(BaseModel):
    session_id: str
    mapping_count: int
    expires_at: float


class MappingItem(BaseModel):
    type: str
    replaced: str


class SessionMappingsResponse(BaseModel):
    session_id: str
    mapping_count: int
    mappings: list[MappingItem]
