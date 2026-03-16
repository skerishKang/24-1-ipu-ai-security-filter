from __future__ import annotations

from engine.src.contracts import Detection, Replacement, SessionMapping
from engine.src.session_store import SessionStore


class TokenReplacer:
    def __init__(self, session_store: SessionStore) -> None:
        self._session_store = session_store

    def replace(
        self,
        content: str,
        detections: list[Detection],
        session_id: str,
        strategy: str = "strict_token",
    ) -> tuple[str, list[Replacement]]:
        replaced_text = content
        replacements: list[Replacement] = []
        counters: dict[str, int] = {}
        planned: list[tuple[int, int, str]] = []

        for detection in detections:
            counters[detection.type] = counters.get(detection.type, 0) + 1
            token = self._build_token(detection.type, counters[detection.type], strategy)
            planned.append((detection.start, detection.end, token))
            replacement = Replacement(
                type=detection.type,
                original=detection.label,
                replaced=token,
                reason=detection.note,
            )
            replacements.append(replacement)
            self._session_store.save_mapping(
                session_id,
                SessionMapping(
                    session_id=session_id,
                    original=detection.label,
                    replaced=token,
                    type=detection.type,
                ),
            )

        for start, end, token in sorted(planned, key=lambda item: item[0], reverse=True):
            replaced_text = replaced_text[:start] + token + replaced_text[end:]

        return replaced_text, replacements

    def _build_token(self, token_type: str, index: int, strategy: str) -> str:
        prefix = token_type if strategy == "strict_token" else f"{token_type}_ALIAS"
        return f"[{prefix}_{index:02d}]"
