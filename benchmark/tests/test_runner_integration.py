"""Runner integration tests (S1-only end-to-end for speed) and determinism."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest


class RunnerEndToEndTest(unittest.TestCase):
    out_dir: str

    @classmethod
    def setUpClass(cls) -> None:
        from benchmark.runner import run_benchmark

        cls.out_dir = tempfile.mkdtemp(prefix="b63r0-runner-")
        cls.summary = run_benchmark(["S1"], cls.out_dir)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.out_dir, ignore_errors=True)

    def test_report_files_written(self) -> None:
        for name in ("results.json", "manifest.json", "corpus_snapshot.json", "summary.csv", "SUMMARY.md"):
            self.assertTrue(os.path.exists(os.path.join(self.out_dir, name)), name)

    def test_results_json_is_valid_and_complete(self) -> None:
        with open(os.path.join(self.out_dir, "results.json"), encoding="utf-8") as handle:
            payload = json.load(handle)
        self.assertIn("S1", payload["systems"])
        system_block = payload["systems"]["S1"]
        for key in ("entity_exact_base", "entity_overlap_base", "high_risk_f2_base", "residual_direct_phi_rate"):
            self.assertIn(key, system_block["privacy"])
        frontier_policies = {row["policy"] for row in payload["frontier"]}
        self.assertEqual(
            {"P0_BLOCK", "P1_MAXIMUM_REDACTION", "P2_TOKENIZATION", "P3_SEMANTIC_GENERALIZATION",
             "P4_PRIVATE_MODEL_PASSTHROUGH"},
            frontier_policies,
        )

    def test_corpus_snapshot_has_synthetic_markers(self) -> None:
        with open(os.path.join(self.out_dir, "corpus_snapshot.json"), encoding="utf-8") as handle:
            snapshot = json.load(handle)
        self.assertTrue(snapshot["manifest"]["synthetic_only"])
        for case in snapshot["cases"]:
            self.assertTrue(case["synthetic"], case["case_id"])

    def test_manifest_records_reproducibility_fields(self) -> None:
        with open(os.path.join(self.out_dir, "manifest.json"), encoding="utf-8") as handle:
            manifest = json.load(handle)
        for key in (
            "seed",
            "corpus_version",
            "schema_version",
            "git_sha",
            "python_version",
            "platform",
            "command",
            "execution_timestamp_utc",
        ):
            self.assertIn(key, manifest)
        self.assertNotEqual("", manifest["git_sha"])

    def test_metric_values_finite(self) -> None:
        privacy = self.summary["systems"]["S1"]["privacy"]
        for key in ("entity_overlap_base", "entity_exact_adversarial"):
            block = privacy[key]
            for field in ("precision", "recall", "f1"):
                value = float(block[field])
                self.assertGreaterEqual(value, 0.0)
                self.assertLessEqual(value, 1.0)


class RunnerDeterminismTest(unittest.TestCase):
    def test_two_runs_produce_identical_metric_payloads(self) -> None:
        from benchmark.corpus.adversarial import build_adversarial_cases
        from benchmark.corpus.generator import build_base_cases
        from benchmark.runner import compute_privacy_block, compute_utility_block, run_system

        base_cases = build_base_cases()[:20]
        cases = base_cases + build_adversarial_cases(base_cases)[:5]

        from benchmark.adapters.s1_generic_pii import S1GenericPiiAdapter

        adapter = S1GenericPiiAdapter()
        results_first, _stats = run_system(adapter, cases)
        results_second, _stats2 = run_system(adapter, cases)

        by_id_first = {case.case_id: (case, result) for case, result in results_first}
        by_id_second = {case.case_id: (case, result) for case, result in results_second}

        partitions_first = {
            "base": [by_id_first[c.case_id] for c in base_cases],
            "adversarial": [by_id_first[c.case_id] for c in cases if c.variant_kind != "base"],
            "negative": [],
            "all_phi": [pair for pair in results_first if pair[0].spans],
        }
        partitions_second = {
            "base": [by_id_second[c.case_id] for c in base_cases],
            "adversarial": [by_id_second[c.case_id] for c in cases if c.variant_kind != "base"],
            "negative": [],
            "all_phi": [pair for pair in results_second if pair[0].spans],
        }

        block_one = json.dumps(
            compute_privacy_block(partitions_first), sort_keys=True, ensure_ascii=False
        )
        block_two = json.dumps(
            compute_privacy_block(partitions_second), sort_keys=True, ensure_ascii=False
        )
        self.assertEqual(block_one, block_two)

        utility_one = json.dumps(compute_utility_block(partitions_first["all_phi"]), sort_keys=True)
        utility_two = json.dumps(compute_utility_block(partitions_second["all_phi"]), sort_keys=True)
        self.assertEqual(utility_one, utility_two)


if __name__ == "__main__":
    unittest.main()
