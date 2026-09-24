---
name: sstack
description: Use when the user wants negative testing, edge-case coverage, failure-mode analysis, robustness checks, hostile or unexpected input handling, "what happens if" questions about code, or to harden a module or API against bad input before shipping. Discovers failure surfaces, attacks them through lenses (boundaries, malformed, missing), verifies observed behavior against a pre-declared oracle, and turns confirmed failures into permanent regression tests. Scope is existing behavior under adverse conditions; happy-path feature work belongs to the feature's own tests.
---

# sstack — structured negative testing

> Don't ask whether the software is robust. Exercise the failure
> condition and collect evidence.

sstack never fixes code. It attacks, verifies, minimizes, and
regresses — and stops there. Editing the target's source to
"handle" a case you just attacked destroys the evidence and
falsifies the run. If a fix is wanted, the human applies it
afterward and your regression tests prove it worked.

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

**Resolve the host repo first.** The host repo is the directory that
contains `.sstack-host-repo`. If that file exists in the current
working directory, the host repo is this directory. If it does not,
search upward for it before writing anything. When no marker exists,
the host repo is the directory the user pointed you at.

Every path in this document — `.sstack/`, scratch scripts, repro
commands — is relative to that host repo. Anchor each write to it
explicitly (or `cd` there once) so nothing lands in whatever
directory the agent happened to start in.

All artifacts live under `<host-repo>/.sstack/`:

- `map.md` — surfaces + assumed contracts (Discover output)
- `plan.md` — scoped run plan: selected lenses, cases, oracles
- `findings/<slug>.md` — one per finding, fields:
  `lens, surface, case, oracle, observed (verbatim), verdict
  (confirmed | refuted | inconclusive), repro (command),
  regression (test file + name + red|green)`
- `scratch/` — throwaway scripts; delete at run end

## Stages

### 1. Discover

Map the target's failure surfaces: public functions and classes,
API routes, anything that parses external input, loops over
collections, or indexes/slices. For each surface, record its
assumed contract — types, ranges, preconditions gleaned from
docstrings, types, and call sites. Write `.sstack/map.md`.

If the target repo has a verification skill or feature map
(pstack `/create-verification-skill`, or a project-local verify
script), read it as a head start on the surface map. It already
knows the entities, the ownership model, and the expected
behaviors — do not re-derive what it documents.

Done when every public function, route, parser, loop, and indexer
in the target has a row in `map.md` with its assumed contract.

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

An attack that never reached the function is not evidence. If the
script raises `ImportError`, `TypeError: missing required
positional argument`, or any error that is not the one your oracle
predicted, fix the call — import path, arguments, signature — and
re-run until the function itself executes. An error from your own
harness is a broken case, never a verdict.

If the target repo already has a property-based testing library
installed, write a property capturing the oracle and let the
library's generator and shrinker find the counterexample instead of
hand-designing cases the library would generate:

- Python: Hypothesis
- TypeScript / JS: fast-check
- Java / Kotlin: jqwik
- C++: RapidCheck, Google FuzzTest

Hand-designed cases remain the fallback when no library is present,
and the oracle is still written FIRST either way.

Cover every selected lens on every mapped surface before
concluding. A lens with zero executed cases on a surface that
consumes record/dict-shaped or string input is an incomplete
run, not a clean result.

### 3. Verify

Per case, compare oracle vs. observed:

Before comparing anything, check the observed output came from
the function under attack and not from your harness. An observed
`ImportError` or missing-argument error is a broken attack:
mark the case inconclusive with the harness error quoted, fix
it, and re-run.

- **confirmed** — observed violates the oracle, and the case
  reproduces on a second run.
- **refuted** — system satisfies the oracle.
- **inconclusive** — oracle unclear or execution unreliable.
  Inconclusive findings are never promoted to regressions.

### 4. Minimize

For each confirmed finding, strip the case to the smallest input
that still violates the oracle. Update the repro command.

Done when no smaller input still violates the oracle and the
finding's repro command runs as written.

### 5. Regress

Write a permanent test in the host repo's real suite — same
directory and assert style as existing tests, asserting the
oracle.

The test goes **red** on current code when the finding is real and
the oracle is right. A **green** test on a confirmed finding pinned
the observed behavior instead of the oracle. Rewrite it to assert
the oracle, or mark the finding refuted and keep the test as
characterization if the code already handles the case.

If the target repo has a mutation testing tool installed, run it
scoped to the surfaces you attacked and record the mutation score.
PIT (Java), Stryker (JS/TS), mutmut (Python). Survived mutants in
code you just confirmed as buggy are evidence your regression test
is incomplete, not evidence the tool is wrong.

Run the new tests. Then deliver the report in chat FIRST;
persisting `findings/` files is bookkeeping that follows.

### Run-end checks

Before delivering the report, verify all of the following:

1. Source, config, and secrets are unchanged. `git status` if the
   target repo is a git repo; the diff must show only new test files
   and `.sstack/` artifacts.
2. Every confirmed finding has a regression.
3. Every regression's state is reported honestly (red or green).
4. No confirmed finding has only a green regression.

A run that fails any of these is invalid. Fix and re-run before
reporting.

## Lens index

| Lens | Applies when | Reference |
|---|---|---|
| boundaries | edge cases: numbers, sizes, indexes, slices, collections, pagination, loops | references/lens-boundaries.md |
| malformed | strings parsed from outside, JSON, encodings, dynamic types | references/lens-malformed.md |
| missing | optional fields, records from external data, null/None/undefined | references/lens-missing.md |
| ownership | entities with an owner; valid request, wrong session. OWASP A01/A01:2025 broken access control, BOLA, IDOR | future: needs authenticated sessions |
| exceptional-conditions | fail-open paths, diagnostic leakage, cascading failures, empty catch blocks. OWASP A10:2025 | future: needs injectable failure points |

## Safety

- Never modify the target's source, config, or secrets — not
  even "small hardening fixes". The only files you may write
  are tests in the target's suite and artifacts under
  `.sstack/`.
- Never mutate source to demonstrate a bug. Reproduce in scratch
  space.
- No test framework detected → ask before scaffolding one.
- Respect the repo's test conventions exactly.

## Report format

One line per finding: `id | lens | surface | verdict | regression
(file::test, red|green)`. Then per confirmed finding the full
field set, with observed output quoted verbatim. End with counts:
confirmed / refuted / inconclusive, regressions landed.

If any finding is confirmed but every landed regression is green,
the run is invalid: re-check those tests against their oracles.
