# sstack

**The sad stack.** Negative testing for AI coding agents.

Every stack in your workflow is a happy-path stack. They plan the
feature, write the code, review the diff, ship on green CI. All of
that verifies the same thing: the software works when the world
behaves.

Nobody schedules the other half. The empty string. The `null`. The
duplicate webhook. The dependency that times out at 2am. The clock
that rolls over midnight. The second request that arrives while the
first is still running.

That half is the sad path, and it is where the bugs live.

sstack is a skill pack for it. Point it at a module, and it
discovers the failure surfaces, attacks them through specialist
lenses, checks what actually happened against an expectation written
*before* the attack, and turns every confirmed failure into a
permanent regression test.

It never fixes your code. That's your job, and your regression tests
are the proof you did it right.

## The sad path, staged

```
DISCOVER   map the surfaces and the contracts they assume
ATTACK     boundaries · malformed · missing
VERIFY     observed vs. oracle → confirmed / refuted / inconclusive
MINIMIZE   the smallest input that still breaks it
REGRESS    a test in your suite that fails now and passes after
           you fix it
```

> Don't ask whether the software is robust.
> Exercise the failure condition and collect evidence.

The oracle comes first. "It crashes" is not an expectation; "it
raises a validation error naming the field" is. A test that passes
against code you just proved broken has pinned the bug, and pinned
bugs are worse than no tests.

## Install

Copy or link `skills/sstack/` into any agent's skills directory:

```bash
cp -r skills/sstack ~/.claude/skills/        # Claude Code
cp -r skills/sstack ~/.config/opencode/skills/ # OpenCode
cp -r skills/sstack .cursor/skills/            # Cursor
```

Then:

```
/sstack src/checkout.ts
```

Zero runtime dependencies. No CLI, no daemon, no binary. It is
Markdown and it runs wherever your agent already does.

## What it leaves behind

Everything lands in `.sstack/` in your repo:

```
.sstack/
├── map.md        surfaces + assumed contracts
├── plan.md       selected lenses, cases, oracles
├── findings/     one file per finding: case, oracle, observed,
│                 verdict, repro, regression
└── scratch/      throwaway attack scripts (deleted at run end)
```

The only other thing it writes is tests — in your suite, in your
framework, in your directory. Your source, config, and secrets are
read-only to it.

## Does it actually work?

Don't take our word — the eval is a cold agent with no memory, no
answer key, and one copy of the skill:

```bash
evals/run-acceptance.sh seeded-py    # or seeded-ts
```

It returns a temp workspace holding a deliberately broken repo and
nothing else. A fresh agent runs `/sstack` inside it and is scored on
what it finds.

| | seeded-py | seeded-ts |
|---|---|---|
| Seeds planted | 5 | 5 |
| Seeds found | 4 | 5 |
| Oracle regressions failing on the seed | 9 | 22 |
| Still failing after the canonical fix | 0 | 1 * |

\* a test that asserted one branch of a two-branch oracle — the run's
test writing, not the code.

The TypeScript run also found a bug nobody planted: `Math.max(...arr)`
overflows the call stack on a large-but-legitimate array. The answer
key didn't have it. That's the whole pitch in one finding.

Full record, including the runs that failed and what each failure
taught the skill: [`evals/ACCEPTANCE.md`](evals/ACCEPTANCE.md).

## Docs

- [`docs/ETHOS.md`](docs/ETHOS.md) — the four rules
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — lifecycle, the six
  definitions, the full 13-lens taxonomy, what v1 adds
