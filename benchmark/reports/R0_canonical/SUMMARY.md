# B63 R0-A Benchmark Summary

Synthetic/public benchmark only. Not hospital validation evidence.

## Manifest

- command: python -m benchmark.runner --systems S0,S1,S3 --out G:\Ddrive\BatangD\task\workdiary\24-1-ipu-ai-security-filter\benchmark/reports/R0_canonical
- corpus_version: 0.1.0
- engine_version_note: engine imported read-only from repository at git_sha
- execution_timestamp_utc: 2026-08-25T07:20:38+00:00
- extra_dependencies: 
- git_dirty: False
- git_sha: ccd61c0e383e63f57c01d498e3a8cd0ee16583d1
- platform: Windows-10-10.0.19045-SP0
- python_version: 3.11.0
- schema_version: 0.1.0
- seed: 20260825

## Corpus

- adversarial_case_count: 76
- base_case_count: 109
- corpus_version: 0.1.0
- schema_version: 0.1.0
- seed: 20260825
- subset_counts: direct=32<br>institutional=20<br>negative=15<br>quasi=24<br>utility=18
- total_case_count: 185

## Systems

| system | contextual_reid_risk_experimental | entity_exact_adversarial | entity_exact_base | entity_overlap_adversarial | entity_overlap_base | high_risk_f2_adversarial | high_risk_f2_base | negative_false_positive | quasi_combination_detection_rate | residual_direct_phi_rate | residual_high_risk_phi_rate | session_cumulative_risk_score | transform_escape_rate |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S0 | documents_scored=84<br>mean_score=0.7208<br>status=EXPERIMENTAL | f1=0.1121<br>fn=409<br>fp=66<br>precision=0.3125<br>recall=0.0683<br>tp=30 | f1=0.1449<br>fn=399<br>fp=73<br>precision=0.3540<br>recall=0.0911<br>tp=40 | f1=0.1570<br>fn=397<br>fp=54<br>precision=0.4375<br>recall=0.0957<br>tp=42 | f1=0.2029<br>fn=383<br>fp=57<br>precision=0.4956<br>recall=0.1276<br>tp=56 | 0.1829 | 0.2389 | document_fp_rate=0.0000<br>documents_with_predictions=0.0000<br>mean_predictions_per_document=0.0000 | flagged_cases=24<br>hits=0<br>rate=0.0000 | rate=0.7155<br>residual=259<br>total=362 | rate=0.7155<br>residual=259<br>total=362 | reason=label definition unstable in R0; no forced number<br>status=NOT_IMPLEMENTED | documents=74<br>escaped_documents=74<br>rate=1.0000 |
| S1 | documents_scored=84<br>mean_score=0.7726<br>status=EXPERIMENTAL | f1=0.1043<br>fn=410<br>fp=88<br>precision=0.2479<br>recall=0.0661<br>tp=29 | f1=0.1772<br>fn=383<br>fp=137<br>precision=0.2902<br>recall=0.1276<br>tp=56 | f1=0.2734<br>fn=363<br>fp=41<br>precision=0.6496<br>recall=0.1731<br>tp=76 | f1=0.3829<br>fn=318<br>fp=72<br>precision=0.6269<br>recall=0.2756<br>tp=121 | 0.1724 | 0.3053 | document_fp_rate=0.0000<br>documents_with_predictions=0.0000<br>mean_predictions_per_document=0.0000 | flagged_cases=24<br>hits=0<br>rate=0.0000 | rate=0.5304<br>residual=192<br>total=362 | rate=0.5304<br>residual=192<br>total=362 | reason=label definition unstable in R0; no forced number<br>status=NOT_IMPLEMENTED | documents=74<br>escaped_documents=74<br>rate=1.0000 |
| S3 | documents_scored=84<br>mean_score=0.9452<br>status=EXPERIMENTAL | f1=0.4672<br>fn=261<br>fp=145<br>precision=0.5511<br>recall=0.4055<br>tp=178 | f1=0.5771<br>fn=192<br>fp=170<br>precision=0.5923<br>recall=0.5626<br>tp=247 | f1=0.6299<br>fn=199<br>fp=83<br>precision=0.7430<br>recall=0.5467<br>tp=240 | f1=0.8318<br>fn=83<br>fp=61<br>precision=0.8537<br>recall=0.8109<br>tp=356 | 0.2101 | 0.2454 | document_fp_rate=0.0000<br>documents_with_predictions=0.0000<br>mean_predictions_per_document=0.0000 | flagged_cases=24<br>hits=24<br>rate=1.0000 | rate=0.2680<br>residual=97<br>total=362 | rate=0.2680<br>residual=97<br>total=362 | reason=label definition unstable in R0; no forced number<br>status=NOT_IMPLEMENTED | documents=74<br>escaped_documents=64<br>rate=0.8649 |

