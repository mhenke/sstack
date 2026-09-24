# sstack

**sad stack** · negative testing for AI coding agents

gstack, pstack, sstack. Same suffix, same shape: a `SKILL.md` your
agent reads, a directory you copy in, a slash command you type. The
family ships features and reviews diffs. This one goes looking for
the not-happy test cases, the ones nobody writes tests for on
purpose:

- the empty string
- the `null`
- the duplicate webhook
- the dependency that dies at 2am
- the second request that lands while the first is still running

It finds the ways your software fails and hands you a test for each
one, failing today and passing after you fix it. Fixing it stays your
job. The test is how you know you did it.

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
expectation; "it raises a validation error naming the field" is. A
test that passes against code you just proved broken has pinned the
bug, and a pinned bug is worse than no test at all.

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

Zero runtime. No CLI, no daemon, no binary. It is Markdown, and it
runs wherever your agent already does.

## Languages

The process is language-agnostic. The evidence is not.

**Proven** - Python and TypeScript. Each has a seeded repo, a clean
cold run, and a negative control. See the table below.

**Works by inference, unproven** - JavaScript, Java, C++, and
everything else. The lifecycle is language-independent, and the agent
brings its own knowledge of the target's idioms, but no run has
measured it. JavaScript is the closest to proven: the `malformed` and
`missing` lenses already reason about erased runtime types, which is
the JavaScript condition, so it mostly needs a seeded repo. C++ is the
furthest - the `missing` lens has no clean analogue there, because
there is no null, only undefined behavior.

`ROADMAP.md` has the per-language plan. If you are about to point this
at Java or C++ and the answer matters, run the eval first.

## What it leaves behind

```
.sstack/
├── map.md        surfaces + assumed contracts
├── plan.md       lenses, cases, oracles
├── findings/     one per finding: case, oracle, observed,
│                 verdict, repro, regression
└── scratch/      throwaway attack scripts (gone at run end)
```

Plus tests, in your suite, in your framework, in your directory.
Your source, config, and secrets stay read-only.

## Is it actually any good?

The eval is a cold agent with no memory, no answer key, one copy of
the skill:

```bash
evals/run-acceptance.sh seeded-py    # or seeded-ts
```

It hands back a temp workspace with a deliberately broken repo and
nothing else. A fresh agent runs `/sstack` inside it and gets scored
on what it finds.

| | seeded-py | seeded-ts |
|---|---|---|
| Bugs planted | 5 | 5 |
| Bugs found | 4 | 5 |
| Regression tests failing on the bug | 9 | 22 |
| Still failing after the fix | 0 | 1 * |

\* one test asserted a single branch of a two-branch oracle, which
was the run's test writing rather than the code.

The TypeScript run turned up a bug nobody planted: `Math.max(...arr)`
overflows the call stack on a large but legitimate array. It is not
in the answer key.

Full record, including the runs that failed and what each one taught
the skill: [`evals/ACCEPTANCE.md`](evals/ACCEPTANCE.md).

Those numbers are from a run before the last two rounds of guardrail
fixes. The skill text has changed since; re-running is the only way to
refresh them.

## Docs

- [`docs/ETHOS.md`](docs/ETHOS.md): the four rules
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): lifecycle, the six
  definitions, the 13-lens taxonomy, what v1 adds
- [`docs/adr/`](docs/adr/README.md): decision records
- [`docs/TOOLS.md`](docs/TOOLS.md): negative-testing tools by language
- [`docs/RESEARCH.md`](docs/RESEARCH.md): the research behind the
  decisions, and what is still open
