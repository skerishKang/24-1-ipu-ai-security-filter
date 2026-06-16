from __future__ import annotations

import secrets

from engine.src.contracts import Detection, Replacement, SessionMapping
from engine.src.session_store import SessionStore


class TokenReplacer:
    def __init__(self, session_store: SessionStore) -> None:
        self._session_store = session_store
        # ``_session_salt`` is generated once per ``TokenReplacer`` instance and
        # acts as a per-engine-deployment salt. Combined with the per-detection
        # random suffix it makes tokens unpredictable across sessions and
        # across detection types.
        self._session_salt = secrets.token_hex(8)

    def replace(
        self,
        content: str,
        detections: list[Detection],
        session_id: str,
        strategy: str = "strict_token",
    ) -> tuple[str, list[Replacement]]:
        replaced_text = content
        replacements: list[Replacement] = []
        # Counter is per (type, session) so a second ``replace()`` call on
        # the same session does not reuse ``[EMAIL_01]``. We start at 0 and
        # consult the session store for the highest existing counter so a
        # restart that re-uses an in-memory counter still increments.
        counters: dict[str, int] = {}
        planned: list[tuple[int, int, str]] = []

        for detection in detections:
            counters[detection.type] = (
                counters.get(detection.type, self._highest_index_for(session_id, detection.type))
            ) + 1
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
        # ``salt`` is unique per-token, ``session_salt`` is unique per
        # ``TokenReplacer`` instance. Together they make the token unguessable
        # across sessions and across replace() calls.
        salt = secrets.token_hex(4)
        return f"[{prefix}_{index:02d}_{self._session_salt[:6]}_{salt}]"

    def _highest_index_for(self, session_id: str, detection_type: str) -> int:
        # Inspect existing tokens for this session/type so a fresh
        # ``TokenReplacer`` instance does not collide with prior replacements.
        highest = 0
        for mapping in self._session_store.get_mappings(session_id):
            if mapping.type != detection_type:
                continue
            try:
                # Token shape: ``[PREFIX_NN_salt_salt]`` — pull the ``NN`` field.
                inner = mapping.replaced.strip("[]")
                parts = inner.split("_")
                if len(parts) < 2:
                    continue
                highest = max(highest, int(parts[1]))
            except (ValueError, IndexError):
                continue
        return highest
