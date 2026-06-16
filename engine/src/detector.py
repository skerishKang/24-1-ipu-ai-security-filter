from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable

from engine.src.contracts import Detection
from engine.src.detector_patterns import (
    ENGLISH_GENERIC_WORDS,
    ENGLISH_ORG_SUFFIXES,
    ENGLISH_PERSON_NAME_INDICATORS,
    ENGLISH_PERSON_TITLES,
    GENERIC_ORG_LABELS,
    GENERIC_PERSON_LABELS,
    ORG_SUFFIXES,
    PERSON_TITLES,
    STRICT_BARE_NAME_PARTICLES,
    STRICT_OBFUSCATED_EMAIL_PATTERN,
)

# Zero-width / format characters an attacker can insert to break regex matching.
_INVISIBLE_CODEPOINT_PATTERN = re.compile(
    "[​-‏﻿⁠­͏؜ᅟᅠ឴឵᠎]"
)


def _normalize_text(content: str) -> tuple[str, list[int]]:
    """Normalize Unicode while keeping a position map back to the original.

    Returns ``(normalized_text, position_map)`` where ``position_map[norm_pos]``
    is the original index of the character at ``norm_pos``. Characters that are
    invisible / format-only (zero-width space, soft hyphen, etc.) are dropped.
    Other characters are NFKC-normalized, so e.g. ``"０"`` (U+FF10) collapses
    to ``"0"`` and ligatures decompose.

    This defeats the most common evasion classes:
    * fullwidth digits splitting ``\d`` patterns
    * zero-width spaces splitting a PII token into fragments
    * soft hyphens and other invisible boundaries
    """
    if not content:
        return content, []

    normalized_chars: list[str] = []
    position_map: list[int] = []
    for orig_pos, ch in enumerate(content):
        if _INVISIBLE_CODEPOINT_PATTERN.match(ch):
            continue
        for sub_ch in unicodedata.normalize("NFKC", ch):
            position_map.append(orig_pos)
            normalized_chars.append(sub_ch)
    return "".join(normalized_chars), position_map


def _luhn_check(digits: str) -> bool:
    """Return True if ``digits`` passes the Luhn check (credit card / IMEI / etc.)."""
    if not digits or not digits.isdigit():
        return False
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


@dataclass(frozen=True)
class DetectionPattern:
    type: str
    regex: re.Pattern[str]
    reason: str


@dataclass(frozen=True)
class DetectionCandidate:
    type: str
    label: str
    start: int
    end: int
    reason: str
    priority: int

    # ``original_label`` is what the user originally typed (preserved even after
    # Unicode normalization that may have changed the match text). When labels
    # come from the original content (e.g. email regex) this is the same as
    # ``label``. Bare-format PII detections fall back to the normalized form.
    original_label: str = ""


