---
name: sstack
description: Use when the user wants negative testing, edge-case coverage, failure-mode analysis, robustness checks, hostile or unexpected input handling, "what happens if" questions about code, or to harden a module or API against bad input before shipping. Discovers failure surfaces, attacks them through lenses (boundaries, malformed, missing, ownership, exceptional-conditions, resource-exhaustion, state), verifies observed behavior against a pre-declared oracle, adds negative regression tests, fixes confirmed failures, and hardens existing suites against future regressions. Scope is existing behavior under adverse conditions; happy-path feature work belongs to the feature's own tests.
disable-model-invocation: true
---

# sstack — structured negative testing

> Don't ask whether the software is robust. Exercise the failure
> condition, write the test that proves it, and fix it.

sstack finds the ways software fails, writes a test that goes red on
the bug, applies the minimal fix that turns it green, and hardens the
existing suite with negative test cases even where nothing is broken.

## The four rules

1. Attack assumptions.
2. Define the oracle before the attack. Expected behavior under the
   adverse condition — error, degradation, retry bound, invariant,
   rejection. "It crashes" is not an oracle; "it raises a
   validation error naming the field" is. One oracle, one observable
   outcome: "throws or returns NaN" is two verdicts wearing one
   sentence — name the one the contract promises; when the contract
   genuinely permits both, the case is inconclusive.
3. Never accept an agent's claim as evidence. Run the real command,
   quote the real output.
4. Every confirmed failure gets a red test, a fix, and a green test.
   Every refuted surface gets a green hardening test.

## Routing

- `/sstack <target>` — run the full lifecycle on a module, file,
  directory, or function.
- `/sstack` (bare) — infer the target from recent changes
  (`git status`, `git diff --stat`); ask only if nothing is
  inferable.
- `/sstack <stage>` (discover | attack | verify | minimize |
  test | fix) — enter that stage using existing `.sstack/` state.
- `/sstack learn` — update `.sstack/learn/` from confirmed findings.
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
- `learn/` — failure classes from prior runs (Discover input,
  Learn output). One line per class:
  `lens | signal | adjacent surfaces to re-test`
