# Project Documentation
> Generated: 2026-09-24 | Mode: DELTA

## Tech Stack

- **Deliverable type**: agent-agnostic skill pack — Markdown (agent-skills `SKILL.md` format). No runtime, no CLI, no daemon.
- **Language**: Markdown (skill + docs); Python 3 stdlib (unified eval entry point); Python 3.10+, TypeScript 5.5+, JavaScript, Java 17+, and C++17 exist only inside `evals/` as fixture code under test.
- **Framework**: pytest (Python), vitest 2.x (TypeScript/Bun), Node test runner (JavaScript), JUnit 5/Maven (Java), CMake/CTest (C++).
- **Database / Styling / State Management**: none. Not applicable to this project.
- **Host**: any agent that reads `skills/sstack/SKILL.md` (Claude Code, OpenCode, Cursor, Codex). Install = `npx skills@latest add mhenke/sstack` or copy the directory.

## Dependencies

- **Core**: none. The pack has zero runtime dependencies by design.
- **Dev / tooling**: `python3` + `pytest`, `bun` + `vitest` + `typescript`, `node --test`, `javac`, `cmake` + `ctest`.
- **Testing**: pytest, vitest, Node test runner, JUnit 5, CTest.

## Architecture Pattern

Content architecture with a strict noun taxonomy (six definitions in ARCHITECTURE.md). The Thermos pattern is implemented: orchestrator skill dispatches per-lens attacker agents in parallel, each loading its own lens rubric from `skills/<lens>/SKILL.md`.

**Lifecycle (9 canonical stages, 6 implemented in SKILL.md):**

| Canonical | Implemented as | Stage # |
|---|---|---|
| Discover | Discover (stage 1) | 1 |
| Model | folded into Discover output | — |
| Attack | Attack (stage 2) | 2 |
| Observe | folded into Attack execution | — |
| Verify | Verify (stage 3) | 3 |
| Minimize | Minimize (stage 4) | 4 |
| Test | Test (stage 5) — writes regression, goes red | 5 |
| Fix | Fix (stage 6) — applies minimal change, goes green | 6 |
| Learn | deferred to v1 | — |

**Six definitions (taxonomy):**

| Noun | v0 realization | Where |
|---|---|---|
| Skill | methodology for a stage | `skills/sstack/SKILL.md` |
| Lens | attack strategy per failure class | `skills/sstack-<lens>/SKILL.md` |
| Agent | per-lens attacker (Thermos pattern) | `agents/sstack-<lens>-attacker.md` |
| Runner | deferred — agent runs real commands | — |
| Oracle | expected behavior declared before the attack | inline in SKILL.md + lens skills |
| Evidence | observed vs. oracle, loose markdown | `.sstack/findings/` in the host repo |

**Lens taxonomy (15 lenses, 6 shipped in v0):**

| Category | Lens | v0 |
|---|---|---|
| Input | boundaries, malformed, missing | ✅ |
| Access | ownership | ✅ (peer skill + agent) |
| Behavior | exceptional-conditions | ✅ (peer skill + agent) |
| Behavior | state, ordering, concurrency, idempotency | future |
| Environment | dependency-failure | future |
| Environment | resource-exhaustion | ✅ (peer skill + agent) |
| Contracts | contract | future |
| Evidence | mutation | future |
| AI/Agent | agent | future |
| Security | security | future |

**Find-test-fix model (ADR-0005):** sstack attacks, writes a red regression test, applies the minimal fix, verifies the test goes green, and hardens existing suites with green characterization tests for refuted surfaces. Source changes only in the Fix stage, only minimal, only for confirmed findings.

## Folder Structure

```
skills/sstack/SKILL.md              orchestrator: routing, rules, 7 stages, lens index
skills/sstack-<lens>/SKILL.md       peer lens skills (6: boundaries, malformed, missing, ownership, exceptional-conditions, resource-exhaustion)
agents/sstack-<lens>-attacker.md    per-lens attacker definitions (Thermos dispatch by name)

docs/
├── ETHOS.md                       the four rules
├── ARCHITECTURE.md                lifecycle, six definitions, 15-lens taxonomy
├── TOOLS.md                       negative-testing tools by language
├── RESEARCH.md                    index into the 30-day scan library
├── LEARNED.md                     distilled research record
└── adr/                           0001–0007 + README index + template

evals/
├── acceptance.py                   unified prepare/grade/replay entry point
├── ACCEPTANCE.md                  run history, verdicts, contamination disclosure
├── goldens.jsonl                  seeded expectations (25 rows, all five fixtures)
├── graders/                       content-match seeded-acceptance grader
├── replay.py                      out-of-loop evidence integrity auditor
├── drift-suite.yaml               frozen eval configuration
├── baseline-base.json             gate token, currently not_run
├── seeded-py/                     Python fixture, 5 bugs + BUGS.md answer key
├── seeded-ts/                     TypeScript fixture, 5 bugs + BUGS.md
├── seeded-js/                     JavaScript fixture, 5 bugs + BUGS.md
├── seeded-java/                   Java fixture, 5 bugs + BUGS.md
└── seeded-cpp/                    C++ fixture, 5 bugs + BUGS.md
README.md                          install, lifecycle diagram, acceptance table, docs links
ROADMAP.md                         v1 (proof quality), v2 (run cost), language breadth, deferred
CHANGELOG.md                       Keep a Changelog format
.claude/pipeline/                  scanner output (this file, state.json)
```

