# Cold acceptance results — sstack v0

Runs: fresh subagent given only a copy of the skills
(`skills/sstack/` plus the six `skills/sstack-<lens>/` peers) and the
six `agents/sstack-<lens>-attacker.md` files, and a BUGS.md-free copy
of the seeded repo, in a temp workspace
(`python3 evals/acceptance.py prepare` copies all of it into one
isolated dir).

## Verdict

> **Graded 2026-09-24** with the content-match grader (`b05b94b`)
> against the current skill text. Findings link to goldens by
> trigger content (function name / trigger words across surface,
> case, oracle); self-reported `seed_id` is advisory, landed
> regressions are verified on disk.

| Repo | Verdict | Detail |
|---|---|---|
| seeded-py | PASS | 7 findings; py-1, py-3 content-matched with landed red→green regressions; label contradictions recorded as warnings |
| seeded-java | PASS | 4 confirmed; java-1, java-2, java-4 content-matched, 4/4 red→green claims verified against workspace test files |
| seeded-ts | INVALID | one empty finding object; run still in progress |
| seeded-js | INVALID | report hand-typed, unparseable JSON (line 33); evidence fingerprints placeholder (`a1b2c3d4...`) — replay grades them fabricated |
| seeded-cpp | not landed | 7 confirmed claimed but regression shape non-compliant (no `before`/`after`); run still in progress |

The historical PASS numbers below were produced by the skill text at
commit `9979718` and are stale for the current text. JavaScript, Java,
and C++ cold-run acceptance is now recorded above; do not report
language support as proven beyond what this table shows.

## Run history (python)

| Run | Skill text | Isolation | Outcome |
|---|---|---|---|
| #1 | pre-guardrail | temp copy, prompt-only | INVALID — 9 regressions pinned the buggy behavior (all passing) |
| #2 | pre-guardrail | temp copy, prompt-only | INVALID — edited source (`shop/pricing.py`), reported 0 findings after self-fixes |
| #3 | pre-guardrail | temp copy, prompt-only | INVALID — escaped temp target, edited the main-repo seeds, read main-repo BUGS.md; seeds restored via `git checkout`, 5/5 green, probes reproduce |
| #4 | decontaminated (CONTAMINATED lens files) | isolated workspace | Superseded — not evidence |
| #5 | decontaminated | isolated workspace | FAIL 0/5 — 105 attack scripts never reached the functions (wrong import path, missing args); every "oracle satisfied" was a harness TypeError |
| #6 | decontaminated + execution-validity fix | isolated workspace | PASS (pre-audit skill text) |
| #7 | v0.1.0 + PBT delegation + mutation + run-end checks + steel-man + edge-case vocab | isolated workspace, read-only lock | INVALID — 10 findings, 10 green characterization regressions (bug-pinning). Source untouched. Run-end check #4 not applied by the cold agent. |
| ColdPy-2 | current text (`e29af03`+) | isolated workspace | PASS on root `report.json` (7 findings, py-1/py-3 matched); `.sstack/report.json` re-emit hit a control-char parse error; evidence files still being written |

## Run history (typescript)

| Run | Skill text | Isolation | Outcome |
|---|---|---|---|
| CleanTs | decontaminated + execution-validity fix | isolated workspace | PASS (pre-audit skill text) |
| RunTs | v0.1.0 + PBT delegation + mutation + run-end checks + steel-man + edge-case vocab | isolated workspace, read-only lock | DID NOT COMPLETE — 40+ min, stuck in Attack, no regressions landed, no findings reported. Fan-out subagents explored the sstack repo, not the temp workspace. Source and tests untouched. |
| ColdTs-2 | current text (`e29af03`+) | isolated workspace | in progress; draft report had one empty finding object (INVALID as of 2026-09-24 21:45) |

## Run history (js / java / cpp, current text)

| Run | Fixture | Outcome |
|---|---|---|
| ColdJs | seeded-js | INVALID — finished 3 confirmed + fixes + 4 test files, but hand-typed `report.json` unparseable (unescaped quotes, line 33) and all evidence fingerprints placeholder (`a1b2c3d4...`); replay grades them fabricated |
| ColdJava | seeded-java | PASS — 4 confirmed red→green; java-1/2/4 content-matched; self-labels shifted (advisory only) |
| ColdCpp | seeded-cpp | in progress — 7 confirmed claimed, regression object non-compliant (`status:"red"` instead of `before`/`after`), evidence JSONs not yet emitted |

Runs #1–#5 drove four product fixes, all committed:
- `2880501` — forbid bug-pinning regressions; require per-surface lens
  coverage; invalid-run gate when confirmed findings have only passing
  regressions
- `7c375b8` — find-only contract at the title, routing, and safety
  (run #2 treated the skill as a hardening command; ADR-0005 later
  added the confirmed-fix path)
- `14a1139` — decontaminate the lens worked examples; harness excludes
  `.pytest_cache`, `__pycache__`, `.vite`; corrected this record
- `f7f5ce6` — attacks must reach the function under attack; harness
  errors are broken cases, never verdicts (run #5 read its own broken
  harness as 105 satisfied oracles)

Also: `python3 evals/acceptance.py prepare` copies the skill INTO the
temp workspace so a cold agent never needs to touch the sstack repo
(run #3 escaped by editing the main-repo seeds and reading BUGS.md).

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
read all six lens files. Those results are NOT evidence of
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
- The 2026-09-24 wave graded INVALID for artifact reasons, not
  judgment reasons: hand-typed JSON (unescaped quotes, control chars,
  placeholder fingerprints, wrong regression shape). The fixes are
  contractual, not polite: script-emitted reports with in-process
  fingerprints, content-match grading, out-of-loop replay. A finding
  whose evidence cannot replay is not proven, however sharp the
  prose.
- Self-reported seed labels are unreliable across all five fixtures
  (Java shifted by one; Python invented `py-6`–`py-8`). The grader
  treats them as advisory; content match carries every pass.
