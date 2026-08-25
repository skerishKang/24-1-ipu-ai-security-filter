"""Independent sealed holdout for B63 R0-A.

This test is intentionally added on an audit-only branch created from the
frozen implementation SHA. It does not modify S3 or production code.

Freeze SHA:
2b003b6cf683e11392b19deaf47ad5c0bce0fcdc

Sealed raw holdout SHA-256 (pre-freeze publication):
d325839fce4eb5d3758f32e9711e016be06ff261ff3c18e9995bade8eaf2c1cb

Canonical semantic SHA-256:
edb2beb86c5d5bf06e590b91ff5f48a4de69c58672c892b627a89217e37b8876
"""

from __future__ import annotations

import hashlib
import json
import unittest

from benchmark.corpus.schema import BenchmarkCase, Span, UtilitySpan, validate_corpus
from benchmark.corpus.taxonomy import QUASI_LABELS
from benchmark.runner import compute_privacy_block, compute_utility_block, load_adapter, run_system

FREEZE_SHA = "2b003b6cf683e11392b19deaf47ad5c0bce0fcdc"
RAW_SEALED_SHA256 = "d325839fce4eb5d3758f32e9711e016be06ff261ff3c18e9995bade8eaf2c1cb"
SEMANTIC_SHA256 = "edb2beb86c5d5bf06e590b91ff5f48a4de69c58672c892b627a89217e37b8876"


def _find_span(text: str, needle: str, label: str, idx: int) -> Span:
    start = text.index(needle)
    return Span(start=start, end=start + len(needle), label=label, span_id=f"p{idx:02d}")


def _find_utility(text: str, needle: str, utility_type: str, idx: int) -> UtilitySpan:
    start = text.index(needle)
    return UtilitySpan(
        start=start,
        end=start + len(needle),
        utility_type=utility_type,
        span_id=f"u{idx:02d}",
    )


def _make_case(case_id: str, text: str, phi_items, utility_items, tags) -> BenchmarkCase:
    spans = tuple(_find_span(text, needle, label, i) for i, (label, needle) in enumerate(phi_items, 1))
    utility_spans = tuple(
        _find_utility(text, needle, utility_type, i)
        for i, (utility_type, needle) in enumerate(utility_items, 1)
    )
    quasi_count = len({label for label, _ in phi_items if label in QUASI_LABELS})
    subset = "negative" if not phi_items else ("quasi" if quasi_count else "utility" if utility_items else "direct")
    return BenchmarkCase(
        case_id=case_id,
        subset=subset,
        text=text,
        spans=spans,
        utility_spans=utility_spans,
        has_quasi_combination=quasi_count >= 2,
        variant_kind="base",
        template_id="sealed_holdout_v0.1",
        synthetic=True,
    )


