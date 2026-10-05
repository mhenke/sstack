# ADR-0021: Evidence is recorded portable, not byte-verbatim

**Status**: Accepted
**Date**: 2026-09-29
**Deciders**: Mike Henke

## Context

[ADR-0006](0006-evidence-re-verifiable-by-machine.md) made evidence machine-re-verifiable: the emitter executes the
repro, records the bytes it captured, and the fingerprint is the hash
of the recorded output; replay and the grader recompute that hash. The
ethos reads as "record what happened, verbatim" — and the bytes did
happen, but they happened *somewhere*: cold-run plan/report artifacts
carried absolute workstation paths, duplicate logs, and timestamps
(field report, 2026-09-29). The cost was not bloat. A Python traceback
embeds the checkout's absolute path, so the identical defect
fingerprinted differently on two machines or two temp checkouts, and
run-over-run triage diffs ([ADR-0019](0019-scan-baseline-for-change-triage.md)) showed moved paths and moved
clocks as changes — noise indistinguishable from signal at diff time.
The glossary now names this a **false change**: evidence changing
under a stable target, the mirror of drift.

Three places could hold the fix: leave evidence verbatim and let each
consumer scrub at read time (every differ re-implements the rule, and
fingerprints stay machine-dependent); keep timestamps and paths but
exclude them from diffing (the exclusion list drifts as fields are
added); or normalize once, at capture, in the only writer.

## Decision

We will normalize at capture, in the emitter — the single writer of
evidence. The absolute workspace path is rewritten to `.` on path
boundaries (a sibling directory sharing the prefix stays intact) in
the recorded command, stdout, and stderr, and the fingerprint is
defined over the recorded, normalized bytes. Integrity is unchanged by
definition — it is the record and the fingerprint agreeing — and
identical defects now fingerprint identically on any machine. Evidence
records no timestamps or durations (nothing consumed them; they only
manufactured false changes), and observed output is quoted once, in
the emitted record, never also pasted into `plan.md`.

## Consequences

**Good**: fingerprints become machine-independent, so replay, grading,
and cross-run comparison agree by construction; [ADR-0019](0019-scan-baseline-for-change-triage.md) triage diffs
show only target changes; the rule lives in one place (both emitters,
mirrored) instead of N consumers; old evidence still grades and
replays, because fingerprints were always computed over the bytes as
recorded.

**Bad**: recorded stdout is not byte-verbatim — a traceback's path is
rewritten to the workspace-relative form, and anyone needing the
literal machine path must re-run the repro. Emit-time provenance is
gone entirely: no field anywhere now records when a finding was
emitted.

**Risks**: a target whose meaningful *output* is an absolute path
(a path-printing utility, a manifest generator) records a rewritten
answer; if such a surface ever matters, the normalization needs a
per-finding escape hatch — revisit when a finding's oracle is itself
about absolute paths. If a future consumer grades on raw bytes rather
than the recorded fingerprint, it inherits neither the original nor
the normalized guarantee and must define its own contract. The
boundary rule is pinned by test (sibling prefix untouched), but a new
path shape could evade it; that surfaces as replay drift, which is
detected, not silent.
