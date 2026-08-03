from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol
from urllib import request
from urllib.parse import urlparse

from engine.src.contracts import Detection, Replacement
from engine.src.detector import RegexDetector

_LOCAL_REWRITE_HOSTS = {"localhost", "127.0.0.1", "::1"}
_HIGH_ENTROPY_TOKEN_PATTERN = re.compile(r"\b[A-Za-z0-9_\-.]{20,}\b")


class OllamaClient(Protocol):
    def generate(self, *, model: str, system: str, prompt: str) -> str: ...


class OllamaHTTPClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        *,
        allow_remote: bool = False,
    ) -> None:
        self._validate_base_url(base_url, allow_remote=allow_remote)
        self._endpoint = f"{base_url.rstrip('/')}/api/generate"

    def generate(self, *, model: str, system: str, prompt: str) -> str:
        payload = json.dumps(
            {
                "model": model,
                "system": system,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            }
        ).encode("utf-8")
        req = request.Request(
            self._endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=90) as response:
            body = json.loads(response.read().decode("utf-8"))
        return str(body.get("response", ""))

    def _validate_base_url(self, base_url: str, *, allow_remote: bool) -> None:
        parsed = urlparse(base_url)
        hostname = (parsed.hostname or "").lower()
        if not parsed.scheme or not hostname:
            raise ValueError("invalid_ollama_base_url")
        if allow_remote:
            return
        if hostname not in _LOCAL_REWRITE_HOSTS:
            raise ValueError("remote_ollama_base_url_not_allowed")


@dataclass(frozen=True)
class LocalRewriteResult:
    replacements: list[Replacement]
    used_fallback: bool
    raw_response: str


class LocalRewriter:
    engine_name: str = "deterministic"


