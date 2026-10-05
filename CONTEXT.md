# sstack

Vocabulary for structured negative testing. The eight product nouns
(Skill, Lens, Agent, Runner, Oracle, Evidence, Customization, Custom lens) live in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md); this file holds the judging vocabulary — the
terms the eval harness and the evidence contract turn on.

## Language

**Stage**:
One of the seven lifecycle steps: Discover, Attack, Verify, Minimize,
Test, Fix, Learn. The process. Only Attack fans out per lens; the other
six are lens-agnostic. A stage is not a file, it is the orchestrator's
own text, so it is neither added, removed, nor extended: there is
nothing to append to and no filename that could select one. A user who
needs different work in a stage ships a lens instead.
_Avoid_: phase, step (both read as a generic workflow stage rather than
this fixed seven)

**Lens**:
An angle of attack over a failure class. A noun, not a step. Fourteen
ship; a target repo adds any number. Which failure class each name
covers — and the category it sits in — is the taxonomy, not this file's
enumeration; see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
The count of attacks is surface × lens, and neither factor is capped.
_Avoid_: attack type, test type, stage

**Agent**:
The subprocess that executes one lens. A `runSubagent` dispatch, one
file per shipped lens, receiving the surface map, the lens rubric, and
the report format pasted into its message. Ships paired 1:1 with a
lens, which is why the two read as one thing; they are not. A lens is
the strategy, an agent is the worker.
_Avoid_: attacker lens, lens agent (both collapse the pair)

**Oracle**:
The expected behavior written down *before* the attack, derived from
the surface's documented contract or caller invariant — what must
stay true under the adverse condition — and chosen for what the
surface risks, never for what is cheapest to execute. Reproducing a
failed assertion proves runtime behavior, not the invariant or a
production exploit path; reachability is assessed separately. One
observable outcome, named in the target language's terms (exception
type, rejected promise, error code, typed result): "it crashes" isn't
an expectation; "it fails with a validation error naming the field" is.
A test that passes against code you just proved broken has pinned the
bug, and a pinned bug is worse than no test at all.
_Avoid_: expected output (a value, not the declared behavior under the
adverse condition); assertion (the test's mechanism, not the
declaration); reproduced assertion (reproducing a failure proves
behavior, not an exploit path or contract violation)

**Evidence file**:
The machine-readable record of one finding: command, recorded output,
fingerprint, oracle, verdict, regression. One per finding, written by
the emitter from its own execution — an agent may write anything it
likes into `findings/<slug>.json`, and the `fingerprint` is what
distinguishes an evidence file from the request sitting beside it.
Nothing but execution confers that field, so a hand-written file is
simply not evidence: the grader reads no evidence from it and the
report never counts it.
_Avoid_: findings JSON, slug file, evidence (unqualified — a request
is not a weak evidence file, it is a different artifact)

**Finding request**:
What an agent writes the moment a verdict is known: the seven report
format fields plus slug, fix, and regression, with `repro` spelled
as the command string or an object containing `command`. A request
is not a finding and not evidence — it is the finding awaiting the
machine. The emitter's upgrade pass turns requests into evidence by
executing each repro; a request whose repro carries no executable
command stays a request forever, because the machine will not invent
the command the agent did not write (ADR-0022).
_Avoid_: finding draft, pending finding (process state, not what the
artifact is), evidence file (the whole point is that it is not one)

**Emitter**:
The stdlib-only reference script (`skills/sstack/scripts/emit_findings.py`,
fallback `emit_findings.js`) that serves as the single source of truth
for converting finding requests into verified evidence. Executes repro
commands, captures exit code and output, strips machine-specific absolute
paths and timestamps, derives the deterministic SHA256 fingerprint, and
writes both `findings/<slug>.json` and canonical `report.json`. Refuses to
emit if scratch probes fail compilation.
_Avoid_: reporter, test runner, harness (the emitter records evidence; it
does not orchestrate the run)

**Report**:
The run-level summary of all findings, at the canonical workspace
path. Graded; the evidence files are replayed.
_Avoid_: results file, output

**Report format**:
The seven-field per-finding block (lens, surface, case, oracle,
observed, verdict, repro) an attacker returns and the orchestrator
deduplicates. Defined once in the skill; the dispatch paste under
`### Report format` is its only carrier to a subagent.
_Avoid_: returns format, findings format

**Lens rubric**:

A lens skill's body, delivered inline to its attacker under that
heading. The attacker's only source of attack strategy; absent it,
the attacker falls back to its own lens description.
_Avoid_: prompt, instructions

