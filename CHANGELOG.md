# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.5.1 - 2026-10-04

### Added
- **5/5 Multi-language cold evaluation baselines (`evals/baseline-cold-eval-*.json`)** —
  recorded verified cold run passes across all five supported languages (`seeded-py`,
  `seeded-ts`, `seeded-js`, `seeded-cpp`, and `seeded-java`), covering seeds `*-17`
  (boundaries/precision), `*-18` (dependency-failure/timeout), and `*-19`
  (security/injection) with landed red→green regressions and intact evidence replays.
- **Bounded concurrency and serial execution controls (`acceptance.py eval --serial`, `--concurrency <n>`)** —
  instructs cold eval agents to evaluate lenses serially or with bounded concurrency to
  prevent upstream LLM rate-limit bursts (HTTP 429) and classfile write collisions in
  shared build directories.
- **Emitter contract tests (`evals/test_emitter.py`)** —
  added unit test coverage verifying schema tolerance on top-level `command`, upgrade
  requests, and shorthand fixture alias resolution.

### Fixed
- **Emitter schema & fixture alias normalization (`emit_findings.py`, `emit_findings.js`)** —
  normalized finding ingestion to accept both `command` and `repro` (and nested
  `repro.command`), and canonicalized short fixture names (`py`, `ts`, `js`, `java`, `cpp`)
  to `seeded-<name>` with `.sstack-host-repo` fallback.
- **Seeded Java CLI repro dispatcher (`evals/seeded-java/src/main/java/com/sstack/Orders.java`)** —
  added CLI switch cases in `Orders.main` for seeds 17–19 (`applycoupon-precision-loss`,
  `fetchtrackingstatus-timeout`, `searchordernotes-sql-injection`), allowing CLI
  reproduction of defect behavior without altering frozen defect implementations.
- **Upstream LLM safety filter false-positives (`skills/sstack-security/SKILL.md`)** —
  neutralized destructive examples (`daily; rm -rf /` → `daily; id`, `DROP TABLE` → schema probe)
  using `writing-for-agents` principles to prevent commercial LLM safety moderation refusal
  loops while preserving semantic coverage and avoiding answer-key leaks.
- **Grader executed fields for content matching (`evals/graders/seeded_acceptance.py`)** —
  added `repro` to `EXECUTED_FIELDS`, allowing the content matcher to recognize trigger
  function calls in the executed repro command line.
- **Site formatting & frozen-copy sync** —
  fixed 320px viewport overflows, cleaned roman accent words, and synced frozen examples.

### Changed
- **Root-cause principles codified**:
  - `evals/README.md`: documented root cause of Windows VS Code sandbox launch failures
    (`&` call operator syntax error in Git Bash/MINGW64 terminals) and mandated matching
    terminal shell profile without disabling sandboxing.
  - `skills/sstack/SKILL.md`: reinforced that prior terminal commands are never scope
    authority; IDE-only or non-code diffs require an explicit target query before starting an audit.
  - `docs/ETHOS.md` & `skills/sstack/SKILL.md`: codified that reproducing a failed assertion
    proves runtime behavior, not contract or exploit paths; oracles must be grounded in
    documented caller invariants and reachability assessed separately.
  - Maintained strict line count ceiling in `skills/sstack/SKILL.md` (537 lines ≤ 540).

## 0.5.0 - 2026-10-04

### Added
- **`/sstack triage <target>` pre-lifecycle subcommand (`references/triage.md`)** —
  churn-ranked surface heat before a full Discover. Ranks target surfaces by git
  touch frequency, `learn/` adjacency, and impact class; performs a friction walk;
  writes snapshot to `.sstack/triage/`. Discover consumes newest snapshot to prioritize
  hot surfaces without shrinking the whole-target map (ADR-0016, ADR-0018, ADR-0020).
- **Parallel exploration and deterministic AST caller tracing (`references/discover.md`)** —
  on-demand reference for multi-surface targets structuring Discover into four roles
  (Gateways/Auth, Models/State, APIs/Parsers, External Boundaries) with local stdlib
  AST caller tracing (dynamic args vs. constant-only callers vs. shallow helper traps)
  without vector stores.
- **Automated model evaluation runner (`evals/acceptance.py eval`)** —
  automates workspace preparation, cold agent invocation with timeouts, grading,
  and replay verification, recording baseline tokens (`evals/baseline-<model>.json`).
