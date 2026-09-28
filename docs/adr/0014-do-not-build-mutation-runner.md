# ADR-0014: Do not build a mutation runner

**Status**: Accepted
**Date**: 2026-09-27
**Deciders**: Mike Henke

## Context

Item 1 on the roadmap proposed an evidence runner for mutation testing to gate Stage 5 (Test) and Stage 6 (Fix) with synthetic AST mutant generation and kill metrics.

Roadmap organizing rule: every item must raise proof quality or lower the cost of a run; anything that does neither is out.

A built-in mutation runner fails that test:
- **Zero runtime (ADR-0002):** Building an in-tree AST mutator across five languages (Python, TS/JS, Java, C++) requires language runtimes, parsers, or compilation toolchains, violating ADR-0002's zero-dependency rule and the v0 scope lock (`runners/` deferred to v1).
- **User lane reality (Two Lanes, AGENTS.md):** End users install only `skills/` and `agents/` into their own projects (`npx skills add`). Over 95% of target repos do not have `mutmut`, `stryker`, or `pitest` installed. A mandatory mutation gate causes `/sstack` to fail or block in almost every real-world project.
- **Run cost explosion:** Generating and executing mutants ($O(\text{mutants} \times \text{tests})$) dramatically inflates token usage and wall-clock latency, stalling fast agent loops.
- **Redundant with existing proof:** Stage 5/6 already gates completion on a concrete negative control: the regression test must go red on the unfixed defect and green on the minimal fix. This proves the test catches the failure without needing AST mutation.

## Decision

We will not build or ship a mutation runner, nor gate Stage 5 or 6 on mutation metrics.

1. Stage 5 and Stage 6 verification remains gated by the red-then-green regression test on the host repository's test runner.
2. Mutation testing remains an optional, opportunistic delegation per ADR-0004: if the target repository already has a mutation tool configured, the agent may invoke it scoped to the diff and record the score. When absent, it degrades inline per ADR-0007 without blocking the run.

## Consequences

**Good**
- Protects target user runs from failing on missing tools or stalling on expensive mutant sweeps.
- Preserves ADR-0002 (zero runtime dependencies, no CLI/daemon/binary) and the v0 scope lock.
- Avoids building and maintaining multi-language AST mutation engines in the pack.
- Maintains high agent velocity in target codebases.

**Bad**
- Does not provide a formal mutation kill ratio ($\frac{\text{killed}}{\text{total}}$) to verify assertion density.
- Relies on the red-to-green flip and agent discipline to ensure tests do not pass vacuously.

**Risks**
- If cold agents frequently land tests that pass vacuously despite the red-to-green check, revisit mutation testing strictly within the contributor lane (`evals/` fixture graders), never as an end-user gate.