- `findings/<slug>.md` — the human view, rendered by the emitter in
  exactly this shape (no front-matter, no restated summary, the
  finding's fields in place):

```
# <surface> — <one-line case>

lens: <lens> | verdict: <confirmed | refuted | inconclusive>

## Case
<concrete input and action>

## Oracle
<expected behavior under the adverse condition>

## Observed
<verbatim output in a fenced block>

## Repro
<fenced command>, exit <exit_code>, fingerprint <fingerprint>

## Fix
<description, confirmed only>

## Regression
`<file>::<test>` — <before> → <after>
```
- `findings/<slug>.json` — the machine view, exact keys:
  `{"command": <shell string>, "exit_code": <int>, "stdout": <str>,
  "stderr": <str>, "fingerprint": "<sha256[:16] of stdout+stderr>",
  "oracle": <str>, "verdict": <confirmed|refuted|inconclusive>,
  "regression": {"file","test","before","after"}}`. `before`/`after`
  are the literal state tokens "red"/"green" — the test's state
  before-fix / after-fix — not output snippets. Verification re-runs
  `command` and recomputes the fingerprint from the recorded bytes,
  agent out of the loop; a hand-typed hash fails it. Any other shape
  is unverifiable.
- `scratch/<lens>/` — every probe, case script, and compiled artifact
  an attack creates, one directory per lens
- `pristine-src/` — the target's originals, snapshotted before Fix, so
  a repro command still shows the buggy behavior after the fix lands

The emitter is `scripts/emit_findings.py`, beside this skill: run it,
never rewrite or copy it. Once per finding, as that case verifies —
`python3 <pack>/skills/sstack/scripts/emit_findings.py --workspace
<host-repo> --fixture <name>` with the finding as JSON on stdin. It
executes the repro, captures real output, computes the fingerprint
itself, and is the only writer of `<slug>.md`, `<slug>.json`, and
`report.json`. The run's human report is the chat summary;
`report.json` is the only report file.

Everything sstack creates lives under `.sstack/` — never the workspace
root, never a temp folder elsewhere. Delete `scratch/` at run end; keep
`pristine-src/` so evidence replays.

## Stages

### 1. Discover

Map the target's failure surfaces: public functions and classes,
API routes, anything that parses external input, loops over
collections, or indexes/slices. Read `.sstack/learn/` first and
prioritize adjacent surfaces of recorded failure classes. For each
surface, record its assumed contract — types, ranges, preconditions
gleaned from docstrings, types, and call sites. Write
`.sstack/map.md`.

If available, use `principle-foundational-thinking` to identify the
target's real invariants, `principle-model-the-domain` to name its
entities and transitions, `principle-experience-first` to anchor the
map in user-observable behavior, and
`principle-exhaust-the-design-space` to cover materially different
failure surfaces rather than variants of one assumption. If available
in the target repo, use `create-verification-skill` to create or
refresh the verification map before mapping, and
`maintain-verification-skill` to keep it current. Read their output,
existing feature maps, and project-local verify scripts as head starts.
If these skills are unavailable, continue with the target's own docs,
types, and call sites.

Done when every public function, route, parser, loop, and indexer
in the target has a row in `map.md` with its assumed contract.

### 2. Attack

For each applicable lens from the index, dispatch the matching
attacker for each selected lens. If available, use
`principle-boundary-discipline` to identify the actual limits and
`principle-exhaust-the-design-space` to cover materially different
attacks. If available, use `principle-attack-the-premise` whenever
two or more fixes share one premise and fail the same gate. Write the
premise down, count the actors and failure classes, and question the
premise before trying another fix. For each surface × lens:

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

**Per-lens fan-out.** Dispatch one subagent per selected lens with
`runSubagent`, one call per lens, same message:

  - agent `sstack-boundaries-attacker` with the `sstack-boundaries`
    skill inline: numeric, size, index, collection, pagination edges.
  - agent `sstack-malformed-attacker` with the `sstack-malformed`
    skill inline: wrong types, corrupt structures, encodings.
  - agent `sstack-missing-attacker` with the `sstack-missing`
    skill inline: absent fields, nulls, empty inputs.
  - agent `sstack-ownership-attacker` with the `sstack-ownership`
    skill inline: subject × object × action × context, BOLA/IDOR,
    field-level read and write, deny-by-default, least privilege,
    token integrity, cross-tenant, CORS/CSRF.
  - agent `sstack-exceptional-conditions-attacker` with the
    `sstack-exceptional-conditions` skill inline: fail-open paths,
    diagnostic leakage, cascading failures.
  - agent `sstack-resource-exhaustion-attacker` with the
    `sstack-resource-exhaustion` skill inline: pools, rate limits,
    memory ceilings, payload limits, disk.
  - agent `sstack-state-attacker` with the `sstack-state` skill
    inline: stale cached reads, write-through to caller data, partial
    updates after failure, escaped internal references.

Pass each subagent the full context inline, not paths. Read
`.sstack/map.md` and paste its contents with labeled sections
(`### Workspace root` with the absolute path and `### Surface map`
with the map contents). Paste the matching lens skill's `SKILL.md`
contents inline under `### Lens rubric`, and the Report format block
below under `### Report format` — a subagent starts blank and cannot
see this file, so anything not pasted does not exist for it.

No subagent tool available, or dispatch fails twice? Run the lenses
yourself, one at a time, in the same order: read the lens skill,
execute its rubric against every mapped surface, record findings in
the Report format. Coverage is the contract; parallelism is
an optimization.

### 3. Verify

If available, use `principle-prove-it-works` before accepting a
verdict and `principle-outcome-oriented-execution` to keep the result
focused on observable behavior. Per case, compare oracle vs. observed.
Write both `findings/<slug>.md` and `findings/<slug>.json` for every
finding, in the exact shapes given under Workspace — through the
emitter script, as each case verifies. Evidence batched to run end is
evidence a crash deletes. Use
`principle-exhaust-the-design-space` to check materially distinct
attack families before declaring a surface covered.
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

Before recording a `confirmed` verdict, let the system argue its way
out: state the strongest case that the observed behavior is correct
given the surface's contract. If that case holds, the oracle is wrong,
not the code. Re-read the contract and mark the finding refuted. Then
name the conditions that would make your verdict wrong: a re-run that
passes, an oracle that turns out to permit the observed behavior, a
contract you inferred rather than read. A verdict you cannot break is
a verdict you did not check.

Synthesizing parallel lens findings: deduplicate defects reported
through more than one lens into a single finding (operating-limit
overlap between `boundaries` and `resource-exhaustion` keeps the
`resource-exhaustion` verdict). Weight overlapping confirmations more
heavily, resolve disagreements against the surface's contract, and
keep the report brief.

### 4. Minimize

If available, use `principle-minimize-reader-load` to keep the
minimal case and repro easy to inspect, and
`principle-sequence-verifiable-units` to reduce it in independently
checkable steps. For each confirmed finding, strip the case to the
smallest input that still violates the oracle. Update the repro command.

Done when no smaller input still violates the oracle and the
finding's repro command runs as written.


### 5. Test

If available, use `principle-test-behavior-not-implementation` for
every regression and hardening test. Call the subject as its users do,
assert a literal expected value or observable effect, and delete or
rewrite any test that would pass when every imported function returns
`undefined`. Use `principle-encode-lessons-in-structure` to preserve
the oracle and failure mode, and `principle-foundational-thinking` to
keep the test tied to the behavior that matters.

Write a permanent negative test in the host repo's real suite — same
directory and assert style as existing tests, asserting the oracle.

For **confirmed** findings: the test goes **red** on current code.
That is the proof the test catches the bug. A green test on a
confirmed finding pinned the observed behavior instead of the oracle.
Rewrite it to assert the oracle.

For **refuted** findings and surfaces that already handle the adverse
condition: add the test as a hardening characterization test. It goes
**green** immediately and locks in the correct behavior against future
regressions.

Run every new test and confirm the verdict matches: red for confirmed,
green for refuted/hardened.

### 6. Fix

For each confirmed finding, trace the observed behavior to its root
cause before editing. If available, use `principle-fix-root-causes`:
reproduce the failure, ask why until the shared cause is found, and fix
that cause rather than adding a symptom guard. Check every sibling
caller of the same behavior before applying the fix. Use
`principle-subtract-before-you-add` to remove obsolete complexity,
`principle-type-system-discipline` to keep boundaries explicit, and
`principle-sequence-verifiable-units` to keep each change checkable.

Then apply the minimal change that satisfies the oracle. Smallest diff
that turns the red test green.

- Validation: add the guard the oracle describes.
- Error handling: wrap the leak in a clean domain error.
- Missing check: add the check the oracle names.

Re-run the confirmed finding's test: it goes **green**. Then run the
full suite: the fix must not break any existing test.

Done when every confirmed finding's test is green and the full suite
passes.

If the target repo has a mutation testing tool installed, run it
scoped to the surfaces you attacked and record the mutation score.
PIT (Java), Stryker (JS/TS), mutmut (Python). Survived mutants in
code you just fixed are evidence your fix or your test is
incomplete, not evidence the tool is wrong.

### Run-end checks

Use `principle-prove-it-works` and
`principle-outcome-oriented-execution` to keep the report focused on
observable results. Use `principle-guard-the-context-window` to keep
the final report concise and the discarded scratch evidence out of the
user-facing output.

Before delivering the report, verify all of the following:

1. Every confirmed finding has a red test and a green post-fix test.
   The regression must be a test FILE in the repo's own suite (added
   to its build/test runner), not a scratch binary you compiled and
   ran yourself. `regression.file` is the path a stranger can open
   and re-run.
