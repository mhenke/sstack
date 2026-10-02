---
name: sstack
description: Use when the user wants negative testing, edge-case coverage, failure-mode analysis, robustness checks, hostile input handling, or to harden a module against bad input before shipping.
---

# sstack — structured negative testing

sstack finds the ways software fails, writes a test that goes red on
the bug, applies the minimal fix that turns it green, and hardens the
existing suite with negative test cases even where nothing is broken.

## The four rules

1. Attack assumptions.
2. Define the oracle before the attack, from the surface's business
   invariant — what must stay true under the adverse condition — not
   from what is cheapest to execute. Shape: given [adverse input],
   the system must [one observable outcome] and must not [critical
   side effect], the outcome named in the language's terms —
   exception type, rejected promise, error code, typed result.
   "Throws or returns NaN" is two verdicts wearing one sentence —
   name the one the contract promises; when the contract permits
   both, the case is inconclusive.
3. Never accept an agent's claim as evidence. Run the real command,
   quote the real output.
4. Every confirmed failure gets a red test, a fix, and a green test.
   Every refuted surface gets a green hardening test.

## Routing

The slash forms are request labels, never a program: no `sstack`
binary exists — you execute each stage yourself with your tools.
- `/sstack <target>` — run the full lifecycle on a module, file,
  directory, or function.
- `/sstack` (bare) — the target is resolved, never chosen: explicit
  naming wins, else the behaviorally relevant working-tree code diff
  (`git status`, `git diff --stat`); a prior terminal command is
  context, never scope authority — no code diff names a target → ask.
- `/sstack <stage>` (discover | attack | verify | minimize |
  test | fix) — enter that stage using existing `.sstack/` state.
- `/sstack learn` — update `.sstack/learn/` from confirmed findings.
- `/sstack lenses` — print the lens index below, then every custom lens found per Customization.
- `/sstack harden <target>` — negative-test gap-filling without a
  full attack; load `references/harden.md` and follow it.

Dispatch fallback: per-lens subagents that fail or go silent twice
transfer to you — run every lens yourself, one at a time, in index
order (fan-out detail under Attack).

## Workspace

**Resolve the host repo first:** the nearest ancestor containing
`.sstack-host-repo`, else the directory the user pointed you at.

Every path here — `.sstack/`, scratch scripts, repro commands — is
relative to that host repo; anchor each write to it. Inside artifacts:
no absolute paths, no timestamps; observed output lives once, in the
emitted record — evidence diffs run over run, a moved path or clock
reads as a false change.

All artifacts live under `<host-repo>/.sstack/`:
- `map.md` — surfaces with language and assumed contracts, plus
  per-surface lens selections and skips (Discover output)
- `learn/` — prior failure classes, one line each:
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
- `findings/<slug>.json` — the machine view (emitter-written; anything
  you write there without a `fingerprint` is a request, not evidence):
  `{"command": <shell string>, "exit_code": <int>, "stdout": <str>,
  "stderr": <str>, "fingerprint": "<sha256[:16] of stdout+stderr>",
  "oracle": <str>, "verdict": <confirmed|refuted|inconclusive>,
  "regression": {"file","test","before","after"}}` (plus optional
  `fix`, `seed`, `counterexample`). `before`/`after`
  are the literal state tokens "red"/"green" — the test's state
  before-fix / after-fix. Verification re-runs `command` and recomputes the
  fingerprint; a hand-typed hash fails it. Any other shape is
  unverifiable.
- `scratch/<lens>/` — this run's probes, one directory per lens
- `pristine-src/` — the target's originals, snapshotted before Fix, so
  a repro command still shows the buggy behavior after the fix lands
- `harden/<date>-<target>-<seq>.md` — harden-mode snapshots, not findings

The emitter is `scripts/emit_findings.py` (or `.js` under Node),
beside this skill: run it, never rewrite or copy it. The moment a
verdict is known, write the finding request to `findings/<slug>.json`
— `repro` is the exact command you ran, as a plain string. Run the
emitter from the repo root
(`python3 skills/sstack/scripts/emit_findings.py --workspace .`) as
each finding lands or at run end: it executes every request's repro
itself, computes the fingerprint, and writes the evidence — a
request without a `fingerprint` field is not evidence; a repro past
120 seconds is killed (exit 124, kill noted in stderr).
To emit one
finding immediately, pass `--finding <file>` (or pipe the JSON on
stdin). Add `--fixture <name>` on the first emit; later runs inherit
it from `report.json`.

