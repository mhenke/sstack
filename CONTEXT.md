# sstack

Vocabulary for structured negative testing. The seven product nouns
(Skill, Lens, Agent, Runner, Oracle, Evidence, Custom lens) live in
`docs/ARCHITECTURE.md`; this file holds the judging vocabulary — the
terms the eval harness and the evidence contract turn on.

## Language

**Stage**:
One of the seven lifecycle steps: Discover, Attack, Verify, Minimize,
Test, Fix, Learn. The process, fixed for the life of the product. Only
Attack fans out per lens; the other six are lens-agnostic. Adding a
stage is not an extension point.
_Avoid_: phase, step, stage of the attack

**Lens**:
An angle of attack over a failure class: boundaries, malformed,
missing, ownership, exceptional-conditions, resource-exhaustion,
state. A noun, not a step. Seven ship; a target repo adds any number.
The count of attacks is surface × lens, and neither factor is capped.
_Avoid_: attack type, test type, stage

**Agent**:
The subprocess that executes one lens. A `runSubagent` dispatch, one
file per shipped lens, receiving the surface map, the lens rubric, and
the report format pasted into its message. Ships paired 1:1 with a
lens, which is why the two read as one thing; they are not. A lens is
the strategy, an agent is the worker.
_Avoid_: attacker lens, lens agent (both collapse the pair)

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

**Custom lens**:
A repo-authored attack strategy in `.sstack/lenses/<name>.md`,
selected by `.sstack/config.md` and narrowed by its `applies-when`
field. Any number of them. It adds a **lens**, never an agent and
never a stage: there is no `sstack-ordering-attacker`. A custom lens
is dispatched to a shipped attacker whose discipline fits, with its
rubric appended after the built-in one, so the seven agents are
reusable executors. The lens index's eight `custom lens` rows
(`ordering`, `concurrency`, …) are unbuilt *shipped* lenses, a third
category from a repo's own.
_Avoid_: plugin, extension (both imply code the pack loads; this is
prose the agent reads)

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
The recorded output and recorded fingerprint agree. What replay
verifies first; the recorded bytes are independent of whether the
command still behaves the same.
_Avoid_: validity

**Fabricated**:
Integrity failed — the fingerprint could not have come from the
recorded output. Typed-in fingerprints are fabricated by definition.

**Drift**:
The re-run output no longer matches the record. Expected for a
confirmed finding whose fix landed; evidence against a `refuted`
verdict. Not a failure of the evidence.
_Avoid_: mismatch (it names the symptom, not the meaning)

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
