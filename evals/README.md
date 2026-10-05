# Evals

Cold-agent evaluation and verification harness for sstack.

## What is an Eval?

sstack is a collection of instructions for AI coding agents: the orchestrator skill in [`skills/sstack/SKILL.md`](../skills/sstack/SKILL.md) and fourteen attacker agent profiles in [`agents/`](../agents/).

Because agent prompt instructions cannot be validated with unit tests alone, sstack evaluates itself through **cold-agent evaluations**:
- We test whether an AI agent, following only sstack's skill and attacker instructions, can independently discover, minimize, test, and fix real bugs in deliberately broken target repositories.
- The evaluation is **cold**: the agent starts in an isolated sandbox with zero prior memory, no chat history, and no answer key ([`BUGS.md`](seeded-py/BUGS.md) is stripped).
- The evaluation is **evidence-gated**: a finding is only accepted if the agent produces machine-reverifiable repro output and a regression test that was **red** on the buggy seed and turns **green** after the code fix.

## Core Concepts

- **Eval harness ([`acceptance.py`](acceptance.py))**: Deterministic local referee (zero LLM calls). Tests fixture baseline health (`test-all`), prepares decontaminated sandboxes (`prepare`), grades agent reports against ground truth (`grade`), and verifies evidence integrity (`replay`).
- **Cold agent**: The live AI model being evaluated. Starts in an isolated sandbox with zero context, no answer key, and no memory; reads [`skills/sstack/SKILL.md`](../skills/sstack/SKILL.md) cold, executes `/sstack`, and emits evidence.
- **Target Fixtures** ([`seeded-py`](seeded-py/), [`seeded-ts`](seeded-ts/), [`seeded-js`](seeded-js/), [`seeded-java`](seeded-java/), [`seeded-cpp`](seeded-cpp/)): Five broken codebases covering Python, TypeScript, JavaScript, Java, and C++. Each ships nineteen seeded defects and a [`BUGS.md`](seeded-py/BUGS.md) answer key.

## Quick start

### Automated Evaluation (Recommended)

Run end-to-end evaluation using your agent CLI:

```bash
# Automated evaluation with an agent CLI (e.g. Claude Code):
python3 evals/acceptance.py eval seeded-py --model claude-3-7-sonnet --agent-cmd "claude -p '{prompt}'"
```

### Manual / Subagent Evaluation Flow

From the repository root:

```bash
# 1. Build an isolated workspace (prints workspace path)
python3 evals/acceptance.py prepare seeded-py

# 2. Launch a fresh cold agent inside the printed directory (see prompt below)

# 3. Grade the run's findings against goldens
python3 evals/acceptance.py grade /tmp/sstack-cold/sstack-seeded-py-<id>

# 4. Verify evidence integrity out-of-loop
python3 evals/acceptance.py replay /tmp/sstack-cold/sstack-seeded-py-<id>
```

## Running the Cold Agent

### 1. Cold Agent Prompt Template

Provide the agent with this exact prompt:

```text
Your workspace root is `<prepared-workspace-path>`.
Read `skills/sstack/SKILL.md` inside that workspace and execute `/sstack shop` against the codebase.
All file reads, file edits, and commands must be executed within `<prepared-workspace-path>`.
Report your findings when finished.
```

### 2. Containment Rules
- **No access to sstack repo or `BUGS.md`**: `prepare` strips [`BUGS.md`](seeded-py/BUGS.md) and initializes a clean git baseline. The cold agent must never read the source repo or answer key.
- **Working directory**: All agent tool calls (`read_file`, `write_file`, `bash`) must set `cwd=<prepared-workspace-path>`.
- **Zero wrappers**: The agent must follow `SKILL.md` and run the emitter directly; creating custom shell wrappers violates the scope lock.

