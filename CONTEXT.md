# sstack

Vocabulary for structured negative testing. The eight product nouns
(Skill, Lens, Agent, Runner, Oracle, Evidence, Customization, Custom lens) live in
`docs/ARCHITECTURE.md`; this file holds the judging vocabulary — the
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
An angle of attack over a failure class: boundaries, malformed,
missing, ownership, exceptional-conditions, resource-exhaustion,
state, ordering, concurrency, idempotency, dependency-failure. A noun,
not a step. Eleven ship; a target repo adds any number.
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
The expected behavior written down *before* the attack: error,
degradation, retry bound, invariant, rejection — not only crashes.
"It crashes" isn't an expectation; "it raises a validation error
naming the field" is. A test that passes against code you just proved
broken has pinned the bug, and a pinned bug is worse than no test at
all.
_Avoid_: expected output (a value, not the declared behavior under the
adverse condition); assertion (the test's mechanism, not the
declaration)

**Evidence file**:
The machine-readable record of one finding: command, recorded output,
fingerprint, oracle, verdict, regression. One per finding, written by
script, never by hand.
_Avoid_: findings JSON, slug file

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
tests rather than attacking code (see `docs/research/MUTATION-RESEARCH.md`).
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

**Collection surface**:
A surface that returns many records: list, search, index, feed,
export, report, autocomplete. Its authorization obligation is the
membership of the result, not the reachability of any one row, so it
needs its own probe: a subject absent from the query leaks even when
every per-object check passes.
_Avoid_: listing endpoint, read surface (names the transport, not the
obligation)

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
a wrong label is a warning, never a disqualification.
_Avoid_: seed_id as truth, claimed id

**Integrity**:
The recorded output and recorded fingerprint agree. Verified twice:
by `replay` against every evidence file, and by the grader before a
run can pass. A pass therefore cannot rest on evidence whose
fingerprint the machine cannot re-derive. The recorded bytes are
independent of whether the command still behaves the same.
_Avoid_: validity

**Fabricated**:
Integrity failed — the fingerprint could not have come from the
recorded output. The emitter hashes its own execution and is the only
writer of evidence files, so a mismatch means the file changed after
emit: a typed-in fingerprint, tampered bytes. Not a capture-time
error; the emitter cannot mis-hash what it just ran.

**Drift**:
The re-run output no longer matches the record. Expected for a
confirmed finding whose fix landed; evidence against a `refuted`
verdict. Not a failure of the evidence.
_Avoid_: mismatch (it names the symptom, not the meaning)

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

**Hardening test**:
A green test landed for a surface that already handles the adverse
condition — the permanent product of a `refuted` finding or a filled
gap. In harden mode, the default output: an unmasked matrix test per
surface × lens gap, named `sstack_<lens>_`. Distinct from a
regression, which is red→green and atomic.
_Avoid_: negative test (covers both kinds), gap-fill test (process
language, not the artifact)

**Landed regression**:
A red→green test whose file exists in the graded workspace and
contains the named test. A claimed regression that cannot be found on
disk has not landed.

**INVALID**:
The deliverable cannot be judged at all: unparseable JSON, missing
evidence fields. Distinct from FAIL, which is a judged negative.
_Avoid_: failed, errored

**Acceptance record**:
`evals/ACCEPTANCE.md` — graded verdicts per fixture with run history.
_Evidence_ alone should not mean this file; evidence is per-finding,
the record is per-run.
