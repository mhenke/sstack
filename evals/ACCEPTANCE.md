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
> evidence out of the agent loop. All five fixtures show verified cold
> passes on 16 of 19 named seeds; `*-17`/`*-18`/`*-19` carry goldens
> with cold-run evidence pending.
>
> **Scope note (2026-09-27)**: All five fixtures (`seeded-py`, `seeded-ts`,
> `seeded-js`, `seeded-java`, and `seeded-cpp`) cover 16 evidenced seeds
> (of 19 seeded) across all 14 shipped lenses with graded cold runs under ADR-0010.
>
> **Staleness note (2026-09-27)**: Recorded cold-run passes predate the
> addition of the inline sensitivity check (Stage 5) and Run-end check #5;
> existing PASS numbers reflect exact pre-check skill text.
> **Staleness note (2026-09-27, later)**: Recorded cold-run passes also
> predate the agent-lens rubric revision (three oracles restated as
> code-observable assertions on the orchestrator's own outputs) and the
> `agent` index row now naming all five owned failure classes. The
> agent-lens cold evidence (py-16/ts-16/js-16/java-16/cpp-16) remains
> valid: those seeds are dispatch-crash defects, unchanged by the
> revision. Other lenses are untouched.
> **Staleness note (2026-09-28)**: Seeds `*-17` (boundaries/precision),
> `*-18` (dependency-failure/timeout), and `*-19` (security/injection)
> added across all five fixtures. Goldens present; cold-run evidence
> pending. Existing 16-seed PASS verdicts remain valid — new seeds are
> additive.
> **Staleness note (2026-09-28, later)**: SKILL.md lens index gained the
> missing `idempotency` row (a duplicate `agent` row was removed) and was
> pruned for headroom (527 lines). Recorded cold-run PASSes predate this
> text. The idempotency cold evidence (py-12, ts-12, js-12, java-12,
> cpp-12) remains valid: Discover loads lens skills directly from the
> skills directories, so those runs reached the rubric despite the
> missing index row.
> **Staleness note (2026-09-28, latest)**: the security and ownership
> rubric passages directing the agent to boot the target's server and
> probe with `curl` (added earlier on 2026-09-28 per ADR-0015) have
> been removed; runtime behavior is out of scope per the amended
> ADR-0015. Recorded PASSes predate both texts; neither is exercised
> by any seeded fixture (none exposes an HTTP server), so fixture
> outcomes are unaffected.
> **Staleness note (2026-09-28, harden mode)**: SKILL.md gained the
> `harden` routing bullet, the findings-report wording amendment, and
> the workspace-list `.sstack/harden/` line;
> `skills/sstack/references/harden.md` shipped. No stage text
> changed, so recorded PASSes stand. Cold harden-mode evidence:
>
> **ColdHarden-1 (seeded-py, buggy target, 2026-09-28): PASS as
> graded.** Cold harden run in an isolated workspace: 69 findings —
> 20 confirmed red→green (8 seeds content-matched: py-1, py-2, py-3,
> py-6, py-7, py-11, py-14, py-15) and 49 refuted gap-fills —
> `grade` pass=true, `replay` exit 0 (0 drift). Doubles as attack
> evidence for 8 seeds via the flip path.
>
> **ColdHarden-2 negative control (seeded-py, canonically fixed by
> hand): FAILED direct judgment.** The cold agent emitted no
> report.json and no findings (hardened §8 after this run), named its
> snapshot `report.md` instead of the `<date>-<target>-<seq>` format
> (§4 tightened after this run), and made three source edits — one of
> which (`fetch_tracking_status` rewritten to call the tracker as a
> callback) **broke the py-18 canonical fix**: the worker-thread
> TypeError is swallowed, no TimeoutError raises, and the agent's own
> 21 green tests hid the regression while it claimed all oracles
> satisfied. Failure kept per ADR-0003; product fixes it forced:
> harden.md §8 now requires emitter output per finding (no
> report.json = invalid run), §4 locks the snapshot filename, Safety
> requires every source edit to trace to a confirmed finding.
> ColdHarden-1 predates those text fixes; **control re-run
> (ColdHarden-4, 2026-09-28, contained temp workspace): PARTIAL.**
> Closed: emitter used, `report.json` present, snapshot named
> `2026-09-28-coldharden3-01.md` per §4, artifacts contained in the
> workspace, UNATTENDED scope banner printed, report structure per §4,
> all 19 canonical fixes intact (py-18 oracle verified live), 49 tests
> green. The run caught one genuine gap the canonical fixes had missed
> (`create_checkout` accepted `qty <= 0`) and flipped it properly.
> Remaining defects, recorded per ADR-0003: (a) 5 of 6 findings are
> marked `confirmed` on surfaces the unmodified canonical fixture
> already handles (paginate page-zero, add_item qty, line_total
> missing key, get_order missing, receipt traversal) — green
> gap-fills recorded as flips, violating §7's verdict split; (b) the
> `add_item` finding's surface label names the wrong function (its fix
> landed in `create_checkout`). An earlier draft of this note also
> claimed `report.json` held 3 findings against 6 evidence files; that
> was a mid-run read taken before the final emit — the rebuilt report
> carries all 6, and the emitter is correct. Product fix forced: 
> run-end check 7 ("every confirmed regression is red against pristine
> source") added to SKILL.md; it mechanically converts all five false
> confirmations. A control run over check-7 text is the next evidence
> run. Staleness: §8's count line reads "live failures found and
> fixed" (was "bugs") per the glossary's finding entry — prose only;
> all recorded harden evidence predates the wording. Recorded PASSes
> also predate the stage-text naming of optional lifecycle skills
> (a2afe0c, 2026-09-29): wording-level, and no fixture workspace
> carries those skills, so fixture outcomes are unaffected. Attack
> step-3 probe-validity wording (2026-09-29, post-0.3.0) likewise
> postdates all recorded evidence; guidance-level.
> **Staleness note (2026-09-29, Discover rewrite)**: the Discover
> stage text was rewritten — broad targets resolve to
> language-convention folders (or the user names a narrower TARGET),
> inventory spans every surface kind across all supported languages,
> and lens select/skip is per surface × lens with recorded evidence
> (run-end check 8 added). Recorded cold-run PASSes predate this
> text; Discover wording shapes every cold run's map, so the numbers
> stand on the pre-rewrite text pending a cold re-run.
> **Staleness note (2026-09-29, oracle rules)**: rule 2 now derives
> oracles from business invariants with a single-outcome shape, map
> rows carry an impact class, Attack orders surfaces by impact, and
> the chat report ends with coverage counts (untested high-impact
> surfaces = partial coverage). Recorded cold-run PASSes predate this
> text; the staleness already flagged for the Discover rewrite now
> covers these edits and every same-day stage-text change after them.
> **Staleness note (2026-09-29, 17–19 evidence batch)**: a five-fixture
> cold batch (ColdEv-Py/Ts/Js/Java/Cpp, prepared workspaces, standard
> `/sstack` prompts) attempted `*-17`/`*-18`/`*-19` evidence. **All five
> runs failed to produce valid evidence; the pending state stands.**
> Failure classes, kept per ADR-0003: Java emitted properly but graded
> FAIL (2 findings, both bug-pinned — regressions green against
> pristine source);
> Py delegated to a nested subagent that worked in a stale leftover
> workspace (`o811cha9`), breached containment (cwd = sstack repo
> root, stray `temp_finding.json` written there — removed; imported
> the repo's emitter instead of the workspace copy), and never
> emitted; the outer agent hand-copied the py-17 fix into the
> prepared workspace;
> Ts wrote 19 hand-authored finding files with invalid shapes (one is
> an aggregate run-state blob) and no `report.json`; Js hand-authored
> 6 findings with typed fingerprints (fabricated per ADR-0006) and no
> `report.json`; Cpp never emitted at all — it hunted ~7 min for a
> literal `/sstack` executable (v0 ships none), ran the emitter once
> with no stdin (crash, no writes), and fixed the source anyway.
> Post-mortem (same-day transcript review): no run read BUGS.md,
> goldens, or any file outside its workspace — evidence validity is
> intact; the Py child's breach was write-side, not answer-key. The
> stale-workspace pool in `.sstack/scratch/` (18 leftover prepare
> outputs) is what the child landed in; purged to today's five. Runs
> take ~30 min because the dispatch model (`omniroute/explorer`)
> averages 60–150 s per turn across 40–110 tool calls; Py's apparent
> hang was a 25 m 47 s blocking `wait` on its child, not a deadlock.
> Root cause (all five): the dispatch prompt's phrase "`/sstack` on
> the src package" reads as an executable to a hostless cold agent —
> all five hunted for a `/sstack` binary (v0 ships none by scope
> lock) and improvised their own runner scripts instead of executing
> the skill's stage text. Fix candidates: (a) harness dispatch prompt
> says "run the full sstack lifecycle on <target>; the skill text is
> the command, there is no `/sstack` executable" (evals lane, no
> product change); (b) emitter prints a usage line with a full
> heredoc example when stdin is empty instead of a bare JSONDecodeError
> (product lane, `scripts/` change + emitter test); (c) `prepare`
> purges stale sibling workspaces so a wandering nested agent cannot
> land in one (evals lane).
> **Validation (ColdSoloPy, 2026-09-29, same day)**: fixes (a)+(b)
> landed — dispatch reworded ("no `/sstack` executable; the skill text
> is the command"), emitter prints a stdin example on empty input
> (test_emitter 14 passed) — then one solo cold run on seeded-py:
> **contract mechanics fixed** (11 m 51 s vs 28–37 m, no runner
> invented, emitted through the script, `report.json` present, grade
> ran instead of refusing), but coverage collapsed: 14 findings all on
> one surface (cart negative-qty, ~12 slug-drifted re-emits of one
> case), one lens, 0 seeds content-matched, 2 workspace tests red.
> 17–19 remains pending. New candidates: (d) emitter dedup guard on
> (surface, case) so re-emits overwrite instead of accumulating;
> (e) coverage abandonment — the run stops after the first lens
> despite the coverage contract. Variance run ColdSoloPy2 dispatched
> to separate one-off from systemic.
> **Variance run (ColdSoloPy2, 2026-09-29)**: coverage was variance —
> 22 surfaces across all four modules, security + exceptional lenses,
> py-18/py-19 target areas named — but the Emit contract failed
> again: all 3 findings hand-written (missing `seed_id`, `regression`,
> `emitted_at`), grader refuses, 0 seeds. **Backend routing discovery
> (decisive)**: `omniroute/explorer` is a routing chain — `model_usage`
> events show the recorded PASSes ran on Qwen3.8-Flash / Qwen3.7-Flash
> / explorer, while all of today's failures ran on glm-5.3 /
> glm-5.3-flash. "Same model" was a label, not a fact. Today's
> capability ceiling (breadth XOR emit discipline) is the glm routing,
> not the skill text — though the rewritten text still carries zero
> cold-run evidence either way. Next evidence attempt: pin dispatch to
> a backend that has produced valid evidence (Qwen Flash), one solo
> run, before any per-lens fan-out machinery.
> **Staleness note (2026-09-29, evidence hygiene + stage text)**:
> both emitters now normalize the absolute workspace path out of the
> recorded command/stdout/stderr at capture — fingerprints become
> machine-independent — and record no `emitted_at`/`duration_ms`
> (nothing consumed them; they only broke run-over-run diffs). The
> Node emitter's `.py` probe preflight now calls `python3 -m
> py_compile` (it ran `node -m py_compile`, which rejects every
> python probe). SKILL.md Workspace states the artifact rule (no
> absolute paths, no timestamps, observed output quoted once),
> Verify emits the moment a verdict is known, Safety keeps evidence
> flowing on a broken suite, run-end check 9 gives prior findings a
> disposition, Discover narrows an untestable-looking target only by
> asking, and `scratch/` survives until the run-end checks pass.
> test_emitter 16 passed, test-all green; every recorded cold-run
> number above predates this text. Old evidence still grades and
> replays (fingerprints were computed over the bytes as recorded).

| fixture | verdict | evidence |
|---|---|---|
| seeded-py | PASS | ColdPy-5 covers py-1/3/4/5/6 (5/5 seeds, 17 tests green, 12/12 replay intact). ColdPy-11 verified py-7 (ownership), py-8 (ordering), py-9 (exceptional-conditions), py-10 (resource-exhaustion), and py-11 (concurrency): 5 confirmed red→green in `tests/test_shop.py`, 5/5 evidence replay intact, 0 drift, 10 tests green. ColdPy-12 verified py-12 (idempotency): 1 confirmed red→green in `tests/test_shop.py`, 1/1 evidence replay intact, 0 drift. ColdPy-13 verified py-13 (dependency-failure): 1 confirmed red→green in `tests/test_shop.py`, 1/1 evidence replay intact, 0 drift. ColdPy-14 verified py-14 (contract): 1 confirmed red→green in `tests/test_shop.py`, 1/1 evidence replay intact, 0 drift. ColdPy-15 verified py-15 (security): 1 confirmed red→green in `tests/test_shop.py`, 1/1 evidence replay intact, 0 drift. ColdPy-16 verified py-16 (agent): 1 confirmed red→green in `tests/test_shop.py`, 1/1 evidence replay intact, 0 drift. ColdPy-18 (2026-09-27, fresh full-lifecycle rerun after SSOT deduplication): 16 confirmed red→green, 16/16 evidence replay intact, 21 tests green, content-matched all 16 seeds including py-2. Full 16/16 named coverage achieved; seeds 17–19 have no cold-run evidence. |
| seeded-java | PASS | 16 of 19 seeds across all 14 lenses verified (seeds 17–19, added by f279baf, have no cold-run evidence). java-1..5 verified in ColdJava-3 (3/5 seeds, 7/7 replay intact); java-6..16 verified in ColdJava-4 (11/11 seeds content-matched, 14/14 tests green, 11 confirmed red→green regressions landed in ShopTest.java, 11/11 evidence replay intact, 0 drift). |
| seeded-ts | PASS | 16 of 19 seeds across all 14 lenses verified (seeds 17–19, added by f279baf, have no cold-run evidence). ts-1..5 verified in CleanTs/ColdTs-4 (5/5 seeds, 19/19 replay intact); ts-6..16 verified in ColdTs-5 (11/11 seeds content-matched, 17/17 tests green, 11 confirmed red→green regressions landed, 11/11 evidence replay intact, 0 drift). |
| seeded-js | PASS | 16 of 19 seeds across all 14 lenses verified (seeds 17–19, added by f279baf, have no cold-run evidence). js-1..5 verified in ColdJs-2 (5/5 seeds, 12/12 replay intact); js-6..16 verified in ColdJs-3 (11/11 seeds content-matched, 12/12 tests green, 11 confirmed red→green regressions landed, 11/11 evidence replay intact, 0 drift). |
| seeded-cpp | PASS | 16 of 19 seeds across all 14 lenses verified (seeds 17–19, added by f279baf, have no cold-run evidence). cpp-1..5 verified in ColdCpp-2 (cpp-1/2/4 content-matched, 13/13 replay intact); cpp-6..16 verified in ColdCpp-3 (11/11 seeds content-matched, 2/2 ctest targets / 12 test assertions green, 11 confirmed red→green regressions landed in tests/shop_test.cpp, 11/11 evidence replay intact, 0 drift). |


## Graded runs (2026-09-27, this morning -> now)

Two significant graded results this cycle, both machine-verified by the
hardened grader (`evals/test_grader.py` pins both gates):

- **ADR-0010 cross-language parity wave.** `ColdTs-5` (seeded-ts),
  `ColdJs-3` (seeded-js), `ColdJava-4` (seeded-java), and `ColdCpp-3`
  (seeded-cpp) each verified seeds 6-16 cold in isolated workspaces:
  11 confirmed red->green regressions landed per fixture, 11/11
  content-matched, evidence replay intact, 0 drift. seeded-py's
  py-8..py-16 seeds verified in ColdPy-11 through ColdPy-16. All five
  fixtures cover 16 seeds in goldens and graded cold runs.
- **ColdPy-18 (seeded-py, 2026-09-27).** Fresh full-lifecycle rerun after
  SSOT deduplication of attacker prompts: 16 confirmed red→green
  regressions landed, 16/16 evidence replay intact, 21 tests green,
  content-matched all 16 seeds (including py-2). Closes the remaining py-2
  gap, achieving 16/16 named coverage on seeded-py.
- **ColdPy-19 (seeded-py, 2026-09-28).** Cold run against the current
  skill text (post-ADR-0015 strip, rubric polish, Discover-stage
  no-socket rule). The subagent produced **29 confirmed findings across
  all 14 lenses** — machine-executed records with fingerprints, exit
  codes, and captured output — then hung in the Fix stage and was
  killed; the orchestrator completed Fix (canonical `paginate` and
  `Cart.count` fixes, one wrong-oracle scratch test removed), reaching
  **18/18 tests green**. Grader: PASS under the pre-2026-09-28 grader
  (bug-pin control held — 4 regressions red against pristine source —
  and `py-5`/`py-9` content-matched with landed regressions);
  **FAIL under the hardened grader** (below), which now gates on
  evidence integrity.
  **Caveats, recorded deliberately:** (a) only 7 of 29 findings could
  be paired unambiguously to a real landed regression; the other 22
  named regression files/tests that do not exist, so they graded as
  unlanded — the run's finding count exceeds its regression count and
  no mapping was guessed to close the gap; (b) `replay` reports
  **11 of 29 findings `fabricated`** (recorded fingerprint ≠ recomputed
  — the hung run's evidence files were edited after emit; the emitter
  computes fingerprints itself, so a mismatch means hand-tampering)
  and 12 with expected post-fix `drift`. This run is a **partial
  re-evidence**: it proves the current text produces confirmed findings
  across all 14 lenses, but it does **not** supersede the 16-seed
  ColdPy-11..18 evidence, which stands. The pre-2026-09-28 staleness
  notes above remain in force.

- **Grader hardening.** The bug-pin control re-runs every confirmed
  finding's regression against the unfixed source (all-green means the
  test asserts the defect), and `matches_golden` gates on executed
  text -- the trigger must appear in `case`/`observed` and the oracle
  must reach the recorded contract -- not labels or defect-shaped prose.
