"""S3 = B63_HYBRID_R0 (bounded research prototype).

Composition: existing IPU strict_token rules (reused read-only through
``RegexDetector``) plus bounded Korean-clinical rules:

- institutional PHI: hospital names, ward/department, MRN, order IDs,
  insurance numbers, clinician names/IDs, guardian names, street addresses,
  exact timestamps;
- quasi-ID categories: age, sex, rare diseases/procedures, detailed region,
  occupation, admission/discharge dates, unique-event phrases.

No model training, no production changes. Utility content (medications,
doses, labs, diagnoses, procedures, symptoms, negation/temporality cues) has
no matching rule, so it is preserved by construction under the default P2
tokenization policy. The optional P1 maximum-redaction output additionally
tokenizes detected quasi categories.
"""

from __future__ import annotations

import re

from benchmark.adapters.base import Prediction, SystemAdapter

_HOSPITAL_NAME = re.compile(r"[가-힣A-Za-z]{1,12}(?:대학교)?병원|[가-힣]{1,10}(?:의료원|의원|보건소)")
_WARD_DEPARTMENT = re.compile(
    r"(?:순환기내과|신경과|흉부외과|소아과|정형외과|소화기내과|응급의학과|영상의학과"
    r"|진단검사의학과|마취통증의학과|비뇨의학과|정신건강의학과|산부인과|내과|외과)"
    r"(?:\s?(?:병동|계|관찰구역))?(?:\s?\d+층)?"
)
_MRN = re.compile(
    r"(?:환자번호|차트번호|병록번호|등록번호)\s*[:：]?\s*[A-Za-z]?-?\d{4,6}(?:-\d{4,6})?"
)
_ORDER_ID = re.compile(
    r"(?:접수번호|처방전번호|검체번호|판독번호)\s*[:：]?\s*[A-Z]?-?\d{6,12}(?:-\d{2,6})?"
)
_INSURANCE_NUMBER = re.compile(
    r"(?:청구번호|보험번호|보험증권번호)\s*[:：]?\s*\d{8}-\d{7}"
)
_CLINICAL_TITLES = (
    r"수간호사|간호사|임상병리사|물리치료사|전공의|수련의|레지던트|원장|부원장|교수|약사|인턴"
)
_CLINICIAN_NAME = re.compile(
    rf"[가-힣]{{2,4}}\s*(?:{_CLINICAL_TITLES})|(?:{_CLINICAL_TITLES})\s+[가-힣]{{2,4}}"
)
_CLINICIAN_ID = re.compile(r"(?:직원\s?ID|사번)\s*[:：]?\s*(?:DR|RN|RT)-?\d{3,8}")
_GUARDIAN_LABEL = re.compile(r"(?:보호자(?:는|인)?|호출자(?:는)?)\s*")
_GUARDIAN_NAME_PARTICLES = ("이며", "이가", "님이", "이라", "님", "이", "가", "은", "는", "을", "를")
_ADDRESS = re.compile(
    r"(?:서울특별시|부산광역시|대구광역시|인천광역시|광주광역시|대전광역시|울산광역시"
    r"|세종특별자치시|제주특별자치도|[가-힣]{2,4}[시도])\s[가-힣]{1,5}[구군]\s"
    r"[가-힣]{1,6}(?:로|길)\s?\d{1,5}(?:[-~]\d{1,5})?"
)
_EXACT_TIMESTAMP = re.compile(r"(?<!\d)\d{4}[.-]\d{2}[.-]\d{2}\s\d{1,2}:\d{2}")

