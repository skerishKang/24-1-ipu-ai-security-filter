# Local Rewrite Evaluation Plan

## Goal
Decide whether `local_rewrite` is only an experiment or ready to become a promoted preview policy.

The decision must be based on repeatable checks, not UI feel alone.

## Scope
Compare these policies:

- `strict_token`
- `local_rewrite`

Use the same input samples and judge them on the same criteria.

## Immediate Evaluation Criteria
Every sample should be checked on four axes:

1. Detection coverage
- Did the engine detect the expected sensitive spans?
- `local_rewrite` is not allowed to reduce coverage relative to `strict_token`.

2. Leak safety
- Does the replaced text still contain original sensitive values?
- Any direct leak is an automatic fail.

3. Restore safety
- Can the replaced result be restored back to the original text through the session mapping?
- This must remain lossless.

4. Readability / business utility
- Is the rewritten result usable as a business-facing sanitized text?
- `strict_token` is allowed to be less readable.
- `local_rewrite` should be more readable without reintroducing leaks.

## Promotion Rule
`local_rewrite` can be promoted from experiment to broader preview use only if:

- coverage is not worse than `strict_token`
- leak safety remains zero-leak on the evaluation set
- restore round-trip remains lossless
- rewritten output is consistently easier to read than tokenized output

If any one of those fails, keep `local_rewrite` as an experiment.

## Evaluation Set
Use two layers:

1. Quick comparison set
- `engine/tests/rewrite_comparison_samples.py`
- fast manual review set for business readability

2. Quality harness set
- `engine/tests/quality_samples.py`
- broader regression set for coverage and restore safety

## Commands
Quick side-by-side comparison:

```powershell
python engine/scripts/run_rewrite_comparison.py
```

Scorecard view:

```powershell
python engine/scripts/run_rewrite_scorecard.py
```

Regression harness:

```powershell
python engine/scripts/run_quality_harness.py
```

Test suite:

```powershell
python -m unittest ^
  engine.tests.test_manual_preview_engine ^
  engine.tests.test_local_rewriter ^
  engine.tests.test_local_rewrite_comparison ^
  engine.tests.test_quality_harness ^
  backend.tests.test_manual_preview_local_rewrite_api
```

## Review Workflow
1. Run `run_rewrite_comparison.py`
2. Run `run_rewrite_scorecard.py`
3. Review samples where `local_rewrite` looks unnatural or leaks context
4. Promote repeated wins into templates or rules
5. Keep one short decision note per evaluation round

## What To Do Next
If `local_rewrite` keeps winning on readability without leaks:

- add document-type overlays
- add model prompt variants by use case
- consider exposing `local_rewrite` more prominently in the UI

If it does not:

- keep it as expert-only experimental mode
- continue improving rules and templates first
