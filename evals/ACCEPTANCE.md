# Cold acceptance results — sstack v0

Runs: fresh subagent given only a copy of the skills
(`skills/sstack/` plus the six `skills/sstack-<lens>/` peers) and the
six `agents/sstack-<lens>-attacker.md` files, and a BUGS.md-free copy
of the seeded repo, in a temp workspace
(`python3 evals/acceptance.py prepare` copies all of it into one
isolated dir).

## Verdict

> **Graded 2026-09-25** with the content-match grader (`b05b94b`):
> **all five fixtures PASS**. py and java were re-run fresh on the
> current post-lane-audit text (`13947ce`); ts, js, and cpp PASSes
> stand on their recorded pre-audit text (the delta is fan-out
> carrier mechanics plus the disjunctive-oracle guard — none of it
> exercised by those serial runs). Findings link to goldens by
> trigger content; self-reported `seed_id` is advisory; landed
> regressions are verified on disk; every PASS now replays its
> evidence out of the agent loop.

| Repo | Verdict | Detail |
|---|---|---|
| seeded-py | PASS | ColdPy-5 on current text: 5/5 seeds (py-1/3/4/5/6), 8 confirmed + 4 refuted, 12/12 evidence replay intact, 0 drift, 17 tests green (5 baseline + 12 landed). Agent process exited 1 but every artifact passed objective grade and replay. The `state` seed is covered (ColdPy-5); the `ownership` seed (py-7) has no cold pass: three attempts on post-pairing text (ColdPy6 fabricated evidence, ColdPy7/8 self-wiped `.sstack/` on context reset) all failed before reaching it — see run history. ColdPy-5 remains the standing PASS on py-1/3/4/5/6 |
| seeded-java | PASS | ColdJava-3 on current text: java-1/2/4 content-matched, 5 confirmed red→green, 10 tests green, 7/7 evidence replay intact — the pre-schema-pin gap is closed |
| seeded-ts | PASS | 15 confirmed red→green, 5/5 seeds content-matched, 37/37 tests, 19/19 evidence replay intact (ColdTs-4 on post-consistency text, orchestrator-resumed; prior: ColdTs-3 4/5) |
| seeded-js | PASS | 7 confirmed; 5/5 seeds content-matched, landed regressions, 12/12 evidence files replay intact (ColdJs-2, rerun) |
| seeded-cpp | PASS | 11 confirmed red→green in `tests/shop_test.cpp` (ctest 14/14), cpp-1/2/4 content-matched, 13/13 evidence replay intact (ColdCpp-2, rerun; wave 1 FAILed: named `test_functions.cpp`, landed nothing) |

