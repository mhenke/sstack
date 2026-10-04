# Triage — churn-ranked surface heat before a full Discover

Routing loads this file on `/sstack triage <target>`. It is not a
stage and never runs inside the lifecycle (the on-demand tier,
ADR-0016/ADR-0018). Triage answers one question: where would a
negative tester look first? It ranks the target's surfaces by change
heat and failure-class adjacency, then hands the ranking to Discover.
It never attacks, never edits source or tests, and never shrinks the
target — ADR-0020's rule is unchanged here: triage reorders, it never
skips.

## 1. Resolve and read

The target is resolved, never chosen — same rule as Routing. Read
`.sstack/map.md` when a prior run left one (reuse its surface rows
and impact classes after re-verifying them against current code) and
`.sstack/learn/` for recorded failure classes. Read `docs/adr/` and
`GLOSSARY.md` (or domain docs) to ground invariants and recorded
decisions before ranking. A prior run's baseline line makes this the
rerun case: ADR-0019's `git diff <baseline>..HEAD` triage applies
directly, and the heat pass below fills the cold-start gap when no
baseline exists yet.

## 2. Heat pass

`git log --since=<window> --name-only -- <target>` — window 90 days,
or all of it when the repo is younger. Count touches per file; fold
paths into surfaces at map-row granularity (variants of one
assumption share a surface). Score = touches, raised one band when
the surface is adjacent to a recorded `learn/` failure class, one
band by impact class (privilege boundary, sensitive-data mutation,
integrity, availability, presentation). No git, empty history, or no
overlapping commits: say so and rank by impact class alone — a
missing signal degrades inline, never fails the run (ADR-0007).

## 3. Friction walk

One subagent, blank start, everything pasted: the top ten surfaces
(all when ten or fewer) with their files, assumed contracts, and
callers. The walk reports per surface, in that surface's language:
where external input enters unvalidated, which callers pass only
constants (reachability caps impact — a constant-only caller
demonstrates no adverse input path), where pure functions were
extracted for testability but defect risk lives in caller integration
(the shallow helper / locality trap — prioritize the caller's seam over
an internal helper), where partial writes or unguarded mutations sit,
and which existing negative tests already cover it when the suite tree
is available. Friction questions, not comprehension questions — the
walk exists to rank attack value, not to re-describe the code.
Dispatch fails or goes silent twice: run the walk inline, one surface
at a time.

## 4. Snapshot

Persist to exactly `.sstack/triage/<date>-<target>-<seq>.md` (seq =
two-digit same-day counter, `01` first). One ranked table: `rank |
surface | heat | impact | adjacent learn | the one-line why` — the
why names the adverse condition a negative test would exercise. End
with the hand-off line: `N surfaces hot of M mapped; full Discover
still owns the target` — the ranking is advice; the whole-target map
remains Discover's to complete, across runs if needed (ADR-0020).

## 5. Hand-off

The next `/sstack <target>` run's Discover reads the newest triage
snapshot and selects lenses in the hot band first. Triage writes
nothing else: no findings, no tests, no source edits, no
`report.json` — a triage workspace carrying findings or a report is
an invalid run.

Worked example — target `billing/`: `git log --since=90d --name-only
-- billing/` shows `credit_note.py` touched 31 times, `statement.py`
twice; `.sstack/learn/` records `idempotency | duplicate retry
double-issue`. Heat ranks `credit_note.py` first — touches,
adjacency, and integrity impact agree; the walk reports its
`retry_hook` accepts external retries unvalidated, so the why reads:
"external retries reach a money mutation — does a duplicate issue
reject?" `statement` ranks last. The next Discover selects
idempotency and boundaries on the credit-note surfaces first and
still maps all of `billing/`.

## Safety

Read-only outside `.sstack/triage/`. Git runs read-only porcelain
commands. A snapshot over an empty hot band (no commits, no learn
entries) says so and ranks by impact class — never silently empty.
Keep secrets, transcripts, and one-off instructions out of snapshots.
