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

It finds the ways your software fails, writes a test for each one
that fails today, and applies the minimal fix that turns it green.

> Don't ask whether the software is robust.
> Exercise the failure condition, write the test that proves it, and
> fix it.

## The not-happy cases, staged

```mermaid
flowchart TD
    D["Discover\nmap surfaces + contracts"] --> A["Attack\n6 lenses"]
    A --> V["Verify\nobserved vs. oracle"]
    V --> M["Minimize\nsmallest repro"]
    M --> T["Test\nwrite regression → red"]
    T --> F["Fix\napply minimal fix → green"]
    F --> L["Learn\nrecord failure class"]
    L --> R["Report"]
```

The oracle is written *before* the attack. "It crashes" isn't an
expectation; "it raises a validation error naming the field" is. A
test that passes against code you just proved broken has pinned the
bug, and a pinned bug is worse than no test at all.

## Install

```bash
npx skills@latest add mhenke/sstack
```

Then:

```
/sstack src/checkout.ts
```

Zero runtime. No CLI, no daemon, no binary. It is Markdown, and it
runs wherever your agent already does.

### Optional lifecycle skills

Install only the skills sstack uses across its lifecycle:

```bash
npx skills@latest add cursor/plugins \
  --skill principle-attack-the-premise \
  --skill create-verification-skill \
  --skill maintain-verification-skill \
  --skill principle-test-behavior-not-implementation \
  --skill principle-fix-root-causes \
  --global
```

Lifecycle mapping:

- Discover → `principle-foundational-thinking`, `principle-model-the-domain`, `principle-exhaust-the-design-space`, `create-verification-skill`, `maintain-verification-skill`
- Attack → `principle-attack-the-premise`, `principle-boundary-discipline`, `principle-exhaust-the-design-space`
- Verify → `principle-prove-it-works`, `principle-outcome-oriented-execution`
- Minimize → `principle-minimize-reader-load`, `principle-sequence-verifiable-units`
- Test → `principle-test-behavior-not-implementation`, `principle-encode-lessons-in-structure`
- Fix → `principle-fix-root-causes`, `principle-subtract-before-you-add`, `principle-type-system-discipline`
- Run-end → `principle-prove-it-works`, `principle-outcome-oriented-execution`, `principle-guard-the-context-window`

All are optional. If they are not installed, sstack falls back to its
built-in prose and the target's documentation, types, and call sites.

## Languages

The process is language-agnostic. The evidence is not.

**Supported fixture coverage** - Python, TypeScript, JavaScript, Java,
and C++. Each has a seeded repo under `evals/` and a happy-path
baseline. Only Python and TypeScript have recorded cold-run
acceptance; the other three are baseline coverage, not proof.

The lifecycle is language-independent. JavaScript, Java, and C++
remain unproven for cold-agent acceptance until their runs are
recorded. `ROADMAP.md` tracks that gap.

## What it leaves behind

```
.sstack/
├── map.md        surfaces + assumed contracts
├── plan.md       lenses, cases, oracles
├── learn/        failure classes for the next run
├── findings/     one .md and one .json per finding
└── scratch/      throwaway attack scripts (gone at run end)
```

Plus regression tests and fixes. Tests land in your suite; fixes land
in your source, scoped to the minimal change that satisfies the
oracle. Config and secrets stay read-only.

## Is it actually any good?

The eval is a cold agent with no memory, no answer key, and the
current skills plus agents:

```bash
python3 evals/acceptance.py prepare seeded-py
```

It hands back a temp workspace with a deliberately broken repo and
nothing else. Launch your host's cold agent in that directory, then:

```bash
python3 evals/acceptance.py grade path/to/workspace
```

`prepare-all` creates workspaces for all five fixtures. `grade`
matches findings to the answer key by content, not by the labels an
agent guesses; `replay` re-audits each finding's evidence file with
the agent out of the loop. The entry point never launches an agent or
reads `BUGS.md`; cold-agent dispatch stays outside the repository.

| Fixture | Seeds | Current cold evidence |
|---|---|---|
| seeded-py | 5 | PASS; Learn-run-2 matched 5/5 seeds, 10/10 evidence replay intact |
| seeded-ts | 5 | PASS; 4/5 seeds content-matched, 7/7 evidence replay intact (rerun) |
| seeded-js | 5 | PASS; 5/5 seeds content-matched, 12/12 evidence replay intact (rerun) |
| seeded-java | 5 | PASS; 3/5 seeds content-matched with landed regressions |
| seeded-cpp | 5 | FAIL; 7 confirmed with replayable evidence, but regression files never landed — caught by landed-check |

Historical clean evidence remains `9979718`: Python 4/5 seeds with 9
red→green regressions, TypeScript 5/5 plus one unseeded real bug with
34/35 flips. That evidence is stale for the current skill text.

Full record, including the runs that failed and what each one taught
the skill: [`evals/ACCEPTANCE.md`](evals/ACCEPTANCE.md).

## Docs

- [`docs/ETHOS.md`](docs/ETHOS.md): the four rules
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): lifecycle, the six
  definitions, the 15-lens taxonomy, what v1 adds
- [`docs/adr/`](docs/adr/README.md): decision records
- [`docs/TOOLS.md`](docs/TOOLS.md): negative-testing tools by language
- [`docs/RESEARCH.md`](docs/RESEARCH.md): the research behind the
  decisions, and what is still open
