# ADR-0011: Keep the lens grid uniform and accept the two-card tail

**Status**: Accepted
**Date**: 2026-09-27
**Deciders**: Mike Henke

## Context

The lens grid ships every lens at the same size, `grid-column: span 1`.
When the shipped count was twelve, a 3-column matrix flowed 3/3/3/3 —
four even rows. The lens waves of 2026-09-26/27 (security, agent, and
four behavior lenses) grew the count to fourteen, and the grid moved to
4 columns at ≥1024px, flowing 4/4/4/2. Two audits disagreed on the
two-card tail: one read it as a regression of DESIGN.md §20's
uniform-matrix rule and proposed span-2 cards to force four clean rows;
the other accepted it as a count artifact. The impeccable layout
doctrine settles the tie: "variation is not a goal by itself;
repetition should support recognition; break it only when content or
priority changes," and repeated cards are honest when they are
"genuinely equivalent, not merely a framework default."

The fourteen lenses are genuine peers — no lens outranks another — so
a wider card would claim hierarchy the content does not have.

## Decision

We will keep the lens grid a uniform matrix with every card at
`span 1` and accept the two-card tail at fourteen lenses. No card is
widened without a content or priority reason. Copy-fit is the
condition: the shipped gist must render without clipping at the
narrowest desktop column (264px at ≥1024px, verified in Chromium:
zero clipped or scrolling cards).

## Consequences

**Good**: the grid reads as an honest inventory of peers; lens
additions and removals never require a bespoke layout pass; the
system documents its own rule so future counts have a precedent
(a fifteenth lens flows 4/4/4/3).

**Bad**: the tail row looks less finished than four even rows, and
the shape changes with every lens wave, so screenshots drift.

**Risks**: a future lens with much longer copy could cramp at
264px. The revisit trigger is a clipped or scrolling card at the
narrowest column — fixed then by shortening copy or (only with a
recorded content reason) a span, never by default.
