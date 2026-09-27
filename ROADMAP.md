# Roadmap

Where sstack goes next. Each open item names its evidence and its done
condition. Shipped items are one line, not design docs. Decisions
behind v0 live in [`docs/adr/`](docs/adr/README.md).

Organizing rule: every item must raise proof quality or lower the cost
of a run. Anything that does neither is out.

## Current state

- Fourteen lenses shipped: boundaries, malformed, missing, ownership,
  exceptional-conditions, resource-exhaustion, state, ordering,
  concurrency, idempotency, dependency-failure, contract, security,
  agent. A target repo can add more without a pack change (ADR-0008).
- Five seeded fixtures: Python, TypeScript, JavaScript, Java, C++.
  Eighty goldens: sixteen seeds per fixture (`py-1` through `py-16`
  and peers), covering all fourteen lenses.
- Cold-run evidence (2026-09-27, content-match grader): **all five
  fixtures PASS**. Every one of the sixteen seeds has a verified cold
  pass in every fixture (run detail in
  [`evals/ACCEPTANCE.md`](evals/ACCEPTANCE.md)). Every PASS carries
  landed regressions verified on disk and evidence that replays with
  integrity ok.
- Findings JSON shipped with a pinned schema and out-of-loop replay;
  Learn loop proven cold (see Shipped below).

## Open, in order

### 1. Evidence runners and mutation

- **What**: `mutation` runner. Mutation testing is an evidence runner
  (Stage 5/6) rather than an attack lens (it mutates ASTs rather than
  executing adverse client cases). It can be activated today by a target
  repo with an evidence runner or custom lens, per ADR-0008, without a
  pack change. All 14 shipped lenses have a seeded defect in
  `evals/seeded-py` — `py-1` through `py-16`, covering every lens in
  `BUGS.md` — and every seed has a verified cold pass (ColdPy-5, -11,
  -12, -13, -14, -15, -16) with 0 drift in `evals/ACCEPTANCE.md`.
- **Done when**: mutation runner gates Stage 5/6 with mutant generation
  and kill metrics.

### 2. Host packaging

- **Why**: install is one command (`npx skills add`) but update has
  no forced path; stale copies linger.
- **What**: a thin per-host updater (Cursor, OpenCode, Claude Code).
  No plugin API, no marketplace entry, no runtime.
- **Done when**: install and update are one command per host.

## Shipped — acceptance baseline, 2026-09-27

- All five fixtures PASS on current skill text with landed red→green
  regressions verified on disk: 16/16 seeds on every fixture. Each
  wave-1 failure converted to PASS on rerun
  and motivated its guardrail: hand-typed JSON → script-emitted
  contract; zombie run → pristine-file rejection; phantom
  `test_functions.cpp` → run-end check #1 (repo suite, not scratch
  binaries).
- Evidence re-verification: `replay` recomputes fingerprints and
  re-runs commands with the agent out of the loop — every confirmed
  finding's evidence replays intact (per-fixture counts in
  [`evals/ACCEPTANCE.md`](evals/ACCEPTANCE.md)); wave-1 fabrications
  were caught by exactly this tool.
- Learn loop proven cold: run 2 opened Discover citing run 1's three
  `.sstack/learn/` classes verbatim, attacked in learned order, and
  matched 5/5 seeds where run 1 matched 3/5.

### Earlier, one line each

- Evidence JSON schema + replay verifier: content-match grading,
  integrity recomputation.
- Run-end checklist, PBT delegation, mutation refs in skill text.
- Thermos fan-out with `runSubagent` + inline context.
- Six peer lens skills + six attacker agents.
- Five seeded fixtures.
- Unified eval entry point `evals/acceptance.py`.
- Learn loop in skill text.
- Lifecycle principle mapping.
- Goldens backfilled for js/java/cpp; junit jar auto-fetch.

## Explicitly not planned

- **A hosted runtime.** sstack runs where the agent runs (ADR-0002).
- **A test-generation product.** Happy-path coverage is the host
  repo's business (ADR-0001).
- **A security scanner.** Security is one lens among many
  (ADR-0001).
- **Mutation as the identity.** A verification strategy, never the
  frame (ADR-0001).

## How a roadmap item ships

Seeded bugs in `evals/`, a cold run that finds them, a negative
control that flips, and the result in `evals/ACCEPTANCE.md`. A roadmap
item without acceptance evidence is not done, however good the prose
is.