_QUASI_AGE = re.compile(r"(?<![\d.])(?:만\s*)?\d{1,3}\s*세(?![\dmLnLg])")
_QUASI_SEX_AFTER_AGE = re.compile(r"(?<=\d세\s)(남|여)(?=[),.\s])")
_QUASI_SEX_LABELED = re.compile(r"성별\s*[:：]?\s*(남|여)")
_QUASI_RARE_DISEASE = re.compile(
    r"근위축성측삭경화증|루게릭병|크론병|낭포성섬유증|헌팅턴병|폐동맥고혈압|전신경화증|다발성경화증"
)
_QUASI_RARE_PROCEDURE = re.compile(
    r"경피적 대동맥판막 삽입술|심장 이식|간 생체 이식|로봇 담도 절제술|ECMO 삽관"
)
_QUASI_DETAILED_REGION = re.compile(
    r"[가-힣]{2,4}도\s[가-힣]{2,4}(?:군|시)\s?[가-힣]{1,4}(?:읍|면|동)"
)
_QUASI_OCCUPATION = re.compile(r"용접공|항공 정비사|상업 잠수사|야간 교대 요원|분진 노출 굴진공")
_QUASI_ADMIT_DISCHARGE_DATE = re.compile(
    r"(?:입원일|퇴원일|시술일)\s*[:：]?\s*\d{4}[.-]\d{2}[.-]\d{2}"
)
_QUASI_UNIQUE_EVENT = re.compile(
    r"(?:지난달|지난주|작년|올 봄)[^.\n]{0,24}?(?:사고|사건|발생 사례|대피 사건)"
)

_CLINICAL_RULES: tuple[tuple[str, re.Pattern[str], int], ...] = (
    ("HOSPITAL_NAME", _HOSPITAL_NAME, 0),
    ("WARD_DEPARTMENT", _WARD_DEPARTMENT, 0),
    ("MRN", _MRN, 0),
    ("ORDER_ID", _ORDER_ID, 0),
    ("INSURANCE_NUMBER", _INSURANCE_NUMBER, 0),
    ("CLINICIAN_NAME", _CLINICIAN_NAME, 0),
    ("CLINICIAN_ID", _CLINICIAN_ID, 0),
    ("ADDRESS", _ADDRESS, 0),
    ("EXACT_TIMESTAMP", _EXACT_TIMESTAMP, 0),
)


def _guardian_name_predictions(text: str) -> list[Prediction]:
    """Label-anchored guardian/caller name extraction with josa trimming."""
    predictions: list[Prediction] = []
    for match in _GUARDIAN_LABEL.finditer(text):
        start = match.end()
        end = start
        while end < len(text) and "가" <= text[end] <= "힣":
            end += 1
        name = text[start:end]
        changed = True
        while changed and len(name) > 4:
            for particle in _GUARDIAN_NAME_PARTICLES:
                if name.endswith(particle) and len(name) - len(particle) >= 2:
                    name = name[: -len(particle)]
                    break
            else:
                changed = False
        if not (2 <= len(name) <= 4):
            continue
        predictions.append(Prediction(type="GUARDIAN_NAME", start=start, end=start + len(name)))
    return predictions

_QUASI_RULES: tuple[tuple[str, re.Pattern[str], int], ...] = (
    ("QUASI_AGE", _QUASI_AGE, 0),
    ("QUASI_SEX", _QUASI_SEX_AFTER_AGE, 1),
    ("QUASI_SEX", _QUASI_SEX_LABELED, 1),
    ("QUASI_RARE_DISEASE", _QUASI_RARE_DISEASE, 0),
    ("QUASI_RARE_PROCEDURE", _QUASI_RARE_PROCEDURE, 0),
    ("QUASI_DETAILED_REGION", _QUASI_DETAILED_REGION, 0),
    ("QUASI_OCCUPATION", _QUASI_OCCUPATION, 0),
    ("QUASI_ADMIT_DISCHARGE_DATE", _QUASI_ADMIT_DISCHARGE_DATE, 0),
    ("QUASI_UNIQUE_EVENT", _QUASI_UNIQUE_EVENT, 0),
)


