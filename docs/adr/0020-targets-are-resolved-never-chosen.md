# ADR-0020: The target is resolved, never chosen — whole-target maps span runs

**Status**: Accepted
**Date**: 2026-09-29
**Deciders**: Mike Henke

## Context

Three field failures in one day share a single premise: that a run may
shrink what it attacks. Lenses were marked checked-N/A from a single
file slice; a cold run on an Angular repo framed the job as choosing
the "smallest valid target"; and under the old run-end check 8 ("an
un-attacked mapped surface invalidates the run"), the rational move on
a large repo was to map fewer surfaces so everything mapped got
attacked. The pack's own vocabulary fed the second failure — the
no-socket test supplied *valid*, Minimize/Fix supplied *smallest*,
bare-invocation diff inference supplied *choose from evidence* — so an
agent could assemble a scope-shrinking criterion from text that never
stated one.

The tension underneath is real and does not dissolve: a whole-module
target (an Angular `src/`) can exceed one run's attack capacity, so
one of three things gives — target size, attack coverage, or the
report's honesty. Choosing target size is what failed three times.
Choosing honesty is ADR-0019's already-accepted ground: triage
prioritizes, it never skips.

## Decision

We will resolve targets mechanically and map them whole. A target is
what the invocation names, or — for a repo root or broad directory —
the language-convention folders inside it, one per supported language
present. Ambiguity across buildable modules is the only question
returned to the user. Testability (the no-socket test) filters
surfaces, never target size.

A run ends every mapped surface attacked or explicitly not-run, and
the coverage counts carry the ledger. Not-run is a reported state, not
a shortcut: per ADR-0019, triage reorders the attack and never decides
a surface out of it. A whole-target map may therefore span runs — the
next run's Discover reuses the prior `map.md` after re-verifying rows
against current code, since landed fixes invalidate contracts (the
ADR-0019 baseline line dates the map; the re-verification dates the
rows).

Probes remain per-run instruments, deleted once the run-end checks
pass (amended 2026-09-29: the checks still exercise scratch — the
sensitivity mutant runs there). The durable cross-run product is the
map, `learn/`, the landed suite tests, and replayable findings
evidence; a probe's full specification survives in its finding's
recorded repro, so deletion loses bytes, not information.

## Consequences

**Good**: complete coverage becomes decidable per run (mapped /
executed / not run), scope-shrink loses every legitimate-looking
route, reruns start from verified contracts and impact classes instead
of re-deriving them, and a report can never read complete while mapped
surfaces went un-attacked.

**Bad**: first contact with a large repo pays a full mapping pass
before attack value lands. Maps go stale as fixes land; re-verification
is real work every rerun pays. The not-run ledger is prose-checkable,
not machine-graded — it is only as honest as the agent writing it.

**Risks**: if cold runs repeatedly die mid-map on very large targets,
whole-target mapping needs batching machinery (a run controller that
pages Discover) — revisit when a run cannot finish a map at all. If
graders ever demand machine-verifiable coverage, the ledger must move
from the chat report into `report.json`; the map and findings already
carry the rows, so that is a schema change, not a behavior change.