class RegexDetector:
    def __init__(self) -> None:
        self._patterns = self._build_patterns()
        self._bare_format_patterns = self._build_bare_format_patterns()

    def detect(
        self,
        content: str,
        content_type: str = "text",
        policy: str = "default",
    ) -> list[Detection]:
        if content_type != "text":
            return []

        # Normalize once: NFKC + zero-width strip defeats the most common
        # evasion classes (fullwidth digits, zero-width space splits, soft hyphens).
        normalized, position_map = _normalize_text(content)

        return [
            Detection(
                type=candidate.type,
                label=candidate.original_label or candidate.label,
                start=candidate.start,
                end=candidate.end,
                score=self._score_for_policy(policy),
                note=self._note_for_policy(candidate.reason, policy),
            )
            for candidate in self._select_non_overlapping(
                self._find_candidates(normalized, position_map, content, policy)
            )
        ]

    def _build_patterns(self) -> list[DetectionPattern]:
        person_titles = "|".join(sorted(PERSON_TITLES, key=len, reverse=True))
        org_suffixes = "|".join(sorted(ORG_SUFFIXES, key=len, reverse=True))
        english_person_titles = "|".join(sorted(ENGLISH_PERSON_TITLES, key=len, reverse=True))
        english_org_suffixes = "|".join(sorted(ENGLISH_ORG_SUFFIXES, key=len, reverse=True))
        english_person_indicators = "|".join(sorted(ENGLISH_PERSON_NAME_INDICATORS, key=len, reverse=True))

        return [
            DetectionPattern(
                type="EMAIL",
                regex=re.compile(
                    r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
                    re.IGNORECASE,
                ),
                reason="외부 전송 시 이메일 주소 직접 노출 방지",
            ),
            DetectionPattern(
                type="PHONE",
                regex=re.compile(r"(?:01[0-9]|02|0[3-9][0-9])(?:[-.\s]?\d{3,4})(?:[-.\s]?\d{4})"),
                reason="연락처 직접 노출 방지",
            ),
            DetectionPattern(
                type="AMOUNT",
                regex=re.compile(
                    r"""
                    (?:
                        \d{1,3}(?:,\d{3})+(?:\.\d+)?\s*(?:원|천원|만원|천만원|억원|조원)
                        |
                        \d+(?:\.\d+)?\s*(?:조|억|천만|백만|십만|만|천|백|십)
                        (?:\s*\d+(?:\.\d+)?\s*(?:천만|백만|십만|万|천|백|십))*
                        \s*원?
                        |
                        [일이삼사오육칠팔구영공십백천만억조]+\s*
                        (?:[일이삼사오육칠팔구영공십백천만억조]+\s*)*
                        원
                    )
                    """,
                    re.VERBOSE,
                ),
                reason="계약 금액 및 재무 정보 보호",
            ),
            DetectionPattern(
                type="PERSON",
                regex=re.compile(
                    rf"""
                    (?:
                        [가-힣]{{2,4}}\s*(?:{person_titles})(?:님)?
                        |
                        (?:{person_titles})\s+[가-힣]{{2,4}}
                        |
                        (?:{english_person_titles})\s+[A-Z][a-z]{{1,15}}\s+[A-Z][a-z]{{1,15}}
                        |
                        [A-Z][a-z]{{1,15}}\s+[A-Z][a-z]{{1,15}}\s*,\s*(?:{english_person_indicators})
                    )
                    """,
                    re.VERBOSE | re.IGNORECASE,
                ),
                reason="담당자 실명 및 직함 보호",
            ),
            DetectionPattern(
                type="ORG",
                regex=re.compile(
                    rf"""
                    (?:
                        (?:주식회사|\(주\)|재단)\s*[가-힣A-Za-z0-9]+(?:\s*[가-힣A-Za-z0-9]+){{0,2}}
                        |
                        [가-힣A-Za-z0-9]{{2,}}(?:{org_suffixes})
                        |
                        (?:[A-Z][a-zA-Z0-9]{{1,25}}\s+){{1,3}}(?:{english_org_suffixes})
                    )
                    """,
                    re.VERBOSE | re.IGNORECASE,
                ),
                reason="조직명 보호",
            ),
            DetectionPattern(
                type="BUSINESS_REGISTRATION_NUMBER",
                regex=re.compile(
                    r"""
                    (?:
                        (?:사업자\s*(?:등록)?\s*번호|사업자등록번호|biz\s*reg\s*no\.?)\s*[:：]?\s*
                    )
                    (?:\d{3}-\d{2}-\d{5}|\d{10})
                    """,
                    re.IGNORECASE | re.VERBOSE,
                ),
                reason="사업자등록번호 직접 노출 방지",
            ),
            DetectionPattern(
                type="IP_ADDRESS",
                regex=re.compile(
                    r"\b(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\b"
                ),
                reason="내부 IP 및 네트워크 정보 보호",
            ),
            DetectionPattern(
                type="API_KEY",
                regex=re.compile(
                    r"""
                    (?:
                        (?:api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|bearer)\s*[:=]\s*
                        |
                        Authorization\s*:\s*Bearer\s+
                    )
                    [A-Za-z0-9_\-\.]{16,}
                    """,
                    re.IGNORECASE | re.VERBOSE,
                ),
                reason="API key 및 접근 토큰 보호",
            ),
            DetectionPattern(
                type="RESIDENT_REGISTRATION_NUMBER",
                regex=re.compile(
                    r"""
                    (?:
                        (?:주민\s*(?:등록)?\s*번호|주민등록번호|rrn)\s*[:：]?\s*
                    )
                    \d{6}[-\s]?\d{7}
                    """,
                    re.IGNORECASE | re.VERBOSE,
                ),
                reason="주민등록번호 직접 노출 방지",
            ),
            DetectionPattern(
                type="FOREIGN_REGISTRATION_NUMBER",
                regex=re.compile(
                    r"""
                    (?:
                        (?:외국인\s*(?:등록)?\s*번호|외국인등록번호|alien\s*registration\s*(?:number|no\.?)|arc)\s*[:：]?\s*
                    )
                    \d{6}[-\s]?\d{7}
                    """,
                    re.IGNORECASE | re.VERBOSE,
                ),
                reason="외국인등록번호 직접 노출 방지",
            ),
            DetectionPattern(
                type="CARD_NUMBER",
                regex=re.compile(
                    r"""
                    (?:
                        (?:카드\s*번호|신용카드\s*번호|credit\s*card|card\s*number)\s*[:：]?\s*
                    )
                    (?:\d{4}[-\s]?){3}\d{4}
                    """,
                    re.IGNORECASE | re.VERBOSE,
                ),
                reason="카드번호 직접 노출 방지",
            ),
            DetectionPattern(
                type="ACCOUNT_NUMBER",
                regex=re.compile(
                    r"""
                    (?:
                        (?:계좌\s*번호|입금\s*계좌|bank\s*account|account\s*number)\s*[:：]?\s*
                    )
                    [0-9]{2,6}(?:[-\s]?[0-9]{2,6}){2,5}
                    """,
                    re.IGNORECASE | re.VERBOSE,
                ),
                reason="계좌번호 직접 노출 방지",
            ),
            DetectionPattern(
                type="VEHICLE_REGISTRATION_NUMBER",
                regex=re.compile(
                    r"""
                    (?:
                        (?:차량\s*번호|자동차\s*번호|번호판|license\s*plate|vehicle\s*(?:registration\s*)?number)\s*[:：]?\s*
                    )
                    (?:\d{2,3}[가-힣]\s?\d{4})
                    """,
                    re.IGNORECASE | re.VERBOSE,
                ),
                reason="차량번호 직접 노출 방지",
            ),
        ]

    def _build_bare_format_patterns(self) -> list[DetectionPattern]:
        """Patterns that catch PII presented *without* a Korean/English label.

        These are noisier (false-positive risk) so they are only consulted when
        the policy is ``strict_token`` or ``local_rewrite``. They protect against
        the obvious bypass: an attacker drops the label and ships the raw value.

        Order matters: more specific shapes run first so the non-overlap
        selection picks the right type when two patterns could match the same
        span (e.g. Korean RRN vs Foreign RRN).
        """
        return [
            # Foreign registration number: same shape as RRN, post-hyphen digit
            # 5-8 indicates a foreign resident. Tried first so it wins over the
            # generic RRN pattern.
            DetectionPattern(
                type="FOREIGN_REGISTRATION_NUMBER",
                regex=re.compile(
                    r"(?<!\d)(?:\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01]))"
                    r"[-\s][5678]\d{6}(?!\d)"
                ),
                reason="라벨 없는 외국인등록번호 형식",
            ),
            # Resident registration number: post-hyphen digit 1-4 (1900-1999) or
            # 9 (1800-1899 / 2000+ Korean nationals). Foreign-resident 5-8 range
            # is excluded here and handled by the FOREIGN pattern above.
            DetectionPattern(
                type="RESIDENT_REGISTRATION_NUMBER",
                regex=re.compile(
                    r"(?<!\d)(?:\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01]))"
                    r"[-\s][12349]\d{6}(?!\d)"
                ),
                reason="라벨 없는 주민등록번호 형식",
            ),
            # Credit card numbers: 13-19 digit groups, validated by Luhn.
            DetectionPattern(
                type="CARD_NUMBER",
                regex=re.compile(
                    r"(?<!\d)(?:\d{4}[-\s]\d{4}[-\s]\d{4}[-\s]\d{4}"
                    r"|\d{4}[-\s]\d{6}[-\s]\d{4,5}"
                    r"|\d{15,19})(?!\d)"
                ),
                reason="라벨 없는 카드번호 형식",
            ),
            # API key: prefix ``sk-``, ``pk-``, ``gho_`` (GitHub), ``xoxb-`` (Slack),
            # or AWS access key pattern.
            DetectionPattern(
                type="API_KEY",
                regex=re.compile(
                    r"(?<![A-Za-z0-9])(?:sk-[A-Za-z0-9]{20,}|pk-[A-Za-z0-9]{20,}"
                    r"|gho_[A-Za-z0-9]{30,}|xox[baprs]-[A-Za-z0-9-]{20,}"
                    r"|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,})(?![\w-])"
                ),
                reason="라벨 없는 API 키 형식",
            ),
            # Bare-format account number: 3+ groups of 2-6 digits separated by
            # hyphens or spaces. The labelled pattern requires a Korean/English
            # prefix; this catches the obvious "drop the label" bypass.
            DetectionPattern(
                type="ACCOUNT_NUMBER",
                regex=re.compile(
                    r"(?<!\d)\d{2,6}[-\s]\d{2,6}[-\s]\d{2,6}(?:\d{2,6})?(?!\d)"
                ),
                reason="라벨 없는 계좌번호 형식",
            ),
        ]

    def _find_candidates(
        self,
        normalized: str,
        position_map: list[int],
        original: str,
        policy: str,
    ) -> list[DetectionCandidate]:
        candidates: list[DetectionCandidate] = []
        for priority, pattern in enumerate(self._patterns):
            if not self._is_enabled_for_policy(pattern.type, policy):
                continue
            for match in pattern.regex.finditer(normalized):
                label = match.group(0).strip()
                if not self._is_valid_candidate(pattern.type, label):
                    continue
                orig_start, orig_end = self._remap_span(
                    position_map, match.start(), match.end()
                )
                original_label = original[orig_start:orig_end]
                if not self._is_valid_candidate(pattern.type, original_label):
                    continue
                candidates.append(
                    DetectionCandidate(
                        type=pattern.type,
                        label=label,
                        start=orig_start,
                        end=orig_end,
                        reason=pattern.reason,
                        priority=priority,
                        original_label=original_label,
                    )
                )
        if policy in {"strict_token", "local_rewrite"}:
            candidates.extend(
                self._find_strict_person_candidates(
                    normalized, position_map, original, len(self._patterns)
                )
            )
            candidates.extend(
                self._find_strict_obfuscated_email_candidates(
                    normalized, position_map, original, len(self._patterns) + 1
                )
            )
            candidates.extend(
                self._find_bare_format_candidates(
                    normalized, position_map, original, len(self._patterns) + 2
                )
            )
        return candidates

    def _remap_span(
        self,
        position_map: list[int],
        norm_start: int,
        norm_end: int,
    ) -> tuple[int, int]:
        """Map a normalized-text span back to the original text span.

        ``norm_end`` is exclusive. We expand to include the last mapped character
        so that decomposition-expanded matches (e.g. NFKC that split one char
        into many) still recover the full original span.
        """
        if not position_map:
            return norm_start, norm_end
        orig_start = position_map[norm_start]
        last_norm_index = norm_end - 1
        if last_norm_index >= len(position_map):
            last_norm_index = len(position_map) - 1
        orig_end = position_map[last_norm_index] + 1
        return orig_start, orig_end

    def _is_valid_candidate(self, detection_type: str, label: str) -> bool:
        if detection_type == "ORG":
            return self._is_valid_org_candidate(label)
        if detection_type == "PERSON":
            return self._is_valid_person_candidate(label)
        if detection_type == "CARD_NUMBER":
            digits = re.sub(r"\D", "", label)
            return 13 <= len(digits) <= 19 and _luhn_check(digits)
        return True

    def _is_valid_person_candidate(self, label: str) -> bool:
        if re.search(r"[A-Za-z]", label):
            return self._is_valid_english_person(label)
        normalized = re.sub(r"\s+", "", label)
        core_name = normalized

        for title in sorted(PERSON_TITLES, key=len, reverse=True):
            if core_name.endswith(title):
                core_name = core_name[: -len(title)]
                break
            if core_name.startswith(title):
                core_name = core_name[len(title):]
                break

        for suffix in ("님", "씨"):
            if core_name.endswith(suffix):
                core_name = core_name[: -len(suffix)]

        core_name = core_name.strip()
        if len(core_name) < 2 or len(core_name) > 4:
            return False
        if core_name in GENERIC_PERSON_LABELS:
            return False
        return core_name.isalpha() and all("가" <= char <= "힣" for char in core_name)

    def _is_valid_org_candidate(self, label: str) -> bool:
        if re.search(r"[A-Za-z]", label):
            return self._is_valid_english_org(label)
        normalized = re.sub(r"\s+", "", label)
        if normalized in GENERIC_ORG_LABELS:
            return False

        if normalized.startswith(("주식회사", "(주)", "재단", "협회")):
            body = normalized
            for prefix in ("주식회사", "(주)", "재단", "협회"):
                if body.startswith(prefix):
                    body = body[len(prefix):]
                    break
            return len(body) >= 2

        return normalized not in ORG_SUFFIXES

    def _is_valid_english_person(self, label: str) -> bool:
        if not label:
            return False
        label_clean = label.strip()
        if "," in label_clean:
            label_clean = label_clean.split(",")[0].strip()
        for title in ("Dr.", "Drs.", "Prof.", "Mr.", "Ms.", "Mrs.", "Miss."):
            label_clean = label_clean.replace(title, "").strip()
        parts = label_clean.split()
        if len(parts) != 2:
            return False
        first, last = parts
        if not (first[0].isupper() and first[1:].islower() and last[0].isupper() and last[1:].islower()):
            return False
        return True

    def _is_valid_english_org(self, label: str) -> bool:
        if not label:
            return False
        label_lower = label.lower().strip()

        # Reject generic words
        for generic in ENGLISH_GENERIC_WORDS:
            if label_lower == generic or label_lower.startswith("the " + generic):
                return False

        # Check if it has an org suffix
        org_suffixes_lower = {s.lower() for s in ENGLISH_ORG_SUFFIXES}
        for part in label.split():
            if part.rstrip(".").lower() in org_suffixes_lower:
                return True

        # If no suffix, reject common document/email phrases
        parts = label.split()
        if len(parts) >= 2:
            common_phrases = {
                "project report", "meeting notes", "meeting summary", "weekly update",
                "quarterly report", "annual report", "sales report", "financial report",
                "status update", "progress report", "action items", "todo list",
                "project plan", "project proposal", "project schedule", "timeline",
                "email subject", "re email", "fw email", "fwd email",
                "dear sir", "dear madam", "dear team", "dear all",
                "kind regards", "best regards", "warm regards",
                "thank you", "thanks for", "thanks regarding",
                "please find", "please review", "please see",
                "attached is", "attached please", "attachment",
                "follow up", "following up", "followup",
                "as discussed", "as agreed", "as requested",
                "let know", "feel free", "dont hesitate",
            }
            if label_lower in common_phrases:
                return False
            for phrase in common_phrases:
                if label_lower.startswith(phrase + " ") or label_lower.startswith("re: " + phrase):
                    return False

        return False

    def _find_strict_person_candidates(
        self,
        normalized: str,
        position_map: list[int],
        original: str,
        priority: int,
    ) -> list[DetectionCandidate]:
        particles = "|".join(re.escape(item) for item in sorted(STRICT_BARE_NAME_PARTICLES, key=len, reverse=True))
        regex = re.compile(
            rf"(?<![가-힣])([가-힣]{{2,4}})(?=(?:{particles}))"
        )

        candidates: list[DetectionCandidate] = []
        for match in regex.finditer(normalized):
            label = match.group(1)
            if not self._is_valid_person_candidate(label):
                continue
            orig_start, orig_end = self._remap_span(position_map, match.start(1), match.end(1))
            original_label = original[orig_start:orig_end]
            if not self._is_valid_person_candidate(original_label):
                continue
            candidates.append(
                DetectionCandidate(
                    type="PERSON",
                    label=label,
                    start=orig_start,
                    end=orig_end,
                    reason="직함 없는 실명 문맥 보강",
                    priority=priority,
                    original_label=original_label,
                )
            )
        return candidates

    def _find_strict_obfuscated_email_candidates(
        self,
        normalized: str,
        position_map: list[int],
        original: str,
        priority: int,
    ) -> list[DetectionCandidate]:
        candidates: list[DetectionCandidate] = []
        for match in STRICT_OBFUSCATED_EMAIL_PATTERN.finditer(normalized):
            label = match.group(0).strip()
            orig_start, orig_end = self._remap_span(position_map, match.start(), match.end())
            original_label = original[orig_start:orig_end]
            candidates.append(
                DetectionCandidate(
                    type="EMAIL",
                    label=label,
                    start=orig_start,
                    end=orig_end,
                    reason="변형 이메일 표기까지 보수적으로 보호",
                    priority=priority,
                    original_label=original_label,
                )
            )
        return candidates

    def _find_bare_format_candidates(
        self,
        normalized: str,
        position_map: list[int],
        original: str,
        priority: int,
    ) -> list[DetectionCandidate]:
        candidates: list[DetectionCandidate] = []
        for pattern in self._bare_format_patterns:
            for match in pattern.regex.finditer(normalized):
                label = match.group(0)
                if not self._is_valid_candidate(pattern.type, label):
                    continue
                orig_start, orig_end = self._remap_span(position_map, match.start(), match.end())
                original_label = original[orig_start:orig_end]
                if not self._is_valid_candidate(pattern.type, original_label):
                    continue
                candidates.append(
                    DetectionCandidate(
                        type=pattern.type,
                        label=label,
                        start=orig_start,
                        end=orig_end,
                        reason=pattern.reason,
                        priority=priority,
                        original_label=original_label,
                    )
                )
        return candidates

    def _select_non_overlapping(
        self,
        candidates: Iterable[DetectionCandidate],
    ) -> list[DetectionCandidate]:
        selected: list[DetectionCandidate] = []
        for candidate in sorted(
            candidates,
            key=lambda item: (item.start, -(item.end - item.start), item.priority),
        ):
            if any(self._overlaps(candidate, existing) for existing in selected):
                continue
            selected.append(candidate)
        return sorted(selected, key=lambda item: (item.start, item.end))

    def _overlaps(self, left: DetectionCandidate, right: DetectionCandidate) -> bool:
        return left.start < right.end and right.start < left.end

    def _is_enabled_for_policy(self, detection_type: str, policy: str) -> bool:
        if policy == "strict_token" or policy == "local_rewrite":
            return True
        return detection_type in {"EMAIL", "PHONE", "PERSON", "ORG"}

    def _score_for_policy(self, policy: str) -> float:
        if policy == "strict_token":
            return 0.93
        return 0.88

    def _note_for_policy(self, reason: str, policy: str) -> str:
        if policy == "strict_token":
            return f"{reason} · policy=strict_token · scope=all_patterns"
        return f"{reason} · policy=default · scope=core_patterns"