The request JSON is the Report format fields — `lens`, `surface`,
`case`, `oracle`, `verdict`, `repro` — plus `slug` (a short kebab-case
name for the finding), `fix` (the minimal change you will make), and
`regression`: `{"file": "tests/test_x.py", "test": "test_name",
"before": "red", "after": "green"}`. Optional for
PBT: `seed` (integer/token) and `counterexample` (minimal failing input).
The seven fields alone are rejected. A finding with no regression yet is
legitimate during Verify: the emitter warns and records the rest.

Everything sstack creates lives under `.sstack/` in the target repo,
created by this run — the pack brings only skills and agents, so
nothing is inherited from wherever it was published. `scratch/` is
deleted once the run-end checks pass: its keepers landed as suite
tests, and a stale probe against fixed code reads as a false
verdict. Keep `pristine-src/` so evidence replays.

## Customization

**A lens is a skill, and an agent is an agent** — the whole extension
model: drop a file in your own tree, named so this skill recognizes it.

```
<host-repo>/.agents/skills/     project scope, resolved against the
                                host repo like every other path here
~/.agents/skills/               global scope, an absolute path
```

Both are searched, project first, and the first `sstack-<lens>`
found wins. The other hosts keep the same shape:
`~/.config/opencode/skills/` and `.opencode/skills/` for OpenCode,
`~/.claude/skills/` for Claude Code; look in whichever the host
uses, all of them if unsure.

Project shadows global, as OpenCode, Claude Code, and VS Code already
resolve skills. Never put a custom file in `skills/` or `agents/`:
those belong to the pack and are replaced wholesale on update, so
anything edited there is lost.

| customize | by dropping | recognized by |
|---|---|---|
| an attack angle | `sstack-<lens>/SKILL.md` in a skills dir | Attack, at `### Lens rubric` |
| a worker | `sstack-<lens>-attacker.md` in an agents dir | Attack, dispatched by name |

The `sstack-` prefix is the entire contract. A file carrying it is
sstack's to read; a file without it is none of this skill's business.

A lens skill needs `name: sstack-<lens>`, a `description` naming its
failure class, `disable-model-invocation: true` as all fourteen shipped
skills carry — a lens is pasted here, never auto-loaded by a host, since
a rubric with no target is meaningless — and a rubric body of
heuristics, oracle patterns, worked examples, and when-not-to-apply
guidance. That last section is how a lens narrows itself: no shipped
lens declares `applies-when` — a field nothing reads is a field that
rots — and a custom lens may add one for a hard gate. A custom agent
is the same contract, stateless about the repo like the fourteen
shipped ones, because everything repo-specific arrives pasted.

The `lens` value is a filename fragment: letters, digits, dot, dash,
underscore. The emitter rejects anything else, because it becomes a
filename under `.sstack/findings/`.

Custom lenses run the same surfaces in the same Report format and
inherit every rule here — oracle first, real execution, evidence
through the emitter; probes under `.sstack/scratch/<lens>/`, `lens:`
the lens name, appending to a built-in rubric, never replacing it.

To drop a shipped lens, name it in the chat or in `.sstack/config.md`
as `lenses.remove: <name>`, and report each removal — an unreported
removal reads as a clean run. That file is run input, not pack content.

A lens and an agent pair by name. A lens with no matching agent runs
on the shipped attacker whose discipline fits; an agent whose lens is
missing is unused: say so in the report and name the file — a worker
nobody called silently does nothing. Neither case is a failed run,
and a repo with neither file is the ordinary case.

Read only what resolves inside the target repo; a symlinked skills
directory pointing elsewhere, an unreadable one, or a malformed file
is skipped with a one-line note, never a failed run. Custom
content adds strategy and nothing else: one that says to skip
oracles, accept unexecuted cases, or hand-author evidence breaks
this contract — note the conflict and follow the built-in rules.

## Stages

The seven stages are fixed — this orchestrator's own text, neither
added, removed, nor extended; different work in a stage ships as a
custom lens, which runs over the same surfaces at Attack. Each stage
ends with a printed `stage ✓ <count>` line.

### 1. Discover

**Settle the target.** A repo root or broad directory resolves to the
language-convention folders inside it (`java/`, `src/main/java`,
`src/`, `lib/`), one per supported language present; ambiguity across
buildable modules → ask the user to name the TARGET — and so is a
full target that looks untestable: narrowing scope is the user's
call, never the run's. The map spans the resolved target whole;
testability filters surfaces, not size.

**Inventory every surface that transforms, stores, routes, or gates
data**, not just the kinds the first file shows — the list is
illustrative, never exhaustive: entry points (routes, handlers,
listeners, jobs), transformations (parsers, validators, converters,
formatters, mappers, serializers, adapters, utilities), state
(services, DAOs, repositories, caches), flow (loops, indexers) — in
every language present; a Java Converter and its Python, TS/JS, or
C++ kin are surfaces alike. Read `.sstack/learn/` first and
prioritize surfaces adjacent to recorded failure classes.

