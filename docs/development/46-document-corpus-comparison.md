# Document Corpus Comparison

## Purpose
Run `strict_token` and `local_rewrite` against real text assets already bundled in the project.

This is the first practical evaluation layer after the synthetic sample checks.

## Current Corpus
The current comparison corpus uses 12 text files already stored in the repository:

- short demo samples
- long demo samples
- derived template `.txt` outputs
- one empty-file negative case

Source registry:

- `engine/tests/document_corpus_registry.py`

## Run

```powershell
python engine/scripts/run_document_corpus_comparison.py
```

## What To Look At
For each file, compare:

1. detection count parity
- `local_rewrite` should not reduce detection coverage

2. safe output
- original detected spans must not remain in `replaced_text`

3. restore round-trip
- both policies should restore losslessly

4. tokenless readability
- `local_rewrite` should produce generalized readable output
- `strict_token` will remain tokenized by design

## Current Positioning
This corpus is not yet customer data.
It is the internal acceptance layer before real pilot documents are added.

## Next Expansion
After this passes consistently, add:

- public-sector document samples
- contract variants
- report variants
- customer support variants
- OCR-derived text samples

Keep new files in the registry instead of hardcoding them into the script.