## Code Style Conventions

- **Skill frontmatter**: exactly `name` + `description`; description is one long trigger-phrase sentence. `SKILL.md` must stay ≤ 500 lines (currently 377).
- **Agent files**: YAML frontmatter with `name` + `description`; body carries the rubric fallback, the work steps, and the Report format block byte-identical to SKILL.md's (seven copies, one commit; a dispatched subagent never sees the orchestrator's file).
- **Lens skill files**: Case-generation heuristics, Oracle patterns with an inline `Worked example` paragraph (one python plus one ts/js example; `observed (bug)` marks the defect), and When not to apply. Extra sections (Operating limits, Language notes, Failure modes to watch for) allowed where the lens needs them.
- **Prose style**: hard-wrapped ~60–72 columns, imperative voice, backticks for identifiers and paths.
- **Python eval**: PEP 8, snake_case, module docstrings, no type hints, no classes, deliberately no validation.
- **TypeScript eval**: ESM, `export function`, `interface` per shape, `strict: true`, 2-space indent, semicolons, double quotes.
- **Commits**: Conventional Commits (`docs:`, `feat:`, `fix:`, `test:`, `chore:`).

## Modularity Practices

- Orchestrator owns routing and rules; each lens skill owns one failure class; each agent wraps one lens for dispatch.
- Lens content is not loaded unless selected.
- New lenses are additive: `agents/sstack-<name>-attacker.md` + `skills/sstack-<name>/SKILL.md` + one index row.
- Deferred subsystems (runners, evidence schema, learn loop, host packaging) are named in ARCHITECTURE.md as v1; they are not stubbed.

## Data Architecture

No database, no ORM. Data shapes:

- **Fixture records**: Python dicts / TS interfaces (`LineItem`, `CartLine`)
- **Run artifacts**: `.sstack/` in the host repo (`map.md`, `plan.md`, `report.json`, `findings/<slug>.md` + `.json`, `learn/`, `scratch/`)
- **Answer keys**: `evals/*/BUGS.md` (never shipped to cold agents)

## Cross-Cutting Concerns

- **Audit-not-fix**: replaced by ADR-0005 find-test-fix model. sstack writes tests and source fixes (minimal, oracle-driven). Config and secrets always read-only.
- **Evidence discipline**: the agent quotes verbatim command output; harness errors are broken cases, never verdicts.
- **Safety contract**: source writable only in the Fix stage, only minimal changes that turn a red test green. Every source change must trace to a finding.
- **Containment**: the caller builds the temp workspace and dispatches the agent into it. Prompt-only containment has failed; the host-repo marker directs the agent to the right root, but enforcement is the caller's responsibility.
- **Coverage rule**: every selected lens must have zero-or-more cases on every mapped surface. A lens with zero cases on a record/string-input surface is an incomplete run.

## Service Communication

None. Single-process, local files. `evals/acceptance.py` copies the orchestrator skill, the six peer lens skills, the six agents, and a decontaminated fixture into a temp dir.

## Test Coverage

- **Overall coverage: not measured** — no coverage tooling, by design.
- **Baselines**: `evals/seeded-py` → `pytest -q`; `evals/seeded-ts` → `bun run test`; `evals/seeded-js` → `npm test`; `evals/seeded-cpp` → CMake/CTest; `evals/seeded-java` → javac + junit-console (jar auto-fetched; `RUN_TESTS.md`).
- **Acceptance**: cold-run eval per ADR-0003, recorded in `evals/ACCEPTANCE.md`. 2026-09-24 current-text runs: **all five fixtures PASS** (py 5/5 seeds twice, js 5/5, ts 4/5, java 3/5, cpp 3/5), each with landed regressions verified on disk and evidence replaying intact (Java's wave predates the schema pin; landed-checks only).

## Entry Points

| Path | Role |
|---|---|
| `skills/sstack/SKILL.md` | product entry (`/sstack <target>`) |
| `agents/sstack-<lens>-attacker.md` | per-lens attacker definitions (Thermos dispatch by name) |
| `skills/sstack-<lens>/SKILL.md` | per-lens rubrics |
| `docs/ETHOS.md` | four rules |
| `docs/ARCHITECTURE.md` | lifecycle, six definitions, taxonomy |
| `docs/adr/README.md` | decision index |
| `evals/acceptance.py` | unified prepare/grade/replay entry point |
| `evals/ACCEPTANCE.md` | evidence record |
| `CONTEXT.md` | judging glossary (integrity, drift, content match, INVALID) |

## Changed Files
AGENTS.md, CHANGELOG.md, docs/ARCHITECTURE.md, agents/sstack-*-attacker.md (`lens: <this lens>` → `lens: <lens>`, block now byte-identical across all seven copies; micro-test recorded)

## Last Scanned
2026-09-25 (delta: fan-out micro-test result + block-sync convention)