**Customization**:
Extending sstack by dropping a file in the user's own tree, named with
the `sstack-` prefix: `sstack-<lens>/SKILL.md` for an attack angle,
`sstack-<lens>-attacker.md` for a worker. Project scope wins over
global, as skills resolve everywhere else. The pack ships no file a user is expected to edit, so
an update never destroys a customization.
_Avoid_: plugin, extension, config (all imply something the pack loads
or parses; this is a file the user writes and the skill reads)

**Unused customization**:
A `sstack-<lens>-attacker.md` whose lens is missing, so nothing ever
dispatches it. Not an error, but the run reports it by name, because a
worker nobody called is a customization that silently does nothing and
a quietly weakened run is indistinguishable from a clean one. The
mirror case, a lens with no agent, is ordinary: it runs on a shipped
attacker with the rubric appended.
_Avoid_: broken config (implies a parse failure; this parsed fine and
matched nothing)

**Custom lens**:
A repo-authored attack strategy, and structurally just a skill: an
ordinary `SKILL.md` carrying `disable-model-invocation: true`, because
a lens is pasted into a dispatch and never auto-loaded by a host. Any
number of them. Adds a **lens**, never an agent and never a stage: it
runs on a shipped attacker with its rubric appended, so the built-in
rubric still applies. `mutation` is a research conclusion, not an
index row: it was pruned from the lens index because it verifies
tests rather than attacking code (see [`docs/research/MUTATION-RESEARCH.md`](docs/research/MUTATION-RESEARCH.md)).
_Avoid_: extension, plugin (both imply code the pack loads)

**Decision site**:
A place in the code where an access decision is made: middleware, a
guard, a decorator, a query filter, a row policy, a gateway rule, or a
check the caller can edit. Access control is only as strong as its
weakest decision site, and it is only deny-by-default if their union
is.
_Avoid_: auth check (singular, implies there is one)

**Tuple**:
The four inputs an access decision binds — subject, object, action,
context. A check that binds only subject and action answers "is this
user an admin", never "may this user have this record", so the omitted
inputs name where the missing check belongs.
_Avoid_: permission (a grant, not the question being asked)

**Target**:
The resolved scope a run attacks: the module, directory, or function
the invocation names, or — for a bare invocation — the behaviorally
relevant working-tree code diff; a prior terminal command is context,
never scope authority (ADR-0020). For a repo root or broad directory,
target resolves to the language-convention folders inside it, one per
supported language present. When working-tree changes are non-code
or IDE-only, the agent must ask for an explicit target rather than
guessing. The map spans the target whole, and testability filters
surfaces, never target size.
_Avoid_: scope (reads as negotiable); smallest valid target (a cold
run's invented selection criterion — targets are resolved, never
chosen); prior command as scope (terminal history is context only)

**Surface**:
One attacked unit in the map: a public function or class, route,
service, DAO, parser, validator, loop over collections, or indexer.
Materially different failure surfaces get rows; variants of one
assumption share one. A row carries language, assumed contract,
impact class, and lens selections. Eligible surfaces pass the
no-socket test: confirmable by importing code and calling a function;
behaviors needing a launched process are recorded as a checked N/A
naming the artifact.
_Avoid_: file (a file holds many surfaces); endpoint (names one
transport only)

**Collection surface**:
A surface that returns many records: list, search, index, feed,
export, report, autocomplete. Its authorization obligation covers
everything the response carries — the membership of the result, the
embedded objects inside in-scope rows, the aggregates and excerpt
text computed over them — not the reachability of any one row. A
subject absent from the query leaks through any of those channels
even when every per-object check passes.
_Avoid_: listing endpoint, read surface (names the transport, not the
obligation)

**Impact class**:
A map row's rating of what a failure on the surface touches:
privilege boundary, sensitive-data mutation (money, legal, personal),
integrity or partial write, availability, presentation. Set at
Discover, orders the attack at Attack, and decides which untested
surfaces make a run partial.
_Avoid_: severity (ranks findings after the fact; impact ranks
surfaces before the attack)