2. Every refuted finding has a green hardening test (if the surface
   consumes external input).
3. Every fix is the minimal change that satisfies the oracle.
4. The full suite passes.

A run that fails any of these is invalid. Fix and re-run before
reporting.

## Lens index

| Lens | Applies when | Reference |
|---|---|---|
| boundaries | edge cases: numbers, sizes, indexes, slices, collections, pagination, loops | sstack-boundaries-attacker |
| malformed | strings parsed from outside, JSON, encodings, dynamic types | sstack-malformed-attacker |
| missing | optional fields, records from external data, null/None/undefined | sstack-missing-attacker |
| ownership | a subject, an object, an action, and the context that joins them. OWASP A01 broken access control: BOLA/IDOR, BOPLA, missing deny-by-default, privilege escalation, token tampering, CORS, force browsing | sstack-ownership-attacker |
| exceptional-conditions | fail-open paths, diagnostic leakage, cascading failures, empty catch blocks. OWASP A10 | sstack-exceptional-conditions-attacker |
| resource-exhaustion | connection pools, rate limits, memory ceilings, payload limits, disk | sstack-resource-exhaustion-attacker |
| state | object with lifetime: cached/derived reads, mutable input written through, partial update after failure, internal collection escaped to callers | sstack-state-attacker |
| ordering | operations applied out of sequence | future |
| concurrency | race conditions, parallel access | future |
| idempotency | same operation applied twice diverges | future |
| dependency-failure | upstream timeout, partial response, unavailable service | future |
| contract | API contract violations between services | future |
| mutation | proof that tests detect seeded faults | future |
| agent | AI agent tool-call errors, truncated context, prompt injection | future |
| security | injection, privilege escalation, data exposure | future |

