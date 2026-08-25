"""Deterministic adversarial variant transforms for the B63 R0 corpus.

Each transform produces a list of non-overlapping text edits over a base case.
A single engine applies the edits, rebuilds the text, and remaps PHI and
utility spans deterministically. No randomness is used anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass

from benchmark.corpus.schema import BenchmarkCase, Span, UtilitySpan

ADVERSARIAL_KINDS: tuple[str, ...] = (
    "fullwidth_digits",
    "zero_width_chars",
    "soft_hyphen",
    "whitespace_split",
    "ocr_zero_O",
    "ocr_one_l",
    "separator_variants",
    "ko_en_mixed",
    "abbreviation",
    "typo_noise",
    "pdf_linebreak_noise",
    "table_noise",
)

Edit = tuple[int, int, str]


@dataclass(frozen=True)
class _RemappedCase:
    text: str
    spans: tuple[Span, ...]
    utility_spans: tuple[UtilitySpan, ...]


def _fullwidth(interior: str) -> str:
    out: list[str] = []
    for ch in interior:
        code = ord(ch)
        if 0x21 <= code <= 0x7E:
            out.append(chr(code + 0xFEE0))
        else:
            out.append(ch)
    return "".join(out)


def _split_digits(interior: str) -> str:
    out: list[str] = []
    chars = list(interior)
    digit_run = 0
    for idx, ch in enumerate(chars):
        out.append(ch)
        if ch.isdigit():
            digit_run += 1
            nxt = chars[idx + 1] if idx + 1 < len(chars) else ""
            if nxt.isdigit() and digit_run % 3 == 0:
                out.append(" ")
        else:
            digit_run = 0
    return "".join(out)


def _separator_variant(interior: str) -> str:
    if "-" in interior:
        return interior.replace("-", ".", 1)
    if "." in interior:
        return interior.replace(".", "-", 1)
    chars = list(interior)
    mid = max(1, len(chars) // 2)
    if all(ch.isdigit() or ch.isalpha() for ch in chars) and len(chars) >= 4:
        return "".join(chars[:mid]) + " " + "".join(chars[mid:])
    return interior


def _interior_edit(kind: str, interior: str) -> str:
    if kind == "fullwidth_digits":
        return _fullwidth(interior)
    if kind == "zero_width_chars":
        return "\u200b".join(interior)
    if kind == "soft_hyphen":
        return "\u00ad".join(interior)
    if kind == "whitespace_split":
        return _split_digits(interior)
    if kind == "ocr_zero_O":
        return interior.replace("0", "O")
    if kind == "ocr_one_l":
        return interior.replace("1", "l")
    if kind == "separator_variants":
        return _separator_variant(interior)
    raise ValueError(f"unknown interior transform: {kind}")


_INTERIOR_KINDS = frozenset(
    {
        "fullwidth_digits",
        "zero_width_chars",
        "soft_hyphen",
        "whitespace_split",
        "ocr_zero_O",
        "ocr_one_l",
        "separator_variants",
    }
)

_TYPO_SWAPS = (
    ("확인 완료", "확인 완 료"),
    ("기록", "기록."),
    ("환자", "환 자"),
    ("오늘", "오 늘"),
    ("병동", "병 동"),
)

_PDF_BREAK_MARKERS = ("이다.", "했다.", "한다.", "습니다.", ".")
_KO_EN_SUFFIX = " (Contact updated via portal, verify patient identity before reply.)\n"
_TABLE_PREFIX = "| 기록 |\n| "
_TABLE_SUFFIX = " |\n"


def _edits_for(case: BenchmarkCase, kind: str) -> list[Edit]:
    if kind in _INTERIOR_KINDS:
        return [(span.start, span.end, _interior_edit(kind, case.text[span.start : span.end])) for span in case.spans]

    text = case.text
    if kind == "ko_en_mixed":
        return [(len(text), len(text), _KO_EN_SUFFIX)]
    if kind == "table_noise":
        return [
            (0, 0, _TABLE_PREFIX),
            (len(text), len(text), _TABLE_SUFFIX),
        ]
    if kind == "pdf_linebreak_noise":
        pos = _break_position(text, case)
        return [(pos, pos, "\n")]
    if kind == "typo_noise":
        target = _typo_target(text, case)
        if target is None:
            return []
        pos, original, replacement = target
        return [(pos, pos + len(original), replacement)]
    if kind == "abbreviation":
        return _abbreviation_edits(case)
    raise ValueError(f"unknown adversarial kind: {kind}")


def _break_position(text: str, case: BenchmarkCase) -> int:
    for marker in ("이다.", "했다.", "한다.", "습니다."):
        search_from = 0
        while True:
            pos = text.find(marker, search_from)
            if pos < 0:
                break
            end = pos + len(marker)
            if not any(span.start < end and pos < span.end for span in case.spans):
                return end
            search_from = pos + 1
    fallback = max(0, len(text) // 2)
    while any(span.start < fallback < span.end for span in case.spans):
        fallback += 1
    return min(fallback, len(text))


def _typo_target(text: str, case: BenchmarkCase) -> tuple[int, str, str] | None:
    for original, replacement in _TYPO_SWAPS:
        search_from = 0
        while True:
            pos = text.find(original, search_from)
            if pos < 0:
                break
            end = pos + len(original)
            if not any(span.start < end and pos < span.end for span in case.spans):
                return (pos, original, replacement)
            search_from = pos + 1
    return None


_ABBREVIATIONS = (
    ("대학교병원", "대병원"),
    ("종합병원", "병원"),
    ("의료원", "의원"),
)


def _abbreviation_edits(case: BenchmarkCase) -> list[Edit]:
    edits: list[Edit] = []
    for span in case.spans:
        if span.label != "HOSPITAL_NAME":
            continue
        interior = case.text[span.start : span.end]
        for original, abbreviated in _ABBREVIATIONS:
            if original in interior:
                edits.append(
                    (span.start, span.end, interior.replace(original, abbreviated))
                )
                break
    return edits


def apply_variant(case: BenchmarkCase, kind: str) -> BenchmarkCase:
    """Apply one deterministic adversarial transform to a base case."""
    edits = _edits_for(case, kind)
    remapped = _transform_case(case, edits)
    return BenchmarkCase(
        case_id=f"adv-{kind}-{case.case_id}",
        subset=case.subset,
        text=remapped.text,
        spans=remapped.spans,
        utility_spans=remapped.utility_spans,
        relations=case.relations,
        event_order_markers=case.event_order_markers,
        has_quasi_combination=case.has_quasi_combination,
        variant_kind=kind,
        parent_case_id=case.case_id,
        template_id=case.template_id,
        synthetic=True,
    )


def _transform_case(case: BenchmarkCase, edits: list[Edit]) -> _RemappedCase:
    ordered = sorted(edits, key=lambda item: (item[0], item[1]))
    for (s1, e1, _), (s2, e2, _) in zip(ordered, ordered[1:]):
        if s2 < e1:
            raise ValueError("overlapping edits are not supported")

    parts: list[str] = []
    boundaries: list[tuple[int, int, int, int]] = []
    cursor = 0
    for start, end, replacement in ordered:
        parts.append(case.text[cursor:start])
        new_start = sum(len(part) for part in parts)
        parts.append(replacement)
        boundaries.append((start, end, new_start, new_start + len(replacement)))
        cursor = end
    parts.append(case.text[cursor:])
    new_text = "".join(parts)

    def shift(position: int) -> int:
        moved = position
        for start, end, new_start, new_end in boundaries:
            if end <= position:
                moved += (new_end - new_start) - (end - start)
        return moved

    def remap_phi(span: Span) -> Span:
        for start, end, new_start, new_end in boundaries:
            if span.start == start and span.end == end:
                return Span(new_start, new_end, span.label, span.span_id)
        return Span(shift(span.start), shift(span.end), span.label, span.span_id)

    def remap_utility(span: UtilitySpan) -> UtilitySpan:
        return UtilitySpan(
            shift(span.start), shift(span.end), span.utility_type, span.span_id
        )

    return _RemappedCase(
        text=new_text,
        spans=tuple(remap_phi(span) for span in case.spans),
        utility_spans=tuple(remap_utility(span) for span in case.utility_spans),
    )


def build_adversarial_cases(base_cases: list[BenchmarkCase]) -> list[BenchmarkCase]:
    """Derive one deterministic adversarial case per PHI-bearing base case.

    Transform kind rotates through ADVERSARIAL_KINDS by base-case index so every
    kind is exercised without randomness.
    """
    variants: list[BenchmarkCase] = []
    phi_bearing = [case for case in base_cases if case.spans]
    for offset, case in enumerate(phi_bearing):
        kind = ADVERSARIAL_KINDS[offset % len(ADVERSARIAL_KINDS)]
        variants.append(apply_variant(case, kind))
    return variants
