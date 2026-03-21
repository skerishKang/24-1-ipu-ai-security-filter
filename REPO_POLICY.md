# Repository Policy

This workspace uses two history systems with different roles.

## Source of Truth
- Fossil is the primary local history system.
- Use Fossil for frequent local checkpoints, safety commits, and dense work-in-progress history.

## Git Role
- Git exists for GitHub sync, remote sharing, and reviewable curated commits.
- Git commits should be intentional, readable, and suitable for pushing to GitHub.
- Do not assume Git is the only or primary local history source.

## Fossil Artifacts
- `_FOSSIL_` and `*.local.fossil` are intentional in this workspace.
- They are not accidental residue by default.
- Do not recommend deleting Fossil artifacts unless the user explicitly says Fossil is no longer needed here.

## Working Rule
- When evaluating repository state, separate:
  - curated Git history
  - primary Fossil local history
  - local runtime or junk files
- Do not treat "not pushed to GitHub" as "not recorded". It may already be safely recorded in Fossil.

## Review Expectations
- Prefer identifying:
  - real code or doc changes that should become curated Git commits
  - local-only helper files that should be ignored
  - accidental runtime or generated artifacts
- Avoid recommending broad cleanup without distinguishing Fossil-managed history from junk.
