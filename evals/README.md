# Evals

Cold-agent evaluation for sstack.

## Evals vs. Cold Agent

- **Eval harness (`evals/acceptance.py`)**: Deterministic local referee (zero LLM calls). Tests baseline fixtures (`test-all`), prepares decontaminated workspaces (`prepare`), grades findings against goldens (`grade`), and verifies evidence integrity (`replay`).
- **Cold agent**: The live AI model being evaluated. Starts in an isolated sandbox with zero context, no answer key, and no memory; reads `skills/sstack/SKILL.md` cold, executes `/sstack`, and emits evidence.

## Quick start

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
- **No access to sstack repo or `BUGS.md`**: `prepare` strips `BUGS.md` and initializes a clean git baseline. The cold agent must never read the source repo or answer key.
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

### `prepare <fixture>`

Creates a temporary workspace and prints its path. The workspace gets:

- one broken fixture
- the current `skills/sstack/` orchestrator
- the fourteen peer lens skills
- the fourteen attacker agents
- `.sstack-host-repo`

It strips `BUGS.md`, `.git`, caches, `node_modules/`, `target/`, and
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
`evals/baseline-<model>.json`:

```bash
# Automated evaluation with an agent CLI:
python3 evals/acceptance.py eval seeded-py --model claude-3-7-sonnet --agent-cmd "claude -p '{prompt}'"

# Or prepare and view the prompt template for manual / subagent execution:
python3 evals/acceptance.py eval seeded-py
```

## Fixtures

| Fixture | Language | Baseline | Cold acceptance |
|---|---|---|---|
| `seeded-py` | Python | `pytest -q` | PASS — graded 2026-09-27, 16/16 named runs |
| `seeded-ts` | TypeScript | `bun run test` | PASS — graded 2026-09-27 |
| `seeded-js` | JavaScript | `npm test` | PASS — graded 2026-09-27 |
| `seeded-java` | Java | `javac` compile | PASS — graded 2026-09-27 |
| `seeded-cpp` | C++ | CMake + CTest | PASS — graded 2026-09-27 |

Each fixture ships sixteen seeded defects and a `BUGS.md` answer
key — every fixture covers all 14 lenses under ADR-0010 parity.
All five fixtures carry full 16/16 named verifying run coverage
(see `ACCEPTANCE.md`). The answer key is never copied into a cold workspace.

## Grading and evidence
- `goldens.jsonl` contains seeded expectations.
- `graders/seeded_acceptance.py` contains the deterministic grader.
- `ACCEPTANCE.md` records historical cold runs and known failures.

A report is not evidence by itself. Evidence requires the report's
verbatim command output plus a red/green regression result. The
workspace preparation command only prepares the run.
