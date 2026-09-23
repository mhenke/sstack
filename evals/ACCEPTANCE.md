# Cold acceptance results — sstack v0

Runs: fresh subagent given only a copy of `skills/sstack/` and a
BUGS.md-free copy of the seeded repo, in a temp workspace
(`evals/run-acceptance.sh` copies both into one isolated dir).

## Verdict

| Repo | Seeds confirmed | Failing oracle regressions | Negative control | Verdict |
|---|---|---|---|---|
| seeded-py | 4/5 (py-1, py-2, py-3, py-5) | 7 | 7/9 flip to canonical fixes | PASS |
| seeded-ts | 2/5 triggered (ts-4, ts-5) | 4 | 3/4 flip; 4th is a test-writing defect | PASS |

Acceptance criterion (≥1 seeded bug confirmed with a fail-then-pass
regression) met for both repos. Stretch (majority of seeds) met for
seeded-py only.

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
| py-1 page=0 → `[]` | finding 1 (boundaries) | fail |
| py-2 add_item qty -5 | finding (malformed qty) + boundaries coverage | fail |
| py-3 line_total({}) KeyError | finding 6 (missing) | fail |
| py-4 discount=None TypeError | finding 5 (missing) | fail |
| py-5 unit_price="abc" | finding 4 (malformed) | fail |

After canonical fixes: 7 of 9 failing tests flipped to pass. The two
residuals are cold-agent oracle divergence, not skill defects:
`test_sstack_findings.py` (a second, redundant file) asserts the RAW
buggy behavior (KeyError / leaked TypeError) that the canonical fix
replaces with clean errors by design, and
`test_line_total_discount_none_validation` declared a stricter oracle
("should raise TypeError") than BUGS.md's ("treat as absent → 0").

## seeded-ts: seed mapping (ColdTs)

| Seed | Outcome |
|---|---|
| ts-4 maxQuantity([]) → -Infinity | confirmed in findings, no regression landed |
| ts-5 totalQuantity string qty | confirmed, regression fails as required |
| ts-1, ts-2, ts-3 | not found — run narrowed scope to `src/cart.ts` only |

Deviations recorded: two "observed" values misquoted (JS `"02"`
coercion reported as 0); one test declared a disjunctive oracle
("throws TypeError or returns NaN") but asserted only `toBeNaN()`, so
it fails against the canonical fix that throws; `.sstack/` artifacts
landed under `src/` instead of the repo root.

## Conclusions

- The oracle-first loop works when the skill is followed: every
  confirmed finding in run #4 (py) carries lens, pre-declared oracle,
  verbatim observed output, and a failing oracle regression.
- Cold-agent compliance is the weak axis, not the skill content: each
  violation found a missing guardrail, and each guardrail closed a
  failure mode. The next material hardening is a run-end checklist
  (untouched source verified via `git status` when available) — v1.
- The acceptance harness must keep the skill + repo in ONE isolated
  workspace. Prompt-only containment failed three times.