**Supported language**:
One of Python, TypeScript, JavaScript, Java, or C++ — the five
languages every lens rubric's Language notes cover and the eval fixtures
exercise (`seeded-py`, `seeded-ts`, `seeded-js`, `seeded-java`,
`seeded-cpp`). Discover inventories surfaces in every one present.
TypeScript and JavaScript maintain separate fixtures and test frameworks
(`vitest` vs Node `--test`).
_Avoid_: target language (names one surface's language, not the set);
collapsing TS/JS (distinct runtimes and fixtures)

**Contamination**:
A shipped artifact handing a cold run its answer — a worked example
pairing a seed's trigger with its oracle, an unstripped `BUGS.md`, a
leftover `.sstack/` copied into the workspace. It makes the run
measure the prompt rather than the attacker, so the run is void
whatever it reports. Distinct from a lucky find: the agent still has
to notice, name, and record the defect unaided.
_Avoid_: leakage, hinting (both name the symptom, not the invalidity)

**Content match**:
The grader's finding↔golden link, made from surface, case, and oracle
text. The only link that can carry a pass.
_Avoid_: fuzzy match

**Seed label**:
A finding's self-reported guess at which planted bug it is. Advisory:
a wrong label surfaces as a label contradiction, which is a warning
and never a disqualification.
_Avoid_: seed_id as truth, claimed id, mislabel (the guess itself, not
the grader's recorded fact)

**Integrity**:
The recorded output and recorded fingerprint agree. Verified twice:
by `replay` against every evidence file, and by the grader before a
run can pass. A pass therefore cannot rest on evidence whose
fingerprint the machine cannot re-derive. The recorded bytes are
independent of whether the command still behaves the same.
_Avoid_: validity

**Fabricated**:
Integrity failed — the fingerprint could not have come from the
recorded output. Two mechanisms, different in kind. After the
emitter's: a file changed post-emit, a typed-in fingerprint, tampered
bytes — the emitter hashes its own execution, so it cannot mis-hash
what it just ran. Before it: a hand-written file claiming evidence no
machine ran. A file carrying no `fingerprint` at all is not one of
these — it is a request, so the run was incomplete, not dishonest.
_Avoid_: forged (implies intent the artifacts cannot establish)

**Label contradiction**:
A content-matched finding whose self-reported seed label names a
different seed than the golden it matched — `cart-count-is-stale!=
py-6`. The match is judged on content, so the contradiction never
disqualifies a run; it is recorded because a pattern of them is what
a run that pattern-matches rather than attacks looks like. Distinct
from a fabricated finding, which is a fingerprint failure, not a
naming one.
_Avoid_: fabricated (a different mechanism entirely), seed mismatch

**Drift**:
The re-run output no longer matches the record. Expected for a
confirmed finding whose fix landed; evidence against a `refuted`
verdict. Not a failure of the evidence.
_Avoid_: mismatch (it names the symptom, not the meaning)

**False change**:
A run-over-run difference in recorded evidence that reflects the
recording machine or its clock — a path that moved with the checkout,
a timestamp that moved with the emit — never the target. The mirror
of drift: drift is the target changing under stable evidence; a
false change is evidence changing under a stable target.
_Avoid_: noise (names the symptom, not the source), nondeterminism
(a general property, not a judging term)

**Finding**:
One attacked case with a recorded outcome — the unit the report format
carries and the evidence file records. A finding is a claim until its
verdict says otherwise; it is never called a bug in the evidence
contract. "Bug" is prose shorthand for a confirmed finding, never a
judging term, and it names no artifact.
_Avoid_: bug (prose only); issue, defect (same looseness)

**Verdict**:
The judging outcome of one finding: `confirmed`, `refuted`, or
`inconclusive`. The truthfulness mechanism — every artifact-level word
(landed regression, hardening test, count) derives from it, so a wrong
verdict corrupts the whole report. `confirmed` requires a red test
against pristine source; a test that passes with the fix reverted is
not a confirmation of anything.
_Avoid_: status, result (both read as raw outcome, not a judgment
against an oracle)

**False confirmation**:
A finding recorded `confirmed` whose regression passes against
pristine source — a green gap-fill wearing a red claim. Run-end check
7 converts it mechanically. It over-claims the report ("N bugs found"
when none were) while the landed tests themselves stay correct.
_Avoid_: false positive (names a classifier, not an evidence verdict)

**Partial coverage**:
A run whose high-impact surfaces went untested. The chat report's
coverage counts (mapped, executed, refuted, confirmed, inconclusive,
not run) state the run's shape; defects found are its content, and
partial is the honest verdict a clean-looking report hides.
_Avoid_: incomplete run (reads as a harness fault, not a reporting
duty)

**Baseline**:
The suite's pre-existing failures, recorded before the run's first
test lands. Baseline is outside the run: exempted from the pass gate
and reported as found — a fix may not claim it, and the gate judges
only the delta the run produced.
_Avoid_: known failures (implies triaged and accepted); pre-existing
bugs (unowned until a run points at those surfaces)

**Negative control**:
The grader's re-execution of every confirmed finding's regression
against pristine source, before a run may pass. All green means each
claimed red→green test actually asserts the buggy behavior, and the
run fails. Distinct from a control run, the same idea at fixture scale.
_Avoid_: bug-pin (the defect the control detects, not the control)

**Control run**:
A negative control at fixture scale: the operation run against a
fixture already known to be fixed, which must yield zero confirmed
findings. `grade` cannot judge it — a zero-confirmed run fails the
content-match gate by design — so a control run is judged directly.
_Avoid_: negative control (the grader's per-finding re-execution),
dry run

**Hardening test**:
A green test landed for a surface that already handles the adverse
condition — the permanent product of a `refuted` finding or a filled
gap. In harden mode, the default output: an unmasked matrix test per
surface × lens gap, named `sstack_<lens>_`. Distinct from a
regression, which is red→green and atomic.
_Avoid_: negative test (covers both kinds), gap-fill test (process
language, not the artifact)

**Harden mode**:
Gap-filling mode, `/sstack harden <target>`: it measures what a suite's
negative tests already cover and writes the missing ones, rather than
attacking for new defects. Not a stage and never inside the lifecycle;
the seven stages are unchanged and all its rules apply. A harden
test that comes back red is a live bug and flips into the lifecycle,
everything else is a hardening test.
_Avoid_: negative-test mode, gap-fill stage (it is neither a stage nor
only a fill)

**Triage mode**:
Surface-prioritization mode, `/sstack triage <target>`: ranks target
surfaces by churn heat, git touch frequency, `learn/` failure adjacency,
and impact class before a full Discover run. Not a stage and never a
filter that shrinks the whole-target surface map; it orders the attack
to focus effort where risk concentrates without abandoning whole-scope
coverage.
_Avoid_: target filter (it reorders attack priority, never trims the map);
triage stage (a pre-lifecycle subcommand, not one of the seven stages)

**Run type**:
Which shape a cold run took, named in the acceptance record: a
default lifecycle run (`ColdPy-…`, `ColdTs-…`, peers) or a harden run
(`ColdHarden-…`). It fixes what a pass means, since a harden run's
output is tests and a lifecycle run's is findings. Never a separate
evidence contract — both emit through the same emitter.
_Avoid_: run mode, harness profile

**Read window**:
The opening span of a shipped document that a cold backend actually
receives: an unbounded `read` of the entry skill truncates around
16KB, roughly line 230 of a 540-line file. Anything a weak backend
must obey — the emit contract, the dispatch fallback — lives inside
that window; a rule past it is not wrong, it is invisible on those
backends. Distinct from sprawl: a long document can be fine as long
as its binding rules are reachable, and a short one can still hide a
rule nobody sees.
_Avoid_: token limit (names the ceiling, not the reachable span),
front matter (a packaging position, not a reading guarantee)

**Probe**:
The throwaway script an attack writes to exercise one case — created
on the fly in `.sstack/scratch/<lens>/`, one directory per lens,
deleted once the run-end checks pass, not before: the checks still
exercise scratch (the sensitivity mutant runs there). A probe is an
attack tool, never evidence and never a shipped test: its output
counts only once it imports and runs, a crashed probe is a broken
probe (repair and re-run — the crash is not a finding), and the
permanent form of a confirmed case is a regression test in the host
suite.
_Avoid_: test script (probes are ephemeral; the shipped test is the
regression or hardening test), payload (names the input, not the
tool)

**Landed regression**:
A red→green test whose file exists in the graded workspace and
contains the named test. A claimed regression that cannot be found on
disk has not landed.

**INVALID**:
The deliverable cannot be judged at all: unparseable JSON, missing
evidence fields. Distinct from FAIL, which is a judged negative.
_Avoid_: failed, errored

**Acceptance record**:
[`evals/ACCEPTANCE.md`](evals/ACCEPTANCE.md) — graded verdicts per fixture with run history.
_Evidence_ alone should not mean this file; evidence is per-finding,
the record is per-run.

**Harden snapshot**:
The dated coverage report a harden run writes to
`.sstack/harden/<date>-<target>-<seq>.md`, one per run, named so a
later run can print the trend against it. Its per-lens table and
banded percentage are the run's headline claim; the findings JSON
beside it is the run's evidence, and the two are graded separately.
_Avoid_: harden report, coverage report
