"""B63 R0-A benchmark runner.

Orchestrates: corpus build → validation → system execution → metrics →
deterministic reports. See benchmark/README.md for scope and interpretation.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys

from benchmark.adapters.base import AdapterStats, CaseRunResult, SystemAdapter, record_stats, run_case
from benchmark.corpus.adversarial import build_adversarial_cases
from benchmark.corpus.generator import build_base_cases, build_manifest as build_corpus_manifest
from benchmark.corpus.schema import CorpusManifest, corpus_to_dict, validate_corpus
from benchmark.corpus.taxonomy import CORPUS_SEED
from benchmark.metrics import privacy as privacy_metrics
from benchmark.metrics import utility as utility_metrics
from benchmark.reproducibility import ReproducibilityManifest, build_manifest, manifest_to_dict
from benchmark.reporting import write_csv, write_json, write_markdown_summary

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SUPPORTED_SYSTEMS = ("S0", "S1", "S3")


def load_adapter(system_id: str) -> SystemAdapter:
    if system_id == "S0":
        from benchmark.adapters.s0_ipu_current import S0IpuCurrentAdapter

        return S0IpuCurrentAdapter()
    if system_id == "S1":
        from benchmark.adapters.s1_generic_pii import S1GenericPiiAdapter

        return S1GenericPiiAdapter()
    if system_id == "S3":
        from benchmark.adapters.s3_b63_hybrid import S3B63HybridAdapter

        return S3B63HybridAdapter()
    raise ValueError(f"unknown system id: {system_id} (supported: {','.join(SUPPORTED_SYSTEMS)})")


def build_corpus(seed: int) -> tuple[list, CorpusManifest]:
    base_cases = build_base_cases(seed)
    adversarial_cases = build_adversarial_cases(base_cases)
    cases = sorted(base_cases + adversarial_cases, key=lambda case: case.case_id)
    validate_corpus(cases)
    return cases, build_corpus_manifest(cases, seed)


def run_system(
    adapter: SystemAdapter,
    cases: list,
) -> tuple[list[tuple[object, CaseRunResult]], AdapterStats]:
    results: list[tuple[object, CaseRunResult]] = []
    stats = AdapterStats(system_id=adapter.system_id)
    for case in cases:
        result = run_case(adapter, case.text, case_key=case.case_id)
        record_stats(stats, result)
        results.append((case, result))
    return results, stats


def _round(value: float) -> float:
    return round(float(value), 4)


def compute_privacy_block(
    partitions: dict[str, list[tuple[object, CaseRunResult]]],
) -> dict[str, object]:
    block: dict[str, object] = {}
    for name in ("base", "adversarial"):
        scored = [
            (case, list(result.predictions))
            for case, result in partitions[name]
            if result.error is None
        ]
        tp_e = fp_e = fn_e = tp_o = fp_o = fn_o = h_tp = h_fp = h_fn = 0
        for case, predictions in scored:
            m = privacy_metrics.entity_metrics(case.spans, predictions, mode="exact")
            tp_e += m.tp
            fp_e += m.fp
            fn_e += m.fn
            m = privacy_metrics.entity_metrics(case.spans, predictions, mode="overlap")
            tp_o += m.tp
            fp_o += m.fp
            fn_o += m.fn
            m = privacy_metrics.entity_metrics(case.spans, predictions, mode="exact", risk_tier_high_only=True)
            h_tp += m.tp
            h_fp += m.fp
            h_fn += m.fn
        exact = privacy_metrics.prf(tp_e, fp_e, fn_e)
        overlap = privacy_metrics.prf(tp_o, fp_o, fn_o)
        high = privacy_metrics.prf(h_tp, h_fp, h_fn)
        block[f"entity_exact_{name}"] = {
            "precision": _round(exact.precision),
            "recall": _round(exact.recall),
            "f1": _round(exact.f1),
            "tp": exact.tp,
            "fp": exact.fp,
            "fn": exact.fn,
        }
        block[f"entity_overlap_{name}"] = {
            "precision": _round(overlap.precision),
            "recall": _round(overlap.recall),
            "f1": _round(overlap.f1),
            "tp": overlap.tp,
            "fp": overlap.fp,
            "fn": overlap.fn,
        }
        block[f"high_risk_f2_{name}"] = _round(privacy_metrics.f_beta(high.precision, high.recall, beta=2.0))

    all_phi = partitions["all_phi"]
    rate, residual, total = privacy_metrics.residual_direct_phi_rate(all_phi)
    block["residual_direct_phi_rate"] = {"rate": _round(rate), "residual": residual, "total": total}
    rate, residual, total = privacy_metrics.residual_high_risk_phi_rate(all_phi)
    block["residual_high_risk_phi_rate"] = {"rate": _round(rate), "residual": residual, "total": total}
    rate, escaped, docs = privacy_metrics.transform_escape_rate(all_phi)
    block["transform_escape_rate"] = {"rate": _round(rate), "escaped_documents": escaped, "documents": docs}

    rate, hits, flagged = privacy_metrics.quasi_combination_detection_rate(partitions["base"])
    block["quasi_combination_detection_rate"] = {"rate": _round(rate), "hits": hits, "flagged_cases": flagged}

    mean, scored_docs = privacy_metrics.contextual_reidentification_risk_experimental(all_phi)
    block["contextual_reid_risk_experimental"] = {
        "status": "EXPERIMENTAL",
        "mean_score": _round(mean),
        "documents_scored": scored_docs,
    }
    block["session_cumulative_risk_score"] = {
        "status": "NOT_IMPLEMENTED",
        "reason": "label definition unstable in R0; no forced number",
    }

    block["residual_by_label"] = privacy_metrics.residual_rate_by_label(all_phi)

    block["negative_false_positive"] = {
        key: _round(value)
        for key, value in privacy_metrics.negative_false_positive_stats(partitions["negative"]).items()
    }
    return block


def compute_utility_block(partition: list[tuple[object, CaseRunResult]]) -> dict[str, object]:
    retentions = utility_metrics.all_category_retentions(partition)
    block: dict[str, object] = {}
    for category in sorted(retentions):
        rate, kept, total = retentions[category]
        if total:
            block[category] = {"rate": _round(rate), "kept": kept, "total": total}
    rate, preserved, total = utility_metrics.relation_preservation(partition)
    if total:
        block["diagnosis_treatment_relation_preservation"] = {
            "rate": _round(rate),
            "preserved": preserved,
            "total": total,
        }
    rate, preserved, total = utility_metrics.event_ordering_preservation(partition)
    if total:
        block["event_ordering_preservation"] = {
            "rate": _round(rate),
            "preserved": preserved,
            "total": total,
        }
    return block


_FRONTIER_METRIC_KEYS = (
    "residual_direct_phi_rate",
    "residual_high_risk_phi_rate",
    "transform_escape_rate",
    "quasi_category_survival_experimental",
    "medication_retention",
    "lab_value_retention",
    "diagnosis_retention",
    "negation_preservation",
    "relation_preservation",
)


def _empty_frontier_cells() -> dict[str, object]:
    return {key: None for key in _FRONTIER_METRIC_KEYS}


def _frontier_summary(
    all_phi_results: list[tuple[object, CaseRunResult]],
    utility_pool: list[tuple[object, CaseRunResult]],
    transformed_override: dict[str, str] | None = None,
) -> dict[str, float | None]:
    adjusted: list[tuple[object, CaseRunResult]] = []
    for case, result in all_phi_results:
        if transformed_override and case.case_id in transformed_override:
            result = CaseRunResult(
                predictions=result.predictions,
                transformed_text=transformed_override[case.case_id],
                quasi_categories=result.quasi_categories,
            )
        adjusted.append((case, result))
    rd, _, _ = privacy_metrics.residual_direct_phi_rate(adjusted)
    rh, _, _ = privacy_metrics.residual_high_risk_phi_rate(adjusted)
    te, _, _ = privacy_metrics.transform_escape_rate(adjusted)
    quasi_survival, _scored = privacy_metrics.contextual_reidentification_risk_experimental(adjusted)
    med, _, _ = utility_metrics.category_retention(utility_pool, "medication")
    lab, _, _ = utility_metrics.category_retention(utility_pool, "lab_value")
    diag, _, _ = utility_metrics.category_retention(utility_pool, "diagnosis")
    neg, _, _ = utility_metrics.category_retention(utility_pool, "negation_cue")
    rel, _, _ = utility_metrics.relation_preservation(utility_pool)
    return {
        "residual_direct_phi_rate": _round(rd),
        "residual_high_risk_phi_rate": _round(rh),
        "transform_escape_rate": _round(te),
        "quasi_category_survival_experimental": _round(quasi_survival),
        "medication_retention": _round(med),
        "lab_value_retention": _round(lab),
        "diagnosis_retention": _round(diag),
        "negation_preservation": _round(neg),
        "relation_preservation": _round(rel),
    }


def compute_frontier(
    adapter: SystemAdapter,
    all_phi_results: list[tuple[object, CaseRunResult]],
    utility_pool: list[tuple[object, CaseRunResult]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    supported = set(adapter.policy_outputs())

    rows.append({"policy": "P0_BLOCK", "status": "NOT_IMPLEMENTED", **_empty_frontier_cells()})

    if hasattr(adapter, "transform_p1_max_redaction"):
        overrides = {
            case.case_id: adapter.transform_p1_max_redaction(case.text)
            for case, _result in all_phi_results
        }
        rows.append(
            {
                "policy": "P1_MAXIMUM_REDACTION",
                "status": "SIMULATED_S3_MAX",
                **_frontier_summary(all_phi_results, utility_pool, overrides),
            }
        )
    else:
        rows.append({"policy": "P1_MAXIMUM_REDACTION", "status": "NOT_IMPLEMENTED", **_empty_frontier_cells()})

    if "P2" in supported:
        rows.append({"policy": "P2_TOKENIZATION", "status": "IMPLEMENTED", **_frontier_summary(all_phi_results, utility_pool)})
    else:
        rows.append({"policy": "P2_TOKENIZATION", "status": "NOT_IMPLEMENTED", **_empty_frontier_cells()})

    rows.append({"policy": "P3_SEMANTIC_GENERALIZATION", "status": "NOT_IMPLEMENTED", **_empty_frontier_cells()})
    rows.append({"policy": "P4_PRIVATE_MODEL_PASSTHROUGH", "status": "NOT_IMPLEMENTED", **_empty_frontier_cells()})
    return rows


def suggest_verdict(system_blocks: dict[str, dict[str, object]]) -> dict[str, object]:
    """Mechanical application of the Issue #736 criteria with raw inputs."""
    reasons: list[str] = []
    s0_ok = "S0" in system_blocks
    s1_ok = "S1" in system_blocks

    def numeric(block: dict[str, object], key: str, subkey: str = "") -> float:
        value = block.get(key)
        if isinstance(value, dict):
            inner = value.get(subkey)
            return float(inner) if isinstance(inner, (int, float)) else 0.0
        if isinstance(value, (int, float)):
            return float(value)
        return 0.0

    baseline_best_f2 = max(
        (numeric(blocks, "high_risk_f2_base") for sid, blocks in system_blocks.items() if sid != "S3"),
        default=0.0,
    )
    s3_block = system_blocks.get("S3")
    s3_f2 = numeric(s3_block, "high_risk_f2_base") if s3_block else 0.0
    baseline_best_qicdr = max(
        (
            numeric(blocks, "quasi_combination_detection_rate", "rate")
            for sid, blocks in system_blocks.items()
            if sid != "S3"
        ),
        default=0.0,
    )
    s3_qicdr = numeric(s3_block, "quasi_combination_detection_rate", "rate") if s3_block else 0.0

    f2_margin = s3_f2 - baseline_best_f2 if s3_block else 0.0
    qicdr_margin = s3_qicdr - baseline_best_qicdr if s3_block else 0.0
    measurable_advantage = s3_block is not None and (f2_margin >= 0.05 or qicdr_margin >= 0.10)
    if s3_block:
        if f2_margin >= 0.05:
            reasons.append(f"S3 high-risk F2 margin over best baseline: {f2_margin:+.4f}")
        if qicdr_margin >= 0.10:
            reasons.append(f"S3 QICDR margin over best baseline: {qicdr_margin:+.4f}")
        if not measurable_advantage:
            reasons.append("no >=5pp high-risk F2 margin and no >=10pp QICDR margin")

    collapse = False
    if s3_block:
        base_recall = numeric(s3_block.get("entity_overlap_base", {}), "recall")
        adv_recall = numeric(s3_block.get("entity_overlap_adversarial", {}), "recall")
        baseline_best_adv_recall = max(
            (
                numeric(blocks.get("entity_overlap_adversarial", {}), "recall")
                for sid, blocks in system_blocks.items()
                if sid != "S3"
            ),
            default=0.0,
        )
        # Collapse gate intent (Issue #736): detect prototype-specific fragility.
        # Universal regex limits shared with baselines (e.g. OCR 0/O digit
        # corruption) are an adversarial-limit finding, not a prototype collapse.
        # S3 collapses only if it loses more than half its base recall AND falls
        # behind the best baseline under the same adversarial partition.
        loses_half = base_recall > 0 and adv_recall < 0.5 * base_recall
        below_baselines = adv_recall < baseline_best_adv_recall
        collapse = loses_half and below_baselines
        if collapse:
            reasons.append(
                f"adversarial recall collapse: base {base_recall:.4f} vs adversarial {adv_recall:.4f} "
                f"(best baseline adversarial {baseline_best_adv_recall:.4f})"
            )

    utility_keys = (s3_block or {}).get("_utility_rates", {})
    utility_ok = any(key.startswith(("medication", "diagnosis")) for key in utility_keys)

    if not (s0_ok and s1_ok):
        verdict = "INCOMPLETE"
        reasons.append("both S0 and S1 must be measured")
    elif measurable_advantage and utility_ok and not collapse:
        verdict = "PASS_CANDIDATE"
    elif collapse:
        verdict = "NARROW"
        reasons.append("adversarial robustness gate failed")
    elif not utility_ok:
        verdict = "NARROW"
        reasons.append("clinical utility measurement incomplete")
    else:
        verdict = "NARROW"
        reasons.append("advantage below thresholds; inspect raw metrics")

    return {
        "verdict": verdict,
        "criteria_inputs": {
            "s0_measured": s0_ok,
            "s1_measured": s1_ok,
            "s3_high_risk_f2_base": _round(s3_f2),
            "baseline_best_high_risk_f2_base": _round(baseline_best_f2),
            "s3_qicdr": _round(s3_qicdr),
            "baseline_best_qicdr": _round(baseline_best_qicdr),
            "adversarial_collapse_detected": collapse,
            "measurable_advantage": measurable_advantage,
        },
        "reasons": reasons,
        "note": "mechanical suggestion only; final interpretation belongs to reviewers per Issue #736",
    }