def build_holdout() -> tuple[list[BenchmarkCase], list[dict[str, object]]]:
    cases: list[BenchmarkCase] = []
    semantic: list[dict[str, object]] = []

    direct_names = ["테스트가온", "모의새별", "가상다온", "시험누리", "샘플해온", "모의라온"]
    hospitals = ["모의임상대학교병원", "가상진료의료원", "테스트중앙병원", "샘플권역의료원"]
    departments = ["혈액종양내과", "재활의학과", "감염내과", "신장내과", "알레르기내과", "핵의학과"]

    for i in range(12):
        n = i + 1
        name = direct_names[i % len(direct_names)]
        phone = f"000-0000-{1000+i:04d}"
        email = f"holdout{n:02d}@clinical.invalid"
        rrn = f"990231-{'1' if i % 2 == 0 else '2'}{123450+i:06d}"
        mrn = f"H-{90000+i}"
        hospital = hospitals[(i * 5) % len(hospitals)]
        dept = departments[i % len(departments)]
        month = (i % 9) + 1
        day = i + 1
        hour = 8 + (i % 10)
        minute = (i * 7) % 60
        timestamp = f"2026-{month:02d}-{day:02d} {hour:02d}:{minute:02d}"
        address = f"광주광역시 모의구 실험로 {900+i}"
        text = (
            f"외부 AI 전송 전 검토 기록. 환자명 {name}, 연락처 {phone}, 이메일 {email}. "
            f"식별번호 {rrn}, 환자번호 {mrn}. 기관 {hospital}, 진료과 {dept}, "
            f"방문시각 {timestamp}, 주소 {address}. 처방은 세파클러 250mg 하루 3회 경구이다."
        )
        phi = [
            ("PATIENT_NAME", name), ("PHONE", phone), ("EMAIL", email), ("RRN", rrn),
            ("MRN", mrn), ("HOSPITAL_NAME", hospital), ("WARD_DEPARTMENT", dept),
            ("EXACT_TIMESTAMP", timestamp), ("ADDRESS", address),
        ]
        utility = [
            ("medication", "세파클러"),
            ("dosage", "250mg"),
            ("frequency_route", "하루 3회 경구"),
        ]
        tags = ["holdout", "direct", "unseen_department", "collision_safe_identifier", "utility_mixed"]
        case_id = f"HOLD-DIR-{n:02d}"
        cases.append(_make_case(case_id, text, phi, utility, tags))
        semantic.append(_semantic(case_id, text, phi, utility, tags))

    ages = [37 + 3*i for i in range(12)]
    sexes = ["여" if i % 2 == 0 else "남" for i in range(12)]
    diseases = ["파브리병", "고셔병", "폼페병", "윌슨병", "베체트병", "유전성 혈관부종"]
    procedures = ["경정맥 간내문맥전신단락술", "심실보조장치 삽입술", "기관지 열성형술", "경피적 승모판막 성형술", "CAR-T 세포치료", "경막외 혈액봉합술"]
    occupations = ["터널 발파 기사", "도금 작업자", "축산 방역요원", "잠수 용접사", "항만 크레인 정비사", "실험동물 사육사"]
    regions = ["전라남도 모의군 별빛면", "충청북도 가상군 새봄읍", "경상북도 시험군 누리면", "강원특별자치도 샘플군 해온면"]
    events = ["금요일 야간 정전 사고", "이번 겨울 연구동 화재 대피", "새벽 냉동창고 누출 사건", "명절 연휴 산간 고립 사건", "봄철 축산 방역 집단노출", "야간 터널 붕괴 구조 사건"]

    for i in range(12):
        n = i + 1
        age = f"{ages[i]}세"
        sex = sexes[i]
        disease = diseases[i % 6]
        procedure = procedures[i % 6]
        occupation = occupations[i % 6]
        region = regions[i % 4]
        event = events[i % 6]
        text = (
            f"특이 병력 요약: {age} {sex}, {disease} 병력. 최근 {procedure} 시행. "
            f"직업은 {occupation}, 거주권역 {region}. 관련 사건: {event}. "
            "현재 간헐적 어지럼은 없음으로 기록."
        )
        phi = [
            ("AGE", age), ("SEX", sex), ("RARE_DISEASE", disease),
            ("RARE_PROCEDURE", procedure), ("OCCUPATION", occupation),
            ("DETAILED_REGION", region), ("UNIQUE_EVENT", event),
        ]
        utility = [("symptom", "간헐적 어지럼"), ("negation_cue", "없음")]
        tags = ["holdout", "quasi", "unseen_rare_disease", "unseen_procedure", "unseen_occupation", "unseen_event_phrase"]
        case_id = f"HOLD-QI-{n:02d}"
        cases.append(_make_case(case_id, text, phi, utility, tags))
        semantic.append(_semantic(case_id, text, phi, utility, tags))

    mixed_hospitals = ["가상진료의료원", "테스트중앙병원", "샘플권역의료원", "모의임상대학교병원"]
    mixed_depts = ["감염내과", "신장내과", "알레르기내과", "핵의학과", "혈액종양내과", "재활의학과", "감염내과", "신장내과"]
    guardians = ["모의보호자갑", "테스트보호자을", "가상가족병", "샘플연락자정"]
    clinicians = ["시험의사갑", "모의간호사을", "가상약사병", "샘플치료사정"]

    for i in range(8):
        n = i + 1
        hospital = mixed_hospitals[i % 4]
        dept = mixed_depts[i]
        guardian = guardians[i % 4]
        clinician = clinicians[i % 4]
        order_id = f"X2609{i:02d}-{30+i:03d}"
        text = (
            f"상담 메모 | 기관={hospital} | 부서={dept} | 보호자 이름={guardian} | "
            f"담당자={clinician} | 오더={order_id} | 진단=철결핍성 빈혈 | "
            "검사=Hb 9.8 g/dL | 판단=출혈 가능성을 배제하기 어렵다."
        )
        phi = [
            ("HOSPITAL_NAME", hospital), ("WARD_DEPARTMENT", dept),
            ("GUARDIAN_NAME", guardian), ("CLINICIAN_NAME", clinician), ("ORDER_ID", order_id),
        ]
        utility = [
            ("diagnosis", "철결핍성 빈혈"),
            ("lab_value", "Hb 9.8 g/dL"),
            ("uncertainty_cue", "출혈 가능성을 배제하기 어렵다"),
        ]
        tags = ["holdout", "mixed", "table_layout", "unseen_labels_context"]
        case_id = f"HOLD-MIX-{n:02d}"
        cases.append(_make_case(case_id, text, phi, utility, tags))
        semantic.append(_semantic(case_id, text, phi, utility, tags))

    negatives = [
        ("교육자료: '환자번호'라는 단어는 병원 정보시스템에서 내부 식별자를 뜻할 수 있다. 실제 번호는 포함하지 않는다.", [("diagnosis", "병원 정보시스템")]),
        ("약제 안내: 메트로니다졸 500mg은 특정 감염에서 사용될 수 있으나 이 문장은 개인 처방 기록이 아니다.", [("medication", "메트로니다졸"), ("dosage", "500mg")]),
        ("검사 참고: CRP 0.5 mg/dL 미만이라는 기준 예시는 환자 결과가 아니라 교육용 수치다.", [("lab_value", "CRP 0.5 mg/dL")]),
        ("보안 정책 예시: 전화번호 형식은 000-0000-0000처럼 표시할 수 있으나 실제 연락처가 아니다.", []),
        ("연구 설명: '파브리병'이라는 질환명 자체는 개인식별자가 아니며, 특정 환자와 연결될 때 위험이 커진다.", [("diagnosis", "파브리병")]),
        ("운영 문서: 감염내과, 신장내과, 재활의학과라는 부서명이 존재한다고 해서 특정 환자를 식별하는 것은 아니다.", []),
        ("문서 템플릿: '보호자 이름=' 뒤에는 실제 이름이 아니라 [보호자명] 자리표시자를 넣는다.", []),
        ("모의주소 예시: 광주광역시 모의구 실험로 999는 교육용 주소이며 실제 거주지를 의미하지 않는다.", []),
    ]
    for i, (text, utility) in enumerate(negatives, 1):
        case_id = f"HOLD-NEG-{i:02d}"
        tags = ["holdout", "hard_negative", "ambiguity"]
        cases.append(_make_case(case_id, text, [], utility, tags))
        semantic.append(_semantic(case_id, text, [], utility, tags))

    return cases, semantic


