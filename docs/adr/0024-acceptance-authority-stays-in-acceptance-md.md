# ADR-0024: Acceptance authority stays in ACCEPTANCE.md

**Status**: Accepted
**Date**: 2026-10-05
**Deciders**: Mike Henke

## Context

Cold acceptance results (pass/fail verdicts, execution dates, seed coverage, and historical run logs) were previously duplicated across the root `README.md`, `evals/ACCEPTANCE.md`, and `evals/README.md`.

When fixture seeds expanded from 16 to 19 under [ADR-0010](0010-cross-language-fixture-parity.md) parity and cold baselines were reset in v0.5.1, `evals/README.md` diverged into an outdated snapshot (claiming 16 seeds and 2026-09-27 dates). This created a maintenance trap and contradicted the live record. Additionally, internal repository artifacts mentioned in `evals/README.md` (`ACCEPTANCE.md`, `BUGS.md`, `acceptance.py`, `goldens.jsonl`, `graders/seeded_acceptance.py`, ADRs) were authored as unlinked backticks, frustrating repository navigation on GitHub and mobile interfaces.

## Decision

We will maintain `evals/ACCEPTANCE.md` as the sole authority of record for all cold-agent acceptance results, dates, and historical run outcomes. Fixture documentation (`evals/README.md`) defines fixture specifications, baseline test commands, and eval workflows without duplicating status tables or snapshot dates, linking directly to `evals/ACCEPTANCE.md`. All internal artifact and ADR references across contributor documentation must use active relative markdown links.

## Consequences

**Good**:
- Eliminates multi-file synchronization drift: running or expanding evals requires updating only `evals/ACCEPTANCE.md` (and the root summary table).
- Navigation across contributor documentation is immediate via clickable relative links.
- `evals/README.md` remains stable across eval runs and focused on operational instructions.

**Bad**:
- Readers viewing `evals/README.md` do not see instant pass/fail tables and must click through to `ACCEPTANCE.md`.

**Risks**:
- Future PRs might attempt to re-introduce status snapshots into `evals/README.md`. Guard: keep fixture documentation strictly structural (language, harness commands, seed definitions).
