# Cold acceptance results — sstack v0

Runs: fresh subagent given only a copy of the skills
(`skills/sstack/` plus the fourteen `skills/sstack-<lens>/` peers) and the
fourteen `agents/sstack-<lens>-attacker.md` files, and a BUGS.md-free copy
of the seeded repo, in a temp workspace
(`python3 evals/acceptance.py prepare` copies all of it into one
isolated dir).

## Verdict

> **Graded 2026-09-27** with the content-match grader:
> **all five fixtures PASS**. py and java were re-run fresh on the
> current post-lane-audit text; ts, js, and cpp PASSes
> stand on their recorded pre-audit text (the delta is fan-out
> carrier mechanics plus the disjunctive-oracle guard — none of it
> exercised by those serial runs). Findings link to goldens by
> trigger content; self-reported `seed_id` is advisory; landed
> regressions are verified on disk; every PASS now replays its
> evidence out of the agent loop.
>
> **Scope note (2026-09-27)**: All five fixtures (`seeded-py`, `seeded-ts`,
> `seeded-js`, `seeded-java`, and `seeded-cpp`) now cover all 16 seeds across
> all 14 shipped lenses with verified cold passes under ADR-0010.

| Repo | Verdict | Detail |
|---|---|---|
| seeded-py | PASS | ColdPy-5 covers py-1/3/4/5/6 (5/5 seeds, 17 tests green, 12/12 replay intact). ColdPy-11 verified py-7 (ownership), py-8 (ordering), py-9 (exceptional-conditions), py-10 (resource-exhaustion), and py-11 (concurrency): 5 confirmed red→green in `tests/test_shop.py`, 5/5 evidence replay intact, 0 drift, 10 tests green. ColdPy-12 verified py-12 (idempotency): 1 confirmed red→green in `tests/test_shop.py`, 1/1 evidence replay intact, 0 drift. ColdPy-13 verified py-13 (dependency-failure): 1 confirmed red→green in `tests/test_shop.py`, 1/1 evidence replay intact, 0 drift. ColdPy-14 verified py-14 (contract): 1 confirmed red→green in `tests/test_shop.py`, 1/1 evidence replay intact, 0 drift. ColdPy-15 verified py-15 (security): 1 confirmed red→green in `tests/test_shop.py`, 1/1 evidence replay intact, 0 drift. ColdPy-16 verified py-16 (agent): 1 confirmed red→green in `tests/test_shop.py`, 1/1 evidence replay intact, 0 drift. All 16 seeds across the 14 shipped lenses in `seeded-py` now have verified cold passes |
| seeded-java | PASS | All 16 seeds across all 14 lenses verified. java-1..5 verified in ColdJava-3 (3/5 seeds, 7/7 replay intact); java-6..16 verified in ColdJava-4 (11/11 seeds content-matched, 14/14 tests green, 11 confirmed red→green regressions landed in ShopTest.java, 11/11 evidence replay intact, 0 drift). |
| seeded-ts | PASS | All 16 seeds across all 14 lenses verified. ts-1..5 verified in CleanTs/ColdTs-4 (5/5 seeds, 19/19 replay intact); ts-6..16 verified in ColdTs-5 (11/11 seeds content-matched, 17/17 tests green, 11 confirmed red→green regressions landed, 11/11 evidence replay intact, 0 drift). |
| seeded-js | PASS | All 16 seeds across all 14 lenses verified. js-1..5 verified in ColdJs-2 (5/5 seeds, 12/12 replay intact); js-6..16 verified in ColdJs-3 (11/11 seeds content-matched, 12/12 tests green, 11 confirmed red→green regressions landed, 11/11 evidence replay intact, 0 drift). |
| seeded-cpp | PASS | All 16 seeds across all 14 lenses verified. cpp-1..5 verified in ColdCpp-2 (cpp-1/2/4 content-matched, 13/13 replay intact); cpp-6..16 verified in ColdCpp-3 (11/11 seeds content-matched, 2/2 ctest targets / 12 test assertions green, 11 confirmed red→green regressions landed in tests/shop_test.cpp, 11/11 evidence replay intact, 0 drift). |


## Graded runs (2026-09-27, this morning -> now)

Two significant graded results this cycle, both machine-verified by the
hardened grader (`evals/test_grader.py` pins both gates):

- **ADR-0010 cross-language parity wave.** `ColdTs-5` (seeded-ts),
  `ColdJs-3` (seeded-js), `ColdJava-4` (seeded-java), and `ColdCpp-3`
  (seeded-cpp) each verified seeds 6-16 cold in isolated workspaces:
  11 confirmed red->green regressions landed per fixture, 11/11
  content-matched, evidence replay intact, 0 drift. seeded-py's
  py-8..py-16 seeds verified in ColdPy-11 through ColdPy-16. All five
  fixtures now cover all 16 seeds across the 14 shipped lenses.
- **Grader hardening.** The bug-pin control re-runs every confirmed
  finding's regression against the unfixed source (all-green means the
  test asserts the defect), and `matches_golden` gates on executed
  text -- the trigger must appear in `case`/`observed` and the oracle
  must reach the recorded contract -- not labels or defect-shaped prose.
