from typing import Literal

from pydantic import BaseModel, Field

PolicyName = Literal["default", "strict_token", "local_rewrite"]
ContentTypeName = Literal["text"]
ReportRiskLevelName = Literal["low-risk", "moderate-risk", "high-risk"]
ReportStrategyName = Literal["alias", "strict_token", "local_rewrite"]
ReportReviewStatusName = Literal["clean", "review-required"]
TaskTypeName = Literal["summarize", "risk_review", "action_items"]


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
        description="Security policy preset: default for readable preview, strict_token for conservative masking, local_rewrite for local-model-assisted rewrite",
    )
    task_type: TaskTypeName | None = Field(
        default=None,
        description="Task type for secure prompt generation: summarize, risk_review, or action_items",
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


class ManualPreviewReadiness(BaseModel):
    ready_to_send: bool
    review_status: str
    reason: str
    remaining_risks: list[str]
    detection_count: int
    risk_level: str


class ManualPreviewResponse(BaseModel):
    session_id: str
    restore_token: str
    original_text: str
    replaced_text: str
    detections: list[DetectionItem]
    replacements: list[ReplacementItem]
    report: ManualPreviewReport
    readiness: ManualPreviewReadiness
    copy_ready_prompt: str


class ManualRestoreRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="Existing manual-preview session id")
    restore_token: str = Field(..., min_length=1, description="Manual-preview restore authorization token")
    replaced_text: str = Field(..., min_length=1, description="Tokenized text to restore")


class ManualRestoreResponse(BaseModel):
    session_id: str
    restored_text: str
    restored: bool