## Clinical utility retention

| system | diagnosis | diagnosis_treatment_relation_preservation | dosage | event_ordering_preservation | frequency_route | lab_value | medication | negation_cue | procedure | symptom | temporality | uncertainty_cue |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S0 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| S1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| S3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

## Privacy-utility policy frontier

| diagnosis_retention | lab_value_retention | medication_retention | negation_preservation | policy | quasi_category_survival_experimental | relation_preservation | residual_direct_phi_rate | residual_high_risk_phi_rate | status | system | transform_escape_rate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| None | None | None | None | P0_BLOCK | None | None | None | None | NOT_IMPLEMENTED | S0 | None |
| None | None | None | None | P1_MAXIMUM_REDACTION | None | None | None | None | NOT_IMPLEMENTED | S0 | None |
| 1.0000 | 1.0000 | 1.0000 | 1.0000 | P2_TOKENIZATION | 0.7208 | 1.0000 | 0.7155 | 0.7155 | IMPLEMENTED | S0 | 1.0000 |
| None | None | None | None | P3_SEMANTIC_GENERALIZATION | None | None | None | None | NOT_IMPLEMENTED | S0 | None |
| None | None | None | None | P4_PRIVATE_MODEL_PASSTHROUGH | None | None | None | None | NOT_IMPLEMENTED | S0 | None |
| None | None | None | None | P0_BLOCK | None | None | None | None | NOT_IMPLEMENTED | S1 | None |
| None | None | None | None | P1_MAXIMUM_REDACTION | None | None | None | None | NOT_IMPLEMENTED | S1 | None |
| 1.0000 | 1.0000 | 1.0000 | 1.0000 | P2_TOKENIZATION | 0.7726 | 1.0000 | 0.5304 | 0.5304 | IMPLEMENTED | S1 | 1.0000 |
| None | None | None | None | P3_SEMANTIC_GENERALIZATION | None | None | None | None | NOT_IMPLEMENTED | S1 | None |
| None | None | None | None | P4_PRIVATE_MODEL_PASSTHROUGH | None | None | None | None | NOT_IMPLEMENTED | S1 | None |
| None | None | None | None | P0_BLOCK | None | None | None | None | NOT_IMPLEMENTED | S3 | None |
| 1.0000 | 1.0000 | 1.0000 | 1.0000 | P1_MAXIMUM_REDACTION | 0.1476 | 1.0000 | 0.2680 | 0.2680 | SIMULATED_S3_MAX | S3 | 0.8649 |
| 1.0000 | 1.0000 | 1.0000 | 1.0000 | P2_TOKENIZATION | 0.9452 | 1.0000 | 0.2680 | 0.2680 | IMPLEMENTED | S3 | 0.8649 |
| None | None | None | None | P3_SEMANTIC_GENERALIZATION | None | None | None | None | NOT_IMPLEMENTED | S3 | None |
| None | None | None | None | P4_PRIVATE_MODEL_PASSTHROUGH | None | None | None | None | NOT_IMPLEMENTED | S3 | None |

## Suggested verdict (mechanical criteria)

- criteria_inputs: adversarial_collapse_detected=False<br>baseline_best_high_risk_f2_base=0.3053<br>baseline_best_qicdr=0.0000<br>measurable_advantage=True<br>s0_measured=True<br>s1_measured=True<br>s3_high_risk_f2_base=0.2454<br>s3_qicdr=1.0000
- note: mechanical suggestion only; final interpretation belongs to reviewers per Issue #736
- reasons: S3 QICDR margin over best baseline: +1.0000
- verdict: PASS_CANDIDATE
