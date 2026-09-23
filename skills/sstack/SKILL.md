---
name: sstack
description: Use when the user wants negative testing, edge-case coverage, failure-mode analysis, robustness checks, hostile or unexpected input handling, "what happens if" questions about code, or to harden a module or API against bad input before shipping. Discovers failure surfaces, attacks them through lenses (boundaries, malformed, missing), verifies observed behavior against a pre-declared oracle, and turns confirmed failures into permanent regression tests. Not for happy-path feature work.
---

# sstack — structured negative testing

> Don't ask whether the software is robust. Exercise the failure
> condition and collect evidence.

## The four rules

1. Attack assumptions.
2. Define the oracle before the attack. Expected behavior under the
   adverse condition — error, degradation, retry bound, invariant,
   rejection. "It crashes" is not an oracle; "it raises a
   validation error naming the field" is.
3. Never accept an agent's claim as evidence. Run the real command,
   quote the real output.
4. Turn confirmed failures into permanent regressions.

## Routing

- `/sstack <target>` — run the full lifecycle on a module, file,
  directory, or function.
- `/sstack` (bare) — infer the target from recent changes
  (`git status`, `git diff --stat`); ask only if nothing is
  inferable.
- `/sstack <stage>` (discover | attack | verify | minimize |
  regress) — enter that stage using existing `.sstack/` state.
- `/sstack lenses` — print the lens index below.

## Workspace

All artifacts live under `.sstack/` in the host repo:

- `map.md` — surfaces + assumed contracts (Discover output)
- `plan.md` — scoped run plan: selected lenses, cases, oracles
- `findings/<slug>.md` — one per finding, fields:
  `lens, surface, case, oracle, observed (verbatim), verdict
  (confirmed | refuted | inconclusive), repro (command),
  regression (test file + name + fail|pass)`
- `scratch/` — throwaway scripts; delete at run end

## Stages

### 1. Discover

Map the target's failure surfaces: public functions and classes,
API routes, anything that parses external input, loops over
collections, or indexes/slices. For each surface, record its
assumed contract — types, ranges, preconditions gleaned from
docstrings, types, and call sites. Write `.sstack/map.md`.

### 2. Attack

Pick applicable lenses from the index. Read each selected
`references/lens-*.md` before designing cases. For each
surface × lens:

1. Design the case (concrete input and action).
2. Write its oracle in `plan.md` FIRST — the expected behavior
   under this adverse condition.
3. Execute for real: a scratch script under `.sstack/scratch/`,
   or a direct call through the repo's test framework.
4. Record the actual output verbatim.

Never design the oracle after seeing the result.

Cover every selected lens on every mapped surface before
concluding. A lens with zero executed cases on a surface that
consumes record/dict-shaped or string input is an incomplete
run, not a clean result.

### 3. Verify

Per case, compare oracle vs. observed:

- **confirmed** — observed violates the oracle, and the case
  reproduces on a second run.
- **refuted** — system satisfies the oracle.
- **inconclusive** — oracle unclear or execution unreliable.
  Inconclusive findings are never promoted to regressions.

### 4. Minimize

For each confirmed finding, strip the case to the smallest input
that still violates the oracle. Update the repro command.

### 5. Regress

Write a permanent test in the host repo's real suite — same
directory and assert style as existing tests, asserting the
oracle. Never assert the observed buggy behavior: a test that
passes against code you just confirmed broken has pinned the
bug and is worthless. After writing each test, run it:

- Test FAILS against current code → correct live-bug
  regression; note it as `fail`.
- Test PASSES → either the bug is already handled (mark the
  finding refuted and keep the test as characterization) or
  the test is wrong — re-check it against the oracle before
  accepting it.

Run the new tests. Then deliver the report in chat FIRST;
persisting `findings/` files is bookkeeping that follows.

## Lens index

| Lens | Applies when | Reference |
|---|---|---|
| boundaries | numbers, sizes, indexes, slices, collections, pagination, loops | references/lens-boundaries.md |
| malformed | strings parsed from outside, JSON, encodings, dynamic types | references/lens-malformed.md |
| missing | optional fields, records from external data, null/None/undefined | references/lens-missing.md |

## Safety

- Read-only toward source, config, and secrets. Write only tests
  and `.sstack/`.
- Never mutate source to demonstrate a bug. Reproduce in scratch
  space.
- No test framework detected → ask before scaffolding one.
- Respect the repo's test conventions exactly.

## Report format

One line per finding: `id | lens | surface | verdict | regression
(file::test, fail|pass)`. Then per confirmed finding the full
field set, with observed output quoted verbatim. End with counts:
confirmed / refuted / inconclusive, regressions landed.

If any finding is confirmed but every landed regression
passes, the run is invalid: re-check those tests against
their oracles.