class OllamaLocalRewriter(LocalRewriter):
    engine_name: str = "ollama"
    SYSTEM_PROMPT = (
        "You rewrite sensitive spans into safe Korean business placeholders. "
        "Keep meaning and document utility. Never repeat original sensitive text. "
        "Return JSON only."
    )

    def __init__(
        self,
        client: OllamaClient | None = None,
        model: str = "qwen2.5:7b-instruct",
        base_url: str = "http://127.0.0.1:11434",
        allow_remote: bool = False,
    ) -> None:
        self._client = client or OllamaHTTPClient(base_url=base_url, allow_remote=allow_remote)
        self._model = model
        self._output_detector = RegexDetector()

    def rewrite(self, content: str, detections: list[Detection]) -> LocalRewriteResult:
        if not detections:
            return LocalRewriteResult(replacements=[], used_fallback=False, raw_response="")

        prompt = self._build_prompt(content, detections)
        raw_response = ""
        try:
            raw_response = self._client.generate(
                model=self._model,
                system=self.SYSTEM_PROMPT,
                prompt=prompt,
            )
            replacements = self._parse_response(raw_response, detections)
            return LocalRewriteResult(
                replacements=replacements,
                used_fallback=False,
                raw_response=raw_response,
            )
        except TimeoutError:
            return LocalRewriteResult(
                replacements=self._fallback_replacements(detections),
                used_fallback=True,
                raw_response=raw_response,
            )
        except json.JSONDecodeError:
            return LocalRewriteResult(
                replacements=self._fallback_replacements(detections),
                used_fallback=True,
                raw_response=raw_response,
            )
        except Exception:
            return LocalRewriteResult(
                replacements=self._fallback_replacements(detections),
                used_fallback=True,
                raw_response=raw_response,
            )

    def _build_prompt(self, content: str, detections: list[Detection]) -> str:
        # We deliberately do NOT include the original content or original labels
        # in the prompt. Only the position and the detection type travel to
        # the local LLM. This protects the original PII even if the Ollama
        # host is misconfigured, exposed on a non-loopback interface, or
        # compromised.
        lines = [
            "Generate a safe Korean business placeholder for each detected span.",
            "Rules:",
            "1. The original text is not provided. Use the type label to choose",
            "   a generic, natural-sounding Korean placeholder (e.g. 담당자 N for",
            "   PERSON, 이메일 주소 N for EMAIL, 비공개 금액 N for AMOUNT).",
            "2. Do not invent values that look like the original format.",
            "3. Keep each replacement short and self-contained.",
            '4. Return JSON only: {"replacements": [{"index": 1, "replacement": "...", "reason": "..."}]}',
            "",
            "Detections:",
        ]
        for index, detection in enumerate(detections, start=1):
            lines.append(
                f"- index={index} type={detection.type} position=({detection.start},{detection.end})"
            )
        # ``content`` is intentionally left unused in the prompt body.
        return "\n".join(lines)

    def _parse_response(self, raw_response: str, detections: list[Detection]) -> list[Replacement]:
        parsed = json.loads(raw_response)
        items = parsed["replacements"]
        if not isinstance(items, list) or len(items) != len(detections):
            raise ValueError("replacement_count_mismatch")

        replacements: list[Replacement] = []
        for index, (item, detection) in enumerate(zip(items, detections, strict=True), start=1):
            replacement = str(item["replacement"]).strip()
            reason = str(item.get("reason", "local_rewrite")).strip() or "local_rewrite"
            if not replacement:
                raise ValueError("invalid_replacement")
            if self._contains_sensitive_output(replacement, reason, detection):
                raise ValueError("unsafe_replacement_output")
            replacement = self._ensure_stable_replacement_text(replacement, detection.type, index)
            replacements.append(
                Replacement(
                    type=detection.type,
                    original=detection.label,
                    replaced=replacement,
                    reason="local_rewrite",
                )
            )
        return replacements

    def _contains_sensitive_output(self, replacement: str, reason: str, detection: Detection) -> bool:
        values_to_check = (replacement, reason)
        original = detection.label.strip()
        # NFKC-normalize both sides so confusables (e.g. Greek Ο for 0,
        # fullwidth digits) cannot bypass the substring check.
        normalized_original = self._normalize_sensitive_text(original)

        for value in values_to_check:
            if not value:
                continue
            if original and original.lower() in value.lower():
                return True
            normalized_value = self._normalize_sensitive_text(value)
            if normalized_original and len(normalized_original) >= 3 and normalized_original in normalized_value:
                return True

        # Hard gate: re-detect the replacement text under strict_token. If
        # the LLM emitted a value that *looks like* the original even after
        # normalization, treat it as unsafe and fall back. The fallback path
        # uses a generic Korean placeholder that the detector cannot mistake
        # for the original.
        if self._output_detector.detect(replacement, content_type="text", policy="strict_token"):
            return True
        return self._looks_like_sensitive_token(replacement)

    def _looks_like_sensitive_token(self, value: str) -> bool:
        return any(
            re.search(r"[A-Za-z]", token) and re.search(r"\d", token)
            for token in _HIGH_ENTROPY_TOKEN_PATTERN.findall(value)
        )

    def _normalize_sensitive_text(self, value: str) -> str:
        import unicodedata
        normalized = unicodedata.normalize("NFKC", value)
        return re.sub(r"[^0-9A-Za-z가-힣]+", "", normalized).lower()

    def _fallback_replacements(self, detections: list[Detection]) -> list[Replacement]:
        counters: dict[str, int] = {}
        replacements: list[Replacement] = []
        for detection in detections:
            counters[detection.type] = counters.get(detection.type, 0) + 1
            replacements.append(
                Replacement(
                    type=detection.type,
                    original=detection.label,
                    replaced=self._fallback_text(detection.type, counters[detection.type]),
                    reason="fallback_local_rewrite",
                )
            )
        return replacements

    def _fallback_text(self, detection_type: str, index: int) -> str:
        if detection_type == "PERSON":
            return f"담당자 {index}"
        if detection_type == "ORG":
            return f"A사 {index}"
        if detection_type == "EMAIL":
            return f"이메일 주소 {index}"
        if detection_type == "PHONE":
            return f"연락처 {index}"
        if detection_type == "AMOUNT":
            return f"비공개 금액 {index}"
        if detection_type == "API_KEY":
            return f"API 키 {index}"
        if detection_type == "IP_ADDRESS":
            return f"IP 주소 {index}"
        if detection_type == "BUSINESS_REGISTRATION_NUMBER":
            return f"사업자등록번호 {index}"
        if detection_type == "RESIDENT_REGISTRATION_NUMBER":
            return f"주민등록번호 {index}"
        if detection_type == "FOREIGN_REGISTRATION_NUMBER":
            return f"외국인등록번호 {index}"
        if detection_type == "CARD_NUMBER":
            return f"카드번호 {index}"
        if detection_type == "ACCOUNT_NUMBER":
            return f"계좌번호 {index}"
        if detection_type == "VEHICLE_REGISTRATION_NUMBER":
            return f"차량번호 {index}"
        return f"비식별 정보 {index}"

    def _ensure_stable_replacement_text(self, replacement: str, detection_type: str, index: int) -> str:
        if str(index) in replacement:
            return replacement
        if detection_type == "PERSON":
            return f"{replacement} {index}"
        if detection_type == "ORG":
            return f"{replacement} {index}"
        if detection_type == "EMAIL":
            return f"{replacement} {index}"
        if detection_type == "PHONE":
            return f"{replacement} {index}"
        if detection_type == "AMOUNT":
            return f"{replacement} {index}"
        return f"{replacement} {index}"


