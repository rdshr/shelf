<!--
Sync Impact Report
- Version change: template -> 1.0.0
- Modified principles:
  - Principle 1 placeholder -> I. Spec-First Delivery
  - Principle 2 placeholder -> II. Traceable Work Items
  - Principle 3 placeholder -> III. Verification Before Merge
  - Principle 4 placeholder -> IV. Operational Clarity
  - Principle 5 placeholder -> V. Keep It Minimal and Reversible
- Added sections:
  - Additional Constraints
  - Delivery Workflow & Quality Gates
- Removed sections:
  - None
- Templates requiring updates:
  - ✅ updated .specify/templates/plan-template.md
  - ✅ updated .specify/templates/spec-template.md
  - ✅ updated .specify/templates/tasks-template.md
  - ⚠ pending .specify/templates/commands/*.md (directory not present in this repository)
- Follow-up TODOs:
  - None
-->
# Shelf Constitution

## Core Principles

### I. Spec-First Delivery
All implementation work MUST be anchored to an approved `spec.md` and `plan.md`
before coding starts. A feature without scoped user stories, measurable success
criteria, and explicit constraints is not ready for implementation.
Rationale: upfront clarity prevents rework and keeps delivery tied to user value.

### II. Traceable Work Items
Every implementation task MUST map to a specific user story and include exact
target file paths. Cross-story coupling MUST be explicitly justified in the plan.
Rationale: traceability enables safe parallel work and predictable review.

### III. Verification Before Merge
Each user story MUST include an independent verification method and objective
acceptance criteria. Verification MAY be automated tests, manual procedures, or
both, but evidence of execution MUST be captured in tasks or PR notes.
Rationale: completed code is not accepted without proof that behavior matches spec.

### IV. Operational Clarity
Changes affecting runtime behavior MUST document configuration, failure modes,
and observable signals (logs, error messages, or metrics) in feature artifacts.
When a quickstart or runbook exists, it MUST be kept consistent with the change.
Rationale: operability is part of feature completeness, not post-release cleanup.

### V. Keep It Minimal and Reversible
Designs MUST choose the simplest option that satisfies current requirements.
New dependencies, abstractions, or architecture layers MUST include a written
need statement and rollback path when risk is non-trivial.
Rationale: simplicity improves change velocity and reduces regression surface.

## Additional Constraints

- Primary workflow tooling is `specify-cli` with Codex (`CODEX_HOME=.codex`).
- Development environment assumptions MUST stay Linux-compatible.
- New process guidance MUST be committed under `.specify/templates` or
  repository docs so automation and human workflows remain aligned.

## Delivery Workflow & Quality Gates

1. Spec Phase Gate: `spec.md` defines prioritized user stories, acceptance
   scenarios, edge cases, and measurable success criteria.
2. Plan Phase Gate: `plan.md` passes Constitution Check with no unresolved
   violations, or violations are documented in Complexity Tracking.
3. Tasks Phase Gate: `tasks.md` groups work by story and includes verification
   tasks or explicit manual validation steps for each story.
4. Review Phase Gate: PR/review notes MUST reference story IDs and include
   verification evidence for changed behavior.

## Governance

This constitution is the authoritative process standard for this repository and
supersedes conflicting guidance in ad hoc documents.

Amendment procedure:
1. Propose changes via PR with a clear rationale and migration impact.
2. Update impacted templates and guidance files in the same change.
3. Obtain maintainer approval before merge.

Versioning policy:
- MAJOR: incompatible governance changes or principle removals/redefinitions.
- MINOR: new principle/section or materially expanded mandatory guidance.
- PATCH: wording clarifications and non-semantic refinements.

Compliance review expectations:
- Every feature plan MUST pass the Constitution Check.
- Every task list MUST preserve story traceability and verification evidence.
- Reviewers MUST block merges that violate mandatory gates without approved
  and documented exceptions.

**Version**: 1.0.0 | **Ratified**: 2026-02-27 | **Last Amended**: 2026-02-27