### 3. Windows Sandbox Terminal Environments
On Windows hosts under VS Code:
- A sandbox launch using `& '...wxc-exec.exe' '...json'` inside a MINGW64 / Git Bash terminal fails due to a PowerShell/Bash syntax mismatch (`&` is PowerShell's call operator; Bash rejects it as unexpected token syntax).
- **Fix the root cause**: Match the terminal shell to the command dispatcher (run in a fresh PowerShell terminal). Do **not** disable sandboxing to diagnose or work around a shell syntax error.

For every fixture:

```bash
python3 evals/acceptance.py prepare-all
```

This prints one workspace path per fixture:

```text
seeded-py
seeded-ts
seeded-js
seeded-java
seeded-cpp
```

## Commands

### `test <fixture>` / `test-all`

Verifies that the target fixtures compile and that their pre-existing tests pass:

```bash
python3 evals/acceptance.py test-all
```

### `prepare <fixture>`

Creates a temporary workspace and prints its path. The workspace gets:

- one broken fixture
- the current [`skills/sstack/`](../skills/sstack/) orchestrator
- the fourteen peer lens skills
- the fourteen attacker agents in [`agents/`](../agents/)
- `.sstack-host-repo`

It strips [`BUGS.md`](seeded-py/BUGS.md), `.git`, caches, `node_modules/`, `target/`, and
`build/` (the java workspace gets its JUnit launcher re-fetched). The
cold agent must run from the printed directory. `.sstack/` is stripped
too, so a fixture never ships a `config.md` or a lens file: custom
lenses are target-repo content, and seeding one would make the run
prove the pack can read a file the pack wrote.

### `prepare-all`

Runs `prepare` for all five fixtures. This only creates workspaces; it
does not launch five agents.

### `grade <workspace>`

Reads the cold-agent report — resolved from `<workspace>/.sstack/report.json`
(first) or `<workspace>/report.json` — and returns binary pass/fail JSON.
A pass requires at least one confirmed seeded finding with a regression
that was red on the seed and green after the fix.

Example report shape:

```json
{
  "findings": [
    {
      "seed_id": "py-1",
      "lens": "boundaries",
      "surface": "paginate",
      "case": "paginate(items, 0, 3)",
      "oracle": "ValueError: page must be >= 1",
      "observed": "returns []",
      "verdict": "confirmed",
      "repro": "pytest -q tests/test_shop.py",
      "regression": {"file": "tests/test_shop.py", "test": "test_page_zero", "before": "red", "after": "green"}
    }
  ]
}
```

### `replay <workspace>`

Re-verifies each `.sstack/findings/<slug>.json` evidence file from a
finished run with no agent in the loop. Checks integrity first: the
recorded `fingerprint` must equal sha256[:16] of the recorded
`stdout`+`stderr` (a typed-in value grades `fabricated`). Then
re-runs the recorded command and reports `drift` — expected after a
landed fix, evidence against a `refuted` verdict. Exit 0 only when
every evidence file is intact.

### `eval <fixture> [--model <name>] [--agent-cmd "<cmd>"]`

Automated end-to-end evaluation against a model or agent CLI (eval-harness-first pattern).
Prepares the workspace, executes the agent, runs `grade` and `replay`, and records
baseline results:

```bash
# Automated evaluation with an agent CLI:
python3 evals/acceptance.py eval seeded-py --model claude-3-7-sonnet --agent-cmd "claude -p '{prompt}'"

# Or prepare and view the prompt template for manual / subagent execution:
python3 evals/acceptance.py eval seeded-py
```

## Fixtures

| Fixture | Language | Baseline Test Suite | Seeds |
|---|---|---|---|
| [`seeded-py`](seeded-py/) | Python | `pytest -q` | 19 seeds (`py-1`..`py-19`) |
| [`seeded-ts`](seeded-ts/) | TypeScript | `bun run test` / `vitest` | 19 seeds (`ts-1`..`ts-19`) |
| [`seeded-js`](seeded-js/) | JavaScript | `npm test` (`node --test`) | 19 seeds (`js-1`..`js-19`) |
| [`seeded-java`](seeded-java/) | Java | `javac` + JUnit Platform | 19 seeds (`java-1`..`java-19`) |
| [`seeded-cpp`](seeded-cpp/) | C++ | CMake + CTest | 19 seeds (`cpp-1`..`cpp-19`) |

Each fixture ships nineteen seeded defects and a [`BUGS.md`](seeded-py/BUGS.md) answer
key — every fixture covers all 14 lenses under [ADR-0010](../docs/adr/0010-cross-language-fixture-parity.md) parity.
The answer key is never copied into a cold workspace.

Per [ADR-0024](../docs/adr/0024-acceptance-authority-stays-in-acceptance-md.md), [`ACCEPTANCE.md`](ACCEPTANCE.md) is the sole authority of record for graded cold acceptance results, verified dates, and historical run logs.

## Grading and evidence

- [`goldens.jsonl`](goldens.jsonl) contains seeded expectations.
- [`graders/seeded_acceptance.py`](graders/seeded_acceptance.py) contains the deterministic grader.
- [`ACCEPTANCE.md`](ACCEPTANCE.md) records historical cold runs, verified baselines, and known failures.
- Baseline eval artifacts: [`baseline-cold-eval-py.json`](baseline-cold-eval-py.json), [`baseline-cold-eval-ts.json`](baseline-cold-eval-ts.json), [`baseline-cold-eval-js.json`](baseline-cold-eval-js.json), [`baseline-cold-eval-java.json`](baseline-cold-eval-java.json), and [`baseline-cold-eval-cpp.json`](baseline-cold-eval-cpp.json).

A report is not evidence by itself. Evidence requires the report's
verbatim command output plus a red/green regression result. The
workspace preparation command only prepares the run.
