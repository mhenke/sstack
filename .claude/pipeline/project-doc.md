# Project Documentation
> Generated: 2026-09-23 | Mode: FULL

## Tech Stack

- **Deliverable type**: agent-agnostic skill pack — Markdown (agent-skills `SKILL.md` format). No runtime, no CLI, no daemon.
- **Language**: Markdown (skill + docs); POSIX `sh` (acceptance harness); Python 3.10+ and TypeScript 5.5+ exist only inside `evals/` as fixture code under test.
- **Framework**: none for the pack itself. Eval repos: pytest (Python), vitest 2.x (TypeScript, run under Bun).
- **Database / Styling / State Management**: none. Not applicable to this project.
- **Host**: any agent that reads `skills/<name>/SKILL.md` (Claude Code, OpenCode, Cursor, Codex). Install = copy the directory.

## Dependencies

- **Core**: none. The pack has zero runtime dependencies by design (v0 is process-only).
- **Dev / tooling (repo maintenance only)**: `rsync` (acceptance harness), `python3` + `pytest` (py eval), `bun` + `vitest` + `typescript` (ts eval).
- **Testing**: pytest 9.x (py eval), vitest ^2.0.0 (ts eval).
- Harness requirement: `rsync` must be on PATH for `evals/run-acceptance.sh`; `mktemp`, `dirname` assumed.

## Architecture Pattern

Not a conventional app. A **content architecture with a strict noun taxonomy** — this is the project's central invariant, defined in `docs/ARCHITECTURE.md` as the "six definitions":

| Noun | v0 realization | Where |
|---|---|---|
| **Skill** | the methodology for a stage | `skills/sstack/SKILL.md` (one entry skill) |
| **Lens** | attack strategy over a failure class | `skills/sstack/references/lens-*.md` (content, loaded on demand) |
| **Agent** | reasoning role | **deferred** — v0 has one agent adopt roles per stage, no agent files |
| **Runner** | deterministic case execution | **deferred** — v0: the agent runs real commands and quotes real output |
| **Oracle** | expected behavior declared *before* the attack | inline in SKILL.md stage instructions + lens files |
| **Evidence** | observed vs. oracle | **loose** — markdown under `.sstack/`; structured schema is v1 |

Lifecycle: Discover → Model → Attack → Observe → Verify → Minimize → Regress → Learn. v0 implements five numbered stages in SKILL.md; Model folds into Discover's output, Observe folds into Attack, Learn is documented-only.

Entry-point-on-demand layout: one `SKILL.md` (routing + rules + stage instructions + lens index) plus `references/` files read only when that lens is selected. Same shape as impeccable's `reference/` and pstack's playbooks.

## Folder Structure

```
skills/sstack/          THE PRODUCT. Entry skill + 3 v0 lens references.
docs/                   Concept freeze: ETHOS.md (4 rules), ARCHITECTURE.md (lifecycle, 6 defs, 13-lens taxonomy, v1 menu)
docs/adr/                Decision records (ADR-0001 domain, 0002 content-only pack, 0003 eval-gated acceptance) + index + template
evals/                  Proof of the skill
evals/seeded-py/        Python fixture repo, 5 deliberate bugs + BUGS.md answer key
evals/seeded-ts/        TypeScript fixture repo, 5 deliberate bugs + BUGS.md answer key
evals/ACCEPTANCE.md     Cold-run acceptance record (history, verdicts, disclosed contamination + fix)
evals/run-acceptance.sh Copies skill + BUGS.md-free repo into ONE temp workspace
.claude/pipeline/       Scanner output (this file, AGENTS.md, state.json)
```

## Code Style Conventions

Inferred from the actual files:

- **Skill frontmatter**: exactly `name` + `description`; description is one long trigger-phrase sentence ("Use when the user wants negative testing, edge-case coverage, …"). `SKILL.md` must stay ≤ 500 lines (currently 157).
- **Prose style**: hard-wrapped ~60–72 columns; imperative voice in instructions; em dash for asides; backticks for code identifiers and file paths.
- **No title-case headers in stage bodies**; `### 1. Discover` style numbering in SKILL.md, `## What assumptions this lens attacks` sentence case in lens files.
- **Python eval**: PEP 8, snake_case functions, module docstrings, no type hints, no classes, deliberately no validation (the bugs are the point).
- **TypeScript eval**: ESM (`"type": "module"`), `export function`, `interface` per data shape, `strict: true`, 2-space indent, semicolons, double quotes.
- **Commits**: Conventional Commits (`docs:`, `feat:`, `fix:`, `test:`, `chore:`).
- **Lens file template** (all 3 files, non-negotiable shape): 5 `##` sections — What assumptions this lens attacks · Case-generation heuristics · Oracle patterns · Worked examples · When not to apply — with exactly one `python` and one `ts` fenced block carrying `# case:` / `# oracle:` / `# observed (bug):` comments. Files end with a trailing newline.

