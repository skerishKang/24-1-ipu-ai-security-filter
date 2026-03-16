from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QualitySample:
    sample_id: str
    description: str
    sample_group: str
    content: str
    minimum_detections: int
    expected_types: tuple[str, ...]
    expected_token_types: tuple[str, ...]
    observation_note: str = ""


QUALITY_SAMPLES: tuple[QualitySample, ...] = (
    QualitySample(
        sample_id="email_only",
        description="고객 응대 메일 주소 보호",
        sample_group="baseline",
        content="고객사 문의는 security@ipu.co.kr 로 접수해 주세요.",
        minimum_detections=1,
        expected_types=("EMAIL",),
        expected_token_types=("EMAIL",),
    ),
    QualitySample(
        sample_id="phone_only",
        description="실무 연락처 보호",
        sample_group="baseline",
        content="긴급 승인 요청은 010-4321-9876 으로 바로 연락 바랍니다.",
        minimum_detections=1,
        expected_types=("PHONE",),
        expected_token_types=("PHONE",),
    ),
    QualitySample(
        sample_id="amount_only",
        description="계약 금액 보호",
        sample_group="baseline",
        content="이번 PoC 계약 금액은 48,000,000원으로 확정되었습니다.",
        minimum_detections=1,
        expected_types=("AMOUNT",),
        expected_token_types=("AMOUNT",),
    ),
    QualitySample(
        sample_id="amount_korean_expression",
        description="한국어 혼합 금액 표현 보호",
        sample_group="baseline",
        content="예산안 기준 총 제안 금액은 3억 2천만원 수준으로 검토 중입니다.",
        minimum_detections=1,
        expected_types=("AMOUNT",),
        expected_token_types=("AMOUNT",),
    ),
    QualitySample(
        sample_id="person_with_title",
        description="직함 포함 이름 보호",
        sample_group="baseline",
        content="제품 검토는 김민수 부장에게 먼저 공유해 주세요.",
        minimum_detections=1,
        expected_types=("PERSON",),
        expected_token_types=("PERSON",),
    ),
    QualitySample(
        sample_id="organization_only",
        description="조직명 보호",
        sample_group="baseline",
        content="아이피유테크와 미래전자 사이의 협력 범위를 검토합니다.",
        minimum_detections=1,
        expected_types=("ORG",),
        expected_token_types=("ORG",),
    ),
    QualitySample(
        sample_id="department_work_memo",
        description="부서 업무 메모 문맥",
        sample_group="baseline",
        content="보안운영팀 김민수 부장이 아이피유테크 점검 메모를 내일까지 공유해 달라고 요청했습니다.",
        minimum_detections=2,
        expected_types=("PERSON", "ORG"),
        expected_token_types=("PERSON", "ORG"),
    ),
    QualitySample(
        sample_id="contract_review_context",
        description="계약 검토 문맥",
        sample_group="baseline",
        content="미래전자 계약서는 박지은 이사가 검토 중이며, 총 계약 금액은 220,000,000원입니다.",
        minimum_detections=3,
        expected_types=("ORG", "PERSON", "AMOUNT"),
        expected_token_types=("ORG", "PERSON", "AMOUNT"),
    ),
    QualitySample(
        sample_id="customer_inquiry_context",
        description="고객 문의 문맥",
        sample_group="baseline",
        content="고객 문의는 support@ipu.co.kr 또는 010-7788-9900 으로 접수하고, 정민수 매니저가 응대합니다.",
        minimum_detections=3,
        expected_types=("EMAIL", "PHONE", "PERSON"),
        expected_token_types=("EMAIL", "PHONE", "PERSON"),
    ),
    QualitySample(
        sample_id="obfuscated_email_context",
        description="변형 이메일 표기 문맥",
        sample_group="baseline",
        content="외부 문의는 security at ipu dot co kr 로 받고, 장애 접수는 운영팀이 분류합니다.",
        minimum_detections=1,
        expected_types=("EMAIL",),
        expected_token_types=("EMAIL",),
    ),
    QualitySample(
        sample_id="bare_name_context",
        description="직함 없는 실명 전달 문맥",
        sample_group="baseline",
        content="검토 의견은 박지은에게 먼저 공유하고, 승인안은 김민수에게 전달해 주세요.",
        minimum_detections=2,
        expected_types=("PERSON",),
        expected_token_types=("PERSON",),
    ),
    QualitySample(
        sample_id="formatted_phone_context",
        description="비정형 전화 표기 문맥",
        sample_group="baseline",
        content="긴급 연락은 02 3456 7890 또는 010.2222.3333 으로 주세요.",
        minimum_detections=2,
        expected_types=("PHONE",),
        expected_token_types=("PHONE",),
    ),
    QualitySample(
        sample_id="internal_report_context",
        description="내부 보고 문맥",
        sample_group="baseline",
        content="아이피유테크 이준호 과장은 주간 보고에서 시범사업 예산 75,000,000원을 언급했습니다.",
        minimum_detections=3,
        expected_types=("ORG", "PERSON", "AMOUNT"),
        expected_token_types=("ORG", "PERSON", "AMOUNT"),
    ),
    QualitySample(
        sample_id="combined_business_note",
        description="업무 문맥 복합 탐지",
        sample_group="baseline",
        content=(
            "아이피유테크 담당자는 박지은 이사입니다. 미래전자와 security@ipu.co.kr 및 "
            "010-2222-3333 연락처를 공유했고, 제안 금액은 120,000,000원입니다."
        ),
        minimum_detections=5,
        expected_types=("ORG", "PERSON", "EMAIL", "PHONE", "AMOUNT"),
        expected_token_types=("ORG", "PERSON", "EMAIL", "PHONE", "AMOUNT"),
    ),
    QualitySample(
        sample_id="ocr_scan_mixed_contact_sheet",
        description="OCR 추출본처럼 줄바꿈이 섞인 연락처 시트",
        sample_group="ocr-baseline",
        content=(
            "미래전자\n"
            "김민수 부장\n"
            "security@ipu.co.kr\n"
            "010 2222 3333\n"
            "계약금액 120,000,000 원"
        ),
        minimum_detections=5,
        expected_types=("ORG", "PERSON", "EMAIL", "PHONE", "AMOUNT"),
        expected_token_types=("ORG", "PERSON", "EMAIL", "PHONE", "AMOUNT"),
        observation_note="줄바꿈과 띄어쓰기가 섞인 OCR 본문에서도 핵심 패턴은 유지돼야 한다",
    ),
    QualitySample(
        sample_id="ocr_scan_internal_report",
        description="스캔 보고서형 OCR 본문",
        sample_group="ocr-baseline",
        content=(
            "아이피유테크 주간 보고\n"
            "이준호 과장\n"
            "support@ipu.co.kr\n"
            "02 3456 7890\n"
            "예산 75,000,000 원 검토"
        ),
        minimum_detections=5,
        expected_types=("ORG", "PERSON", "EMAIL", "PHONE", "AMOUNT"),
        expected_token_types=("ORG", "PERSON", "EMAIL", "PHONE", "AMOUNT"),
        observation_note="보고서형 OCR 텍스트에서 연락처와 금액, 조직, 담당자 검출을 유지한다",
    ),
    QualitySample(
        sample_id="false_positive_candidate",
        description="false positive 가능 문맥",
        sample_group="observe-only",
        content="브랜드 대표 색상은 청록색이며, 소개 문구는 다음 주에 교체합니다.",
        minimum_detections=0,
        expected_types=(),
        expected_token_types=(),
        observation_note="현재 PERSON 규칙이 '브랜드 대표'를 사람 이름처럼 과탐할 수 있는 문맥",
    ),
    QualitySample(
        sample_id="false_negative_candidate",
        description="false negative 가능 문맥",
        sample_group="observe-only",
        content="문의는 sec.urity at ipu dot co kr 로 보내고, 승인 요청은 외부 담당에게 전달해 주세요.",
        minimum_detections=0,
        expected_types=(),
        expected_token_types=(),
        observation_note="특수문자가 섞인 변형 이메일, 일반 명사 기반 호칭은 여전히 미탐 또는 보수적으로 비탐지된다",
    ),
    QualitySample(
        sample_id="false_positive_org_candidate",
        description="generic org 과탐 가능 문맥",
        sample_group="observe-only",
        content="협력기업 담당 절차와 외부회사 보안 규정을 먼저 정리합니다.",
        minimum_detections=0,
        expected_types=(),
        expected_token_types=(),
        observation_note="generic suffix 용어는 조직명으로 과탐하지 않아야 한다",
    ),
    QualitySample(
        sample_id="ocr_observe_confused_digits",
        description="OCR 숫자/문자 혼동 관찰용",
        sample_group="ocr-observe",
        content="긴급 연락처는 O1O-2222-3333 이고 문의 메일은 securlty@ipu.co.kr 로 보입니다.",
        minimum_detections=0,
        expected_types=(),
        expected_token_types=(),
        observation_note="O와 0, l과 i 혼동은 현재 정규식 기반 탐지 한계로 남겨 둔다",
    ),
    QualitySample(
        sample_id="ocr_observe_spaced_email",
        description="OCR 공백 분리 이메일 관찰용",
        sample_group="ocr-observe",
        content="외부 문의는 security @ ipu . co.kr 로 보내고, 회신은 운영팀이 담당합니다.",
        minimum_detections=0,
        expected_types=(),
        expected_token_types=(),
        observation_note="기호 주변 공백이 많은 OCR 이메일은 아직 직접 패턴으로 잡지 못한다",
    ),
)
