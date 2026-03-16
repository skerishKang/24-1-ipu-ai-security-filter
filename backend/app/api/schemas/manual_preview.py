from typing import Literal

from pydantic import BaseModel, Field

PolicyName = Literal["default", "strict_token"]
ContentTypeName = Literal["text"]
ReportRiskLevelName = Literal["low-risk", "moderate-risk", "high-risk"]
ReportStrategyName = Literal["alias", "strict_token"]
ReportReviewStatusName = Literal["clean", "review-required"]


class ManualPreviewRequest(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        max_length=50_000,
        description="Original content to inspect",
    )
    content_type: ContentTypeName = Field(default="text", description="Input content type")
    policy: PolicyName = Field(
        default="default",
        description="Security policy preset: default for readable preview, strict_token for conservative masking",
    )


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
    risk_level: ReportRiskLevelName
    strategy: ReportStrategyName
    review_status: ReportReviewStatusName


class ManualPreviewResponse(BaseModel):
    session_id: str
    original_text: str
    replaced_text: str
    detections: list[DetectionItem]
    replacements: list[ReplacementItem]
    report: ManualPreviewReport
    copy_ready_prompt: str


class ManualRestoreRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="Existing manual-preview session id")
    replaced_text: str = Field(..., min_length=1, description="Tokenized text to restore")


class ManualRestoreResponse(BaseModel):
    session_id: str
    restored_text: str
    restored: bool