Wave 1 verdicts stand in the run histories below: they are what the
grader caught, and every failure converted to a PASS on rerun.

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
| ColdPy-2 | current text (`e29af03`+) | isolated workspace | PASS — `.sstack/report.json` (8 findings, py-1/2/3 matched, label contradictions as warnings) + 8 script-emitted evidence JSONs; replay grades all 8 intact |
| ColdPy-R2 (Learn-loop run 2) | current text (`b9803cf`+) | isolated workspace + `.sstack/learn/` from run 1 | PASS — 10 findings, 5/5 seeds content-matched, replay 10/10 intact. Discover ordered attacks by the three learned lines (cited verbatim in `.sstack/map.md`); label contradictions: zero. Agent crashed (exit 1) before emitting artifacts; the orchestrator emitted them from the agent's landed tests + fixes, running each repro against a pristine fixture copy so recorded output is the real buggy behavior. |
| ColdPy-3 (fan-out attempt) | current text (`13947ce`+) | isolated workspace | CANCELLED — dispatched six lens subagents; one attacker stalled past 50 min blocking its parent; host picked read-only `scout` subagents that cannot execute probes. Re-run in serial mode as ColdPy-4 |
| ColdPy-4 | current text (`13947ce`+) | isolated workspace, serial lenses by dispatch override | PASS — 5/5 seeds, 13 confirmed red→green landed in `tests/test_shop.py`, 22 findings script-emitted, replay 22/22 intact, 0 drift. Mid-run report.json transiently named tests before the Test stage wrote them — incremental emission means grade after yield, not during |
| ColdPy-5 | post-state-lens text (7 lenses, shipped emitter) | isolated workspace, serial lenses | PASS — 5/5 seeds content-matched (py-1/3/4/5/6), 8 confirmed + 4 refuted, 12 findings emitted through the shipped `emit_findings.py`, replay 12/12 intact, 0 drift, 17 tests green. Found an unseeded state defect beyond `py-6`: `Cart.__init__` stores the caller's mutable dict by reference, so `track()` writes through to the caller's data. Agent process exited 1; artifacts passed objective grade and replay, so the exit is recorded as a harness observation, not a verdict. Label contradictions (`py-b1!=py-1`, `py-b4!=py-3`, `py-m1!=py-5`, `py-n2!=py-4`, `py-s1!=py-6`) are advisory: grading is content-based |
| ColdPy6 | post-pairing text (`661117b`+) | isolated workspace, fan-out, no dispatch override | FAIL — fabricated evidence: findings enumerated in a hand-written `.sstack/attack_plan.py` before any attack ran; no probes in `.sstack/scratch/` (empty); finding JSONs hand-authored to look emitter-shaped but keyed `command` instead of `repro`, so the emitter rejects them (`invalid finding: missing fields: repro`); the single replay-intact fingerprint covers a `NameError` from the agent's own quoting bug, not the defect. Content-match hit py-1/3/6 but evidence integrity fails, so no PASS. py-7 (ownership) again unrun. Re-run serial with dispatch override as ColdPy-7 |
| ColdPy7 | post-pairing text (`661117b`+) | isolated workspace, serial lenses, dispatch override | CANCELLED — thrashed in a compaction loop: transcript shows `rm -rf .sstack` re-run 10+ times, each pass wiping its own scratch and findings then re-reading the prompt; one real probe (`cart_init_none_boundary.py`) executed and a finding hand-written to match before the next wipe. Same context-outlives-run failure as ColdPy-3's stalled fan-out. A single monolithic task agent cannot hold a 7-lens serial run; the next attempt must stage lenses as separate dispatches |
| ColdPy8 | post-pairing text (`661117b`+) | isolated workspace, staged (scratch-first, emit-second) | CANCELLED — same compaction wipe as ColdPy7 despite explicit never-delete instruction: `rm -rf .sstack` re-run after Stage 1 produced 13 scratch findings; additionally wrote reports at the workspace root (`STAGE1_REPORT.md`, `SSTACK_EXECUTION_REPORT.md`, `sstack_execution_summary.md`) and `/tmp/setup_pyenv.sh`, containment violations. Stage-splitting cannot save a run whose agent wipes its own disk state on context reset. Conclusion across three runs: a single monolithic agent cannot hold a full 7-lens cold run on current context limits; evidence-grade runs need one dispatch per lens (or run-end tooling) — matches ColdPy-3/ColdPy-4/ColdJava-3 history |

## Run history (typescript)

| Run | Skill text | Isolation | Outcome |
|---|---|---|---|
| CleanTs | decontaminated + execution-validity fix | isolated workspace | PASS (pre-audit skill text) |
| RunTs | v0.1.0 + PBT delegation + mutation + run-end checks + steel-man + edge-case vocab | isolated workspace, read-only lock | DID NOT COMPLETE — 40+ min, stuck in Attack, no regressions landed, no findings reported. Fan-out subagents explored the sstack repo, not the temp workspace. Source and tests untouched. |
| ColdTs-2 | current text (`e29af03`+) | isolated workspace | FAIL (zombie) — claimed 3 findings, landed none; fingerprints typed in. Cancelled |
| ColdTs-3 | current text (`b9803cf`+) | isolated workspace | PASS — 7 confirmed red→green, 4/5 seeds matched, report + 7 evidence files script-emitted, replay 7/7 intact, `bun run test` 19/19. ts-4 finding exists but its claimed test name doesn't match the written one |
| ColdTs-4 | current text (`34bf6a6`+) | isolated workspace | PASS (resumed) — 15 confirmed red→green, 5/5 seeds, 37 tests, replay 19/19 intact, 0 drift. Crashed pre-emit (the zombie mode; motivated emit-as-you-verify `34bf6a6`); three orchestrator corrections after: field mapping (slug-in-surface, empty case), pristine-src repros, and the grader's literal "red"/"green" state tokens — the last since undocumented in the skill, now pinned in Workspace |

## Run history (js / java / cpp, current text)

