# sstack

A structured negative-testing skill pack for AI coding agents.
sstack discovers failure surfaces, attacks them through specialist
lenses, verifies observed behavior against a pre-declared oracle,
minimizes confirmed failures, and turns them into permanent
regression tests.

> Don't ask whether the software is robust. Exercise the failure
> condition and collect evidence.

## Install (any agent that reads skills)

Copy or link `skills/sstack/` into your agent's skills directory
(e.g. `~/.claude/skills/`, `~/.config/opencode/skills/`,
`.cursor/skills/`). Then invoke `/sstack <target>`.

## What it does

1. **Discover** — map surfaces and assumed contracts
2. **Attack** — boundaries / malformed / missing lenses, oracle
   written before each case
3. **Verify** — confirmed / refuted / inconclusive; confirmed
   findings must reproduce
4. **Minimize** — smallest repro
5. **Regress** — permanent test in your repo's suite

Artifacts land in `.sstack/` (`map.md`, `plan.md`, `findings/`).
The skill never edits your source code.

## Docs

- `docs/ETHOS.md` — the four rules
- `docs/ARCHITECTURE.md` — lifecycle, six definitions, full lens
  taxonomy, v1 roadmap

## Evals

`evals/seeded-py` and `evals/seeded-ts` contain deliberately buggy
repos (answer keys in `BUGS.md`). Acceptance: a cold agent given
only the skill finds seeds and lands regression tests that fail on
the buggy code and pass after the canonical fix.

    evals/run-acceptance.sh seeded-py   # prints temp dir sans BUGS.md