def run_benchmark(system_ids: list[str], out_dir: str, seed: int = CORPUS_SEED) -> dict[str, object]:
    started = _dt.datetime.now(_dt.timezone.utc)
    command = f"python -m benchmark.runner --systems {','.join(sorted(system_ids))} --out {out_dir}"

    cases, corpus_manifest = build_corpus(seed)
    base_cases = [case for case in cases if case.variant_kind == "base"]
    adversarial_cases = [case for case in cases if case.variant_kind != "base"]
    negative_cases = [case for case in base_cases if case.subset == "negative"]
    utility_annotated = [case for case in base_cases if case.utility_spans]

    manifest: ReproducibilityManifest = build_manifest(
        repo_root=_REPO_ROOT,
        seed=seed,
        corpus_version=corpus_manifest.corpus_version,
        schema_version=corpus_manifest.schema_version,
        command=command,
        timestamp_utc=started.isoformat(timespec="seconds"),
    )

    privacy_blocks: dict[str, dict[str, object]] = {}
    utility_blocks: dict[str, dict[str, object]] = {}
    adapter_stats_out: dict[str, dict[str, object]] = {}
    frontier_by_system: dict[str, list[dict[str, object]]] = {}

    for system_id in sorted(system_ids):
        adapter = load_adapter(system_id)
        all_results, stats = run_system(adapter, cases)
        by_id = {case.case_id: (case, result) for case, result in all_results}

        partitions = {
            "base": [by_id[c.case_id] for c in base_cases],
            "adversarial": [by_id[c.case_id] for c in adversarial_cases],
            "negative": [by_id[c.case_id] for c in negative_cases],
            "all_phi": [pair for pair in all_results if pair[0].spans],
        }
        utility_partition = [by_id[c.case_id] for c in utility_annotated]

        privacy_blocks[system_id] = compute_privacy_block(partitions)
        privacy_blocks[system_id]["_utility_rates"] = {
            key: float(value["rate"])
            for key, value in compute_utility_block(utility_partition).items()
            if isinstance(value, dict)
        }
        utility_blocks[system_id] = compute_utility_block(utility_partition)
        frontier_by_system[system_id] = compute_frontier(adapter, partitions["all_phi"], utility_partition)
        adapter_stats_out[system_id] = {
            "cases_run": stats.cases_run,
            "cases_failed": stats.cases_failed,
            "errors": stats.errors[:10],
        }

    verdict = suggest_verdict(privacy_blocks)

    summary = {
        "manifest": manifest_to_dict(manifest),
        "corpus": {
            "corpus_version": corpus_manifest.corpus_version,
            "schema_version": corpus_manifest.schema_version,
            "seed": seed,
            "base_case_count": corpus_manifest.base_case_count,
            "adversarial_case_count": corpus_manifest.adversarial_case_count,
            "total_case_count": corpus_manifest.total_case_count,
            "subset_counts": dict(sorted(corpus_manifest.subset_counts.items())),
        },
        "systems": {
            system_id: {
                "privacy": {
                    key: value
                    for key, value in privacy_blocks[system_id].items()
                    if not str(key).startswith("_")
                },
                "utility": utility_blocks[system_id],
                "adapter_stats": adapter_stats_out[system_id],
            }
            for system_id in sorted(privacy_blocks)
        },
        "frontier": [
            {"system": system_id, **row}
            for system_id in sorted(frontier_by_system)
            for row in frontier_by_system[system_id]
        ],
        "suggested_verdict": verdict,
    }

    write_json(os.path.join(out_dir, "results.json"), summary)
    write_json(os.path.join(out_dir, "manifest.json"), manifest_to_dict(manifest))
    write_json(os.path.join(out_dir, "corpus_snapshot.json"), corpus_to_dict(corpus_manifest, cases))
    write_csv(os.path.join(out_dir, "summary.csv"), _flatten_summary(summary))
    write_markdown_summary(os.path.join(out_dir, "SUMMARY.md"), summary)

    print(json.dumps({"out_dir": out_dir, "verdict": verdict["verdict"]}, ensure_ascii=False))
    return summary


