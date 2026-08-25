"""S1 = GENERIC_PII_BASELINE (in-repo reference implementation).

Self-contained generic PII heuristics of the kind common to free/local
de-identification tools: email, phone, national-ID digit shapes, credit card
shape, street-address keywords, and labeled ID numbers. It has no Korean
clinical knowledge (no name lexicon, no hospital context, no quasi-ID logic)
— that gap is precisely what R0 measures.

This is a reference baseline, not an optimized external product. See
benchmark/README.md limitations.
"""

from __future__ import annotations

import re

from benchmark.adapters.base import Prediction, SystemAdapter

_LUHN = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
_EMAIL = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_PHONE = re.compile(
    r"(?:\+?82[-.\s]?)?(?:01[016789]|0\d{1,2})[-.\s]?\d{3,4}[-.\s]?\d{4}"
)
_NATIONAL_ID = re.compile(
    r"(?<!\d)(\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01]))[-.\s]?([1-9]\d{6})(?!\d)"
)
_DATE = re.compile(r"(?<!\d)\d{4}[.-]\d{2}[.-]\d{2}(?!\d)")
_ADDRESS = re.compile(
    r"(?:서울특별시|부산광역시|대구광역시|인천광역시|광주광역시|대전광역시|울산광역시"
    r"|세종특별자치시|제주특별자치도|[가-힣]{2,4}[시도])\s[가-힣]{1,5}[구군]\s"
    r"[가-힣]{1,6}(?:로|길)\s?\d{1,5}(?:[-~]\d{1,5})?"
)
_LABELED_ID = re.compile(
    r"(?:환자번호|차트번호|병록번호|등록번호|접수번호|처방전번호|검체번호|판독번호"
    r"|보험번호|청구번호|보험증권번호|사번|직원\s?ID)\s*[:：]?\s*[A-Za-z0-9-]{4,}"
)


def _luhn_ok(digits: str) -> bool:
    total = 0
    parity = len(digits) % 2
    for index, char in enumerate(digits):
        digit = int(char)
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


class S1GenericPiiAdapter(SystemAdapter):
    system_id = "S1_GENERIC_PII_BASELINE"

    _patterns: tuple[tuple[str, re.Pattern[str]], ...] = (
        ("EMAIL", _EMAIL),
        ("PHONE", _PHONE),
        ("NATIONAL_ID", _NATIONAL_ID),
        ("CREDIT_CARD", _LUHN),
        ("DATE", _DATE),
        ("ADDRESS", _ADDRESS),
        ("GENERIC_ID", _LABELED_ID),
    )

    def detect(self, text: str) -> list[Prediction]:
        found: list[Prediction] = []
        for type_name, pattern in self._patterns:
            for match in pattern.finditer(text):
                if type_name == "CREDIT_CARD":
                    digits = re.sub(r"\D", "", match.group(0))
                    if len(digits) < 13 or len(digits) > 19 or not _luhn_ok(digits):
                        continue
                found.append(Prediction(type=type_name, start=match.start(), end=match.end()))
        return _drop_overlaps(found)

    def transform(self, text: str, case_key: str) -> str:
        predictions = self.detect(text)
        counters: dict[str, int] = {}
        replaced = text
        for prediction in sorted(predictions, key=lambda item: item.start, reverse=True):
            counters[prediction.type] = counters.get(prediction.type, 0) + 1
            token = f"[GENERIC_{prediction.type}_{counters[prediction.type]:02d}]"
            replaced = replaced[: prediction.start] + token + replaced[prediction.end :]
        return replaced


def _drop_overlaps(predictions: list[Prediction]) -> list[Prediction]:
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
