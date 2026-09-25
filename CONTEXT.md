# sstack

Vocabulary for structured negative testing. The six product nouns
(Skill, Lens, Agent, Runner, Oracle, Evidence) live in
`docs/ARCHITECTURE.md`; this file holds the judging vocabulary — the
terms the eval harness and the evidence contract turn on.

## Language

**Evidence file**:
The machine-readable record of one finding: command, recorded output,
fingerprint, oracle, verdict, regression. One per finding, written by
script, never by hand.
_Avoid_: findings JSON, slug file

**Report**:
The run-level summary of all findings, at the canonical workspace
path. Graded; the evidence files are replayed.
_Avoid_: results file, output

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
