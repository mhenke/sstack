# Roadmap

Where sstack goes next. Each open item names its evidence and its done
condition. Shipped items are one line with the commit, not design
docs. Decisions behind v0 live in [`docs/adr/`](docs/adr/README.md).

Organizing rule: every item must raise proof quality or lower the cost
of a run. Anything that does neither is out.

## Current state

- Six lenses shipped: boundaries, malformed, missing, ownership,
  exceptional-conditions, resource-exhaustion.
- Five seeded fixtures: Python, TypeScript, JavaScript, Java, C++.
- Cold-run evidence (2026-09-24, content-match grader): Python PASS
  twice — Learn-run-2 matched 5/5 seeds; Java PASS (3/5 seeds); C++
  FAIL (evidence intact, regressions never landed); TS FAIL (zombie,
  nothing landed); JS INVALID first wave. Reruns in progress:
  ColdJs-2, ColdTs-3, ColdCpp-2.
- Findings JSON shipped with a pinned schema and out-of-loop replay
  (`b05b94b`); Learn loop proven cold (see item 3).

## Open, in order

### 1. Acceptance re-runs

- **Why**: no current claim is proven. Fresh runs exist but are
  ungraded or malformed; historical passes are stale.
- **What**: cold runs against all five fixtures on the current skill
  text, graded by `evals/acceptance.py grade`, recorded in
  `evals/ACCEPTANCE.md`.
- **Done when**: every fixture has a graded verdict and every PASS has
  a red→green negative control.

### 2. Evidence re-verification — nearly done

- **What**: `evals/acceptance.py replay <workspace>` recomputes each
  evidence file's fingerprint (integrity) and re-runs its command
  (drift, informational post-fix).
- **Status**: Python replays 10/10 intact (Learn-run-2) and 8/8 (run
  1). JS wave 1 and TS wave 1 caught as fabricated/unparseable —
  those ARE the filed failures. Java's PASS shipped no evidence
  JSONs (it ran before the schema pin); its reruns will carry them.
- **Done when**: the three in-flight reruns (js/ts/cpp) each replay
  with integrity ok or their failures are recorded.

### 3. Learn-loop proof — DONE (2026-09-24)

- Run 1 (ColdPy-2) recorded three learned classes; run 2 (ColdPy-R2)
  opened Discover citing all three verbatim in `.sstack/map.md` and
  attacked `paginate`, `line_total`, `add_item` in learned order.
  Result: 5/5 seeds content-matched (run 1: 3/5), zero label
  contradictions, 10/10 evidence replay intact.

### 4. Remaining lenses

- **What**: `state`, `ordering`, `concurrency`, `idempotency` next,
  then `dependency-failure`, `contract`. Additive: one agent file,
  one skill file, one index row each.
- **Done when**: new seeds per shipped lens, majority confirmed per
  fixture.

### 5. Host packaging

- **Why**: install is one command (`npx skills add`) but update has
  no forced path; stale copies linger.
- **What**: a thin per-host updater (Cursor, OpenCode, Claude Code).
  No plugin API, no marketplace entry, no runtime.
- **Done when**: install and update are one command per host.

## Shipped (one line each)

- Structured evidence JSON in skill text (`0765cb3`); re-verification open.
- Run-end checklist in skill text (`5de75b3`); acceptance pending.
- PBT delegation and mutation refs in skill text (`5de75b3`); acceptance pending.
- Thermos fan-out with `runSubagent` + inline context (`e78ee07`, `07f3e5c`).
- Six peer lens skills + six attacker agents (`0765cb3`).
- Five seeded fixtures (`aae7108`).
- Unified eval entry point `evals/acceptance.py` (`2aa556f`).
- Learn loop in skill text (`4da9a5f`); proof open.
- Lifecycle principle mapping (`f7e053a`).
- Content-match grader + integrity replay (`b05b94b`).
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
