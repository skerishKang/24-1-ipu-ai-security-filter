# 19. Main Branch Protection Policy

## Purpose

This document defines the repository merge gate and branch protection decision for IPU AI Firewall after the cleanup and productization planning queue.

This is a policy and runbook document only. It does not mutate GitHub branch protection, repository rulesets, GitHub Environments, deployment settings, DNS, or secrets.

## Current baseline

```text
MAIN_HEAD = 37871f63c6d93bb736cc69852ec81398bb8db5a0
OPEN_PR_COUNT = 0 before #114 work
OPEN_ISSUE_COUNT = 0 before #114 work
REMOTE_BRANCHES = main + B63 evidence branches only
MAIN_BRANCH_PROTECTED = false
REQUIRED_STATUS_CHECKS = enforcement off
```

The repository has moved from cleanup/product planning into demo preparation. The next work may touch deployment secrets, hosting configuration, and public demo exposure. `main` should therefore stop accepting unreviewed or untested changes by default.

## Decision

```text
MAIN_BRANCH_PROTECTION_DECISION = YES
MAIN_BRANCH_PROTECTION_RECOMMENDED = YES
APPLY_IMMEDIATELY_IN_THIS_PR = NO
OWNER_APPROVAL_REQUIRED_BEFORE_MUTATION = YES
```

`main` should be protected before actual owner-only demo environment configuration begins.

This PR records the policy. A separate explicit owner approval is required before applying repository settings.

## Required checks

```text
REQUIRED_CHECKS_DEFINED = YES
REQUIRE_CI = YES
REQUIRED_CHECK = CI / Engine, backend, and frontend smoke
REQUIRE_BRANCH_UP_TO_DATE = recommended after confirming GitHub UI check name behavior
```

The current CI gate covers:

```text
Python lint
engine tests
backend tests
frontend-backend live integration tests
frontend smoke tests
template mode smoke tests
frontend unit tests
```

For this repository, the required check should be the single GitHub Actions job currently named:

```text
Engine, backend, and frontend smoke
```

If GitHub exposes the required check as workflow/job combined text, use the exact UI-displayed check name. Do not guess a different status context.

## Pull request policy

```text
PR_REVIEW_POLICY_DEFINED = YES
REQUIRE_PULL_REQUEST_BEFORE_MERGE = YES
REQUIRE_APPROVAL_COUNT = 1
DISMISS_STALE_REVIEWS = optional for solo-owner phase
REQUIRE_CODE_OWNER_REVIEW = NO until CODEOWNERS exists
ALLOW_OWNER_ADMIN_BYPASS = YES for emergency only during early PoC
```

All normal changes should go through PR.

Emergency owner bypass is allowed only when all of the following are true:

```text
PRODUCTION_OR_DEMO_OUTAGE = YES
NO_SAFE_PR_PATH = YES
OWNER_EXPLICITLY_APPROVES_BYPASS = YES
POST_BYPASS_AUDIT_COMMENT_REQUIRED = YES
```

## Merge method policy

```text
SQUASH_MERGE_POLICY_DEFINED = YES
DEFAULT_MERGE_METHOD = squash
MERGE_COMMITS = discouraged
REBASE_MERGE = not default
DELETE_BRANCH_AFTER_MERGE = YES for ordinary feature/docs/test branches
```

Squash merge should remain the default because the repository is operated through narrow issue/PR units and clean main history is more useful than preserving every intermediate agent/local commit.

## Direct push policy

```text
DIRECT_PUSH_POLICY_DEFINED = YES
DIRECT_PUSH_TO_MAIN = NO
ALLOW_FORCE_PUSH = NO
ALLOW_DELETIONS = NO
```

Direct pushes to `main` should be blocked for normal work. If an emergency owner bypass occurs, it must be followed by an issue or PR comment recording:

```text
BYPASS_REASON
COMMAND_OR_SETTING_USED
HEAD_BEFORE
HEAD_AFTER
CI_OR_SMOKE_RESULT
FOLLOWUP_REMEDIATION_IF_ANY
```

## Evidence branch policy

```text
EVIDENCE_BRANCH_POLICY_DEFINED = YES
B63_EVIDENCE_BRANCHES_REMAIN = YES
EVIDENCE_BRANCH_PROTECTION_REQUIRED = NO
EVIDENCE_BRANCH_MUTATION = NO by convention
EVIDENCE_BRANCH_MERGE_TARGET = never unless separate owner decision
```

The two evidence branches are preserved as sealed/historical evidence branches:

```text
feat/b63-r0-clinical-privacy-benchmark
audit/b63-r0-sealed-holdout
```

They should not be deleted or merged as part of branch protection work. They can remain unprotected because they are not active integration branches; the governing rule is convention and explicit owner approval before mutation.

## Recommended GitHub setting target

When the owner approves actual application, configure `main` with this target:

```text
BRANCH = main
REQUIRE_PULL_REQUEST = true
REQUIRED_APPROVING_REVIEWS = 1
DISMISS_STALE_REVIEWS = false initially
REQUIRE_STATUS_CHECKS = true
REQUIRED_STATUS_CHECK = Engine, backend, and frontend smoke
REQUIRE_BRANCH_UP_TO_DATE = true if compatible with current queue flow
RESTRICT_PUSHES = false unless a team structure is introduced
ALLOW_FORCE_PUSHES = false
ALLOW_DELETIONS = false
LOCK_BRANCH = false
```

Do not enable stricter organization/team constraints until there is a stable collaborator/team model.

## Manual application runbook

Use the GitHub repository Settings UI or a verified `gh api` command after explicit owner approval.

Before applying:

```text
OPEN_PR_COUNT = 0
OPEN_ISSUE_OR_APPROVAL_THREAD_IDENTIFIES_POLICY = YES
LATEST_MAIN_HEAD_RECORDED = YES
REQUIRED_CHECK_NAME_CONFIRMED_IN_GITHUB_UI = YES
```

After applying:

```text
MAIN_BRANCH_PROTECTED = true
REQUIRED_STATUS_CHECKS_ENFORCEMENT = on
REQUIRED_CHECK_PRESENT = YES
DIRECT_PUSH_BLOCKED_OR_POLICY_CONFIRMED = YES
FORCE_PUSH_DISABLED = YES
DELETION_DISABLED = YES
```

Record the result in #114 or the follow-up settings-change issue.

## Acceptance mapping

```text
MAIN_BRANCH_PROTECTION_DECISION = YES
REQUIRED_CHECKS_DEFINED = YES
PR_REVIEW_POLICY_DEFINED = YES
SQUASH_MERGE_POLICY_DEFINED = YES
DIRECT_PUSH_POLICY_DEFINED = YES
EVIDENCE_BRANCH_POLICY_DEFINED = YES
NO_BRANCH_PROTECTION_MUTATION_WITHOUT_OWNER_APPROVAL = YES
```

## Next work

After this policy is merged, the next safe step is one of:

1. Owner explicitly approves applying main branch protection.
2. Create a settings-change issue/runbook for branch protection application.
3. Continue to actual demo environment secret/config preparation, but only after deciding whether main protection must be applied first.