def _semantic(case_id, text, phi_items, utility_items, tags):
    return {
        "case_id": case_id,
        "text": text,
        "gold_phi": [{"label": label, "text": needle} for label, needle in phi_items],
        "gold_utility": [{"type": typ, "text": needle} for typ, needle in utility_items],
        "tags": tags,
        "synthetic_only": True,
    }


def _semantic_hash(semantic: list[dict[str, object]]) -> str:
    payload = json.dumps(semantic, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _evaluate(system_id: str, cases: list[BenchmarkCase]) -> tuple[dict[str, object], int]:
    adapter = load_adapter(system_id)
    results, stats = run_system(adapter, cases)
    partitions = {
        "base": results,
        "adversarial": [],
        "all_phi": [(case, result) for case, result in results if case.spans],
        "negative": [(case, result) for case, result in results if not case.spans],
    }
    privacy = compute_privacy_block(partitions)
    utility = compute_utility_block(results)
    privacy["_utility_rates"] = {
        key: value["rate"]
        for key, value in utility.items()
        if isinstance(value, dict) and isinstance(value.get("rate"), (int, float))
    }
    return {"privacy": privacy, "utility": utility}, stats.cases_failed


class SealedHoldoutAuditTest(unittest.TestCase):
    def test_sealed_holdout_semantics_and_evaluation(self) -> None:
        cases, semantic = build_holdout()
        self.assertEqual(len(cases), 40)
        self.assertEqual(_semantic_hash(semantic), SEMANTIC_SHA256)
        validate_corpus(cases)

        blocks: dict[str, dict[str, object]] = {}
        failures: dict[str, int] = {}
        for system_id in ("S0", "S1", "S3"):
            blocks[system_id], failures[system_id] = _evaluate(system_id, cases)
            self.assertEqual(failures[system_id], 0, msg=f"{system_id} adapter failures")

        def p(system, key, subkey=None):
            value = blocks[system]["privacy"][key]
            return value[subkey] if subkey else value

        baseline_best_f2 = max(p("S0", "high_risk_f2_base"), p("S1", "high_risk_f2_base"))
        s3_f2 = p("S3", "high_risk_f2_base")
        baseline_best_qicdr = max(
            p("S0", "quasi_combination_detection_rate", "rate"),
            p("S1", "quasi_combination_detection_rate", "rate"),
        )
        s3_qicdr = p("S3", "quasi_combination_detection_rate", "rate")

        summary = {
            "freeze_sha": FREEZE_SHA,
            "sealed_raw_sha256": RAW_SEALED_SHA256,
            "semantic_sha256": SEMANTIC_SHA256,
            "case_count": len(cases),
            "systems": {
                sid: {
                    "entity_overlap_f1": p(sid, "entity_overlap_base", "f1"),
                    "entity_overlap_recall": p(sid, "entity_overlap_base", "recall"),
                    "high_risk_f2": p(sid, "high_risk_f2_base"),
                    "residual_direct_phi_rate": p(sid, "residual_direct_phi_rate", "rate"),
                    "transform_escape_rate": p(sid, "transform_escape_rate", "rate"),
                    "qicdr": p(sid, "quasi_combination_detection_rate", "rate"),
                    "negative_document_fp_rate": p(sid, "negative_false_positive", "document_fp_rate"),
                }
                for sid in ("S0", "S1", "S3")
            },
            "margins": {
                "s3_high_risk_f2_minus_best_baseline": round(s3_f2 - baseline_best_f2, 4),
                "s3_qicdr_minus_best_baseline": round(s3_qicdr - baseline_best_qicdr, 4),
            },
        }
        print("B63_SEALED_HOLDOUT_RESULT=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
