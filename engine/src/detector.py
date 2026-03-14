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

        return [
            DetectionPattern(
                type="EMAIL",
                regex=re.compile(
                    r"""
                    (?:
                        [A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}
                        |
                        [A-Z0-9._%+-]+\s+(?:at|AT)\s+[A-Z0-9.-]+
                        (?:
                            \s+(?:dot|DOT)\s+[A-Z]{2,}
                        )+
                        (?:\s+[A-Z]{2,})?
                    )
                    """,
                    re.IGNORECASE | re.VERBOSE,
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
                        (?:\s*\d+(?:\.\d+)?\s*(?:천만|백만|십만|만|천|백|십))*
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
                    )
                    """,
                    re.VERBOSE,
                ),
                reason="담당자 실명 및 직함 보호",
            ),
            DetectionPattern(
                type="ORG",
                regex=re.compile(
                    rf"""
                    (?:
                        (?:주식회사|\(주\)|㈜)\s*[가-힣A-Za-z0-9]+(?:\s*[가-힣A-Za-z0-9]+){{0,2}}
                        |
                        [가-힣A-Za-z0-9]{{2,}}(?:{org_suffixes})
                    )
                    """,
                    re.VERBOSE,
                ),
                reason="조직명 보호",
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
        return candidates

    def _is_valid_candidate(self, detection_type: str, label: str) -> bool:
        if detection_type == "ORG":
            return self._is_valid_org_candidate(label)
        if detection_type == "PERSON":
            return self._is_valid_person_candidate(label)
        return True

    def _is_valid_org_candidate(self, label: str) -> bool:
        normalized = re.sub(r"\s+", "", label)
        if normalized in self._GENERIC_ORG_LABELS:
            return False

        if normalized.startswith(("주식회사", "(주)", "㈜")):
            body = normalized
            for prefix in ("주식회사", "(주)", "㈜"):
                if body.startswith(prefix):
                    body = body[len(prefix):]
                    break
            return len(body) >= 2

        return normalized not in self._ORG_SUFFIXES

    def _is_valid_person_candidate(self, label: str) -> bool:
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
        if policy == "strict_token":
            return True
        return detection_type in {"EMAIL", "PHONE", "PERSON"}

    def _score_for_policy(self, policy: str) -> float:
        if policy == "strict_token":
            return 0.93
        return 0.88

    def _note_for_policy(self, reason: str, policy: str) -> str:
        if policy == "strict_token":
            return f"{reason} · policy=strict_token · scope=all_patterns"
        return f"{reason} · policy=default · scope=core_patterns"
