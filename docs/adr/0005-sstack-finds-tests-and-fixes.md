# ADR-0005: sstack finds, tests, and fixes

**Status**: Accepted (supersedes the audit-not-fix portion of ADR-0002)
**Date**: 2026-09-23
**Deciders**: Mike Henke

## Context

ADR-0002 established sstack as an audit, not a refactor. The skill
attacked, verified, minimized, and reported, but never fixed the
target's source. The rationale was evidence preservation: if the
attacker fixes the bug, you cannot prove the test would have caught it.

Six acceptance runs and a live product decision reversed that
position. The reasons:

1. **One run should close the loop.** Audit-only forces a context
   switch: the human reads the findings, understands each one, applies
   the fix, and re-runs sstack to verify. That friction is the reason
   negative testing does not happen.
2. **The fix is oracle-driven.** The oracle was declared before the
   attack. The fix is the minimal change that satisfies it. That is a
   small, mechanical, well-scoped diff, not an architectural rewrite.
3. **The red-then-green sequence preserves the evidence.** The test is
   written first and proven red on the buggy code. The fix is applied
   second and the test goes green. The evidence trail is intact: you
   know the test catches the bug because it was red before the fix.
4. **Hardening is the other half.** Surfaces that already handle the
   adverse condition correctly get green characterization tests. These
   lock in correct behavior against future regressions, even though no
   bug exists today.

## Decision

sstack finds, tests, and fixes. The lifecycle is Discover, Attack,
Verify, Minimize, Test, Fix. Source changes are allowed only in the
Fix stage, only for confirmed findings, and only the minimal change
that turns a red test green. Every source change must trace to a
finding.

## Consequences

**Good**

- One run closes the loop: find, test, fix, verify.
- The red-then-green sequence preserves the evidence that the test
  catches the bug.
- Hardening tests lock in correct behavior even where no bug exists.
- The fix is oracle-driven, so it is mechanical and minimal.

**Bad**

- The read-only containment barrier can no longer lock the full
  repo for the entire run. The lock applies during Attack and Test
  stages; the Fix stage requires write access to source.
- The same agent that found the bug also wrote the fix. Independent
  review of the fix is the human's job, not the tool's.
- Acceptance evidence is harder to produce: a cold run must
  demonstrate the full find-test-fix-green loop, not just find-and-test.

**Risks**

- The agent may over-fix or make non-minimal changes. Mitigated by
  the oracle-first constraint: the fix must satisfy a pre-declared
  oracle, and the diff must be the smallest one that does.
- The agent may break existing tests with the fix. Mitigated by the
  run-end check: the full suite must pass after all fixes are applied.
