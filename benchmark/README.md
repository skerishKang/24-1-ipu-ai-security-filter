# B63 Benchmark R0-A — Synthetic/Privacy–Clinical-Utility Benchmark Harness

Parent tracking: `skerishKang/ai-revenue-lab` Issue #731 → #735 → **#736** (direct authority).

Authority for this local run:

```text
DRIVEFS_AVAILABLE = NO
DRIVE_DEPENDENCY_BYPASSED = YES
AUTHORITY_USED = ISSUE_736_PLUS_GITHUB_OVERRIDE
```

Google Drive B63 documents were not readable during this run (DriveFS unmounted). Per the
Issue #736 "Drive-independent execution override" comment, the Issue body plus that comment
are the operational authority for this implementation.

## 1. What R0 is — and is not

R0-A is a **synthetic/public benchmark harness only**. It answers one question:

> Does a healthcare-specific Korean clinical privacy layer produce measurable advantage
> over current IPU and a generic PII baseline while preserving clinically important meaning?

This is NOT:

- real patient data processing (forbidden);
- a hospital connector or FHIR/HL7 integration (forbidden);
- production deployment or medical-device claim (forbidden);
- a production clinical NER model (forbidden in R0);
- evidence of hospital performance. **A good score here is not clinical validation.**
  Hospital validation remains a separate future gate.

Production freeze: nothing under `engine/src`, `backend`, `frontend`, deployment configs,
or API contracts was semantically modified. The IPU engine is invoked read-only through its
existing public interfaces (`RegexDetector.detect`, `ManualPreviewEngine.manual_preview`).

## 2. Directory layout

```text
benchmark/
├── README.md            ← this document
├── __init__.py
├── corpus/
│   ├── taxonomy.py      ← label/risk-tier/utility-type constants (single source)
│   ├── schema.py        ← dataclasses + corpus validation
│   ├── generator.py     ← deterministic synthetic base-case builder (seeded)
│   └── adversarial.py   ← deterministic variant transforms + span remapping
├── adapters/
│   ├── base.py          ← system adapter contract + failure isolation
│   ├── s0_ipu_current.py
│   ├── s1_generic_pii.py
│   └── s3_b63_hybrid.py
├── metrics/
│   ├── privacy.py       ← entity/span/transformation/context metrics
│   └── utility.py       ← clinical-utility retention metrics
├── runner.py            ← orchestration
├── reporting.py         ← deterministic JSON/CSV/Markdown writers
├── reproducibility.py   ← manifest builder (git SHA, versions, seed)
├── run_benchmark.py     ← CLI entry point
├── schemas/
│   └── corpus_case.schema.json
├── tests/               ← unittest-based benchmark tests
└── reports/             ← generated output snapshots (canonical run committed)
```

## 3. Corpus construction rules

- Base cases are generated deterministically from templates with a fixed seed
  (`CORPUS_SEED = 20260825`). No randomness at import time; the same seed always
  yields byte-identical corpora.
- Target: >= 100 synthetic base cases before any tuning. Current composition target:
  - direct-identifier cases (patient/guardian name, phone, email, address, RRN,
    foreign registration number, MRN, insurance/account number, clinician name/ID);
  - institutional/context cases (hospital name, ward/department, order/accession IDs,
    exact timestamps);
  - quasi-identifier cases (age, sex, rare disease/procedure, detailed region,
    occupation, admission/discharge timing, unique events, combinations);
  - clean negatives (no personal information at all; used for false-positive scoring);
  - clinical-utility cases (medication/dose/frequency/route/lab values, diagnosis and
    procedures, negation, uncertainty, temporality, diagnosis–treatment relation,
    event ordering).
- Adversarial variants are deterministic pure-function transforms of base cases
  (fullwidth digits, zero-width characters, soft hyphens, whitespace splitting,
  OCR confusion 0/O and 1/l/I, separator variants of phone/RRN, Korean/English mixing,
  abbreviation, typo noise, PDF line-break noise, table-like noise). Gold spans are
  remapped through each transform.
- Every case carries `"synthetic": true` and every corpus manifest carries
  `"synthetic_only": true`. Validation rejects corpora without these markers.

### Synthetic-only boundary

All names, hospitals, addresses, numbers, dates, and IDs are invented. Example values use
obviously fictional shapes (`김예환`, `한빛대학교병원`, `서울특별시 예시구 예시로 123`).
RRNs/phones are generated with fictional digit patterns. No scraped notes, no EMR dumps,
no ambiguous de-identification sources. The automated safety test
(`benchmark/tests/test_corpus_synthetic_safety.py`) re-checks marker presence and scans
fixtures for accidental secret-shaped strings.

## 4. Annotation taxonomy v0.1

Labels live in `benchmark/corpus/taxonomy.py` (single source; schema JSON mirrors it).

Direct identifiers (risk tier `high`):

