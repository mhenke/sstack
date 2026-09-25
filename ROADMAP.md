# Roadmap

Where sstack goes next. Each open item names its evidence and its done
condition. Shipped items are one line with the commit, not design
docs. Decisions behind v0 live in [`docs/adr/`](docs/adr/README.md).

Organizing rule: every item must raise proof quality or lower the cost
of a run. Anything that does neither is out.

## Current state

- Seven lenses shipped: boundaries, malformed, missing, ownership,
  exceptional-conditions, resource-exhaustion, state. A target repo
  can add more without a pack change (ADR-0008).
- Five seeded fixtures: Python, TypeScript, JavaScript, Java, C++.
  Twenty-seven goldens; seeded-py carries seven.
- Cold-run evidence (2026-09-25, content-match grader): **all five
  fixtures PASS**. Seeds matched: py 5/5 (ColdPy-5, the state seed
  included; Learn-run-2 proved the loop), js 5/5, ts 5/5, java 3/5
  (ColdJava-3 re-run — first java wave with replayed evidence), cpp
  3/5. Every PASS carries landed regressions verified on disk and
  evidence that replays with integrity ok.
- Findings JSON shipped with a pinned schema and out-of-loop replay
  (`b05b94b`); Learn loop proven cold (see Shipped below).

## Open, in order

### 1. Remaining lenses

- **What**: `ordering`, `concurrency`, `idempotency` next, then
  `dependency-failure`, `contract`. Any of the eight unbuilt index
  rows can be activated today by a target repo with a lens file, per
  ADR-0008, without a pack change. Shipping one in the pack stays
  additive: one agent file, one skill file, one index row. (`state`
  shipped 2026-09-25 with seed `py-6`, exercised in ColdPy-5.
  `ownership` gained collection surfaces and seed `py-7`, which has
  had a targeted carrier run but no full cold pass.)
- **Done when**: new seeds per shipped lens, majority confirmed per
  fixture.

### 2. Host packaging

- **Why**: install is one command (`npx skills add`) but update has
  no forced path; stale copies linger.
- **What**: a thin per-host updater (Cursor, OpenCode, Claude Code).
  No plugin API, no marketplace entry, no runtime.
- **Done when**: install and update are one command per host.

## Shipped — acceptance baseline, 2026-09-24

- All five fixtures PASS on current skill text with landed red→green
  regressions verified on disk: py 5/5 seeds (twice), js 5/5, ts 4/5,
  java 3/5, cpp 3/5. Each wave-1 failure converted to PASS on rerun
  and motivated its guardrail: hand-typed JSON → script-emitted
  contract; zombie run → pristine-file rejection; phantom
  `test_functions.cpp` → run-end check #1 (repo suite, not scratch
  binaries).
- Evidence re-verification: `replay` recomputes fingerprints and
  re-runs commands with the agent out of the loop — py 10/10 + 8/8,
  ts 7/7, js 12/12, cpp 13/13 intact; wave-1 fabrications caught by
  exactly this tool.
- Learn loop proven cold: run 2 opened Discover citing run 1's three
  `.sstack/learn/` classes verbatim, attacked in learned order, and
  matched 5/5 seeds where run 1 matched 3/5.

### Earlier, one line each

- Evidence JSON schema + replay verifier (`0765cb3`, `0ddecd6`,
  `b05b94b`): content-match grading, integrity recomputation.
- Run-end checklist, PBT delegation, mutation refs in skill text (`5de75b3`).
- Thermos fan-out with `runSubagent` + inline context (`e78ee07`, `07f3e5c`).
- Six peer lens skills + six attacker agents (`0765cb3`).
- Five seeded fixtures (`aae7108`).
- Unified eval entry point `evals/acceptance.py` (`2aa556f`).
- Learn loop in skill text (`4da9a5f`).
- Lifecycle principle mapping (`f7e053a`).
- Goldens backfilled for js/java/cpp; junit jar auto-fetch (`fd3004e`).

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
