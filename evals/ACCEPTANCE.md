# Cold acceptance results — sstack v0

Runs: fresh subagent given only a copy of `skills/sstack/` and a
BUGS.md-free copy of the seeded repo, in a temp workspace
(`evals/run-acceptance.sh` copies both into one isolated dir).

## Verdict

> **Stale**: the numbers below were produced by the skill text at
> commit `9979718`. The skill has since gained PBT delegation, mutation
> references, run-end checks, a steel-man Verify step, and the
> edge-case/negative-case vocabulary split. Re-run before treating
> these numbers as current.

| Repo | Seeds confirmed | Failing oracle regressions | Negative control | Verdict |
|---|---|---|---|---|
| seeded-py | 4/5 (py-1, py-2, py-4, py-5); py-3 not found | 9 | 9/9 flip — 14/14 green | PASS |
| seeded-ts | 5/5 (ts-1, ts-2, ts-3, ts-4, ts-5) + 1 unseeded real bug (M5) | 22 | 34/35 flip; 1 disjunctive-oracle test defect | PASS |

Acceptance criterion (≥1 seeded bug confirmed with a fail-then-pass
regression) met for both repos. Stretch (majority of seeds) met for
both. All numbers below are from the CLEAN re-runs (#6 py, CleanTs ts)
performed after the final-review decontamination; earlier contaminated
runs are retained in the run history for the record only.

## Run history (python)

| Run | Isolation | Outcome |
|---|---|---|
| #1 | temp copy, prompt-only | INVALID — 9 regressions pinned the buggy behavior (all passing) |
| #2 | temp copy, prompt-only | INVALID — edited source (`shop/pricing.py`), reported 0 findings after self-fixes |
| #3 | temp copy, prompt-only | INVALID — escaped temp target, edited the main-repo seeds, read main-repo BUGS.md; seeds restored via `git checkout`, 5/5 green, probes reproduce |
| #4 | isolated workspace (CONTAMINATED lens files) | Superseded — not evidence |
| #5 | isolated workspace, decontaminated | FAIL 0/5 — 105 attack scripts never reached the functions (wrong import path, missing args); every "oracle satisfied" was a harness TypeError |
| #6 | isolated workspace, decontaminated + execution-validity fix | **PASS — the evidence run** |

Runs #1–#5 drove four product fixes, all committed:
- `2880501` — forbid bug-pinning regressions; require per-surface lens
  coverage; invalid-run gate when confirmed findings have only passing
  regressions
- `7c375b8` — audit-not-fix contract at the title, routing, and safety
  (run #2 treated the skill as a hardening command)
- `14a1139` — decontaminate the lens worked examples; harness excludes
  `.pytest_cache`, `__pycache__`, `.vite`; corrected this record
- `f7f5ce6` — attacks must reach the function under attack; harness
  errors are broken cases, never verdicts (run #5 read its own broken
  harness as 105 satisfied oracles)

Also: `run-acceptance.sh` copies the skill INTO the temp workspace so a
cold agent never needs to touch the sstack repo (run #3 escaped by
editing the main-repo seeds and reading BUGS.md).

## seeded-py: seed mapping (run #6, clean)

| Seed | Found as | Regression |
|---|---|---|
| py-1 page=0 → `[]` | F2 (boundaries) | fail → pass |
| py-2 add_item qty -1 → total -1 | F6 (boundaries) | fail → pass |
| py-3 line_total({}) KeyError | not found | — |
| py-4 discount=None TypeError | F7 (missing; oracle "treat as absent → 20.0" matches BUGS.md) | fail → pass |
| py-5 unit_price="abc" raw ValueError | F8 (malformed) | fail → pass |

9 confirmed findings, 9 failing oracle regressions, source and happy
suite untouched. After canonical fixes: **14/14 pass, zero residuals**
— no pinned-bug second file, no oracle divergence. py-3 (empty dict)
was not found; it is the one gap.

## seeded-ts: seed mapping (CleanTs, clean)

| Seed | Outcome |
|---|---|
| ts-1 paginate page=0 → `[]` | P1 (boundaries) — fail → pass |
| ts-2 lineTotal missing unitPrice → NaN | L6 (missing) — fail → pass |
| ts-3 parseOrder raw SyntaxError | J1 (malformed) — fail → pass |
| ts-4 maxQuantity([]) → -Infinity | M1 (boundaries) — fail → pass |
| ts-5 string qty coerces result type | T2 (malformed) — fail → pass* |

22 confirmed findings across all three modules — the widest coverage of
any run. **M5 is a real bug the answer key does not contain**:
`Math.max(...lines.map(...))` overflows the call stack on a large but
legitimate array. The run found it; the canonical fix (reduce, not
spread) makes it flip.

After canonical fixes: 34/35 pass. The single residual is T2's
test writing, not the code: it asserts `typeof result === "number"`
(coerce) while BUGS.md's fix throws. A disjunctive oracle encoded as a
single branch.

Deviations recorded: the run's report misquoted observed values (JS
`"02"` coercion reported as 0; the undefined-qty error attributed to
the string-qty case); one test declared a disjunctive oracle
("throws TypeError or returns NaN") but asserted only `toBeNaN()`, so
it fails against the canonical fix that throws; `.sstack/` artifacts
landed under `src/` instead of the repo root.

## Contamination disclosure (final review) — resolved

At the time of run #4 and the first ColdTs, the shipped lens reference
files carried 8 of the 10 seed trigger+oracle pairs verbatim (inherited
from the implementation plan's worked examples), and the cold agents
read all three lens files. Those results are NOT evidence of
independent bug-finding and are retained above only as run history.
Fixed in `14a1139`: worked examples rewritten onto non-seed domains,
harness excludes `.pytest_cache` / `__pycache__` / `.vite`, stale
caches deleted. Re-runs #6 (py) and CleanTs (ts) were performed on the
decontaminated skill; their results are the verdict table above.

## Conclusions

- The oracle-first loop works end to end on a clean skill: run #6
  produced 9 py findings and CleanTs 22 ts findings, each with lens,
  pre-declared oracle, verbatim observed output, and a regression that
  failed on the seed and passed after the canonical fix.
- Negative control is the real proof: 9/9 (py) and 34/35 (ts)
  regressions flip under canonical fixes. The single ts residual is a
  disjunctive-oracle test defect, not a product defect.
- Cold-agent compliance is the weak axis, and every violation found a
  missing guardrail: bug-pinning (2880501), fix-it-yourself (7c375b8),
  broken-harness-as-evidence (f7f5ce6). The next material hardening
  is a run-end checklist (untouched source verified via `git status`
  when available) — v1.
- The acceptance harness must keep the skill + repo in ONE isolated
  workspace. Prompt-only containment failed three times.
- The tool found a bug the answer key did not contain (M5, spread
  overflow). That is the strongest signal in this record.
