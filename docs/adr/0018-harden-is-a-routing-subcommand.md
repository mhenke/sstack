# ADR-0018: Harden is a routing subcommand that fills gaps, not a stage or lens

**Status**: Accepted
**Date**: 2026-09-29
**Deciders**: Mike Henke

## Context

[ADR-0005](0005-sstack-finds-tests-and-fixes.md) made sstack find-tests-and-fixes: one run attacks, proves,
tests, and repairs. The Test stage's hardening path fires only per
finding, so a surface whose adverse condition already works gets a
test only if some lens happened to probe it — and a surface no lens
probed never gets one. Real suites carry most of their negative
coverage debt exactly there: nothing is broken, and nothing is tested.

Harden mode fills those gaps directly: it assesses what the suite
actually asserts against what the target's contracts admit, and writes
the missing negative tests even where nothing is broken. This is a
third position in the project's lineage — audit-only ([ADR-0002](0002-content-only-agent-agnostic-skill.md)), then
find-tests-and-fixes ([ADR-0005](0005-sstack-finds-tests-and-fixes.md)), now fill-gaps-proactively — and reads
as drift unless the boundary is recorded.

Three placements were considered:

- **A stage** — rejected. The seven stages are fixed by doctrine
  (ApoSD: the orchestrator's own text, nothing to append to); harden
  also inverts the lifecycle (tests before any attack), which a stage
  slot cannot express.
- **A lens** — rejected. A lens is an attack strategy over surfaces
  and can only emit findings. Gap-filling needs the suite side too:
  admitted contract families minus extracted assertions. That is an
  A−B assessment, not an attack.
- **A routing subcommand** — chosen. One routing bullet, body in the
  on-demand references tier ([ADR-0016](0016-on-demand-references-tier.md)), reusing Stage 5's hardening
  conventions, the emitter, and the flip path unchanged.

## Decision

`/sstack harden <target>` is a routing subcommand, not a stage and not
a lens. Its body lives at `skills/sstack/references/harden.md`. Rules
that keep it inside the existing contract:

- Writes only test files; a source edit must trace to a confirmed
  finding (run-end check: every confirmed regression is red against
  pristine source). Red flips enter the existing Test/Fix lifecycle
  untouched.
- Unattended runs default to P0+P1 scope behind a printed banner;
  attended runs ask at the ≥3-gap threshold. A threshold run that
  neither asks nor carries the banner is invalid.
- Every outcome emits through the evidence emitter like any other run;
  a harden workspace without `report.json` is an invalid run.
- Pure-green runs write nothing to `.sstack/learn/`.

## Consequences

- A run's output is proportional to the suite's actual negative
  coverage, not to its bug count — a clean run is a full hardening
  pass, and the harden snapshot records the percentage so the next run
  prints a trend.
- The mode inherits the evidence contract wholesale, so graders,
  replay, and acceptance rules apply without a second track.
- Control runs are the mode's acceptance mechanism: each cold control
  run's violations force mechanical run-end checks ([ADR-0003](0003-eval-gated-acceptance.md)'s
  failures-compound doctrine applied to a mode that mostly writes
  green tests, where over-claiming — not breakage — is the failure
  mode to guard).
