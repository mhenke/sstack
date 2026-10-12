# ADR-0025: Decision-lane findings are a distinct verdict

**Status**: Accepted
**Date**: 2026-10-12
**Deciders**: Mike Henke

## Context

Negative testing kept surfacing two kinds of failure the lifecycle
treated identically: defects the contract clearly forbids, and adverse
conditions whose desired behavior the contract never determined —
business or contract decisions, and upstream data or process gaps.
Fixing the second kind means guessing desired behavior; hardening
around it hides the broader issue. A reviewing human lacks the context
to know which behavior is actually desired.

The evidence contract admits only `confirmed`, `refuted`, and
`inconclusive`, and `confirmed` requires a red test against pristine
source flipped green by a fix — an unfixed finding cannot honestly be
confirmed. The alternatives were overloading `inconclusive` (real
discoveries then read as attack noise in every count) or reporting the
classification in prose only (machine-blind: no filtering, no
trending, no run-end enforcement).

## Decision

We will judge a reproduced failure whose desired behavior is
undetermined as `needs-decision`: report-only evidence requesting a
human contract decision. Every `confirmed` and `needs-decision` finding
carries a root-cause class — `contract-violation`, `contract-gap`, or
`upstream-data-process`, first match in that order — and only
`contract-violation` is ever fixed. A `needs-decision` finding forbids
a fix, lands no test, and records what contract evidence was searched
and found silent.

## Consequences

**Good**: report counts stay honest (a decision request is never
counted as a bug found); the lanes are mechanically checkable at run
end; the human gets decision context instead of a guessed behavior;
rule 4 stays inviolable on harden's red-flip path.

**Bad**: the verdict enum and finding shape change — both emitters,
GLOSSARY.md, and the run-end checks move together, and recorded
cold-run numbers need a staleness note (ADR-0003).

**Risks**: misclassification lanes a real defect as report-only or a
decision as a fix — mitigated by the precedence rule, mandatory
provenance evidence per lane, and the can't-classify → `inconclusive`
fallback that keeps the fix lane conservative by construction. Weak
backends may echo the old three verdict tokens — the enum lives in
the read window and the emitter rejects unknown verdicts loudly.
Revisit if `needs-decision` findings pile up unresolved.