| Label | Meaning |
| --- | --- |
| `PATIENT_NAME` | patient real name |
| `GUARDIAN_NAME` | guardian/family name tied to patient |
| `PHONE` | phone/contact number |
| `EMAIL` | email address |
| `ADDRESS` | street-level address |
| `RRN` | 주민등록번호 |
| `FOREIGN_REG_NUMBER` | 외국인등록번호 |
| `MRN` | 환자번호/차트번호/병록번호 |
| `INSURANCE_NUMBER` | 보험/계정/청구 번호 |
| `CLINICIAN_NAME` | clinician real name |
| `CLINICIAN_ID` | clinician staff ID where policy requires |

Institutional/context identifiers (risk tier `standard`, class `contextual`):
`HOSPITAL_NAME`, `WARD_DEPARTMENT`, `ORDER_ID`, `EXACT_TIMESTAMP`.

Quasi-identifiers (class `quasi`): `AGE`, `SEX`, `RARE_DISEASE`, `RARE_PROCEDURE`,
`DETAILED_REGION`, `OCCUPATION`, `ADMIT_DISCHARGE_DATE`, `UNIQUE_EVENT`.

Clean negatives carry no PHI spans. Utility annotations use utility types:
`medication`, `dosage`, `frequency_route`, `lab_value`, `diagnosis`, `procedure`,
`symptom`, `negation_cue`, `temporality`, `event_order_marker`; relation cases add
`relation_diagnosis_treatment` pairs referencing span ids.

## 5. Systems

| ID | Name | Status | Definition |
| --- | --- | --- | --- |
| `S0` | `IPU_CURRENT` | IMPLEMENTED | current engine `strict_token` detection + token replacement, called read-only |
| `S1` | `GENERIC_PII_BASELINE` | IMPLEMENTED (in-repo reference) | self-contained generic PII heuristics (email/phone/national-ID shape/card/address keyword/labeled ID). Free, local, deterministic, no external dependency. NOT an optimized commercial product; see limitations |
| `S2` | `CLINICAL_BASELINE` | NOT_IMPLEMENTED | no reproducible public Korean-clinical baseline available offline in this environment; forcing one would violate honesty rules |
| `S3` | `B63_HYBRID_R0` | IMPLEMENTED (prototype) | bounded research prototype: S0 rules + additional Korean-clinical rules (hospital/ward/MRN/order-ID/clinician/address/quasi combos) + utility-preservation policy. No model training |

Policy frontier rows reported per §10 below.

## 6. Metric definitions

All metrics operate on gold spans vs predicted spans mapped into gold-label space via a
documented equivalence table (e.g. gold `RRN` accepts predictions typed
`RESIDENT_REGISTRATION_NUMBER`; gold `PATIENT_NAME`/`GUARDIAN_NAME`/`CLINICIAN_NAME`
accept `PERSON`). The table lives in `benchmark/metrics/privacy.py` and is part of the
schema version record.

Entity level (per partition):

- Precision = TP / (TP + FP); Recall = TP / (TP + FN); F1 = 2PR/(P+R).
- Exact match: identical `(start, end)` and mapped label.
- Overlap match: any overlap with equal mapped label, matched greedily left-to-right,
  one-to-one (deterministic).
- High-risk F2 = ((1+β²)PR)/(β²P+R) with β=2 over gold entities with risk tier `high`.

Transformation level (after each system transforms the text):

