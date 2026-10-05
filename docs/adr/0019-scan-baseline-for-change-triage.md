# ADR-0019: map.md records a scan baseline; the next run triages by git diff

**Status**: Accepted
**Date**: 2026-09-29
**Deciders**: Mike Henke

## Context

A repeat run re-attacks every surface with no memory of what changed
since the previous one, but the user's first question on run two is
"what changed since last time?" Learn already compounds knowledge
across runs — as prioritization, "never as proof" — and harden keeps
coverage trend snapshots; the main lifecycle has no change memory at
all.

Per-file SHA tables were considered and rejected: a file hash proves a
file changed, not that a surface's contract changed. Per-function
hashing needs per-language AST parsing (violates the zero-runtime
lock) or text spans that shatter on any edit above the function. The
target repo's own git metadata is the source of truth for change —
rename detection, per-commit history, and blame come free, and a
baseline that does not exist must degrade to today's full Discover,
not fail ([ADR-0007](0007-optional-deps-degrade-inline.md)).

## Decision

Discover records one baseline line in `map.md`: the target repo's HEAD
commit SHA, the run date, and the scope argument. The next run over
the same scope reads it, derives changed files with
`git diff --name-only <baseline>..HEAD`, and marks surfaces in changed
files as priority surfaces for that run's attack.

Changed means prioritized, never skipped: unchanged surfaces are still
mapped and attacked, mirroring the Learn rule. The baseline is
rewritten at run end, after Fix, so post-fix source does not
false-flag every later run. No git, no baseline, or a scope with no
overlap: full Discover exactly as today. Prior evidence is never
re-verdicted or pruned; baseline comparison is additive triage only.

## Consequences

**Good**: repeat runs answer "what changed" with one git call; attack
effort concentrates on drift; the whole feature is one map line and
one invocation — no new artifacts, no schema change, no emitter
change, nothing for a user to configure.

**Bad**: crossing branches flips the whole diff — correct, but noisy.
The baseline can rot if a run dies between Fix and run end; the
rewrite-at-run-end rule is the mitigation.

**Risks**: treating "unchanged" as "clean" would reduce coverage below
today's behavior — the never-skip rule is the guardrail, and a run
that skips unchanged surfaces is invalid. Semantic contract diffing
(comparing derived contracts, not files) is a v1 project; this ADR
triages, it does not diff contracts.

Shipped-text note (2026-10-02): the baseline line and triage rule now
live in SKILL.md's Discover stage; no recorded cold run predating
that text exercised the rule.
