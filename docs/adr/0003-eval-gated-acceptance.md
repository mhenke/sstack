# ADR-0003: Eval-gated acceptance with seeded repos

**Status**: Accepted
**Date**: 2026-09-23
**Deciders**: Mike Henke

## Context

A skill pack is prose, and prose does not fail a test suite. The only
honest way to know whether sstack works is to run it: give a cold
agent nothing but the skill and a deliberately broken repository, and
see what it finds. "The demo looked good" is not evidence.

The design had to answer four questions the demos kept getting wrong:

- How is the answer key kept from the agent? (`BUGS.md` answer keys,
  stripped at run time)
- How is a "finding" scored? (a regression test that fails on the
  seed and passes after the canonical fix, not a claim)
- How is the run kept from being contaminated? (the skill's own
  worked examples once leaked 8 of 10 seed oracles; the agent read
  them)
- How is the target kept from reaching the real repo? (prompt-only
  containment failed; skill + decontaminated fixture now ship in one
  isolated temp workspace)

## Decision

Acceptance is a **cold-run eval**, recorded in `evals/ACCEPTANCE.md`:

- Five seeded repos (Python/pytest, TypeScript/vitest, JavaScript/node,
  Java/JUnit, C++/CTest), five bugs each, every bug mapped to exactly
  one lens and listed in a `BUGS.md` answer key.
- `python3 evals/acceptance.py prepare <fixture>` copies the skill and
  a BUGS.md-free, cache-free fixture into one temp workspace. The cold
  agent works only inside it.
- A repo passes when the agent confirms seeded bugs with oracle
  regressions that go **red** on the seed and **green** after the
  canonical fix.
- Every cold-run failure is kept in the record, with the product fix
  it forced. The failing runs are the reason the skill's guardrails
  exist.

## Consequences

**Good**

- The acceptance record is evidence, not marketing; it names seeds
  found, seeds missed, and every run that failed.
- Failures compound into product fixes. Six cold runs produced four
  shipped guardrails (bug-pinning, audit-not-fix, decontamination,
  attack-validity) that the record explains.
- The negative control is the real proof: a regression that cannot go
  green after the fix was pinning the bug, not catching it.

**Bad**

- Expensive: a full re-run is roughly 20–35 minutes of subagent time
  across both repos.
- Any edit to the skill invalidates the record by the repo's own rule
  (the evidence came from exact text), so shipping a wording change
  carries a re-run debt.
- Contamination is a live failure mode. The answer key lives in the
  same repo as the skill, one grep away from leaking into a lens
  example.

**Risks**

- If the answer key ever leaks again, the affected run's numbers are
  void until re-run on clean lens files. Guard: keep every lens
  worked example on a surface absent from both `BUGS.md` files, and
  re-check with a seed-string grep after any lens edit.
