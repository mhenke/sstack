# ADR-0013: Do not build a dedicated PBT runner; record seeds in evidence

**Status**: Accepted
**Date**: 2026-09-27
**Deciders**: Mike Henke

## Context

Following ADR-0004's delegation to target testing tools and the addition of PBT references to Stage 2 (Attack) and Stage 5 (Test) in `skills/sstack/SKILL.md`, the question arose whether sstack should build a dedicated PBT runner script under `runners/` (e.g. `runners/pbt.py` / `runners/pbt.js`) for v1.

Roadmap organizing rule: every item must raise proof quality or lower the cost of a run; anything that does neither is out.

A dedicated PBT runner script fails that test:
- It does not lower run cost: the agent already executes target test frameworks directly via native CLI commands (`pytest`, `vitest`, `mvn`). A custom wrapper script does nothing the native command cannot do.
- It does not raise proof quality: PBT frameworks already print their own random seeds and shrunk counterexamples to stdout. A wrapper script adds zero signal.
- It inflates pack maintenance: adds boilerplate scripts, extra cognitive load for cold agents, and complicates the zero-runtime promise of ADR-0002.
- Like mutation testing (evaluated and rejected in ADR-0014 due to runtime, toolchain, and latency constraints), in-tree runners add runtime bloat without sufficient return. PBT requires only standard target CLI execution with framework flags.

However, PBT introduces a real integrity risk to machine replay (ADR-0006): because PBT is pseudorandom, a counterexample found by an agent cannot be reliably replayed out-of-loop by `evals/replay.py` unless the random seed and minimized counterexample are captured.

## Decision

1. sstack will **not** build, ship, or bundle a dedicated PBT runner script. Attack and verification will continue to delegate directly to target CLI commands.
2. The evidence schema (`emit_findings.py` and `emit_findings.js`) will support recording optional `seed` and `counterexample` fields in finding payloads.
3. When PBT is used by an agent, recording the seed and minimal counterexample is required so that machine replay under ADR-0006 is 100% deterministic.

## Consequences

**Good**
- Zero added script bloat or runner complexity in the pack.
- Replay determinism (ADR-0006) preserved when targets use Hypothesis, fast-check, jqwik, or RapidCheck.
- Adheres strictly to the ROADMAP organizing rule (cuts unnecessary tooling; keeps what raises proof quality).

**Bad**
- Agents must extract the seed and counterexample from CLI stdout and include them in the finding emission payload.
