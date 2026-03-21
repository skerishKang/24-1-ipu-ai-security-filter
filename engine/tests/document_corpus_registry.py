from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentCorpusSample:
    sample_id: str
    relative_path: str
    description: str
    category: str


DOCUMENT_CORPUS_SAMPLES: tuple[DocumentCorpusSample, ...] = (
    DocumentCorpusSample(
        sample_id="contract_review_short",
        relative_path="demo-samples/sample-contract-review.txt",
        description="짧은 계약 검토 문서",
        category="demo-short",
    ),
    DocumentCorpusSample(
        sample_id="customer_inquiry_short",
        relative_path="demo-samples/sample-customer-inquiry.txt",
        description="짧은 고객 문의 문서",
        category="demo-short",
    ),
    DocumentCorpusSample(
        sample_id="internal_report_short",
        relative_path="demo-samples/sample-internal-report.txt",
        description="짧은 내부 보고 문서",
        category="demo-short",
    ),
    DocumentCorpusSample(
        sample_id="empty_text_case",
        relative_path="demo-samples/sample-empty.txt",
        description="빈 파일 예외 케이스",
        category="negative",
    ),
    DocumentCorpusSample(
        sample_id="contract_review_long",
        relative_path="demo-samples/sample-long-contract-review.txt",
        description="긴 계약 검토 문서",
        category="demo-long",
    ),
    DocumentCorpusSample(
        sample_id="customer_inquiry_long",
        relative_path="demo-samples/sample-long-customer-inquiry.txt",
        description="긴 고객 문의 문서",
        category="demo-long",
    ),
    DocumentCorpusSample(
        sample_id="internal_report_long",
        relative_path="demo-samples/sample-long-internal-report.txt",
        description="긴 내부 보고 문서",
        category="demo-long",
    ),
    DocumentCorpusSample(
        sample_id="security_incident_long",
        relative_path="demo-samples/sample-long-security-incident-note.txt",
        description="긴 보안 사고 대응 문서",
        category="demo-long",
    ),
    DocumentCorpusSample(
        sample_id="vendor_coordination_long",
        relative_path="demo-samples/sample-long-vendor-coordination.txt",
        description="긴 협력사 조율 문서",
        category="demo-long",
    ),
    DocumentCorpusSample(
        sample_id="customer_inquiry_template_txt",
        relative_path="demo-samples/derived/sample-long-customer-inquiry.template.txt",
        description="고객 문의 템플릿 텍스트 산출물",
        category="derived-template",
    ),
    DocumentCorpusSample(
        sample_id="contract_review_template_txt",
        relative_path="demo-samples/derived/sample-long-contract-review.template.txt",
        description="계약 검토 템플릿 텍스트 산출물",
        category="derived-template",
    ),
    DocumentCorpusSample(
        sample_id="internal_report_template_txt",
        relative_path="demo-samples/derived/sample-long-internal-report.template.txt",
        description="내부 보고 템플릿 텍스트 산출물",
        category="derived-template",
    ),
)
