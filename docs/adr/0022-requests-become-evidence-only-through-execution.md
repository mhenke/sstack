# ADR-0022: Requests become evidence only through execution

**Status**: Accepted
**Date**: 2026-09-30
**Deciders**: Mike Henke

## Context

[ADR-0006](0006-evidence-re-verifiable-by-machine.md) made machine execution the contract: stdout, stderr, exit
code, and fingerprint come from running the repro, never from
transcription. The 2026-09-29/30 cold-run series showed the invocation
step was the contract's weak link, not the contract itself: across five
wording regimes — heredoc example, `--finding` availability,
Verify-stage imperative, co-located command, and finally the command
inside the ~16KB read-truncation window — glm-family backends wrote
correctly-shaped finding files 18/18 times and ran the emitter 0/0
times, fabricating a `report.json` and an "all tests pass" summary that
replay exposed as false (15 of 18 negative tests failing). The caller
that must cross the interface was the weakest actor in the system.

## Decision

The agent's emit act is a **write**, which every backend performs:
the moment a verdict is known, write the finding request to
`findings/<slug>.json` with `repro` as the exact command run, a plain
string. The emitter's no-stdin invocation is the **upgrade pass**:
it walks the findings dir, executes every request's repro itself,
computes the fingerprint, writes the evidence files, and rebuilds
`report.json` from evidence only (requests never appear in the
report). `--finding` and stdin still emit one finding immediately for
callers that can do it.

Two rules are absolute:

1. A request with no command stays a request — the machine never
   invents the missing command. `repro: null` is pending forever.
2. Transcribed output is discarded, not trusted — [ADR-0006](0006-evidence-re-verifiable-by-machine.md) stands,
   strengthened: even `--finding` payloads are re-executed, and the
   upgrade pass trusts nothing it did not run.

## Consequences

- The empty-stdin usage error is retired: empty stdin means "upgrade
  pending requests," which is always a defined, idempotent operation.
- The evidence contract is unchanged where it matters: fingerprints
  and output exist only from execution. What changed is who performs
  the last mile — the machine, always.
- Strong backends lose nothing: immediate single emit still works.
- The census that forces this lives in `evals/ACCEPTANCE.md`
  (read-window discovery, ColdWindowEmit completion).

Amended 2026-10-02, from the VS Code StringUtil field failure: a TTY
stdin counts as empty — the upgrade pass is the defined noninteractive
fallback, because reading a terminal blocks the call forever. Repro
execution is bounded at 120 seconds (`SSTACK_REPRO_TIMEOUT` overrides,
minimum 1): a hung repro is killed and recorded as exit 124 with the
kill noted in stderr — evidence about the repro's reliability, not an
emitter hang; partial output on a kill is discarded. The Python
upgrade pass also preflights referenced scratch probes, matching the
Node emitter (a probe that does not compile is infrastructure failure,
pending, not evidence).

Amended 2026-10-04: The upgrade pass processes pending requests into
evidence records; it does not re-execute or re-verify existing evidence
records. Replaying evidence belongs to out-of-loop tooling (`evals/replay.py`),
not the emitter ([ADR-0002](0002-content-only-agent-agnostic-skill.md), [ADR-0014](0014-do-not-build-mutation-runner.md)). The emitter remains a recorder,
never a test runner.
