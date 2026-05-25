from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from engine.src.contracts import Detection


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


class RegexDetector:
    _PERSON_TITLES = (
        "대표이사",
        "부사장",
        "전무",
        "상무",
        "본부장",
        "센터장",
        "실장",
        "팀장",
        "파트장",
        "그룹장",
        "리드",
        "책임",
        "수석",
        "선임",
        "연구원",
        "프로",
        "대표",
        "이사",
        "부장",
        "차장",
        "과장",
        "대리",
        "주임",
        "매니저",
        "PM",
        "PL",
        "님",
    )
    _ORG_SUFFIXES = (
        "솔루션즈",
        "시스템즈",
        "네트웍스",
        "네트워크",
        "모빌리티",
        "솔루션",
        "시스템",
        "캐피탈",
        "미디어",
        "에너지",
        "데이터",
        "바이오",
        "그룹",
        "금융",
        "전자",
        "기업",
        "회사",
        "산업",
        "증권",
        "보험",
        "카드",
        "제약",
        "건설",
        "물산",
        "상사",
        "통신",
        "테크",
    )
    _GENERIC_ORG_LABELS = {
        "회사",
        "기업",
        "전자",
        "금융",
        "보험",
        "증권",
        "카드",
        "캐피탈",
        "건설",
        "제약",
        "산업",
        "미디어",
        "데이터",
        "통신",
        "에너지",
        "대기업",
        "중견기업",
        "중소기업",
        "고객기업",
        "협력기업",
        "내부회사",
        "외부회사",
    }
    _GENERIC_PERSON_LABELS = {
        "브랜드",
        "고객",
        "사용자",
        "담당",
        "담당자",
        "대표자",
        "관리자",
        "운영팀",
        "보안팀",
        "개발팀",
        "사업팀",
        "영업팀",
        "재무팀",
        "인사팀",
        "법무팀",
        "마케팅팀",
        "서비스팀",
        "플랫폼팀",
        "디자인팀",
        "데이터팀",
        "연구팀",
        "사업부",
        "본부",
        "센터",
        "실",
        "팀",
    }
    _ENGLISH_PERSON_TITLES = (
        "Dr\\.",
        "Drs\\.",
        "Prof\\.",
        "Prof\\s+\\.",
        "Mr\\.",
        "Ms\\.",
        "Mrs\\.",
        "Miss\\.",
    )
    _ENGLISH_ORG_SUFFIXES = (
        "Inc\\.",
        "Corp\\.",
        "LLC",
        "Ltd\\.",
        "Co\\.",
        "Holdings",
        "Group",
        "Technologies",
        "Systems",
        "Solutions",
        "Enterprises",
        "Partners",
    )
    _ENGLISH_PERSON_NAME_INDICATORS = (
        "CEO", "CTO", "CFO", "COO", "CMO", "CIO", "VP",
        "Director", "Manager", "Lead", "Engineer", "Developer",
        "Designer", "Analyst", "Consultant", "Advisor", "Attorney",
    )
    _ENGLISH_GENERIC_WORDS = {
        "company", "corporation", "incorporated", "limited", "llc", "inc", "corp",
        "the company", "this company", "our company", "your company",
        "example", "sample", "test", "demo", "mock", "fake",
    }
    _STRICT_BARE_NAME_PARTICLES = (
        "에게",
        "에게는",
        "에게만",
        "님께",
        "씨에게",
        "씨는",
        "씨가",
        "씨를",
        "와 공유",
        "와 전달",
        "에게 공유",
        "에게 전달",
        "에게 보고",
        "에게 문의",
        "에게 회신",
        "에게 보내",
    )
    _STRICT_OBFUSCATED_EMAIL_PATTERN = re.compile(
        r"""
        [A-Z0-9._%+-]+\s+(?:at|AT)\s+[A-Z0-9.-]+
        (?:
            \s+(?:dot|DOT)\s+[A-Z]{2,}
        )+
        (?:\s+[A-Z]{2,})?
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    def __init__(self) -> None:
        self._patterns = self._build_patterns()

    def detect(
        self,
        content: str,
        content_type: str = "text",
        policy: str = "default",
    ) -> list[Detection]:
        if content_type != "text":
            return []

        return [
            Detection(
                type=candidate.type,
                label=candidate.label,
                start=candidate.start,
                end=candidate.end,
                score=self._score_for_policy(policy),
                note=self._note_for_policy(candidate.reason, policy),
            )
            for candidate in self._select_non_overlapping(self._find_candidates(content, policy))
        ]

    def _build_patterns(self) -> list[DetectionPattern]:
        person_titles = "|".join(sorted(self._PERSON_TITLES, key=len, reverse=True))
        org_suffixes = "|".join(sorted(self._ORG_SUFFIXES, key=len, reverse=True))
        english_person_titles = "|".join(sorted(self._ENGLISH_PERSON_TITLES, key=len, reverse=True))
        english_org_suffixes = "|".join(sorted(self._ENGLISH_ORG_SUFFIXES, key=len, reverse=True))
        english_person_indicators = "|".join(sorted(self._ENGLISH_PERSON_NAME_INDICATORS, key=len, reverse=True))

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
        ]

    def _find_candidates(self, content: str, policy: str) -> list[DetectionCandidate]:
        candidates: list[DetectionCandidate] = []
        for priority, pattern in enumerate(self._patterns):
            if not self._is_enabled_for_policy(pattern.type, policy):
                continue
            for match in pattern.regex.finditer(content):
                label = match.group(0).strip()
                if not self._is_valid_candidate(pattern.type, label):
                    continue
                candidates.append(
                    DetectionCandidate(
                        type=pattern.type,
                        label=label,
                        start=match.start(),
                        end=match.end(),
                        reason=pattern.reason,
                        priority=priority,
                    )
                )
        if policy == "strict_token":
            candidates.extend(self._find_strict_person_candidates(content, len(self._patterns)))
            candidates.extend(self._find_strict_obfuscated_email_candidates(content, len(self._patterns) + 1))
        return candidates

    def _is_valid_candidate(self, detection_type: str, label: str) -> bool:
        if detection_type == "ORG":
            return self._is_valid_org_candidate(label)
        if detection_type == "PERSON":
            return self._is_valid_person_candidate(label)
        return True

    def _is_valid_person_candidate(self, label: str) -> bool:
        if re.search(r"[A-Za-z]", label):
            return self._is_valid_english_person(label)
        normalized = re.sub(r"\s+", "", label)
        core_name = normalized

        for title in sorted(self._PERSON_TITLES, key=len, reverse=True):
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
        if core_name in self._GENERIC_PERSON_LABELS:
            return False
        return core_name.isalpha() and all("가" <= char <= "힣" for char in core_name)

    def _is_valid_org_candidate(self, label: str) -> bool:
        if re.search(r"[A-Za-z]", label):
            return self._is_valid_english_org(label)
        normalized = re.sub(r"\s+", "", label)
        if normalized in self._GENERIC_ORG_LABELS:
            return False

        if normalized.startswith(("주식회사", "(주)", "재단", "협회")):
            body = normalized
            for prefix in ("주식회사", "(주)", "재단", "협회"):
                if body.startswith(prefix):
                    body = body[len(prefix):]
                    break
            return len(body) >= 2

        return normalized not in self._ORG_SUFFIXES

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
        for generic in self._ENGLISH_GENERIC_WORDS:
            if label_lower == generic or label_lower.startswith("the " + generic):
                return False

        # Check if it has an org suffix
        org_suffixes_lower = {s.lower() for s in self._ENGLISH_ORG_SUFFIXES}
        for part in label.split():
            if part.rstrip(".").lower() in org_suffixes_lower:
                return True

        # If no suffix, reject common document/email phrases
        parts = label.split()
        if len(parts) >= 2:
            # Avoid document titles, email subjects, common phrases
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
            # Also reject if starts with common words
            for phrase in common_phrases:
                if label_lower.startswith(phrase + " ") or label_lower.startswith("re: " + phrase):
                    return False

        return False

    def _find_strict_person_candidates(self, content: str, priority: int) -> list[DetectionCandidate]:
        particles = "|".join(re.escape(item) for item in sorted(self._STRICT_BARE_NAME_PARTICLES, key=len, reverse=True))
        regex = re.compile(
            rf"(?<![가-힣])([가-힣]{{2,4}})(?=(?:{particles}))"
        )

        candidates: list[DetectionCandidate] = []
        for match in regex.finditer(content):
            label = match.group(1)
            if not self._is_valid_person_candidate(label):
                continue
            candidates.append(
                DetectionCandidate(
                    type="PERSON",
                    label=label,
                    start=match.start(1),
                    end=match.end(1),
                    reason="직함 없는 실명 문맥 보강",
                    priority=priority,
                )
            )
        return candidates

    def _find_strict_obfuscated_email_candidates(self, content: str, priority: int) -> list[DetectionCandidate]:
        candidates: list[DetectionCandidate] = []
        for match in self._STRICT_OBFUSCATED_EMAIL_PATTERN.finditer(content):
            label = match.group(0).strip()
            candidates.append(
                DetectionCandidate(
                    type="EMAIL",
                    label=label,
                    start=match.start(),
                    end=match.end(),
                    reason="변형 이메일 표기까지 보수적으로 보호",
                    priority=priority,
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
