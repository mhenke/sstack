# Research index

The dated community scans behind decisions in this repo, and the ones
still open. Full raw transcripts live in the local research library
(`~/Documents/Last30Days/`, or `LAST30DAYS_MEMORY_DIR`). This file is
the index into them and the record of what each one changed.

## Applied to shipped decisions

### Negative testing across five languages (2026-09-23)

Tool inventory from this scan: [`TOOLS.md`](TOOLS.md).

Source: `negative-testing-edge-case-unit-testing-across-languages-raw-v3.md`
in the library. Distilled into
[LEARNED.md](LEARNED.md). Fed [ADR-0004](adr/0004-delegate-to-target-existing-tools.md)
(lenses delegate to the target's own property-based and mutation
tooling), the edge-case/negative-case Vocabulary block in
[ARCHITECTURE.md](ARCHITECTURE.md), and the property-based and
mutation items on the roadmap.

## Relevant to open roadmap work

### Agent harness evaluations (2026-07-13 to 2026-08-12)

Source: `ai-harness-evaluations-best-practices-oh-my-opencode-slim-omos-raw-v3.md`.
Relevant because sstack's whole thesis is eval-gated acceptance
(ADR-0003). The scan covers custom native evaluation harnesses for AI
systems, including the point that production AI degrades silently
without one. Worth reading before the structured-evidence-schema item:
it is the same problem sstack solves for prose skills, approached from
the harness side.

### Evals for agents (2026-07-21 to 2026-08-20)

Source: `evals-for-agents-raw-v3.md`. Same subject from a later
window, and it overlaps the acceptance-harness work already shipped.
Relevant to any v1 decision about how seeded-repo evals should be
structured or scored.

### Loop engineering (2026-05-28 to 2026-06-27)

Source: `loop-engineering-raw-v3.md`. Relevant to the learn-loop
roadmap item. Covers driving long autonomous agent runs to completion;
the learn loop is a smaller version of the same problem, keeping a run
prioritized by what a prior run learned.

## Background, no action yet

### Rolling out AI into the software lifecycle (2026-06-14 to 2026-07-14)

Source: `rolling-out-ai-into-the-software-development-lifecycle-raw.md`.
General SDLC framing. No specific roadmap item depends on it; kept for
context if the project scope widens beyond testing.

## Adding to this index

When a scan changes a decision, distill it the way `LEARNED.md` does
and link it from here. Do not paste raw transcripts into this repo.
The library is the archive; this file is the map.
