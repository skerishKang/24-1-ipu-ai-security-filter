"""Deterministic synthetic Korean clinical corpus generator for B63 R0-A.

Every value is invented. No real patient data, no scraped notes, no ambiguous
sources. The same seed always produces a byte-identical corpus.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from benchmark.corpus.schema import (
    BenchmarkCase,
    CorpusManifest,
    RelationPair,
    Span,
    UtilitySpan,
    validate_corpus,
)
from benchmark.corpus.taxonomy import CORPUS_SEED, CORPUS_VERSION, SCHEMA_VERSION

# ---------------------------------------------------------------------------
# Fictional value pools (synthetic by construction)
# ---------------------------------------------------------------------------

PATIENT_NAMES = (
    "김예찬", "이소리", "박한결", "최다솜", "정여준", "강수리", "윤태결", "문가람",
    "임세별", "오하람", "한지운", "신아린", "곽도현", "민서진", "길하늘", "표나경",
)
GUARDIAN_NAMES = ("김정묵", "이난향", "박성균", "초미란", "정학수", "양재임")
CLINICIAN_NAMES = (
    "유원준 원장", "서해린 교수", "고은찬 전공의", "문설아 수련의",
    "하재모 교수", "나경찬 원장",
)
HOSPITALS = (
    "한빛대학교병원", "예솔종합병원", "다래의료원", "소담보건소",
    "바름대학교병원", "노을의원",
)
WARDS = (
    "순환기내과 병동 7층", "신경과 병동 5층", "흉부외과 계 3층",
    "소아과 병동 4층", "응급의학과 관찰구역 1층",
)
METRO_ADDRESSES = (
    "서울특별시 예시구 예시로 123", "부산광역시 바름구 해맞이길 45-6",
    "대전광역시 노을구 소담로 8", "인천광역시 다래구 예찬로 301",
)
PROVINCE_ADDRESSES = (
    "경기도 바름군 한빛로 45-6", "충청남도 노을군 소리길 12",
    "전라남도 예송군 가람길 77",
)
DETAILED_REGIONS = (
    "경기도 바름군 노을면", "충청남도 예송군 한빛읍", "전라북도 소담군 다래동",
)
OCCUPATIONS = ("용접공", "항공 정비사", "상업 잠수사", "야간 교대 요원", "분진 노출 굴진공")
RARE_DISEASES = (
    "근위축성측삭경화증", "루게릭병", "크론병", "낭포성섬유증",
    "헌팅턴병", "폐동맥고혈압", "전신경화증", "다발성경화증",
)
RARE_PROCEDURES = (
    "경피적 대동맥판막 삽입술", "심장 이식", "간 생체 이식", "로봇 담도 절제술", "ECMO 삽관"
)
UNIQUE_EVENTS = (
    "지난달 지역 집단 식중독 사건", "작년 상습 홍수 대피 사건",
    "지난주 공장 분진 폭발 사고", "올 봄 집단 발진 발생 사례",
)
EMAIL_DOMAINS = ("hanbitmed.example", "yesol-clinic.example", "darae.example")
PHONE_SERVICE_BLOCKLIST_PREFIXES = ("1566", "1577", "1588", "1600", "1644", "1666", "1677", "1688")

MEDICATIONS = (
    "아목시실린", "메트포르민", "라시스", "아토르바스타틴", "암로디핀",
    "클로피도그렐", "파모티딘", "세트리진", "부데소니드", "살부타몰",
    "레보플록사신", "트라마돌",
)
DOSES = ("500mg", "850mg", "20mg", "10mg", "100mg", "2.5mg")
FREQ_ROUTES = (
    "하루 3회 식후 경구", "하루 1회 취침 전 경구", "하루 2회 아침 저녁 경구",
    "매일 아침 흡입", "하루 4회 필요 시 복용",
)
LAB_VALUES = (
    "혈압 128/76 mmHg", "Hb 11.2 g/dL", "공복혈당 134 mg/dL",
    "eGFR 62 mL/min/1.73m2", "SpO2 95% (room air)", "LDL 148 mg/dL",
    "CRP 0.4 mg/dL", "혈청 크레아티닌 1.1 mg/dL",
)
DIAGNOSES = (
    "고혈압", "제2형 당뇨병", "천식", "위식도역류질환", "골관절염", "부정맥",
)
PROCEDURES_UTILITY = (
    "대장내시경", "위내시경", "관상동맥 조영술", "물리치료", "피부 봉합술",
)
SYMPTOMS = ("기침", "가슴 답답함", "복부 팽만감", "간헐적 두통", "운동 시 호흡곤란")
NEGATION_CUES = ("없음", "아니었다", "배제된다")
UNCERTAINTY_CUES = ("가능성을 배제하기 어렵다", "으로 추정된다", "가능성이 있다")
TEMPORALITY_CUES = ("3일 전부터", "지난주부터", "내원 당시부터", "2주 전까지")

# ---------------------------------------------------------------------------
# Text builder
# ---------------------------------------------------------------------------


@dataclass
class _Draft:
    template_id: str
    text: str = ""
    spans: list[Span] = field(default_factory=list)
    utility_spans: list[UtilitySpan] = field(default_factory=list)
    relations: list[RelationPair] = field(default_factory=list)
    event_order_markers: list[str] = field(default_factory=list)
    _phi_counter: int = 0
    _util_counter: int = 0

    def literal(self, chunk: str) -> None:
        self.text += chunk

    def entity(self, value: str, label: str) -> str:
        self._phi_counter += 1
        span_id = f"{self.template_id}-phi-{self._phi_counter:02d}"
        start = len(self.text)
        self.text += value
        self.spans.append(Span(start=start, end=len(self.text), label=label, span_id=span_id))
        return span_id

    def utility(self, value: str, utype: str) -> str:
        self._util_counter += 1
        span_id = f"{self.template_id}-util-{self._util_counter:02d}"
        start = len(self.text)
        self.text += value
        self.utility_spans.append(
            UtilitySpan(start=start, end=len(self.text), utility_type=utype, span_id=span_id)
        )
        return span_id

    def relation(self, diagnosis_span_id: str, treatment_span_id: str) -> None:
        self.relations.append(
            RelationPair(diagnosis_span_id=diagnosis_span_id, treatment_span_id=treatment_span_id)
        )

    def order_markers(self, *markers: str) -> None:
        self.event_order_markers.extend(markers)


def make_case(case_id: str, subset: str, draft: _Draft, *, has_quasi_combination: bool) -> BenchmarkCase:
    return BenchmarkCase(
        case_id=case_id,
        subset=subset,
        text=draft.text,
        spans=tuple(draft.spans),
        utility_spans=tuple(draft.utility_spans),
        relations=tuple(draft.relations),
        event_order_markers=tuple(draft.event_order_markers),
        has_quasi_combination=has_quasi_combination,
        variant_kind="base",
        template_id=draft.template_id,
        synthetic=True,
    )


# ---------------------------------------------------------------------------
# Synthetic value generators (seeded)
# ---------------------------------------------------------------------------


def _synthetic_phone(rng: random.Random) -> str:
    while True:
        middle = rng.randrange(2000, 9999)
        if not any(str(middle).startswith(p[:4]) for p in PHONE_SERVICE_BLOCKLIST_PREFIXES):
            return f"010-{middle}-{rng.randrange(1000, 9999)}"


def _synthetic_landline(rng: random.Random) -> str:
    area = rng.choice(("02", "031", "051", "053"))
    if area == "02":
        return f"02-7{rng.randrange(100, 999)}-{rng.randrange(1000, 9999)}"
    return f"{area}-{rng.randrange(200, 999)}-{rng.randrange(1000, 9999)}"


def _synthetic_rrn(rng: random.Random) -> str:
    yy = rng.randrange(40, 99)
    mm = rng.randrange(1, 13)
    dd = rng.randrange(1, 28)
    tail = f"{rng.choice((1, 2))}{rng.randrange(0, 10**6):06d}"
    return f"{yy:02d}{mm:02d}{dd:02d}-{tail}"


def _synthetic_foreign_reg(rng: random.Random) -> str:
    yy = rng.randrange(60, 99)
    mm = rng.randrange(1, 13)
    dd = rng.randrange(1, 28)
    tail = f"{rng.choice((5, 6, 7, 8))}{rng.randrange(0, 10**6):06d}"
    return f"{yy:02d}{mm:02d}{dd:02d}-{tail}"


def _email(rng: random.Random, index: int) -> str:
    local = f"pt{index:03d}.contact"
    return f"{local}@{rng.choice(EMAIL_DOMAINS)}"


def _mrn(rng: random.Random) -> str:
    return f"M{rng.randrange(2020, 2027)}-{rng.randrange(10000, 99999)}"


def _order_id(rng: random.Random, prefix: str) -> str:
    return f"{prefix}{rng.randrange(20260101, 20261231)}-{rng.randrange(100, 999)}"


def _timestamp(rng: random.Random) -> str:
    minute = rng.choice(("00", "15", "30", "45"))
    return f"2026-{rng.randrange(1, 13):02d}-{rng.randrange(1, 29):02d} {rng.randrange(7, 20):02d}:{minute}"


def _date(rng: random.Random) -> str:
    return f"2026-{rng.randrange(1, 13):02d}-{rng.randrange(1, 29):02d}"


def _insurance_number(rng: random.Random) -> str:
    return f"{rng.randrange(20260000, 20269999)}-{rng.randrange(1000000, 9999999)}"


def _clinician_id(rng: random.Random) -> str:
    role = rng.choice(("DR", "RN", "RT"))
    return f"{role}-{rng.randrange(10000, 99999)}"


# ---------------------------------------------------------------------------
# Base-case templates
# ---------------------------------------------------------------------------


def _tpl_direct_registration(index: int, rng: random.Random, pool: dict[str, object]) -> _Draft:
    d = _Draft("direct_registration")
    d.literal("외래 등록 기록. ")
    d.entity(pool["patient_name"], "PATIENT_NAME")
    d.literal("(")
    d.entity(f"{pool['age']}세", "AGE")
    d.literal(" ")
    d.entity(pool["sex"], "SEX")
    d.literal(")이 오늘 ")
    d.entity(pool["hospital"], "HOSPITAL_NAME")
    d.literal(" 순환기내과 외래에 접수되었다. 연락처는 ")
    d.entity(_synthetic_phone(rng), "PHONE")
    d.literal("이며, 주소는 ")
    d.entity(pool["address"], "ADDRESS")
    d.literal("이다. 환자번호: ")
    d.entity(_mrn(rng), "MRN")
    d.literal(". 보호자 ")
    d.entity(pool["guardian_name"], "GUARDIAN_NAME")
    d.literal("(연락처 ")
    d.entity(_synthetic_phone(rng), "PHONE")
    d.literal(") 동행 확인.")
    return d


def _tpl_direct_referral(index: int, rng: random.Random, pool: dict[str, object]) -> _Draft:
    d = _Draft("direct_referral")
    d.entity(pool["hospital"], "HOSPITAL_NAME")
    d.literal(" ")
    d.entity(pool["clinician_name"], "CLINICIAN_NAME")
    d.literal("입니다. 진료 의뢰합니다. 환자 ")
    d.entity(pool["patient_name"], "PATIENT_NAME")
    d.literal("(주민등록번호 ")
    d.entity(_synthetic_rrn(rng), "RRN")
    d.literal(")을 소화기내과 진료를 위해 의뢰합니다. 보호자는 ")
    d.entity(pool["guardian_name"], "GUARDIAN_NAME")
    d.literal("이며 연락처 ")
    d.entity(_synthetic_phone(rng), "PHONE")
    d.literal("입니다. 판독 결과는 이메일 ")
    d.entity(_email(rng, index), "EMAIL")
    d.literal(" 회신 부탁드립니다.")
    return d


def _tpl_direct_insurance(index: int, rng: random.Random, pool: dict[str, object]) -> _Draft:
    d = _Draft("direct_insurance")
    d.literal("청구 메모. 청구번호 ")
    d.entity(_insurance_number(rng), "INSURANCE_NUMBER")
    d.literal(" / 외국인등록번호 ")
    d.entity(_synthetic_foreign_reg(rng), "FOREIGN_REG_NUMBER")
    d.literal(" 건에 대한 서류 검토 요청. 환자 ")
    d.entity(pool["patient_name"], "PATIENT_NAME")
    d.literal(", 거주지 ")
    d.entity(pool["address"], "ADDRESS")
    d.literal(". 담당 의사 ")
    d.entity(pool["clinician_name"], "CLINICIAN_NAME")
    d.literal("(직원 ID ")
    d.entity(_clinician_id(rng), "CLINICIAN_ID")
    d.literal(") 서명 확인 완료.")
    return d


def _tpl_direct_call_log(index: int, rng: random.Random, pool: dict[str, object]) -> _Draft:
    d = _Draft("direct_call_log")
    d.literal("전화 문의 기록. 접수번호 ")
    d.entity(_order_id(rng, "R"), "ORDER_ID")
    d.literal(" 예약 변경 문의. 호출자 ")
    d.entity(pool["guardian_name"], "GUARDIAN_NAME")
    d.literal(", 연락처 ")
    d.entity(_synthetic_landline(rng), "PHONE")
    d.literal(". 차트상 환자명 ")
    d.entity(pool["patient_name"], "PATIENT_NAME")
    d.literal(" / 환자번호 ")
    d.entity(_mrn(rng), "MRN")
    d.literal(" 일치 여부 확인 후 회신. 처리 시각 ")
    d.entity(_timestamp(rng), "EXACT_TIMESTAMP")
    d.literal(".")
    return d


def _tpl_inst_admission(index: int, rng: random.Random, pool: dict[str, object]) -> _Draft:
    d = _Draft("inst_admission")
    d.entity(pool["hospital"], "HOSPITAL_NAME")
    d.literal(" 입원 기록. 입원일 ")
    d.entity(_date(rng), "ADMIT_DISCHARGE_DATE")
    d.literal(", 배치 병동은 ")
    d.entity(pool["ward"], "WARD_DEPARTMENT")
    d.literal("이다. 접수번호 ")
    d.entity(_order_id(rng, "A"), "ORDER_ID")
    d.literal(". 오늘 ")
    d.entity(_timestamp(rng), "EXACT_TIMESTAMP")
    d.literal(" 시점 활력 징후는 안정적이다.")
    return d


def _tpl_inst_specimen(index: int, rng: random.Random, pool: dict[str, object]) -> _Draft:
    d = _Draft("inst_specimen")
    d.literal("검체 접수 대장. 검체번호 ")
    d.entity(_order_id(rng, "S"), "ORDER_ID")
    d.literal(", 판독번호 ")
    d.entity(_order_id(rng, "P"), "ORDER_ID")
    d.literal(". 접수 시각 ")
    d.entity(_timestamp(rng), "EXACT_TIMESTAMP")
    d.literal(". 위탁 기관 ")
    d.entity(pool["hospital"], "HOSPITAL_NAME")
    d.literal(" ")
    d.entity(pool["ward"].split()[0], "WARD_DEPARTMENT")
    d.literal("에서 의뢰.")
    return d


def _tpl_inst_rounds(index: int, rng: random.Random, pool: dict[str, object]) -> _Draft:
    d = _Draft("inst_rounds")
    d.literal("회진 메모. 담당 ")
    d.entity(pool["clinician_name"], "CLINICIAN_NAME")
    d.literal(", 병동 ")
    d.entity(pool["ward"], "WARD_DEPARTMENT")
    d.literal(". 처방전번호 ")
    d.entity(_order_id(rng, "D"), "ORDER_ID")
    d.literal(" 약제 반출 확인. 기록 시각 ")
    d.entity(_timestamp(rng), "EXACT_TIMESTAMP")
    d.literal(".")
    return d


def _tpl_inst_discharge(index: int, rng: random.Random, pool: dict[str, object]) -> _Draft:
    d = _Draft("inst_discharge")
    d.entity(pool["hospital"], "HOSPITAL_NAME")
    d.literal(" 퇴원 요약. 담당부서 ")
    d.entity(pool["ward"].split()[0], "WARD_DEPARTMENT")
    d.literal(". 퇴원일 ")
    d.entity(_date(rng), "ADMIT_DISCHARGE_DATE")
    d.literal(". 행정 처리 접수번호 ")
    d.entity(_order_id(rng, "T"), "ORDER_ID")
    d.literal(". 최초 등록 시각 ")
    d.entity(_timestamp(rng), "EXACT_TIMESTAMP")
    d.literal(" 기준으로 세션 종결.")
    return d


def _tpl_quasi_rare_combo(index: int, rng: random.Random, pool: dict[str, object]) -> _Draft:
    d = _Draft("quasi_rare_combo")
    d.entity(f"{pool['age']}세", "AGE")
    d.literal(" ")
    d.entity(pool["sex"], "SEX")
    d.literal(" 환자가 내원했다. ")
    d.entity(pool["rare_disease"], "RARE_DISEASE")
    d.literal(" 확진 병력이 있으며 ")
    d.entity(pool["region"], "DETAILED_REGION")
    d.literal(" 거주 중이다. 직업은 ")
    d.entity(pool["occupation"], "OCCUPATION")
    d.literal("이다.")
    return d


def _tpl_quasi_rare_procedure(index: int, rng: random.Random, pool: dict[str, object]) -> _Draft:
    d = _Draft("quasi_rare_procedure")
    d.literal("지난달 ")
    d.entity(pool["rare_procedure"], "RARE_PROCEDURE")
    d.literal("을 시행한 ")
    d.entity(f"{pool['age']}세", "AGE")
    d.literal(" ")
    d.entity(pool["sex"], "SEX")
    d.literal(" 환자의 경과 관찰 기록이다. 시술일 ")
    d.entity(_date(rng), "ADMIT_DISCHARGE_DATE")
    d.literal(", 현재 ")
    d.entity(pool["region"], "DETAILED_REGION")
    d.literal(" 자가 재가 상태다.")
    return d


def _tpl_quasi_event_timing(index: int, rng: random.Random, pool: dict[str, object]) -> _Draft:
    d = _Draft("quasi_event_timing")
    d.entity(pool["unique_event"], "UNIQUE_EVENT")
    d.literal(" 이후 발열과 두통을 주소로 응급실을 방문했다. ")
    d.entity(f"{pool['age']}세", "AGE")
    d.literal(" ")
    d.entity(pool["sex"], "SEX")
    d.literal(". 입원일 ")
    d.entity(_date(rng), "ADMIT_DISCHARGE_DATE")
    d.literal(", 퇴원일 ")
    d.entity(_date(rng), "ADMIT_DISCHARGE_DATE")
    d.literal(".")
    return d


def _tpl_quasi_occupation_exposure(index: int, rng: random.Random, pool: dict[str, object]) -> _Draft:
    d = _Draft("quasi_occupation_exposure")
    d.entity(pool["occupation"], "OCCUPATION")
    d.literal(" 종사자가 직업 관련 증상 평가를 받았다. 거주지는 ")
    d.entity(pool["region"], "DETAILED_REGION")
    d.literal("이고, 병력에 ")
    d.entity(pool["rare_disease"], "RARE_DISEASE")
    d.literal("이 보고되었다. 나이 ")
    d.entity(f"{pool['age']}세", "AGE")
    d.literal(", ")
    d.entity(pool["sex"], "SEX")
    d.literal(".")
    return d


def _tpl_neg_general(index: int, rng: random.Random, pool: dict[str, object]) -> _Draft:
    d = _Draft("neg_general")
    d.literal(
        "충분한 수면과 규칙적인 운동은 만성 피로 개선에 도움이 된다. "
        "카페인 섭취는 오후 이후 줄이는 것이 권장된다. 물을 자주 나누어 마시고 "
        "장시간 같은 자세를 피한다."
    )
    return d


def _tpl_neg_lab_reference(index: int, rng: random.Random, pool: dict[str, object]) -> _Draft:
    d = _Draft("neg_lab_reference")
    d.utility("공복혈당 참고범위는 70-100 mg/dL이다.", "lab_value")
    d.literal(" ")
    d.utility("총 콜레스테롤은 200 mg/dL 미만을 유지하는 것이 일반적 권고다.", "lab_value")
    return d


def _tpl_neg_med_info(index: int, rng: random.Random, pool: dict[str, object]) -> _Draft:
    d = _Draft("neg_med_info")
    d.utility("아세트아미노펜은 해열진통제로 일반적으로 사용된다.", "medication")
    d.literal(" ")
    d.utility("성인 기준 1회 500mg을 하루 4회 이내로 복용할 수 있다.", "dosage")
    d.literal(" 과량 복용 시 간 손상 위험이 있으니 주의한다.")
    return d


def _tpl_util_med_list(index: int, rng: random.Random, pool: dict[str, object]) -> _Draft:
    d = _Draft("util_med_list")
    dx_span = d.utility(pool["diagnosis"], "diagnosis")
    d.literal("으로 진단받고 약물 치료를 시작했다. 처방: ")
    med_span = d.utility(pool["medication"], "medication")
    d.literal(" ")
    d.utility(pool["dose"], "dosage")
    d.literal(" ")
    d.utility(pool["freq_route"], "frequency_route")
    d.literal(". 복약 순서는 먼저 아침 식후, 이후 저녁 식후다.")
    d.order_markers("먼저", "이후")
    d.relation(dx_span, med_span)
    return d


def _tpl_util_labs(index: int, rng: random.Random, pool: dict[str, object]) -> _Draft:
    d = _Draft("util_labs")
    d.utility(pool["lab_value_a"], "lab_value")
    d.literal(", ")
    d.utility(pool["lab_value_b"], "lab_value")
    d.literal(" 확인. 내원 당시부터 혈당 변동이 컸고 그 후 안정화되었다.")
    d.order_markers("그 후")
    return d


def _tpl_util_negation_uncertainty(index: int, rng: random.Random, pool: dict[str, object]) -> _Draft:
    d = _Draft("util_negation_uncertainty")
    d.utility(pool["symptom"], "symptom")
    d.literal("은 호전 중이며 폐렴 소견은 ")
    d.utility(pool["negation_cue"], "negation_cue")
    d.literal(". 다만 결핵 ")
    d.utility(pool["uncertainty_cue"], "uncertainty_cue")
    d.literal(".")
    return d


def _tpl_util_temporality(index: int, rng: random.Random, pool: dict[str, object]) -> _Draft:
    d = _Draft("util_temporality")
    d.utility(pool["temporality_cue"], "temporality")
    d.literal(" ")
    d.utility(pool["symptom"], "symptom")
    d.literal("이 지속되어 내원했다. ")
    d.utility(pool["procedure"], "procedure")
    d.literal(" 예약은 유지되며 퇴원 후 외래 계획을 설명했다.")
    return d


def _tpl_util_relation_ordering(index: int, rng: random.Random, pool: dict[str, object]) -> _Draft:
    d = _Draft("util_relation_ordering")
    dx_span = d.utility(pool["diagnosis"], "diagnosis")
    d.literal("으로 진단받았고 먼저 식이 조절을 시행했다. 이후 ")
    med_span = d.utility(pool["medication"], "medication")
    d.literal(" ")
    d.utility(pool["dose"], "dosage")
    d.literal("을 복용했다. 다음날 증상은 ")
    d.utility(pool["negation_cue"], "negation_cue")
    d.literal(". 그 후 외래 추적을 예약했다.")
    d.order_markers("먼저", "이후", "다음날", "그 후")
    d.relation(dx_span, med_span)
    return d


def _tpl_util_procedure_note(index: int, rng: random.Random, pool: dict[str, object]) -> _Draft:
    d = _Draft("util_procedure_note")
    d.utility(pool["procedure"], "procedure")
    d.literal("을 시행했다. 시술 중 합병증은 ")
    d.utility(pool["negation_cue"], "negation_cue")
    d.literal(". 3일 전부터 나타난 ")
    d.utility(pool["symptom"], "symptom")
    d.literal("은 시술 이후 완화 경향이다.")
    d.order_markers("이후")
    return d


DIRECT_TEMPLATES = (
    _tpl_direct_registration,
    _tpl_direct_referral,
    _tpl_direct_insurance,
    _tpl_direct_call_log,
)
INSTITUTIONAL_TEMPLATES = (
    _tpl_inst_admission,
    _tpl_inst_specimen,
    _tpl_inst_rounds,
    _tpl_inst_discharge,
)
QUASI_TEMPLATES = (
    _tpl_quasi_rare_combo,
    _tpl_quasi_rare_procedure,
    _tpl_quasi_event_timing,
    _tpl_quasi_occupation_exposure,
)
NEGATIVE_TEMPLATES = (_tpl_neg_general, _tpl_neg_lab_reference, _tpl_neg_med_info)
UTILITY_TEMPLATES = (
    _tpl_util_med_list,
    _tpl_util_labs,
    _tpl_util_negation_uncertainty,
    _tpl_util_temporality,
    _tpl_util_relation_ordering,
    _tpl_util_procedure_note,
)

TEMPLATE_COUNTS = {
    "direct": 8,
    "institutional": 5,
    "quasi": 6,
    "negative": 5,
    "utility": 3,
}


def _base_pool(subset: str, index: int) -> dict[str, object]:
    return {
        "patient_name": PATIENT_NAMES[index % len(PATIENT_NAMES)],
        "guardian_name": GUARDIAN_NAMES[index % len(GUARDIAN_NAMES)],
        "clinician_name": CLINICIAN_NAMES[(index + len(subset)) % len(CLINICIAN_NAMES)],
        "hospital": HOSPITALS[index % len(HOSPITALS)],
        "ward": WARDS[index % len(WARDS)],
        "address": METRO_ADDRESSES[index % len(METRO_ADDRESSES)]
        if index % 2 == 0
        else PROVINCE_ADDRESSES[index % len(PROVINCE_ADDRESSES)],
        "region": DETAILED_REGIONS[index % len(DETAILED_REGIONS)],
        "occupation": OCCUPATIONS[index % len(OCCUPATIONS)],
        "rare_disease": RARE_DISEASES[index % len(RARE_DISEASES)],
        "rare_procedure": RARE_PROCEDURES[index % len(RARE_PROCEDURES)],
        "unique_event": UNIQUE_EVENTS[index % len(UNIQUE_EVENTS)],
        "age": 19 + ((index * 7) % 70),
        "sex": "여" if index % 2 == 0 else "남",
        "diagnosis": DIAGNOSES[index % len(DIAGNOSES)],
        "medication": MEDICATIONS[index % len(MEDICATIONS)],
        "dose": DOSES[index % len(DOSES)],
        "freq_route": FREQ_ROUTES[index % len(FREQ_ROUTES)],
        "procedure": PROCEDURES_UTILITY[index % len(PROCEDURES_UTILITY)],
        "symptom": SYMPTOMS[index % len(SYMPTOMS)],
        "negation_cue": NEGATION_CUES[index % len(NEGATION_CUES)],
        "uncertainty_cue": UNCERTAINTY_CUES[index % len(UNCERTAINTY_CUES)],
        "temporality_cue": TEMPORALITY_CUES[index % len(TEMPORALITY_CUES)],
        "lab_value_a": LAB_VALUES[index % len(LAB_VALUES)],
        "lab_value_b": LAB_VALUES[(index + 3) % len(LAB_VALUES)],
    }


def build_base_cases(seed: int = CORPUS_SEED) -> list[BenchmarkCase]:
    cases: list[BenchmarkCase] = []
    plan = (
        ("direct", DIRECT_TEMPLATES),
        ("institutional", INSTITUTIONAL_TEMPLATES),
        ("quasi", QUASI_TEMPLATES),
        ("negative", NEGATIVE_TEMPLATES),
        ("utility", UTILITY_TEMPLATES),
    )
    running = 0
    for subset, templates in plan:
        count_per_template = TEMPLATE_COUNTS[subset]
        for template in templates:
            for _ in range(count_per_template):
                running += 1
                rng_instance = random.Random(f"{seed}:{subset}:{running}")
                pool = _base_pool(subset, running)
                draft = template(running, rng_instance, pool)
                cases.append(
                    make_case(
                        case_id=f"base-{subset}-{running:03d}",
                        subset=subset,
                        draft=draft,
                        has_quasi_combination=(subset == "quasi"),
                    )
                )
    validate_corpus(cases)
    return cases


def build_manifest(cases: list[BenchmarkCase], seed: int = CORPUS_SEED) -> CorpusManifest:
    base_cases = [case for case in cases if case.variant_kind == "base"]
    adversarial_cases = [case for case in cases if case.variant_kind != "base"]
    subset_counts: dict[str, int] = {}
    for case in base_cases:
        subset_counts[case.subset] = subset_counts.get(case.subset, 0) + 1
    return CorpusManifest(
        synthetic_only=True,
        corpus_version=CORPUS_VERSION,
        schema_version=SCHEMA_VERSION,
        seed=seed,
        base_case_count=len(base_cases),
        adversarial_case_count=len(adversarial_cases),
        total_case_count=len(cases),
        subset_counts=subset_counts,
    )
