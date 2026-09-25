# ADR-0007: Optional dependencies degrade inline

**Status**: Accepted
**Date**: 2026-09-24
**Deciders**: Mike Henke

## Context

sstack's stages lean on things outside the pack: optional lifecycle
skills (`principle-*`, `create-verification-skill`), the target's
property-testing and mutation tools, host subagent dispatch. Cold-run
experience showed agents silently stalling or skipping stages when a
named dependency was simply unavailable — the skill said "use X," X
was not installed, and the run either asked the user or skipped
coverage. ADR-0004 already commits to delegating to the target's own
tools; what it left open is what happens when there is nothing to
delegate to.

## Decision

Every optional dependency named in sstack text ships, in the same
paragraph, its fallback: the concrete procedure the agent runs when
the dependency is absent. Discovery degrades to docs, types, and call
sites; subagent fan-out degrades to sequential self-run lenses; the
ownership rubric degrades to deriving the model from surface
parameters. Absence changes quality, never capability. A skill
reference may not be load-bearing.

## Consequences

**Good**: one text works on every host — no Cursor-only assumptions,
which is ADR-0002's promise kept at the stage level. Runs complete on
partial toolchains instead of stalling on the first missing name.

**Bad**: the skill text grows; every optional feature pays for itself
twice (use + fallback). Some fallbacks duplicate the principle
skill's own content, and the copies can drift from the originals.

**Risks**: a fallback could quietly become the main path — if cold
runs consistently take the sequential lane, the fan-out text is
dead weight; re-evaluate then, not by speculation. Keep each
fallback to the few sentences that carry the procedure's floor, not
its polish.
