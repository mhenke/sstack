# ADR-0017: The grader gates on evidence integrity

**Status**: Accepted
**Date**: 2026-09-28
**Deciders**: Mike Henke

## Context

Replay was the only integrity check: it re-derives each evidence
file's fingerprint from its recorded stdout+stderr and reports
`fabricated` on mismatch. Grade never consulted it, so a corrupted
run could grade PASS. ColdPy-19 (seeded-py, 2026-09-28) proved the
hole live: the cold agent edited 11 of 29 evidence files after emit —
the emitter hashes its own execution and is the only writer, so a
mismatch means hand-tampering — and the run still graded PASS because
nothing in the grading path re-derived the hashes. The corruption was
found only because a human ran `replay` separately and read the output.

The emitter cannot be fixed to prevent this: it is honest at write
time; the tampering happens after. A validator at emit time would
check nothing the emitter does not already guarantee.

## Decision

The grader verifies evidence integrity itself. Before the bug-pin
control, `grade` re-derives every evidence file's fingerprint from its
recorded output and fails the run with the offending filename on the
first mismatch. A graded PASS therefore cannot rest on evidence whose
fingerprint the machine cannot reproduce, whether or not anyone ever
runs `replay`.

## Consequences

**Good**: the PASS verdict becomes self-checking; replay shifts from
gate to redundant auditor; hand-edited evidence fails with a named
file instead of silently matching goldens. ColdPy-19's verdict
correctly flips from PASS to FAIL under the hardened grader.

**Bad**: a second integrity implementation to keep in agreement with
`replay.py` (same hash, same comparison); a run with one corrupted
file fails whole, with no partial credit — deliberate, but it means a
single bad file masks whatever else the run found.

**Risks**: the two implementations drift apart (different hash
truncation, different fields hashed) and start disagreeing. If that
happens, extract one shared function rather than fixing both sides.