## Safety

- Only modify target source in the Fix stage, only for confirmed
  findings, and only the minimal change that turns a red test green.
  Every source change must trace to a finding.
- Never modify config or secrets.
- No test framework detected → ask before scaffolding one.
- Respect the repo's test conventions exactly.

## Report format

One finding per confirmed violation, in this exact shape (agents use
this block; the lens name fills the `lens:` field):

```
lens: <lens>
surface: <function or endpoint>
case: <concrete input and action>
oracle: <expected behavior under the adverse condition>
observed: <actual output, verbatim>
verdict: confirmed | refuted | inconclusive
repro: <command that reproduces>
```

Write the machine-readable run report to exactly
`<host-repo>/.sstack/report.json` — the canonical path any verifier
reads — one object per finding: `{"fixture", "findings":
[{"seed_id", "lens", "surface", "case", "oracle", "observed",
"verdict", "repro", "regression": {"file","test","before","after"}}]}`.
`seed_id` is your best guess at which planted bug this is (or
"other"); the finding's content is what carries the outcome, so a
wrong guess costs nothing. The emitter in Workspace writes it, per
finding, as each case verifies — so a crash keeps every finding
written so far. A report or evidence file that does not parse is not
evidence.

In the chat report, one line per finding: `id | lens | surface |
verdict | regression (file::test, red→green)` or `id | lens |
surface | refuted | hardening (file::test, green)`. Then per confirmed
finding the full field set, with observed output quoted verbatim and
the fix applied. End with counts: confirmed / refuted / inconclusive,
fixes applied, regressions landed, hardening tests added.

## Learn loop

### 7. Learn

If available, dispatch `agents-memory-updater` from the
`continual-learning` plugin with the confirmed findings and the
host repo path. Otherwise record one line per confirmed failure
class in `.sstack/learn/<lens>.md`:
`lens | signal | adjacent surfaces to re-test`. Treat learned
classes as prioritization for the next Discover, never as proof.
Never write secrets, transcripts, or one-off instructions into
`.sstack/learn/`.
