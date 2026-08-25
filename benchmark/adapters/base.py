"""Adapter contract and failure isolation for benchmark systems."""

from __future__ import annotations

import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Prediction:
    type: str
    start: int
    end: int


@dataclass
class CaseRunResult:
    predictions: tuple[Prediction, ...] = ()
    transformed_text: str = ""
    quasi_categories: frozenset[str] = frozenset()
    error: str | None = None


@dataclass
class AdapterStats:
    system_id: str
    cases_run: int = 0
    cases_failed: int = 0
    errors: list[str] = field(default_factory=list)


class SystemAdapter(ABC):
    """A benchmarked de-identification system.

    Implementations must be read-only with respect to production code paths.
    ``transform`` returns text where detected entities are replaced; it must be
    safe to call even when nothing was detected.
    """

    system_id: str = "UNKNOWN"

    @abstractmethod
    def detect(self, text: str) -> list[Prediction]:
        """Return entity predictions over the raw text."""

    @abstractmethod
    def transform(self, text: str, case_key: str) -> str:
        """Return the transformed (de-identified) text."""

    def quasi_categories(self, text: str) -> frozenset[str]:
        """Names of quasi categories the system itself flagged for this text."""
        return frozenset()

    def policy_outputs(self) -> dict[str, str]:
        """Policy levels this adapter can execute (used by frontier rows)."""
        return {"P2": "tokenization"}


def run_case(adapter: SystemAdapter, text: str, case_key: str) -> CaseRunResult:
    """Execute one case through an adapter, isolating failures.

    A failing adapter never aborts the benchmark; the failure is recorded and
    scored as a miss (empty predictions, untransformed text).
    """
    try:
        predictions = tuple(adapter.detect(text))
        transformed = adapter.transform(text, case_key)
        if not isinstance(transformed, str):
            raise TypeError("transform() must return str")
        return CaseRunResult(
            predictions=predictions,
            transformed_text=transformed,
            quasi_categories=adapter.quasi_categories(text),
        )
    except Exception as exc:  # noqa: BLE001 - benchmark must survive adapter crashes
        return CaseRunResult(
            error="".join(traceback.format_exception_only(type(exc), exc)).strip()
        )


def record_stats(stats: AdapterStats, result: CaseRunResult) -> None:
    stats.cases_run += 1
    if result.error is not None:
        stats.cases_failed += 1
        stats.errors.append(result.error)
