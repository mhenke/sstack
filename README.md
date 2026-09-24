# sstack

**sad stack** · negative testing for AI coding agents

gstack. pstack. sstack. Same suffix, same shape — a `SKILL.md` your
agent reads, a directory you copy in, a slash command you type. The
family ships features and reviews diffs. This one is the sad member
of the family: it goes looking for the **not-happy test cases**.

The empty string. The `null`. The duplicate webhook. The dependency
that dies at 2am. The second request that lands while the first is
still running. Nobody writes tests for those on purpose — that's the
job sstack was named for.

It finds the ways your software fails, proves each one with a test
that fails today and passes after you fix it, and hands you the
evidence. It won't fix your code — it's an auditor, not a
therapist. The repair is yours; the proof it worked is a green test.

> Don't ask whether the software is robust.
> Exercise the failure condition and collect evidence.

## The not-happy cases, staged

```
DISCOVER   map the surfaces and the contracts they quietly assume
ATTACK     boundaries · malformed · missing
VERIFY     observed vs. oracle → confirmed / refuted / inconclusive
MINIMIZE   the smallest input that still breaks it
REGRESS    a test in your suite that fails now, passes after the fix
```

The oracle is written *before* the attack. "It crashes" isn't an
expectation; "it raises a validation error naming the field" is. And
a test that passes against code you just proved broken has pinned the
bug — pinned bugs are worse than no tests.

## Install

Drop it in any agent's skills directory:

```bash
cp -r skills/sstack ~/.claude/skills/         # Claude Code
cp -r skills/sstack ~/.config/opencode/skills/ # OpenCode
cp -r skills/sstack .cursor/skills/            # Cursor
```

```
/sstack src/checkout.ts
```

Zero runtime. No CLI, no daemon, no binary. Markdown all the way
down — it runs wherever your agent already does.

## What it leaves behind

```
.sstack/
├── map.md        surfaces + assumed contracts
├── plan.md       lenses, cases, oracles
├── findings/     one per finding: case, oracle, observed,
│                 verdict, repro, regression
└── scratch/      throwaway attack scripts (gone at run end)
```

Plus tests — in your suite, your framework, your directory. Your
source, config, and secrets stay read-only.

## Is it actually any good?

The eval is a cold agent with no memory, no answer key, one copy of
the skill:

```bash
evals/run-acceptance.sh seeded-py    # or seeded-ts
```

It hands back a temp workspace with a deliberately broken repo and
nothing else. A fresh agent runs `/sstack` inside it, and gets scored
on what it finds.

| | seeded-py | seeded-ts |
|---|---|---|
| Bugs planted | 5 | 5 |
| Bugs found | 4 | 5 |
| Regression tests failing on the bug | 9 | 22 |
| Still failing after the fix | 0 | 1 * |

\* one test asserted a single branch of a two-branch oracle — the
run's test writing, not the code.

The TypeScript run turned up a bug nobody planted: `Math.max(...arr)`
overflows the call stack on a large-but-legitimate array. Not in the
answer key. That's the whole pitch in a single finding.

Full record — including the runs that failed and what each one taught
the skill: [`evals/ACCEPTANCE.md`](evals/ACCEPTANCE.md).

## Docs

- [`docs/ETHOS.md`](docs/ETHOS.md) — the four rules
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — lifecycle, the six
  definitions, the 13-lens taxonomy, what v1 adds