## Modularity Practices

- One concern per file: the entry skill owns routing/rules; each lens owns one failure class; each docs file owns one abstraction level.
- Lens content is **not** loaded unless selected — keeps invocation context small.
- New lenses are additive: drop a `lens-<name>.md` into `references/` and add one index row. No restructuring.
- Deferred subsystems (runners, evidence schema, learn loop, agents-as-files, host packaging) are named in ARCHITECTURE.md as v1 so additions have a documented home. **They are not stubbed — they do not exist in the tree.**

## Data Architecture

None. No database, no ORM, no persistence layer.

The only data shapes are:
- **Fixture records** — Python dicts (`{"unit_price", "qty", "discount"}`) and TS `LineItem` / `CartLine` interfaces; the negative tests attack these shapes.
- **Run artifacts** — `.sstack/` in the *host* repo at run time: `map.md`, `plan.md`, `findings/<slug>.md` (fields: `lens, surface, case, oracle, observed, verdict, repro, regression`), `scratch/`. Markdown, not schema-enforced in v0.
- **Answer keys** — `evals/*/BUGS.md` tables (id, module, lens, trigger, buggy behavior, oracle, fix note). Never copied into a cold-run workspace.

## Cross-Cutting Concerns

- **Error handling (in the fixture code)**: deliberately absent — raw `KeyError` / `TypeError` / `SyntaxError` leaks are seeded bugs, not oversights. Never "fix" them in the fixtures.
- **Validation philosophy (the product)**: oracles distinguish *clean boundary validation* from *raw deep-inside leaks*. The skill rejects both silent wrong data and unhandled internal errors.
- **Safety contract**: the skill writes only tests and `.sstack/`; it must never modify target source, config, or secrets. Enforced in three places in SKILL.md (title block, Routing, Safety) because a cold run violated it.
- **Evidence discipline**: the agent quotes verbatim command output; harness errors (`ImportError`, missing-argument `TypeError`) are *broken cases*, never verdicts. This rule exists because a cold run once scored 105 broken scripts as satisfied oracles.
- **Logging**: none. Evidence is the test result / observed output.
- **Auth**: not applicable.

## Service Communication

None. Single-process, local files only. The one cross-boundary move is `run-acceptance.sh` copying the skill + a decontaminated fixture into a temp dir; the cold agent communicates back only via its chat report.

## Test Coverage

- **Overall coverage: not measured** — no coverage tooling is configured, by design. The deliverable is prose, not shipped runtime code; there is nothing to instrument.
- **Baselines that must stay green**: `evals/seeded-py` → `pytest -q` (5 passed); `evals/seeded-ts` → `bun run test` (6 passed).
- **The real test suite is the cold acceptance run** — a fresh agent given only the skill + a BUGS.md-free fixture, scored on: seeds confirmed, oracle regressions failing pre-fix, and flipping to pass after canonical fixes. Record: `evals/ACCEPTANCE.md` (py 4/5 seeds, 9/9 flip; ts 5/5 seeds + 1 unseeded real bug, 34/35 flip).
- **Test patterns**: fixture unit tests (happy path only) + behavioral acceptance via subagent. No e2e, no integration layer.
- **Untested areas by design**: Learn stage, evidence schema, runner determinism — all deferred to v1.

## Entry Points

| Path | Role |
|---|---|
| `skills/sstack/SKILL.md` | the product; agent entry point (`/sstack <target>`) |
| `skills/sstack/references/lens-*.md` | on-demand lens content |
| `docs/ETHOS.md` | the four rules — read before changing skill voice |
| `docs/ARCHITECTURE.md` | lifecycle + six definitions + full 13-lens taxonomy |
| `evals/run-acceptance.sh` | build the cold-run workspace |
| `evals/ACCEPTANCE.md` | evidence + run history |
| `evals/*/BUGS.md` | answer keys — **never** readable by a cold agent |

No env vars, no build step, no CI.

## Last Scanned

2026-09-23
