"""Deterministic report writers (JSON / CSV / Markdown).

Ordering rules: JSON uses ``sort_keys=True`` with stable key insertion; CSV
rows are emitted in sorted metric order; Markdown tables iterate sorted keys.
Reports never contain raw transformed text, only derived metric values.
"""

from __future__ import annotations

import csv
import json
import os
from typing import Any


def write_json(path: str, payload: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")


def write_csv(path: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    fieldnames = sorted({key for row in rows for key in row})
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    if isinstance(value, dict):
        return "<br>".join(f"{key}={_fmt(value[key])}" for key in sorted(value))
    if isinstance(value, list):
        return "; ".join(_fmt(item) for item in value)
    return str(value)


def write_markdown_summary(path: str, summary: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# B63 R0-A Benchmark Summary")
    lines.append("")
    lines.append("Synthetic/public benchmark only. Not hospital validation evidence.")
    lines.append("")

    manifest = summary["manifest"]
    lines.append("## Manifest")
    lines.append("")
    for key in sorted(manifest):
        lines.append(f"- {key}: {_fmt(manifest[key])}")
    lines.append("")

    corpus = summary["corpus"]
    lines.append("## Corpus")
    lines.append("")
    for key in sorted(corpus):
        lines.append(f"- {key}: {_fmt(corpus[key])}")
    lines.append("")

    lines.append("## Systems")
    lines.append("")
    systems = summary["systems"]
    metric_keys = sorted(systems["S0"]["privacy"].keys()) if "S0" in systems else []
    header = "| system | " + " | ".join(metric_keys) + " |"
    lines.append(header)
    lines.append("|" + "---|" * (len(metric_keys) + 1))
    for system_id in sorted(systems):
        privacy = systems[system_id]["privacy"]
        cells = " | ".join(_fmt(privacy[key]) for key in metric_keys)
        lines.append(f"| {system_id} | {cells} |")
    lines.append("")

    lines.append("## Clinical utility retention")
    lines.append("")
    utility_categories = (
        sorted(systems["S0"]["utility"].keys()) if "S0" in systems else []
    )
    header = "| system | " + " | ".join(utility_categories) + " |"
    lines.append(header)
    lines.append("|" + "---|" * (len(utility_categories) + 1))
    for system_id in sorted(systems):
        utility = systems[system_id]["utility"]
        cells = " | ".join(
            _fmt(utility[key]["rate"]) if isinstance(utility.get(key), dict) else _fmt(utility.get(key))
            for key in utility_categories
        )
        lines.append(f"| {system_id} | {cells} |")
    lines.append("")

    frontier = summary.get("frontier", [])
    if frontier:
        lines.append("## Privacy-utility policy frontier")
        lines.append("")
        frontier_keys = sorted({key for row in frontier for key in row})
        header = "| " + " | ".join(frontier_keys) + " |"
        lines.append(header)
        lines.append("|" + "---|" * len(frontier_keys))
        for row in frontier:
            lines.append("| " + " | ".join(_fmt(row.get(key)) for key in frontier_keys) + " |")
        lines.append("")

    verdict = summary.get("suggested_verdict", {})
    if verdict:
        lines.append("## Suggested verdict (mechanical criteria)")
        lines.append("")
        for key in sorted(verdict):
            lines.append(f"- {key}: {_fmt(verdict[key])}")
        lines.append("")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines))