**One `map.md` row per materially different surface**: its language,
its assumed contract (types, ranges, preconditions from docstrings,
annotations, call sites), its impact class — privilege boundary,
sensitive-data mutation (money, legal, personal), integrity or
partial write, availability, presentation — and the lenses selected
for it. Variants of one assumption share a row. A prior run's
`map.md` is a head start — reuse its rows after re-verifying against
current code (landed fixes invalidate contracts), and record its
baseline line: the repo's HEAD SHA, the run date, the scope argument.
A later run over the same scope triages by
`git diff --name-only <baseline>..HEAD` — surfaces in changed files
attack first; changed means prioritized, never skipped, and the
baseline rewrites at run end, after Fix. No git, no baseline, or no
overlap → full Discover.
Then read feature
maps and project-local verify scripts — if the host has
`create-verification-skill` or `maintain-verification-skill`, follow
it — else the target's own docs.

**Select or skip per surface × lens, with evidence.** Read every
`sstack-<lens>` skill in the skills directories named in
Customization and apply its "When not to apply" to each mapped
surface, never to the repo as a whole. Record each selection with the
surface property that admits it; skip a lens only when every mapped
surface is ruled out, recording the quoted ruling line and the
surfaces checked — a deselected lens is a recorded decision, not an
omission. A behavior is testable only if the agent can confirm it by
importing code and calling a function — the no-socket test;
launch-and-observe-HTTP is out of scope, recorded as a checked N/A
naming the artifact.

Done when every source file in the target is accounted for — its
surfaces have `map.md` rows, or the file is recorded as carrying none
(pure types, constants, config) with the rule that excluded it — and
every lens is selected per surface or skipped with evidence.

### 2. Attack

Dispatch the matching attacker for each lens selected from the index.
Order surfaces by impact class — privilege boundaries and
sensitive-data mutations first, duplicate processing and partial
writes next, parsers and validators last, still valuable at public
boundaries — and identify each surface's actual limits; cover
materially different attacks, not variants of one. Two fixes sharing
a premise and gate — if `principle-attack-the-premise` is installed,
follow it — write the premise down, count actors and failure
classes, question it before retrying. For each surface × lens, and as
many cases per pair as the contract admits:

1. Design the case (concrete input and action).
2. Write its oracle in `plan.md` FIRST — the expected behavior under
   this adverse condition, anchored to an observable invariant
   (inverse, idempotence, metamorphic) or a rejection contract:
   invalid input yields a typed domain error, never crash/500.
3. Execute for real: a scratch script under `.sstack/scratch/` or a
   direct call through the repo's test framework. Python probes open
   with the bootstrap
   `sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))`
   after `import sys, pathlib` — imports resolve anywhere. Read
   oversized targets in ranges, never from a truncated read; repair a
   crashed probe and re-run before recording output verbatim.

If the target repo already has a property-based testing library
installed, write a property capturing the oracle and let the
library's generator and shrinker find the counterexample instead of
hand-designing cases the library would generate (Python: Hypothesis,
TS/JS: fast-check, Java: jqwik, C++: RapidCheck, Google FuzzTest).
Cap scratch runs to 25 iterations (`max_examples=25`, `numRuns: 25`,
`tries = 25`) to keep attack loops sub-second. When emitting, bake
the seed into the `repro` command (`--hypothesis-seed=<seed>`,
`{ seed: <seed> }`) so machine replay runs deterministically.

Cover every selected lens on every mapped surface; a lens with zero
executed cases on a surface consuming record/dict or string input is
an incomplete run, not a clean result.

**Per-lens fan-out.** Dispatch one subagent per selected lens with
`runSubagent`, one call per lens, concurrently: dispatch agent
`sstack-<lens>-attacker` with the matching `sstack-<lens>` skill
inline under `### Lens rubric`. A custom lens without a dedicated
agent runs on the shipped attacker whose discipline fits, the custom
rubric appended after the built-in text (per Customization).

Pass each subagent the full context inline, not paths. Read
`.sstack/map.md` and paste its contents with labeled sections
(`### Workspace root` with the absolute path and `### Surface map`
with the map contents). Paste the matching lens skill's `SKILL.md`
contents inline under `### Lens rubric`, and the Report format block
below under `### Report format` — a subagent starts blank and cannot
see this file, so anything not pasted does not exist for it.

### 3. Verify