class PlaceholderLocalRewriter(LocalRewriter):
    """Fallback rewriter when Ollama is not available."""

    engine_name = "deterministic"

    def rewrite(self, content: str, detections: list[Detection]) -> LocalRewriteResult:
        if not detections:
            return LocalRewriteResult(replacements=[], used_fallback=True, raw_response="")

        replacements = self._fallback_replacements(detections)
        return LocalRewriteResult(
            replacements=replacements,
            used_fallback=True,
            raw_response="",
        )

    def _fallback_replacements(self, detections: list[Detection]) -> list[Replacement]:
        counters: dict[str, int] = {}
        replacements: list[Replacement] = []
        for detection in detections:
            counters[detection.type] = counters.get(detection.type, 0) + 1
            replacements.append(
                Replacement(
                    type=detection.type,
                    original=detection.label,
                    replaced=self._fallback_text(detection.type, counters[detection.type]),
                    reason="placeholder_local_rewrite",
                )
            )
        return replacements

    def _fallback_text(self, detection_type: str, index: int) -> str:
        if detection_type == "PERSON":
            return f"담당자 {index}"
        if detection_type == "ORG":
            return f"A사 {index}"
        if detection_type == "EMAIL":
            return f"이메일 주소 {index}"
        if detection_type == "PHONE":
            return f"연락처 {index}"
        if detection_type == "AMOUNT":
            return f"비공개 금액 {index}"
        if detection_type == "API_KEY":
            return f"API 키 {index}"
        if detection_type == "IP_ADDRESS":
            return f"IP 주소 {index}"
        if detection_type == "BUSINESS_REGISTRATION_NUMBER":
            return f"사업자등록번호 {index}"
        if detection_type == "RESIDENT_REGISTRATION_NUMBER":
            return f"주민등록번호 {index}"
        if detection_type == "FOREIGN_REGISTRATION_NUMBER":
            return f"외국인등록번호 {index}"
        if detection_type == "CARD_NUMBER":
            return f"카드번호 {index}"
        if detection_type == "ACCOUNT_NUMBER":
            return f"계좌번호 {index}"
        if detection_type == "VEHICLE_REGISTRATION_NUMBER":
            return f"차량번호 {index}"
        return f"비식별 정보 {index}"
