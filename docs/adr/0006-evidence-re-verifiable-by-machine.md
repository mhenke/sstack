# ADR-0006: Finding evidence is machine-re-verifiable

**Status**: Accepted
**Date**: 2026-09-24
**Deciders**: Mike Henke

## Context

ADR-0003 defined a finding as evidence-backed: oracle declared before
the attack, observed output quoted verbatim, a regression that goes
red on the seed and green after the fix. Every link in that chain was
verified by the agent that produced it. The acceptance record shows
what that costs trust: run #5 read 105 broken-harness TypeErrors as
satisfied oracles; a cold run reported five confirmed C++ findings
that no grader could trace to commands.

The findings JSON existed as prose ("command, exit code, stdout,
stderr, input fingerprint…") with no pinned key names, so every agent
invented its own shape and nothing downstream could read it.

## Decision

The `.sstack/findings/<slug>.json` machine view has one exact shape,
pinned in the skill: `command`, `exit_code`, `stdout`, `stderr`,
`fingerprint` (sha256[:16] of stdout+stderr), `oracle`, `verdict`,
`regression{file,test,before,after}`. `python3
evals/acceptance.py replay <workspace>` re-runs each recorded command
with the agent out of the loop and compares exit code and output
fingerprint against the record. A finding whose evidence does not
replay is a finding not proven.

## Consequences

**Good**: the four rules keep their meaning without trusting the
actor — "never accept an agent's claim as evidence" now has a second,
agent-free checker. Grading and replay share one entry point. Report
fraud and honest harness mistakes both surface as `mismatch`.

**Bad**: the schema is a compliance tax on cold agents; the current
five runs predate it and hold no replayable evidence, so item 2 of
the roadmap needs the fresh runs already in flight. Strict shapes
also fail loudly on near-misses (a trailing-whitespace difference
flips `verified` to `mismatch`).

**Risks**: fingerprint stability depends on the recorded command
being deterministic in the recorded workspace; flaky tests will
produce false mismatches. Revisit if mismatch rate in replay exceeds
the actual error rate in findings — the fix would be a normalized
fingerprint (trim, sort), not a weaker check.
