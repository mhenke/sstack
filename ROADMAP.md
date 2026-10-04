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
  Ninety-five goldens: nineteen seeds per fixture (`py-1` through
  `py-19` and peers), covering all fourteen lenses.
- Cold-run evidence (2026-09-27, content-match grader): **all five
  fixtures PASS**. Sixteen of nineteen seeds per fixture carry
  verified cold passes, py-2 included (closed by ColdPy-18);
  `*-17`/`*-18`/`*-19` carry goldens with cold-run evidence pending
  (run detail in [`evals/ACCEPTANCE.md`](evals/ACCEPTANCE.md)). Every
  PASS carries landed regressions verified on disk and evidence that
  replays with integrity ok.
- Findings JSON shipped with a pinned schema and out-of-loop replay;
  Learn loop proven cold (see Shipped below).

## Open, in order

### 1. Scan baseline triage *(shipped in text 2026-10-02 — cold evidence pending)*

- **Why**: a repeat run re-attacks everything with no memory of what
  changed; "what changed since last time?" is the user's first
  question on run two.
- **What**: Discover records the target's HEAD commit SHA in
  `map.md`; the next run derives changed files with one
  `git diff --name-only <baseline>..HEAD` and marks their surfaces as
  priority attack targets, re-deriving and diffing their recorded
  contracts. Changed = prioritized, never skipped; no baseline, no
  git, or scope mismatch degrades to a full run (ADR-0007, ADR-0019).
- **Done when**: a cold run on a changed scope cites its baseline
  diff in Discover and prioritizes changed surfaces; a non-git target
  takes the full-Discover path; both recorded in
  [`evals/ACCEPTANCE.md`](evals/ACCEPTANCE.md).

### 2. Host packaging *(blocked by v0 scope lock — requires v1 lift)*

- **Why**: install is one command (`npx skills add`) but update has
  no forced path; stale copies linger.
- **What**: a thin per-host updater (Cursor, OpenCode, Claude Code).
  No plugin API, no marketplace entry, no runtime. Requires lifting
  the scope lock's "no CLI, daemon, or binary" constraint (ADR pending).
- **Done when**: install and update are one command per host.

## Watch signals

- **`/sstack triage` skipped in practice**: if cold/field runs go
  straight to `/sstack <target>` without a triage pass, fold the
  heat pass into Discover's inventory step and retire the
  subcommand — the ideas (churn weighting, friction walk) then live
  in stage text, and `references/triage.md` shrinks to the snapshot
  format. Packaging follows usage, not precedent.

## Shipped — acceptance baseline, 2026-09-27

- All five fixtures PASS on current skill text with landed red→green
  regressions verified on disk: 15/16 named-seed coverage on
  seeded-py (py-2 unmatched, ColdPy-17 rerun missed it), 16/16 on
  ts/js/java/cpp. Each
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
- PBT seed and counterexample captured in evidence schema for replay determinism (ADR-0013).

## Explicitly not planned

- **A hosted runtime.** sstack runs where the agent runs (ADR-0002).
- **A test-generation product.** Happy-path coverage is the host
  repo's business (ADR-0001).
- **A security scanner.** Security is one lens among many
  (ADR-0001).
- **Mutation as the identity.** A verification strategy, never the
  frame (ADR-0001).
- **A dedicated PBT runner.** Delegates to target CLI; seed and
  counterexample captured in findings JSON (ADR-0013).
- **A built-in mutation runner.** Mutation testing in target repos
  violates zero-runtime (ADR-0002), fails in repos lacking tooling,
  explodes run latency, and duplicates the existing red-to-green proof
  gate (ADR-0014). Target repos delegate opportunistically via ADR-0004.
- **A live-surface runner.** The agent boots the target's own server
  and probes with `curl` through the emitter; a wrapper script adds no
  signal over the native command and would cost replay lifecycle
  management (ADR-0015).
- **Heavy reachability machinery on map rows.** Turns sstack into an
  AST security auditor or code-structure analyzer rather than negative
  testing (ADR-0001, ADR-0002). Reachability is an attack constraint
  ("a constant-only caller demonstrates no input path" in Verify), not
  an upfront mapping pass requiring AST or compiler toolchains.
- **Mechanical test-runner replay or baseline audits in the emitter.**
  evals/replay.py verifies evidence integrity outside the loop. The
  emitter records evidence and executes finding requests; it is not a
  test runner, CI orchestrator, or git state validator (ADR-0002,
  ADR-0006, ADR-0014).

## How a roadmap item ships

Seeded bugs in `evals/`, a cold run that finds them, a negative
control that flips, and the result in `evals/ACCEPTANCE.md`. A roadmap
item without acceptance evidence is not done, however good the prose
is.
