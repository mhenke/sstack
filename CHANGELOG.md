# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- ADR-0004: lenses delegate to the target's existing tools
- ADR-0005: sstack finds, tests, and fixes (supersedes the
  audit-not-fix portion of ADR-0002)
- Per-lens attacker agents (`agents/sstack-<lens>-attacker.md`):
  boundaries, malformed, missing, ownership, exceptional-conditions,
  resource-exhaustion — each with the Report format field names as
  fallback, constraints, and an inline-rubric handoff
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
  attacker work step. Blinded carrier test: a cold attacker given
  only the rubric found the seeded leak with four distinct confirmed
  findings (shared-sku match, wildcard query, count/volume leak,
  absent principal) and correctly refuted itself on the two surfaces
  that were implemented correctly
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

- Acceptance re-verified on the post-lane-audit text (`13947ce`):
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
  exactly the zombie failure the emit-as-you-verify rule (`34bf6a6`)
  exists to prevent
- Cold acceptance baseline complete: all five fixtures PASS on the
  current skill text (2026-09-24). py 5/5 seeds twice (Learn-run-2
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
- Lane audit: `npx skills add` ships only `skills/` and `agents/`;
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

## [0.1.0] - 2026-09-23

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

[unreleased]: https://github.com/mhenke/sstack/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/mhenke/sstack/releases/tag/v0.1.0