- **Explicit `--upgrade` flag on emitters (`emit_findings.py`, `emit_findings.js`)** —
  allows running the request upgrade pass without relying on stdin piping. Non-blocking
  `select` check on non-TTY stdin prevents EOF hangs on bare invocations.
- **`emit --report` summary rendering** —
  renders formatted run summary directly from `report.json`.

### Fixed
- Emitter stdin no longer hangs on non-TTY EOF via non-blocking select check.
- Cold-run workspaces isolated outside the repository tree (`/tmp/sstack-cold/`).
- Malformed fingerprints treated as requests rather than valid evidence.
- Replay path normalization across host and isolated workspaces.
- Report view strictly derived from verified evidence files, never authoritative state.

### Changed
- **Architectural reset**: hard reset back to commit 5410309, discarding experimental
  anti-cheat/DRM gates (run nonces, exit-4 traps, report recitation) to return to
  first principles: sstack is a negative-testing skill pack, not an anti-tamper harness.
- **Scope authority & target resolution**: bare `/sstack` resolves scope strictly via
  working tree code diff (`git diff --stat`). Terminal command history is explicitly
  banned from defining scope. Non-code diffs trigger a mandatory user query.
- Banned creating `sstack` CLI wrappers or shell scripts in target workspaces (scope lock).
- Clarified `regression` anatomy in `skills/sstack/SKILL.md`: `file` must point to a test
  suite file under `tests/` (never source code under test) and `test` to its def/method name.
- Emphasized explicit execution of the emitter via command tools so `.sstack/report.json`
  is generated on disk rather than hallucinated in chat.
- Clarified that business invariants and documented domain contracts are valid oracle
  sources in Verify, distinguishing them from unstated preferences; constant-only callers
  demonstrate no input path.
- Purged heavy AST reachability machinery from ROADMAP, preserving zero-runtime simplicity.
- Graded cold eval on `seeded-py` PASS (15 confirmed findings, 15 red→green suite tests, 0 failures, 17/17 replay integrity intact).

## 0.4.0 - 2026-10-02

### Added
- **Emitter upgrade pass (ADR-0022)** — empty stdin now upgrades
  pending requests: the agent's emit act is writing
  `findings/<slug>.json` with `repro` as the exact command run (a
  plain string), and the emitter executes every request itself,
  fingerprints it, and rebuilds `report.json` from evidence only.
  A request without a command stays pending — the machine never
  invents it. Field evidence: across five wording regimes cold
  agents wrote finding files 18/18 times and invoked the emitter
  0/0 times, fabricating report and test results that replay
  exposed; the agent's emit act is now the write every backend
  performs, and the last mile is always machine execution. The
  empty-stdin usage error is retired.
- The upgrade pass accepts a request that nests the command under
  `repro.command` (the evidence-view shape cold agents copy) and
  identifies evidence by the `fingerprint` field rather than
  `command`, so transcribed output on a nested request is discarded,
  never trusted. ColdRequestMode (2026-09-30, kimi-code/k3) wrote 26
  of 27 requests as plain strings and one nested; both now execute.
- Emitters accept `--finding <file>`: the finding JSON may be written
  to a file and passed by path, with stdin piping still working.
  Field evidence across nine cold runs: agents reliably write the
  finding file and reliably skip the heredoc-pipe invocation, on every
  backend and both text generations — the pipe was the one step no
  model survived. The emitter still executes the repro and computes
  the fingerprint itself, so machine execution remains the contract
  (ADR-0006 unchanged).

### Changed

- **Repro execution is bounded at 120 seconds** (ADR-0022,
  `SSTACK_REPRO_TIMEOUT` overrides, minimum 1): a hung repro is
  killed and recorded as exit 124 with the kill noted in stderr —
  evidence about the repro's reliability, not an emitter hang;
  partial output on a kill is discarded. A TTY stdin counts as
  empty, so the upgrade pass is the defined noninteractive fallback
  instead of blocking forever (VS Code StringUtil field failure).
  The Python upgrade pass preflights referenced scratch probes,
  matching the Node emitter — a probe that does not compile is
  infrastructure failure: pending, not evidence.
- **ADR-0023** records the read-window placement rule: binding rules
  (emit contract, dispatch fallback, routing execution model) live
  inside the first ~200 lines of SKILL.md, pinned by a rerunnable
  contract test. Evidence: four wording regimes edited the skill
  correctly and produced zero emitter invocations because the
  contract sat past a cold backend's ~16KB read truncation.