def _flatten_summary(summary: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    systems = summary["systems"]
    for system_id in sorted(systems):
        for section_name in ("privacy", "utility"):
            section = systems[system_id][section_name]
            for metric_key in sorted(section):
                value = section[metric_key]
                if isinstance(value, dict):
                    for field_name in sorted(value):
                        rows.append(
                            {
                                "system": system_id,
                                "section": section_name,
                                "metric": metric_key,
                                "field": field_name,
                                "value": value[field_name],
                            }
                        )
                else:
                    rows.append(
                        {
                            "system": system_id,
                            "section": section_name,
                            "metric": metric_key,
                            "field": "value",
                            "value": value,
                        }
                    )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="B63 R0-A synthetic benchmark")
    parser.add_argument("--systems", default="S0,S1,S3", help="comma-separated: S0,S1,S3")
    parser.add_argument("--out", default=os.path.join("benchmark", "reports", "R0_canonical"))
    parser.add_argument("--seed", type=int, default=CORPUS_SEED)
    args = parser.parse_args(argv)

    system_ids = [item.strip().upper() for item in args.systems.split(",") if item.strip()]
    unknown = [item for item in system_ids if item not in SUPPORTED_SYSTEMS]
    if unknown:
        raise SystemExit(f"unsupported systems: {unknown}")

    out_dir = args.out if os.path.isabs(args.out) else os.path.join(_REPO_ROOT, args.out)
    run_benchmark(system_ids, out_dir, seed=args.seed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
