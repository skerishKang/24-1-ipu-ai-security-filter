from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RewriteComparisonSample:
    sample_id: str
    description: str
    content: str


REWRITE_COMPARISON_SAMPLES: tuple[RewriteComparisonSample, ...] = (
    RewriteComparisonSample(
        sample_id="customer_contact_note",
        description="고객 문의 연락처 메모",
        content="담당자 홍길동 이사는 contact@ipu.co.kr 과 010-1234-5678로 회신을 요청했습니다.",
    ),
    RewriteComparisonSample(
        sample_id="contract_amount_review",
        description="계약 검토 메모",
        content="미래전자와의 계약 금액 120,000,000원은 박민수 부장이 최종 검토 중입니다.",
    ),
    RewriteComparisonSample(
        sample_id="public_bid_note",
        description="공공 제안서 메모",
        content="아이피유테크 제안서는 김수진 과장이 support@ipu.co.kr로 접수하고 있습니다.",
    ),
    RewriteComparisonSample(
        sample_id="meeting_followup",
        description="회의 후속 조치 메모",
        content="보안위원회 메모는 이준호 대표에게 전달하고 긴급 연락처 010-9988-7766도 함께 남겨 주세요.",
    ),
    RewriteComparisonSample(
        sample_id="finance_summary",
        description="재무 요약 문구",
        content="이번 시범사업 예산은 48,000,000원이며 담당자는 정다은 매니저입니다.",
    ),
    RewriteComparisonSample(
        sample_id="vendor_mail_note",
        description="협력사 메일 메모",
        content="협력사 문의는 security at ipu dot co kr로 받고, 검토본은 박팀장에게 먼저 공유해 주세요.",
    ),
    RewriteComparisonSample(
        sample_id="mixed_business_note",
        description="조직명, 인명, 금액이 섞인 메모",
        content="아이피유그룹과 미래전자의 공동 계약은 220,000,000원 규모이며 김민수 이사가 리뷰합니다.",
    ),
    RewriteComparisonSample(
        sample_id="customer_callback",
        description="고객 콜백 문구",
        content="고객 답변은 support@ipu.co.kr 또는 010-7777-8899로 받고, 담당자 최유진 님이 정리합니다.",
    ),
    RewriteComparisonSample(
        sample_id="board_report",
        description="이사회 보고 문구",
        content="이사회 보고서는 아이피유금융 측과 공유 예정이며 예산 75,000,000원을 포함합니다.",
    ),
    RewriteComparisonSample(
        sample_id="internal_passdown",
        description="내부 전달 문구",
        content="검토 결과는 김현우 부장에게 전달하고 연락처 010-5555-1111은 외부 전송에서 제외해야 합니다.",
    ),
)
