# Evals

Cold-agent evaluation for sstack. The repo ships a prepared fixture
set, a deterministic grader, and one Python entry point. It does not
launch agents itself because agent APIs differ by host.

## Quick start

From the repository root:

```bash
# Build one isolated workspace. The command prints its path.
python3 evals/acceptance.py prepare seeded-py

# Launch a fresh cold agent in the printed directory.
# Run /sstack against the fixture.

# Score the JSON report.
python3 evals/acceptance.py grade path/to/workspace
```

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
- the six peer lens skills
- the six attacker agents
- `.sstack-host-repo`

It strips `BUGS.md`, `.git`, caches, `node_modules/`, `target/`, and
`build/` (the java workspace gets its JUnit launcher re-fetched). The
cold agent must run from the printed directory.

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
finished run with no agent in the loop: re-runs the recorded command,
compares exit code and output fingerprint against the record. Exit 0
only when every finding replays verified.

## Fixtures

| Fixture | Language | Baseline | Cold acceptance |
|---|---|---|---|
| `seeded-py` | Python | `pytest -q` | stale historical evidence |
| `seeded-ts` | TypeScript | `bun run test` | stale historical evidence |
| `seeded-js` | JavaScript | `npm test` | pending |
| `seeded-java` | Java | `javac` compile | pending |
| `seeded-cpp` | C++ | CMake + CTest | pending |

Each fixture contains five seeded defects and a `BUGS.md` answer key.
The answer key is never copied into a cold workspace.

## Grading and evidence

- `goldens.jsonl` contains seeded expectations.
- `graders/seeded_acceptance.py` contains the deterministic grader.
- `drift-suite.yaml` freezes the current eval configuration.
- `baseline-base.json` is the promotion gate and is currently
  `not_run`.
- `ACCEPTANCE.md` records historical cold runs and known failures.

A report is not evidence by itself. Evidence requires the report's
verbatim command output plus a red/green regression result. The
workspace preparation command only prepares the run.