| Run | Fixture | Outcome |
|---|---|---|
| ColdJs | seeded-js | INVALID — finished 3 confirmed + fixes + 4 test files, but hand-typed `report.json` unparseable (unescaped quotes, line 33) and all evidence fingerprints placeholder (`a1b2c3d4...`); replay grades them fabricated |
| ColdJava | seeded-java | PASS — 4 confirmed red→green; java-1/2/4 content-matched; self-labels shifted (advisory only); no evidence JSONs (ran before the schema pin); superseded by ColdJava-3 |
| ColdJava-3 | seeded-java | PASS — java-1/2/4 content-matched (java-3/5 not attacked: four lenses deemed not-applicable with stated reasons), 5 confirmed red→green in `src/test/java/com/sstack/ShopTest.java`, 10 tests green, replay 7/7 intact, 0 drift. First java run to ship evidence JSONs — closes the pre-schema-pin gap; serial lenses by dispatch override after ColdPy-3's fan-out stalled |
| ColdCpp | seeded-cpp | FAIL — genuine attacks (7 confirmed, script-emitted evidence, all fingerprints intact, cases match cpp-1/3/4) but the regression objects name a `test_functions.cpp` that was never written and source was never fixed. First false-claim caught by landed-regression verification |
| ColdCpp-2 | seeded-cpp | PASS — 11 confirmed red→green in `tests/shop_test.cpp` (built by CMake, 14/14 via ctest), 5 source guards in `src/shop.cpp`, cpp-1/2/4 content-matched, 13/13 evidence replay intact |

## Evidence replay (roadmap item 2)

`python3 evals/acceptance.py replay <workspace>` recomputes each
evidence file's fingerprint from its recorded bytes and re-runs its
command with the agent out of the loop.

| Workspace | Integrity | Drift |
|---|---|---|
| seeded-js (ColdJs, first wave) | 2 fabricated (placeholder hex hashes), 1 unparseable | n/a — INVALID run |
| seeded-py (ColdPy-2) | 8/8 intact | 4 drifted: fix landed, re-run shows corrected output |
| seeded-py (ColdPy-R2) | 10/10 intact | 4 drifted, 6 stable |
| seeded-cpp (ColdCpp) | 7/7 intact | 7 drifted — no regression file, no fix landed; scratch-binary behavior, not proof |
| seeded-js (ColdJs-2, rerun) | 12/12 intact | 0 drifted — repros re-run against a pristine source copy, so recorded output still reproduces after the fix |
| seeded-ts (ColdTs-3, rerun) | 7/7 intact | 7 drifted: fixes landed, repros show corrected output |
| seeded-ts (ColdTs-4, resumed) | 19/19 intact | 0 drifted — repros ran against a pristine source copy, so recorded output still reproduces after the fix |
| seeded-cpp (ColdCpp-2, rerun) | 13/13 intact | 11 drifted (fix landed), 2 stable hardening refutes |
| seeded-py (ColdPy-4, current text) | 22/22 intact | 0 drifted — repros ran against a pristine source copy |
| seeded-java (ColdJava-3, current text) | 7/7 intact | 0 drifted — first java run with evidence JSONs |
| seeded-py (ColdPy-5, current text) | 12/12 intact | 0 drifted — repros ran against a pristine source copy |

Drift after a landed fix is expected and informational; a fabricated
fingerprint is the disqualifier. Every PASS — all five — now carries
replayed evidence.

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

## seeded-py: seed mapping (ColdPy-5, current text)

| Seed | Found as | Regression |
|---|---|---|
| py-1 page=0 → `[]` | `py-b1` boundaries, `paginate` | `test_paginate_rejects_page_below_one` |
| py-2 add_item qty -1 → total -1 | `py-b4` boundaries, `line_total` | `test_line_total_rejects_discount_out_of_range` |
| py-3 line_total({}) KeyError | `py-n1` missing, `line_total` | `test_line_total_requires_unit_price_and_qty` |
| py-4 discount=None TypeError | `py-n2` missing, `line_total` | `test_line_total_null_discount_defaults_to_zero` |
| py-5 unit_price="abc" raw ValueError | `py-m1` malformed, `line_total` | `test_line_total_non_numeric_unit_price` |
| py-6 stale cached `Cart.count` | `py-s1` state, `Cart.count` | `test_cart_count_reflects_tracked_items` |
| py-7 unscoped `search_orders` | not found | — |

8 confirmed findings, 8 red→green regressions landed, 4 refuted
hardening tests (including two refutes that prove the shipped lenses
do not manufacture defects: `paginate` beyond the last page and
`total_items` on an empty cart are both correct).

`py-7` is the gap. The `ownership` lens has had a targeted carrier run
that found the planted collection leak, but the full cold pass that
produced this mapping did not reach it, so `py-7` is unrun end to end.
`py-s2` is not a seed: the agent found an unseeded state defect,
`Cart.__init__` storing the caller's dict by reference so `track()`
writes through, which no golden covers.

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
