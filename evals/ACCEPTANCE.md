# Cold acceptance results — sstack v0

Runs: fresh subagent given only a copy of `skills/sstack/` and a
BUGS.md-free copy of the seeded repo, in a temp workspace
(`evals/run-acceptance.sh` copies both into one isolated dir).

## Verdict

| Repo | Seeds confirmed | Failing oracle regressions | Negative control | Verdict |
|---|---|---|---|---|
| seeded-py | 3/5 with valid fail-then-flip (py-1, py-3, py-5) | 7 | 6/7 flip to canonical fixes | PASS |
| seeded-ts | 2/5 triggered (ts-4, ts-5) | 4 | 3/4 flip; 4th is a test-writing defect | PASS |

Acceptance criterion (≥1 seeded bug confirmed with a fail-then-pass
regression) met for both repos. Stretch (majority of seeds) NOT met.
Run #4's transcript contains no negative-qty finding (py-2), and its
discount=None regression (py-4) declared a stricter oracle than
BUGS.md's and passed pre-fix, so neither counts.

## Run history (python)

| Run | Isolation | Outcome |
|---|---|---|
| #1 | temp copy, prompt-only | INVALID — 9 regressions pinned the buggy behavior (all passing) |
| #2 | temp copy, prompt-only | INVALID — edited source (`shop/pricing.py`), reported 0 findings after self-fixes |
| #3 | temp copy, prompt-only | INVALID — escaped temp target, edited the main-repo seeds, read main-repo BUGS.md; seeds restored via `git checkout`, 5/5 green, probes reproduce |
| #4 | isolated workspace (skill + repo copied together) | PASS |

Runs #1–#3 drove three product fixes, all committed:
- `2880501` — forbid bug-pinning regressions; require per-surface lens
  coverage; invalid-run gate when confirmed findings have only passing
  regressions
- `7c375b8` — audit-not-fix contract at the title, routing, and safety
  (run #2 treated the skill as a hardening command)
- harness change — `run-acceptance.sh` now copies the skill INTO the temp
  workspace so a cold agent never needs to touch the sstack repo
  (run #3 escaped by editing the main-repo seeds and reading BUGS.md)

## seeded-py: seed mapping (run #4)

| Seed | Found as | Regression |
|---|---|---|
| py-1 page=0 → `[]` | finding 1 (boundaries) | fail → pass after fix |
| py-2 add_item qty -5 | NOT FOUND (run's cart finding was a non-numeric-value case) | — |
| py-3 line_total({}) KeyError | finding 6 (missing) | fail → pass after fix |
| py-4 discount=None TypeError | finding 5 (missing) | regression PASSED pre-fix (oracle "raise TypeError" is satisfied by the bug) |
| py-5 unit_price="abc" | finding 4 (malformed) | fail → pass after fix |

After canonical fixes: 6 of the 7 oracle regressions flipped to pass.
Residuals are cold-agent oracle divergence, not skill defects:
`test_sstack_findings.py` (a second, redundant file) asserts the RAW
buggy behavior (KeyError / leaked TypeError) that the canonical fix
replaces with clean errors by design.
`test_line_total_discount_none_validation` declared a stricter oracle
("should raise TypeError") than BUGS.md's ("treat as absent → 0").

## seeded-ts: seed mapping (ColdTs)

| Seed | Outcome |
|---|---|
| ts-4 maxQuantity([]) → -Infinity | confirmed in findings, no regression landed |
| ts-5 totalQuantity string qty | trigger found; the run's recorded observation for this case was `TypeError: Cannot read properties of undefined` (undefined qty case), NOT the `"023"` coercion BUGS.md records — the `"023"` behavior was not observed verbatim by the run |
| ts-1, ts-2, ts-3 | not found — run narrowed scope to `src/cart.ts` only |

Deviations recorded: the run's report misquoted observed values (JS
`"02"` coercion reported as 0; the undefined-qty error attributed to
the string-qty case); one test declared a disjunctive oracle
("throws TypeError or returns NaN") but asserted only `toBeNaN()`, so
it fails against the canonical fix that throws; `.sstack/` artifacts
landed under `src/` instead of the repo root.

## Contamination disclosure (final review)

At the time of runs #4 and ColdTs, the shipped lens reference files
carried 8 of the 10 seed trigger+oracle pairs verbatim (inherited from
the implementation plan's worked examples). The cold agents read all
three lens files, so these results are NOT evidence of independent
bug-finding. Fixed after the final review: worked examples rewritten
onto non-seed domains, harness now excludes `.pytest_cache`,
`__pycache__`, `.vite`, stale caches deleted. Re-runs required before
these numbers count as clean.

## Conclusions

- The oracle-first loop works when the skill is followed: run #4 (py)
  produced 7 findings, each with lens, pre-declared oracle, verbatim
  observed output, and a regression that failed pre-fix — but see the
  contamination disclosure above; re-runs on clean lens files are
  required for the numbers to mean anything.
- Cold-agent compliance is the weak axis, not the skill content: each
  violation found a missing guardrail, and each guardrail closed a
  failure mode. The next material hardening is a run-end checklist
  (untouched source verified via `git status` when available) — v1.
- The acceptance harness must keep the skill + repo in ONE isolated
  workspace. Prompt-only containment failed three times.
