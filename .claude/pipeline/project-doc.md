# Project Documentation
> Generated: 2026-09-23 | Mode: FULL

## Tech Stack

- **Deliverable type**: agent-agnostic skill pack — Markdown (agent-skills `SKILL.md` format). No runtime, no CLI, no daemon.
- **Language**: Markdown (skill + docs); POSIX `sh` (acceptance harness); Python 3.10+ and TypeScript 5.5+ exist only inside `evals/` as fixture code under test.
- **Framework**: none for the pack itself. Eval repos: pytest (Python), vitest 2.x (TypeScript, run under Bun).
- **Database / Styling / State Management**: none. Not applicable to this project.
- **Host**: any agent that reads `skills/sstack/SKILL.md` (Claude Code, OpenCode, Cursor, Codex). Install = `npx skills@latest add mhenke/sstack` or copy the directory.

## Dependencies

- **Core**: none. The pack has zero runtime dependencies by design.
- **Dev / tooling (repo maintenance only)**: `rsync` (acceptance harness), `python3` + `pytest` (py eval), `bun` + `vitest` + `typescript` (ts eval).
- **Testing**: pytest 9.x (py eval), vitest ^2.0.0 (ts eval).

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
| Lens | attack strategy per failure class | `skills/sstack/skills/<lens>/SKILL.md` |
| Agent | per-lens attacker (Thermos pattern) | `skills/sstack/agents/<lens>-attacker.md` |
| Runner | deferred — agent runs real commands | — |
| Oracle | expected behavior declared before the attack | inline in SKILL.md + lens skills |
| Evidence | observed vs. oracle, loose markdown | `.sstack/findings/` in the host repo |

**Lens taxonomy (15 lenses, 3 shipped in v0):**

| Category | Lens | v0 |
|---|---|---|
| Input | boundaries, malformed, missing | ✅ |
| Access | ownership | next (highest priority) |
| Behavior | exceptional-conditions | next |
| Behavior | state, ordering, concurrency, idempotency | future |
| Environment | dependency-failure, resource-exhaustion | future |
| Contracts | contract | future |
| Evidence | mutation | future |
| AI/Agent | agent | future |
| Security | security | future |

**Find-test-fix model (ADR-0005):** sstack attacks, writes a red regression test, applies the minimal fix, verifies the test goes green, and hardens existing suites with green characterization tests for refuted surfaces. Source changes only in the Fix stage, only minimal, only for confirmed findings.

## Folder Structure

```
skills/sstack/                     THE PRODUCT
├── SKILL.md                       entry: routing, rules, 6 stages, lens index
├── agents/                        per-lens attacker definitions (Thermos pattern)
│   ├── boundaries-attacker.md     frontmatter + dispatch instructions
│   ├── malformed-attacker.md
│   ├── missing-attacker.md
│   └── resource-exhaustion-attacker.md  (future lens, rubric inline)
└── skills/                        per-lens rubrics (loaded by agents)
    ├── boundaries/SKILL.md
    ├── malformed/SKILL.md
    └── missing/SKILL.md

docs/
├── ETHOS.md                       the four rules
├── ARCHITECTURE.md                lifecycle, six definitions, 15-lens taxonomy
├── TOOLS.md                       negative-testing tools by language
├── RESEARCH.md                    index into the 30-day scan library
├── LEARNED.md                     distilled research record
└── adr/                           0001–0005 + README index + template

evals/
├── run-acceptance.sh              builds isolated cold-run workspace
├── ACCEPTANCE.md                  run history, verdicts, contamination disclosure
├── seeded-py/                     Python fixture, 5 bugs + BUGS.md answer key
│   ├── shop/                      pagination.py, pricing.py, cart.py
│   ├── tests/                     happy-path baseline (5 tests)
│   └── BUGS.md                    answer key (never shipped to cold agent)
├── seeded-ts/                     TypeScript fixture, 5 bugs + BUGS.md
│   ├── src/                       pagination.ts, pricing.ts, cart.ts
│   ├── tests/                     happy-path baseline (6 tests)
│   └── BUGS.md                    answer key
README.md                          install, lifecycle diagram, acceptance table, docs links
ROADMAP.md                         v1 (proof quality), v2 (run cost), language breadth, deferred
CHANGELOG.md                       Keep a Changelog format
.claude/pipeline/                  scanner output (this file, state.json)
```