- Residual Direct-PHI Rate = (# `high`-tier gold entities whose verbatim text still
  appears in the transformed output) / (# `high`-tier gold entities).
- Residual High-Risk-PHI Rate = same computation restricted to direct-class high-risk
  labels (names, RRN, MRN, phone, email, address).
- Under taxonomy v0.1 the high-risk tier is exactly the direct class, so these two
  rates coincide by construction; both are reported for schema stability and a
  per-label residual breakdown (`residual_by_label`) is included in `results.json`.
- Transform Escape Rate = fraction of PHI-bearing documents with at least one residual
  direct-class entity.
- Verbatim-presence is a conservative proxy: a string that survives coincidentally
  elsewhere still counts as escaped. Documented limitation, applied equally to all systems.

Context level:

- Quasi-Identifier Combination Detection Rate (QICDR): over cases annotated with
  `has_quasi_combination=true`, the fraction where the system itself detected at least two
  distinct quasi-class categories present in the case.
- Contextual Re-identification Risk Score (**EXPERIMENTAL**): mean over documents of
  (distinct un-redacted quasi categories present) / (distinct quasi categories present).
  Label semantics are unstable; treat as exploratory only.
- Session Cumulative Risk Score: **NOT_IMPLEMENTED** in R0 (label definition unstable;
  no forced numbers).

Clinical utility level (per category, after transformation):

- Retention(category) = (# gold utility spans of that category whose verbatim text appears
  in transformed output) / (# gold utility spans of that category).
- Negation Preservation / Temporality Preservation: retention over their cue span sets.
- Diagnosis–Treatment Relation Preservation = fraction of annotated relation cases where
  both endpoint texts remain present.
- Event Ordering Preservation = fraction of event-ordering cases where all ordered markers
  remain present.
- Privacy–utility trade-off is reported as separate raw numbers; **no composite score is
  computed and none hides the frontier.**

False-positive behavior on clean negatives:

- Negative False-Positive Rate = fraction of clean-negative documents with ≥1 prediction;
  plus mean prediction count per negative document.

## 7. Policy frontier

| Policy | Status in R0 | Meaning |
| --- | --- | --- |
| P0 BLOCK | NOT_IMPLEMENTED | block transmission entirely |
| P1 MAXIMUM_REDACTION | SIMULATED_S3_MAX | S3 detections expanded to redact all quasi-category entities too; executed on S3 output only |
| P2 TOKENIZATION | IMPLEMENTED | strict-token replacement of detected PHI (default S0/S1/S3 behavior) |
| P3 SEMANTIC_GENERALIZATION_OR_LOCAL_REWRITE | NOT_IMPLEMENTED | out of R0 scope |
| P4 APPROVED_PRIVATE_MODEL_PASSTHROUGH | NOT_IMPLEMENTED | out of R0 scope |

The frontier table prints privacy and utility raw metrics per policy row with its status,
including `quasi_category_survival_experimental` (the CRIS proxy) so the effect of the
P1 maximum-redaction simulation on quasi-ID exposure is visible next to its unchanged
direct-PHI numbers. Unsupported policies are never labeled SUPPORTED.

## 8. Reproducibility

Fixed inputs recorded in every `manifest.json`: fixed random seed, corpus version,
schema version, git SHA, Python version, platform, dependency versions relevant to the
benchmark, baseline versions, execution timestamp, and exact command line.

Determinism rules: seeded generation; sorted case/system iteration; `sort_keys=True` JSON;
CSV rows in stable order; adversarial transforms are pure functions. S0's runtime tokens
contain random salts by design; the harness therefore stores derived metric-relevant
flags (residual booleans, retained booleans), never raw replaced text, so reports stay
byte-deterministic across runs.

Run:

```bash
cd 24-1-ipu-ai-security-filter
python -m benchmark.runner --systems S0,S1,S3 --out benchmark/reports/R0_canonical
# equivalent script entry point:
python benchmark/run_benchmark.py --systems S0,S1,S3 --out benchmark/reports/R0_canonical
```

Tests:

```bash
python -m unittest discover -s benchmark/tests -t . -v
```

## 9. Known limitations

1. Synthetic-only corpus: measures behavior on constructed Korean-clinical-like text,
   not real clinical language distribution. Real-note validation is future work.
2. S1 is an in-repo reference implementation of generic PII heuristics, not an external
   product. Advantage over S1 must be interpreted with this asymmetry in mind.
3. Verbatim-presence transformation metrics are conservative proxies.
4. Utility retention is measured as textual presence of clinically important content,
   not downstream task performance. "downstream task utility delta" is NOT measured in R0.
5. Quasi-identifier combination ground truth encodes the taxonomy's assumptions about
   which combinations are risky (expert review of synthetic cases is a later step).
6. S2 absent; no public Korean-clinical baseline comparison.
7. Adversarial set is bounded and template-driven; it cannot prove robustness generally.

## 10. PASS / NARROW / STOP interpretation

Raw numbers decide; the runner emits a suggested verdict mechanically from these criteria,
and humans interpret them against Issue #736:

- PASS candidate: reproducible benchmark; S0 and S1 measured; B63 prototype shows material
  high-risk-PHI improvement OR clear contextual-risk capability unavailable in baselines;
  clinical utility measurable; no catastrophic adversarial recall collapse.
- NARROW: benefit confined to narrow entity families; weak utility gain; unstable
  contextual-risk agreement; small margin vs generic baseline.
- STOP/REFRAME: generic baseline already satisfies target clinical cases; no measurable
  B63 value; privacy gains destroy utility; benchmark itself cannot guide hospital validation.

Mechanical gates used by the runner (raw inputs are always attached to the verdict):

- measurable advantage: S3 high-risk F2 margin ≥ +5pp over the best baseline on base
  cases, OR QICDR margin ≥ +10pp;
- adversarial collapse: S3 loses more than half its base overlap-recall under the
  adversarial partition AND falls behind the best baseline there. Universal regex
  limits shared with baselines (e.g. OCR `0→O` corruption) are an adversarial-limit
  finding, not a prototype collapse;
- utility gate: at least medication/diagnosis retention measured for S3.

Tuning the benchmark to improve outcomes is forbidden; FAIL is an acceptable research result.

## 11. Result interpretation disclaimer

R0 results are synthetic-benchmark measurements. They do not constitute hospital
validation, regulatory evidence, or a medical-device performance claim.
