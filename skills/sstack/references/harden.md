# Harden mode — fill the suite's negative-test gaps

Routing loads this file on `/sstack harden <target>`. It is not a
stage and never runs inside the lifecycle. Every rule from the entry
skill still applies: oracle before execution, real commands only,
evidence through the emitter, the four rules. Harden changes what
gets written, not how anything is proven.

## 1. Map

Reuse `.sstack/map.md` only when its recorded target matches this
invocation's target; on mismatch or absence, run Discover first. A
stale-target map writes tests for the wrong module into the host
suite.

## 2. Assess — two isolated assessments

Dispatch two subagents concurrently. Neither sees the other's output,
and both start blank, so paste each everything it needs.

- **A, contract side.** Paste `map.md` and the selected lens rubrics.
  A enumerates, per surface × lens, the case families the surface's
  contract admits — each rubric's Case-generation heuristics, minus
  its When-not-to-apply. A never sees the suite.
- **B, suite side.** Paste the target's test tree. B extracts what
  the existing tests actually assert: literal test names and
  assertion text, no judgment about adequacy. B never sees A's list.

No subagent tool, or a dispatch fails or goes silent twice: run A,
then B, inline, and open the report with `⚠️ DEGRADED: single-context`
— Attack's serial fallback convention.

## 3. Synthesize

Gaps = A − B: admitted families no extracted assertion covers. Tag
each gap:

- P0 — external-input surface with zero negative coverage
- P1 — failure class present in `.sstack/learn/`
- P2 — partial coverage
- P3 — internal surface, low blast radius

## 4. Report

One per-lens table: `lens | admitted | covered | gaps | %`. Overall
percentage with bands: ≥90 Excellent, 70–89 Good, 50–69 Acceptable,
30–49 Poor, <30 Critical. Name positive findings (surfaces already
well covered) and systemic patterns (zero boundaries coverage
anywhere → recommend a custom lens).

Persist the report to exactly
`.sstack/harden/<date>-<target>-<seq>.md` — never `report.md`, never
another name (seq = two-digit same-day counter, `01` first; the trend
line dies without it). Print the trend across prior snapshots for the
same target: `24% → 61%`.

## 5. Scope

At ≥3 P0/P1 gaps, ask: fill all / P0+P1 only / one lens. Fewer —
fill without asking. When no user can answer (unattended run),
default to P0+P1 only and open the report with
`⚠️ UNATTENDED: defaulted to P0+P1 scope`. A run over the ≥3
threshold that neither asks nor carries the banner is invalid; small
inventories ask nothing and carry no banner by design.

## 6. Fill

One unmasked matrix test per surface × lens covering its gap
families — Stage 5's hardening convention: parametrized/subtest
vectors over baseline collections, same directory and assert style as
the existing suite, in P0→P3 order. Where the repo already imports a
property-based testing library, Stage 5's PBT branch applies: an
invariant property test may replace the matrix. Test names carry the
`sstack_<lens>_` prefix so a later run — or a stranger — can grep
what harden wrote. The oracle goes into the assertion before the
test ever runs.

Worked example — target `tokens.py` (a URL-token issuer), suite
asserting only happy-path issuance. A admits `ttl_seconds = 0`,
`ttl_seconds = -1`, `max_uses = 0` on `issue()` (boundaries); B
finds no covering assertion. Gap, P0 (external input). Fill writes:

```python
@pytest.mark.parametrize("ttl", [0, -1])
def test_sstack_boundaries_issue_rejects_nonpositive_ttl(ttl):
    with pytest.raises(ValueError, match="ttl_seconds must be positive"):
        issue(ttl_seconds=ttl)
```

## 7. Execute and split

Run each test as written.

- **Green** — it lands as a hardening test. Emit `verdict: refuted`,
  regression `green → green`.
- **Red** — the gap hid a live bug. Flip into the lifecycle:
  1. Snapshot the target's originals into `.sstack/pristine-src/`
     before any fix; replay depends on it.
  2. Rewrite the red matrix as the single-vector atomic test Stage 5
     requires for confirmed findings — `regression.test` names the
     atomic test, never the matrix.
  3. Minimize, sensitivity check, minimal fix, green — the confirmed
     path, unchanged.

Rule 4 is inviolable: harden never pins a bug with a red test left
in the suite.

## 8. Emit

Every landed test and every flip becomes a finding through
`emit_findings.py` — harden runs emit like any other run, and a
harden workspace with no `report.json` is an invalid run, whatever
its tests say. The chat report ends with counts: gaps filled,
hardening tests added, live bugs found and fixed.

## Learn

Pure-green harden runs write nothing to `.sstack/learn/`. A flip
records its confirmed failure class per the existing rule.

## Safety

Outside a flip, harden writes only test files. Every source edit must
trace to a confirmed finding; an edit with no finding behind it is an
invalid run. No test framework detected → ask before scaffolding one.
Target build configs stay read-only.