def _match_predictions(pattern: re.Pattern[str], type_name: str, group: int, text: str) -> list[Prediction]:
    out: list[Prediction] = []
    for match in pattern.finditer(text):
        if group:
            start = match.start(group)
            end = match.end(group)
        else:
            start = match.start()
            end = match.end()
        if end > start:
            out.append(Prediction(type=type_name, start=start, end=end))
    return out


class S3B63HybridAdapter(SystemAdapter):
    system_id = "S3_B63_HYBRID_R0"

    def __init__(self) -> None:
        from engine.src.detector import RegexDetector

        self._engine_detector = RegexDetector()

    def detect(self, text: str) -> list[Prediction]:
        base = [
            Prediction(type=item.type, start=int(item.start), end=int(item.end))
            for item in self._engine_detector.detect(text, content_type="text", policy="strict_token")
        ]
        clinical = self._clinical_predictions(text)
        quasi = self._quasi_predictions(text)
        merged = _merge_prefer_longer(base, clinical)
        merged = _merge_prefer_longer(merged, quasi)
        return _resolve_non_overlapping(merged)

    def transform(self, text: str, case_key: str) -> str:
        return self._transform_with_policy(text, include_quasi=False)

    def policy_outputs(self) -> dict[str, str]:
        return {"P2": "tokenization", "P1": "maximum_redaction_simulated"}

    def transform_p1_max_redaction(self, text: str) -> str:
        """P1 SIMULATED_S3_MAX: additionally tokenize detected quasi categories."""
        return self._transform_with_policy(text, include_quasi=True)

    def quasi_categories(self, text: str) -> frozenset[str]:
        categories = frozenset(
            type_name
            for type_name, pattern, group in _QUASI_RULES
            if _match_predictions(pattern, type_name, group, text)
        )
        return categories

    def _clinical_predictions(self, text: str) -> list[Prediction]:
        found: list[Prediction] = []
        for type_name, pattern, group in _CLINICAL_RULES:
            found.extend(_match_predictions(pattern, type_name, group, text))
        found.extend(_guardian_name_predictions(text))
        return found

    def _quasi_predictions(self, text: str) -> list[Prediction]:
        found: list[Prediction] = []
        for type_name, pattern, group in _QUASI_RULES:
            found.extend(_match_predictions(pattern, type_name, group, text))
        return found

    def _transform_with_policy(self, text: str, *, include_quasi: bool) -> str:
        predictions = [
            p
            for p in self.detect(text)
            if include_quasi or not p.type.startswith("QUASI_")
        ]
        counters: dict[str, int] = {}
        replaced = text
        for prediction in sorted(predictions, key=lambda item: item.start, reverse=True):
            counters[prediction.type] = counters.get(prediction.type, 0) + 1
            token = f"[B63_{prediction.type}_{counters[prediction.type]:02d}]"
            replaced = replaced[: prediction.start] + token + replaced[prediction.end :]
        return replaced


def _merge_prefer_longer(primary: list[Prediction], secondary: list[Prediction]) -> list[Prediction]:
    """Add secondary predictions that extend or beat overlapping primary ones."""
    kept_secondary: list[Prediction] = []
    for candidate in secondary:
        overlaps = [p for p in primary if p.start < candidate.end and candidate.start < p.end]
        if not overlaps:
            kept_secondary.append(candidate)
            continue
        if all(
            (candidate.end - candidate.start) > (p.end - p.start) for p in overlaps
        ):
            primary = [p for p in primary if p not in overlaps]
            kept_secondary.append(candidate)
    return primary + kept_secondary


def _resolve_non_overlapping(predictions: list[Prediction]) -> list[Prediction]:
    ordered = sorted(
        predictions,
        key=lambda item: (item.start, -(item.end - item.start)),
    )
    selected: list[Prediction] = []
    for prediction in ordered:
        if any(p.start < prediction.end and prediction.start < p.end for p in selected):
            continue
        selected.append(prediction)
    return sorted(selected, key=lambda item: (item.start, item.end))