### Fixed

- Emitters print the full invocation with a heredoc example when
  invoked with no finding on stdin (exit 2, both languages), instead
  of a bare JSON parse error. Field report: a cold agent hit the bare
  error, could not tell what to pipe, and abandoned the run's evidence
  step.
- The ownership lens's collection-leak section gains four probes —
  unscoped embeds on scoped rows, suggestion/autocomplete match
  lists, aggregates over an unscoped population, and snippet/highlight
  text — with matching failure-class rows. Motivated by the
  check-search leak scenario (search by a non-key attribute returning
  all subjects' records), which the section already covered; these
  broaden sibling leak shapes. Grounding research:
  `docs/research/bola-tenant-isolation-negative-testing.md`. Cold
  validation pending.

## 0.3.1 - 2026-09-29

### Fixed

- Discover resolves a broad target to its language-convention folders
  (or asks for a narrower TARGET), inventories every surface kind
  across all supported languages — services, DAOs, parsers,
  validators, loops, indexers — and selects or skips per surface ×
  lens with recorded evidence: a lens is skipped only when every
  mapped surface is ruled out. Run-end check 8 invalidates a report
  produced while a mapped surface carries no executed cases. Field
  report: lenses were marked checked-N/A from a single file slice
  instead of being evaluated across all repository surfaces.
- Attack step 3: a crashed scratch probe is a broken probe, not a
  finding. Probes must import and run before their output counts;
  oversized target files are read in ranges and never probed from a
  truncated read; a crashed probe is repaired (split read or
  hand-written against signatures actually read) and re-run before
  recording. Reported from the field: a generated `probe.py` built
  from a truncated source read crashed and was recorded as a finding.
- The emitters enforce it mechanically: before recording, any
  `.sstack/scratch` `.py`/`.js` file referenced by the repro is
  compiled (`py_compile` / `node --check`); a probe that does not
  compile refuses emission (exit 3) and writes nothing. Python probes
  also get a documented import bootstrap so they resolve from any
  working directory.
- Oracles are derived from the surface's business invariant, not from
  what is cheapest to execute (field report: oracle selection bias
  favored easy exceptions over high-impact failures). Rule 2 gains a
  single-outcome oracle shape — given [adverse input], the system
  must [one outcome] and must not [critical side effect]. Map rows
  carry an impact class (privilege boundary, sensitive-data mutation,
  integrity/partial-write, availability, presentation); Attack orders
  surfaces by it. The chat report ends with coverage counts —
  mapped, executed, refuted, confirmed, inconclusive, not run — and a
  run with untested high-impact surfaces is reported as partial
  coverage, never clean. Tests must prove returned state and side
  effects, not merely the absence of a throw. Oracle and test wording
  stays language-neutral across Python, TS/JS, Java, and C++ —
  exception type, rejected promise, error code, or typed result.
- Discover treats a prior run's `map.md` as a head start: rows are
  reused after re-verification against current code, since landed
  fixes invalidate contracts. Probes stay per-run — `scratch/` is
  deleted at run end because its keepers land as suite tests and a
  stale probe against fixed code reads as a false verdict.
- A test framework present but broken is the no-framework case: ask
  before repairing it (configs stay read-only without approval). A
  pre-existing red suite is recorded as baseline and exempted from
  the pass gate — reported, never silently repaired or ignored.
- Target resolution is non-discretionary: a resolved target is mapped
  whole; testability filters surfaces, never target size. Field
  report: a cold run on an Angular repo framed the job as choosing
  the "smallest valid target" — the no-socket test's validity
  vocabulary plus the narrowing rule licensed scope-shrinking. Only
  ambiguity across buildable modules goes back to the user. Run-end
  check 8 follows: each mapped surface ends attacked or explicitly
  not-run, so a whole-target map may span runs without faking
  completeness.
- Recorded evidence is portable and diff-stable: both emitters
  rewrite the absolute workspace path to `.` at capture (command,
  stdout, stderr — the fingerprint is computed over the normalized
  bytes, so identical defects fingerprint identically on any
  machine) and record no `emitted_at`/`duration_ms` in findings or
  report.json. Field report: cold-run plan/report files carried
  absolute workstation paths, duplicate logs, and timestamps —
  noise when evidence is diffed run over run. The skill states the
  rule once, in Workspace: no absolute paths, no timestamps;
  observed output lives once, in the emitted record.
- The Node emitter's `.py` probe preflight calls `python3 -m
  py_compile` — it previously ran `node -m py_compile`, which never
  compiles anything, so any Python scratch probe was refused as
  non-compiling under Node.
- Stage text hardened from the 2026-09-29 cold runs: Verify emits
  the moment a verdict is known (a fix applied before its red
  evidence is emitted strands it; the first emission doubles as the
  emitter smoke test); Safety — evidence does not wait on a broken
  suite, and a target that will not build emits inconclusive
  findings quoting the build error, not silence; run-end check 9
  gives prior confirmed findings a disposition (replayed via their
  regression or blocked with a quoted reason, re-emit on change);
  Discover narrows an untestable-looking target only by asking the
  user; `scratch/` is deleted once the run-end checks pass.

## 0.3.0 - 2026-09-29

### Added

- Stage text names the optional lifecycle skills from cursor/plugins
  (`principle-attack-the-premise`, `create-verification-skill`,
  `maintain-verification-skill`, `principle-test-behavior-not-implementation`,
  `principle-fix-root-causes`) with the install pointer, so the
  companions are discoverable from the pack itself (#2).
- Harden mode: `/sstack harden <target>` fills the suite's
  negative-test gaps — dual isolated assessments (contract side vs
  suite side), per-lens coverage report with percentage bands and
  trend snapshots, P0–P3 gap severity, unattended scope default with
  banner, matrix tests carrying the `sstack_<lens>_` prefix, red
  flips through the existing Test/Fix lifecycle (ADR-0018). Body in
  the on-demand `references/` tier (ADR-0016).
- Lens deselection is now recorded and checked. Discover already
  skipped a lens whose "When not to apply" section ruled the mapped
  surface out, but nothing recorded the decision, so a run that dropped
  a lens read exactly like a clean one. `map.md` now carries every
  skipped lens with the line that ruled it out, and run-end check #6
  fails a run that deselects without naming that line.

- Agent-lens rubric revision, from the all-lenses value/cost audit:
  three oracles restated as code-observable assertions (delimiter check
  on the constructed prompt, system-prompt presence in the truncated
  message list, structured tool result), an "Interaction with other
  lenses" section adjudicating the 4-way overlap with `malformed`,
  `contract`, and `dependency-failure`, and the `agent` index row plus
  skill description plus site card now naming all five owned failure
  classes. Attacker fallback guards against accepting model-reply
  judgments as `observed`.

### Changed

- Stage 5 (Test) and Stage 6 (Fix) upgraded with in-agent mutant checks
  (testing against ROR, boundary shift, and statement deletion in scratch),
  assertion exactness density rules, and general invariant relational guards.
  Stage 6 mutation delegation diff-scoped with a 60s timebox. Run-end check
  #5 added to SKILL.md.
- Lens index pruned in `SKILL.md`: removed unbuilt `mutation` row; index now
  strictly matches the 14 shipped attacker lenses.
- Lens rubrics extended with mutation vectors: `boundaries` and
  `resource-exhaustion` (paired boundary/capacity probes), `contract`
  (paired schema mutation probes), and `idempotency` (payload divergence
  mutation under IETF draft §2.7).
- PBT scratch execution capped to 25 iterations with seed capture in repro
  and emitter schemas for deterministic machine replay.
- Boundaries lens extended from the `docs/lens/lens-boundaries.md` research
  review: precision/scale cases (money needing more decimal places
  than the type holds, floats where the contract implies exactness,
  just-past-`MAX_SAFE_INTEGER`), time/duration cases (`0`/negative
  durations, interval arithmetic, the `month - 1` time twin of
  `(page - 1)`), a no-silent-truncation oracle pattern, a third worked
  example (`round(2.675, 2)` → 2.67, banker's rounding on a binary
  approximation), and the BVA canon citation (ISO/IEC/IEEE 29119-4,
  Myers). Rubric, attacker fallback text, fan-out gloss, and lens
  index row updated together. Cold probes (py, ts): new heuristics
  applied unprompted where surfaces admit them, seven-field Report
  format exact, scratch contained. Boundaries evidence refreshed by
  ColdPy-17 (2026-09-27): 2 confirmed boundaries findings on current
  text, replay intact.
- State lens extended from the `docs/lens/lens-state.md` research review:
  lifecycle & post-disposal invocation (CWE-672), escaped internal
  collection references (CWE-375), callee argument write-through
  mutation (CWE-374), and mid-operation rollback atomicity (CWE-366).
  Added failure modes, language notes (Python, TS/JS, Java, C++),
  structured attacker heuristics, explicit rejection oracles (409 Conflict,
  IllegalStateError), and updated lens index in `SKILL.md`. State
  evidence refreshed by ColdPy-17 (2026-09-27): 1 confirmed state
  finding on current text, replay intact.

### Added

- ADR-0013 (`docs/adr/0013-no-dedicated-pbt-runner.md`): Reject dedicated PBT
  runner; capture seed and minimal counterexample in findings schema and emitters.
- ADR-0014 (`docs/adr/0014-do-not-build-mutation-runner.md`): Reject built-in
  mutation runner engine to preserve ADR-0002 zero-runtime and target repo
  portability; gate Stage 5/6 via in-agent sensitivity check and diff-scoped
  delegation.
- `ordering`, `concurrency`, `idempotency`, and `dependency-failure`
  lenses ship: one `agents/sstack-<lens>-attacker.md`, one
  `skills/sstack-<lens>/SKILL.md`, and one lens-index row each. All
  fourteen shipped lenses now route to a dedicated attacker.
- `evals/acceptance.py` gains `test <fixture>` and `test-all`, the
  single entry point for the py/ts/js/java/cpp baseline suites. AGENTS.md
  baselines updated to match.
- `seeded-py` carries six new seeds: `py-8` (ordering), `py-9`
  (exceptional-conditions), `py-10` (resource-exhaustion), `py-11`
  (concurrency), `py-12` (idempotency), `py-13` (dependency-failure).
  Goldens 27 → 33. Seeds stay defective; each maps to one lens in
  `BUGS.md`.

### Fixed

- `evals/acceptance.py prepare` copies every shipped lens skill into the
  cold workspace. `LENSES` had fallen behind the skill directories, so
  `dependency-failure` was silently dropped from every cold run.
- Lens and golden counts corrected across `AGENTS.md`, `CONTEXT.md`,
  `docs/LENS.md`, `docs/CUSTOMIZING.md`, `docs/ARCHITECTURE.md`,
  `evals/README.md`, `ROADMAP.md`, `CHANGELOG.md`, and `site/index.html`
  — fourteen shipped lenses, eighty goldens. Taxonomy row for
  `dependency-failure` moved from `future` to shipped.
- `site/index.html` gains the four missing lens cards (ordering,
  concurrency, idempotency, dependency-failure). Grid verified in
  Chromium at 1024px: 14 cards, every card span 1, flow 4 / 4 / 4 /
  2, no overflow, no orphan row.
- Install instructions now list each host's own agents directory
  (`.agents`, Claude Code, VS Code, OpenCode) instead of naming three
  paths in one prompt, which told a Cursor user to write into
  `~/.claude/agents/`. `docs/CUSTOMIZING.md` had `opencode/agent/`;
  the directory is `opencode/agents/`.
- `site/index.html` gains the `contract` lens card and drops the
  `lens-card-wide` double-width rule: one wide card makes the grid's
  unit count indivisible by three, and it was on the card whose copy
  needed the space most. Twelve cards now flow 3 / 3 / 3 / 3.
  Measured in Chromium at 1365px and 390px — 357px columns, no
  overflow, single column on mobile.
- README and site evidence tables updated: `seeded-py` carries 14
  seeds with all 14 cold-verified, replacing the `7` count and the
  stale "py-7 has no cold pass" note that ColdPy-11 through -14
  resolved. `ROADMAP.md` goldens 33 → 34, shipped lenses 11 → 12,
  and the "contract next" item corrected — it has shipped.
- `PRODUCT.md` had a false palette claim ("one lime pop per
  section"). Sentry's lime is dropped entirely per `DESIGN.md`; the
  accent is the only pop. Lens counts and the install description
  corrected to match the repo.
- `docs/` restructured: `lens.md` → `LENS.md`; per-lens research into
  `docs/lens/`; dated scans and research notes into `docs/research/`.
  All relative links re-verified (76 across the repo, all resolve).
- `LEARNED.md` → `docs/research/FINDINGS-2026-09-27.md`. The old name
  collided with the Learn stage's `.sstack/learn/`, which is unrelated.

- Stale-count audit: `docs/CUSTOMIZING.md` lens list (seven →
  fourteen), `CONTEXT.md` custom-lens rows (four → `mutation` only),
  `docs/lens/lens-state.md` taxonomy labels (custom/future → shipped
  for ordering, concurrency, idempotency), `evals/ACCEPTANCE.md`
  cold-run setup (six peers → fourteen), `ROADMAP.md` goldens
  (thirty-six → eighty) and leftover partial-seed fractions, README
  v0.2.0 lens delta (seven → eleven), site lifecycle sub (eight
  stages → seven stages and a report), `AGENTS.md` install claim
  (`npx skills add` carries `skills/` only), and the version-tag
  links dropped until the tags exist.
- ColdPy-17 (seeded-py, 2026-09-27): fresh full-lifecycle cold run on
  current skill text after the docs audit. 12 confirmed red→green
  regressions, 12/12 evidence replay intact, 20 tests green,
  content-matched py-1/3/8/9/11/13. py-2 (cart `add_item` qty) went
  unfound: named-run coverage corrected to 15/16 across README,
  ROADMAP, evals/README, site, and ACCEPTANCE; `prepare` now stamps
  the fixture name into `.sstack-host-repo` so a cold run cannot
  misname it; `drift-suite.yaml` and `baseline-base.json` deleted for
  real (README said removed, they weren't).

## 0.2.0 - 2026-09-27

### Added

- Customization, documented in [`docs/CUSTOMIZING.md`](docs/CUSTOMIZING.md).
  A user extends sstack by dropping a file in their own tree named
  with the `sstack-` prefix: a lens in a skills dir, a
  worker in an agents dir, project scope winning over global exactly
  as OpenCode, Claude Code, and VS Code already resolve skills. No
  directory, registry, or installer of sstack's own, and nothing to
  add to `skills/` or `agents/`, which are replaced wholesale on
  update. A lens is a skill, so it carries
  `disable-model-invocation: true` and is pasted into a dispatch
  rather than auto-loaded by a host with no target for it. A custom
  lens appends its rubric to an existing attacker's `### Lens rubric`
  rather than adding an agent, mirroring how `<agent>_append.md`
  composes onto a resolved base prompt. Identity comes from `name`
  frontmatter, not the filename, matching
  `discoverProjectLocalSkillNames`; files resolving outside the target
  are skipped, the same realpath guard that keeps a symlinked
  `.opencode` from becoming arbitrary content injection. One directive
  remains, `lenses.remove` in `.sstack/config.md`, for skipping a
  shipped lens, and it is run input rather than pack content. The
  eight `future` rows in the lens index, `ordering` and `concurrency`
  among them, are now activatable by anyone. ADR-0008 records the
  decision and its cost: this is an extension point the pack cannot
  test, since the agent is the loader
- ADR-0008: the user extends sstack by naming a file, not by editing ours
- Emitter/skill contract closed. The Report format block names
  seven fields, but the emitter also requires `slug`, `fix`, and
  `regression`; a cold agent following the skill verbatim had its
  findings rejected with exit 2. SKILL.md now enumerates the
  payload, and `evals/test_emitter.py` (11 tests) pins the contract in
  the repo's own runner, including negative controls proving each test
  turns red when its guarantee is reverted
- ADR-0004: lenses delegate to the target's existing tools
- ADR-0005: sstack finds, tests, and fixes (supersedes the
  audit-not-fix portion of ADR-0002)
- Per-lens attacker agents (`agents/sstack-<lens>-attacker.md`):
  boundaries, malformed, missing, ownership, exceptional-conditions,
  resource-exhaustion, state — each with the Report format field names
  as fallback, constraints, and an inline-rubric handoff
- Thermos pattern: per-lens fan-out at Attack stage, one agent per
  lens, parallel when the host supports subagent dispatch
- Ownership lens rebuilt against OWASP ASVS V8 and A01:2025, not just
  C1. The rubric now starts from a subject × object × action × context
  tuple per surface, sweeps every decision site (middleware, guards,
  query filters, row policies, client-side) and attacks the weakest,
  and carries a 24-row probe table: field-level read and write
  (BOPLA), deny-by-default and policy fall-through, least privilege,
  hard-coded roles, missing write-method controls, force browsing,
  token replay/tampering, logout invalidation, stale grants (V8.3.2),
  confused-deputy delegation (V8.3.3), cross-tenant writes (V8.4.1),
  admin-interface context (V8.4.2), contextual step-up, CORS, CSRF,
  SSRF, static resources, error-based enumeration, and decommissioned
  accounts. Attacker gained the tuple-first work order and a rule that
  a check on the read path proves nothing about the write path
- Collection surfaces added to the ownership lens, after a user
  reported a real incident: a signed-in user saw other users' data in
  search results. A list, search, index, feed, export, or report
  surface has no single object to protect, so no per-object check
  fails; the subject is simply absent from the query while every
  individual record check passes. The lens now derives the tuple per
  surface, requires establishing a two-subject population before
  probing, and compares result *contents* and counts against
  entitlement. Seven probe-table rows, a collection oracle, and an
  attacker work step. Blinded carrier test, re-run against the
  decontaminated lens: a cold attacker given only the rubric found the
  seeded leak with five confirmed findings (shared-sku match, wildcard
  query, cross-subject read, error-based enumeration, field-level
  sweep) and correctly refuted itself on the BOLA control, where the
  detail route was implemented correctly
- `state` lens (`skills/sstack-state` + `sstack-state-attacker`):
  stale cached/derived reads, mutable input written through, partial
  update after a failed call, internal collections escaped to callers
- Evidence emitter ships with the entry skill
  (`skills/sstack/scripts/emit_findings.py`): stdlib-only, run per
  finding as it verifies; it executes the repro, captures the output,
  fingerprints it, and is the only writer of `findings/<slug>.{md,json}`
  and `report.json`. Every cold run so far re-invented this code
  (2 zombie runs, 1 unparseable report, 1 fabricated-hash wave), and
  each invented its own `findings/*.md` layout. Scope lock narrowed:
  no CLI/daemon/binary, stdlib-only reference scripts allowed
- Property-based testing delegation: Attack stage checks for
  Hypothesis, fast-check, jqwik, RapidCheck and writes a property
  before hand-designing cases
- Mutation testing references: PIT (Java), Stryker (JS/TS), mutmut
  (Python)
- Run-end checks: every confirmed finding has a red test and a green
  post-fix test, every refuted finding on external input has a green
  hardening test, every fix is minimal, full suite passes
- Steel-man Verify step: strongest case that the observed behavior is
  correct, before recording confirmed
- Edge-case vs negative-case vocabulary split in ARCHITECTURE.md and
  the boundaries lens
- Ownership lens (OWASP A01): authorization-scope violations, BOLA,
  IDOR. Unit tier works with mocks; integration tier needs sessions
- Exceptional-conditions lens (OWASP A10): fail-open paths,
  diagnostic leakage, cascading failures. Unit tier works with mocks;
  integration tier needs injectable failures
- Containment: the earlier `evals/verify-isolation.sh` lock/unlock
  experiment was removed; workspace preparation is now unified under
  `evals/acceptance.py`, with containment enforced by the caller.
- Tool inventory by language (`docs/TOOLS.md`)
- Research index (`docs/RESEARCH.md`)
- Research record (`docs/LEARNED.md`)
- Language breadth on the roadmap: Python, JavaScript, TypeScript,
  Java, C++
- Roadmap: Thermos per-lens fan-out architecture, C++ second
  verification mode question, Readme honesty line
- ADR-0006: finding evidence is machine-re-verifiable; evidence
  schema pinned in skill text; `evals/acceptance.py replay` audits
  fingerprints out of the agent loop
- ADR-0007: optional dependencies degrade inline; coverage is the
  contract, parallelism is an optimization
- Java test baseline: javac + junit-console with auto-fetched jar
  (`evals/seeded-java/RUN_TESTS.md`); goldens backfilled for js,
  java, and cpp fixtures

### Changed

- Acceptance re-verified on the post-lane-audit text:
  ColdPy-4 PASS 5/5 seeds, 13 red→green, 22/22 replay intact;
  ColdJava-3 PASS java-1/2/4, 5 red→green, 7/7 replay intact — java's
  pre-schema-pin evidence gap is closed, every PASS now replays
- Fan-out field failure modes logged (ColdPy-3, cancelled): an
  attacker subagent stalled 50+ min blocking its parent, and one host
  dispatched lens attackers as read-only scouts that cannot execute
  probes. Serial override (skill's own fallback) carried both re-runs
- Evidence contract: `regression.before`/`after` are the literal state
  tokens "red"/"green" — the grader always required that and the skill
  never said it; ColdTs-4 wrote output snippets and graded zero matches
- ColdTs-4 (seeded-ts, post-consistency text): PASS, 5/5 seeds,
  15 confirmed red→green, 19/19 evidence replay intact, 0 drift — the
  run crashed pre-emit and was resumed by the orchestrator, which is
  exactly the zombie failure the emit-as-you-verify rule
  exists to prevent
- Cold acceptance baseline complete: all five fixtures PASS on the
  current skill text (2026-09-27). py 5/5 seeds twice (Learn-run-2
  proved the loop: run 2 cited run 1's `.sstack/learn/` classes and
  attacked in learned order), js 5/5, ts 4/5, java 3/5, cpp 3/5;
  every PASS replays evidence intact (py 10/10+8/8, ts 7/7,
  js 12/12, cpp 13/13)
- Grader rejects a regression whose file is byte-identical to the
  frozen fixture original (ColdTs-2 claimed tests it never wrote)
- Run-end check #1 forbids scratch-binary regressions: the file must
  live in the repo's own suite (ColdCpp named `test_functions.cpp`,
  absent from disk)
- Lifecycle expanded: Regress split into Test (write regression, goes
  red) and Fix (apply minimal change, goes green)
- Verify requires steel-manning observed behavior before recording
  confirmed
- Discover reads a verification skill or feature map as a head start
- AGENTS.md restructured for the always-loaded budget
- ROADMAP.md humanized and expanded
- README language support stated honestly
- Grader rewritten from first principles: findings match goldens by
  content (trigger function/words across surface, case, oracle), not
  by self-reported seed_id; landed regressions verified on disk;
  `grade` takes a workspace and resolves `.sstack/report.json`
- Replay semantics split: integrity (recomputed fingerprint vs
  record; typed-in hashes grade fabricated) and drift (live re-run,
  informational after a landed fix)
- Report contract: JSON emitted by script with in-process
  fingerprint; hand-typed reports grade INVALID
- Report format carrier redesigned after the lane audit: the block is
  defined once in the skill and reaches a subagent only pasted into
  its dispatch under `### Report format`; attacker files keep the
  seven field names as fallback. The earlier design (a verbatim copy
  in all seven files) was a drift cache — it contradicted itself
  within the hour. Re-probed on fresh-context subagents: pasted 5/5
  exact blocks, paste omitted 2/4 all-seven — paste is the carrier
- Lane audit: `npx skills add` ships only `skills/` (the `agents/` files are copied by hand);
  AGENTS.md, CONTEXT.md, docs/, and evals/ exist only in a git
  checkout. Three shipped-text references to checkout machinery
  (`evals/replay.py`, "the grader", "grading matches by content")
  rewritten verifier-neutral; AGENTS.md's failure-modes paragraph
  deleted — all six modes proved to have authoritative shipped
  homes; the disjunctive-oracle guard that lacked one moved into
  rule 2 of the skill and ETHOS

### Fixed

- Attack coverage paragraph restored after silent deletion
- Acceptance harness and skill corrected after guardrail iterations
- SKILL.md lens index gains the missing `state` row; Report format
  block named once ("Report format", replacing "sstack returns
  format")
- writing-for-agents sweep: restored eaten verbs, co-located skill
  names, single "attacker" term

### Security

- Acceptance containment: cold runs ship all skills and agents into
  one temp workspace with BUGS.md stripped; containment is caller
  responsibility (prompt-only boundaries already failed)

### Removed

- `docs/superpowers/` (process artifacts, gitignored)
- `references/lens-*.md` (superseded by peer skills and agents)

## 0.1.0 - 2026-09-27

First release. A structured negative-testing skill pack for AI coding
agents.

### Added

- Orchestrator skill (`skills/sstack/SKILL.md`): five-stage lifecycle
  (Discover, Attack, Verify, Minimize, Regress), oracle-first
  verification, red/green regression vocabulary, per-surface lens
- Three input lenses (historical v0.1.0 layout): boundaries, malformed,
  missing
- Concept freeze (`docs/`): ETHOS.md, ARCHITECTURE.md
- Seeded-bug eval repos: `evals/seeded-py` and `evals/seeded-ts`
- Unified Python eval entry point (`evals/acceptance.py`) prepares
  isolated workspaces and grades JSON reports
- Acceptance record (`evals/ACCEPTANCE.md`)
- MIT license

