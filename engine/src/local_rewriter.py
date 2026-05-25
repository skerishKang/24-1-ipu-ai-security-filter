from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol
from urllib import request
from urllib.parse import urlparse

from engine.src.contracts import Detection, Replacement

_LOCAL_REWRITE_HOSTS = {"localhost", "127.0.0.1", "::1"}


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


class OllamaLocalRewriter:
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
        lines = [
            "Rewrite each detected sensitive span into a safe Korean placeholder.",
            "Rules:",
            "1. Preserve business meaning and sentence utility.",
            "2. Do not reveal or paraphrase the original exact value.",
            "3. Use natural Korean business wording.",
            '4. Return JSON object: {"replacements": [{"index": 1, "replacement": "...", "reason": "..."}]}',
            "",
            "Original content:",
            content,
            "",
            "Detected spans:",
        ]
        for index, detection in enumerate(detections, start=1):
            lines.append(
                f"- index={index} type={detection.type} label={detection.label} span=({detection.start},{detection.end})"
            )
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
            if not replacement or replacement == detection.label:
                raise ValueError("invalid_replacement")
            replacement = self._ensure_stable_replacement_text(replacement, detection.type, index)
            replacements.append(
                Replacement(
                    type=detection.type,
                    original=detection.label,
                    replaced=replacement,
                    reason=reason,
                )
            )
        return replacements

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


class PlaceholderLocalRewriter:
    """Fallback rewriter when Ollama is not available."""

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