## Code Style Conventions

- **Skill frontmatter**: exactly `name` + `description`; description is one long trigger-phrase sentence. `SKILL.md` must stay ≤ 500 lines (currently 253).
- **Agent files**: YAML frontmatter with `name` + `description`; body is a thin dispatch wrapper that loads its lens skill and returns findings.
- **Lens skill files**: exactly 5 `##` sections: What assumptions this lens attacks · Case-generation heuristics · Oracle patterns · Worked examples · When not to apply. Plus Language notes. One `python` and one `ts` block with `# case:` / `# oracle:` / `# observed (bug):` comments.
- **Prose style**: hard-wrapped ~60–72 columns, imperative voice, backticks for identifiers and paths.
- **Python eval**: PEP 8, snake_case, module docstrings, no type hints, no classes, deliberately no validation.
- **TypeScript eval**: ESM, `export function`, `interface` per shape, `strict: true`, 2-space indent, semicolons, double quotes.
- **Commits**: Conventional Commits (`docs:`, `feat:`, `fix:`, `test:`, `chore:`).

## Modularity Practices

- Orchestrator owns routing and rules; each lens skill owns one failure class; each agent wraps one lens for dispatch.
- Lens content is not loaded unless selected.
- New lenses are additive: `agents/<lens>-attacker.md` + `skills/<lens>/SKILL.md` + one index row.
- Deferred subsystems (runners, evidence schema, learn loop, host packaging) are named in ARCHITECTURE.md as v1; they are not stubbed.

## Data Architecture

No database, no ORM. Data shapes:

- **Fixture records**: Python dicts / TS interfaces (`LineItem`, `CartLine`)
- **Run artifacts**: `.sstack/` in the host repo (`map.md`, `plan.md`, `findings/<slug>.md`, `scratch/`)
- **Answer keys**: `evals/*/BUGS.md` (never shipped to cold agents)

## Cross-Cutting Concerns

- **Audit-not-fix**: replaced by ADR-0005 find-test-fix model. sstack writes tests and source fixes (minimal, oracle-driven). Config and secrets always read-only.
- **Evidence discipline**: the agent quotes verbatim command output; harness errors are broken cases, never verdicts.
- **Safety contract**: source writable only in the Fix stage, only minimal changes that turn a red test green. Every source change must trace to a finding.
- **Containment**: the caller builds the temp workspace and dispatches the agent into it. Prompt-only containment has failed; the host-repo marker directs the agent to the right root, but enforcement is the caller's responsibility.
- **Coverage rule**: every selected lens must have zero-or-more cases on every mapped surface. A lens with zero cases on a record/string-input surface is an incomplete run.

## Service Communication

None. Single-process, local files. `run-acceptance.sh` copies the skill and a decontaminated fixture into a temp dir.

## Test Coverage

- **Overall coverage: not measured** — no coverage tooling, by design.
- **Baselines**: `evals/seeded-py` → `pytest -q` (5 passed); `evals/seeded-ts` → `bun run test` (6 passed).
- **Acceptance**: cold-run eval per ADR-0003, recorded in `evals/ACCEPTANCE.md`. Current status: **stale** (see staleness marker in the verdict table). The find-test-fix lifecycle has not been re-confirmed since the skill restructure.

## Entry Points

| Path | Role |
|---|---|
| `skills/sstack/SKILL.md` | product entry (`/sstack <target>`) |
| `skills/sstack/agents/*.md` | per-lens attacker definitions |
| `skills/sstack/skills/*/SKILL.md` | per-lens rubrics |
| `docs/ETHOS.md` | four rules |
| `docs/ARCHITECTURE.md` | lifecycle, six definitions, taxonomy |
| `docs/adr/README.md` | decision index |
| `evals/run-acceptance.sh` | acceptance harness |
| `evals/ACCEPTANCE.md` | evidence record |

## Last Scanned
2026-09-23 (second full scan, post-Thermos restructure)