Prove a verdict before accepting it: per case, compare oracle vs.
observed. The moment a verdict is known, emit it — the emitter
command and the evidence rule sit under Workspace, above. Batched
evidence is evidence a crash deletes: emit while the failing state
still runs — a fix applied before its red evidence is emitted
strands it. The first emission is the emitter smoke test: repair any
failure before attacking further. Check for materially distinct attack families
before declaring a surface covered. Before comparing anything, check
the observed output came from the function under attack and not from
your harness. An observed `ImportError` or missing-argument error is
a broken attack: mark the case inconclusive with the harness error
quoted, fix it, and re-run.

- **confirmed** — observed violates the oracle, and the case
  reproduces on a second run.
- **refuted** — system satisfies the oracle.
- **inconclusive** — oracle unclear or execution unreliable.
  Inconclusive findings are never promoted to regressions.

Before recording a `confirmed` verdict, let the system argue its way
out: state the strongest case that the observed behavior is correct
given the surface's contract; if it holds, the oracle is wrong —
re-read the contract and mark the finding refuted. Then name what
would make the verdict wrong: a re-run that passes, an oracle that
permits the observed behavior, a contract inferred rather than read.
Name the oracle's source — documented contract, caller requirement,
existing test, inference; an oracle quoting a test asserts the test,
not the contract, and inference caps the verdict at inconclusive.
Reachability is separate: a constant-only caller shows no input path.
A verdict you cannot break is a verdict you did not check.

Synthesizing parallel lens findings: deduplicate defects reported
through more than one lens into a single finding (an operating-limit
overlap keeps the `resource-exhaustion` verdict); disagreements
resolve against the surface's contract.

### 4. Minimize

For each confirmed finding, shrink the input in independently
checkable steps until the smallest failing case is found:
- Numbers: binary search toward zero (`1000` → `500` → `0` → `-1`).
- Strings: halve length, then simplify characters (`"payload"` → `"a"` → `""`).
- Collections & Objects: bisect items; drop keys one by one.
Update the repro command.

Done when no simpler input violates the oracle and the repro runs as
written.

### 5. Test

Test behavior, not implementation — if the host has
`principle-test-behavior-not-implementation` installed, load and
follow it. Call the subject as its users do, asserting exact scalar
values, concrete error types, and specific error codes or message
substrings. Delete or rewrite any test that would pass when every
imported function returns `undefined`. Verify error identity, not
merely that something failed; a returning call is proven by its
returned state and side effects, not by the absence of an error.

Write a permanent negative test in the host repo's real suite — same
directory and assert style as existing tests, asserting the oracle.
Use the target's existing test dependencies only; target build configs
(`pom.xml`, `package.json`, `build.gradle`) stay read-only.

For **confirmed** findings (atomic regression): exactly one test
method per finding asserting the single minimized vector — no loops
(they mask failures). It goes **red** on current code; that is the
proof it catches the bug. A green test on a confirmed finding pinned
the observed behavior instead of the oracle: rewrite it.

Verify test sensitivity (the inline mutant check): in scratch, run
the test against one canonical mutant — relational inversion,
boundary shift, or statement deletion. It must go red immediately; a
pass under mutated logic is a vacuous test: rewrite it to assert the
observable contract.

For **refuted** findings and surfaces that already handle the adverse
condition (hardening): write an unmasked matrix (`assertAll`, subtests)
with baseline collections (`Arrays.asList`) so every vector executes.
It goes **green** immediately and locks in the correct behavior against
future regressions.

If the target repo already imports a property-based testing library,
write an invariant property test instead.

Run every new test and confirm the verdict matches: red for confirmed,
green for refuted/hardened, and passes the sensitivity check.

### 6. Fix

For each confirmed finding, trace the observed behavior to its root cause before
editing — if the host has `principle-fix-root-causes` installed, load and follow it:
reproduce the failure, ask why until the shared cause is found, and fix that cause
rather than adding a symptom guard. Fix the general invariant rather than the single
test input: guard the entire invalid domain (relational checks like `<= 0`, not literal
equality `== 0`). Check every sibling caller of the same behavior
before applying the fix.

Then apply the minimal change that satisfies the oracle. Smallest diff
that turns the red test green.

Re-run the confirmed finding's test: it goes **green**. Verify against
a second distinct vector in the invalid domain to confirm the fix
generalizes. Then run the full suite: the fix must not break any existing
test.

If the target repo has a mutation testing tool installed, run it
strictly scoped to the fix diff (incremental/diff flags, timebox
60s). Survived mutants in code you just fixed are evidence your fix
or your test is incomplete, not that the tool is wrong.

### Run-end checks

Before delivering the report, verify all of the following:

1. Every confirmed finding has a red test and a green post-fix test —
   a test FILE in the repo's own suite, a path a stranger can re-run.
2. Every refuted finding has a green hardening test (if the surface
   consumes external input).
3. Every fix is the minimal change that satisfies the oracle.
4. The full suite passes, minus pre-existing baseline failures;
   zero executed tests is a blocked check, never a pass.
5. Every confirmed regression test passed the sensitivity check (turns
   red when the fix guard is bypassed in scratch).
6. Every skipped lens in `map.md` names the "When not to apply"
   line that ruled it out — an unrecorded skip never ran.
7. Every confirmed regression is red against pristine source; one that
   passes with the fix reverted is a false confirmation (record refuted).
8. Every mapped surface ends attacked or explicitly not-run; a
   complete-looking report over un-attacked surfaces is invalid.
9. Prior confirmed findings get a disposition — replayed via their
   suite regression or blocked with a quoted reason; re-emit on change.

A run that fails any of these is invalid. Fix and re-run before
reporting.

## Lens index

| Lens | Applies when | Reference |
|---|---|---|
| boundaries | edge cases: numbers, sizes, indexes, slices, collections, pagination, precision, time, loops | sstack-boundaries-attacker |
| malformed | strings parsed from outside, JSON, encodings, dynamic types | sstack-malformed-attacker |
| missing | optional fields, records from external data, null/None/undefined, falsy traps, PATCH omission | sstack-missing-attacker |
| ownership | a subject, an object, an action, and the context that joins them. OWASP A01 broken access control: BOLA/IDOR, BOPLA, missing deny-by-default, privilege escalation, token tampering, header/IP bypasses, CORS, force browsing | sstack-ownership-attacker |
| exceptional-conditions | fail-open paths, diagnostic leakage, cascading failures, empty catch blocks. OWASP A05, CWE-209/636 | sstack-exceptional-conditions-attacker |
| resource-exhaustion | connection and thread pools, rate limits, memory ceilings, payload limits, unbounded queries, disk | sstack-resource-exhaustion-attacker |
| state | object with lifetime: cached/derived reads, mutable input written through, partial update after failure, internal collection escaped to callers, invalid transitions | sstack-state-attacker |
| ordering | operations applied out of sequence, multi-step pipeline bypass, step skipping | sstack-ordering-attacker |
| concurrency | race conditions, parallel access, double-spend, lost updates | sstack-concurrency-attacker |
| agent | tool-call schema divergence, tool errors crashing the loop, prompt injection delimiters, system prompt eviction, runaway tool loops | sstack-agent-attacker |
| dependency-failure | upstream timeout, partial response, unavailable service, circuit breaker trip | sstack-dependency-failure-attacker |
| contract | API contract violations, schema drift, undeclared fields | sstack-contract-attacker |
| idempotency | retried operations, duplicate requests, Idempotency-Key collisions and tampering, safe method purity | sstack-idempotency-attacker |
| security | injection (SQL, command, path traversal), crypto token tampering | sstack-security-attacker |

## Safety

- Only modify target source in the Fix stage, only for confirmed
  findings, and only the minimal change that turns a red test green.
  Every source change must trace to a finding.
- Never modify config or secrets.
- No test framework detected → ask before scaffolding one.
- A framework present but broken → same rule: ask before repairing
  it. Evidence does not wait: probes execute and emit without the
  suite — only regression landing blocks, repaired or routed around
  in the repo's own suite, never a downgraded verdict. A target that
  will not build yields inconclusive findings quoting the build
  error, not silence. A pre-existing red suite is baseline, not
  finding: record it, exempt it from the pass gate, report it.
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
`seed_id` is an optional free-form label or "other" — a finding's
content carries its outcome, so nothing depends on the label. The
emitter in Workspace writes it, per finding, as each case verifies —
so a crash keeps every finding written so far. A report or evidence
file that does not parse is not evidence.

In the chat report, one line per finding: `id | lens | surface |
verdict | regression (file::test, red→green)` or `id | lens |
surface | refuted | hardening (file::test, green)`. Per confirmed
finding, the full field set with observed output quoted verbatim and
the fix applied. End with coverage counts — surfaces mapped,
executed, refuted, confirmed, inconclusive, not run — then fixes
applied, regressions landed, hardening tests added. Untested
high-impact surfaces make the run partial coverage: report it as
partial.

### 7. Learn

Record one line per confirmed failure class in
`.sstack/learn/<lens>.md`: `lens | signal | adjacent surfaces to
re-test` — prioritization for the next Discover, never proof. Keep
secrets, transcripts, and one-off instructions out.
