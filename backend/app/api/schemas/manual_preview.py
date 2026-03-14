from typing import Literal

from pydantic import BaseModel, Field

PolicyName = Literal["default", "strict_token"]
ContentTypeName = Literal["text"]


class ManualPreviewRequest(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        max_length=50_000,
        description="Original content to inspect",
    )
    content_type: ContentTypeName = Field(default="text", description="Input content type")
    policy: PolicyName = Field(default="default", description="Security policy preset")


class DetectionItem(BaseModel):
    type: str
    label: str
    start: int
    end: int
    score: float
    note: str


class ReplacementItem(BaseModel):
    type: str
    original: str
    replaced: str
    reason: str


class ManualPreviewReport(BaseModel):
    total_detections: int
    risk_level: str
    strategy: str
    review_status: str


class ManualPreviewResponse(BaseModel):
    session_id: str
    original_text: str
    replaced_text: str
    detections: list[DetectionItem]
    replacements: list[ReplacementItem]
    report: ManualPreviewReport
    copy_ready_prompt: str
