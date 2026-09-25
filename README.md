# sstack

> This one goes looking for the not-happy test cases, the ones
> nobody writes tests for on purpose:
>
> - the empty string
> - the `null`
> - the duplicate webhook
> - the dependency that dies at 2am
> - the second request that lands while the first is still running

**sad stack** · negative testing for AI coding agents

gstack, pstack, sstack. Same suffix, same shape: a `SKILL.md` your
agent reads, a directory you copy in, a slash command you type. The
family ships features and reviews diffs. sstack finds the ways your
software fails, writes a test for each one that fails today, and
applies the minimal fix that turns it green.

> Don't ask whether the software is robust.
> Exercise the failure condition, write the test that proves it, and
> fix it.

## The not-happy cases, staged

```mermaid
flowchart TD
    D["Discover\nmap surfaces + contracts"] --> A["Attack\n7 lenses"]
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

That installs the skills. It leaves out the seven
`agents/sstack-*-attacker.md` files, which `npx skills add` does not
carry; the install prompt below covers those. It also registers
`/sstack` in Claude Code only. Cursor, Windsurf, Codex, and the rest
have no command to install: open the skill directory in your editor
and ask for it in your own words.

### Attacker agent install prompt

Paste into your agent:

```text
Copy the seven agents/*.md files from https://github.com/mhenke/sstack into ~/.agents/agents/ (the .agents Protocol hub; create it if missing), plus a VS Code copy in ~/.copilot/agents/ renamed <name>.agent.md.
```

Claude Code: also copy them to `~/.claude/agents/`. Per-repo VS Code:
`.github/agents/`.

### Running it

The command takes what to test. In Claude Code:

```text
/sstack src/checkout.ts
```

The argument is the scope: a file, a directory, a module, a package,
or a URL. sstack reads that scope, maps the surfaces inside it, and
works only within what you named. A narrow scope keeps the run small;
a directory keeps it broad.

In an agent without slash commands, say the same thing in a prompt:
"use the sstack skill on src/checkout.ts".

No CLI, no daemon, no binary, nothing to install. The pack is
Markdown plus one stdlib-only Python script the agent runs to write
its own evidence; where Python is absent, the same evidence is two
shell commands (see [Evidence](#evidence)).

### Custom lenses

The seven shipped lenses are a floor. A repo can add its own under
`.sstack/lenses/`, and sstack picks them up on the next run with no
change to the pack:

```
.sstack/
├── config.md        lenses.add / lenses.remove
└── lenses/
    └── ordering.md  name, description, applies-when, then the rubric
```

```markdown
---
name: ordering
description: Operations applied out of sequence.
applies-when: operations whose order changes the result
---

# Ordering lens rubric

Case-generation heuristics, oracle patterns, worked examples, and
when-not-to-apply guidance.
```

```markdown
lenses.add: ordering, idempotency
lenses.remove: ownership
```

`lenses.add` runs your lenses alongside the built-ins, not instead of
them, and `lenses.remove` is reported in the summary so a dropped lens
cannot hide. Both files are committable: run output is ignored, so a
team's lenses travel with the repo they protect.

### For contributors

`docs/`, `evals/`, and the acceptance record live only in a git
checkout: they are the contributor lane, the place the evidence
gets produced and audited.

### Optional lifecycle skills

Install only the skills sstack uses across its lifecycle:

```bash
npx skills@latest add cursor/plugins \
  --skill principle-attack-the-premise \
  --skill create-verification-skill \
  --skill maintain-verification-skill \
  --skill principle-test-behavior-not-implementation \
  --skill principle-fix-root-causes \
  --global -y
```

`-y` answers the interactive agent picker. Without it, a non-TTY
run prints "Nothing was installed" and exits 0.

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

## Evidence

Every finding carries a fingerprint of the output it was judged on:
the first 16 hex characters of `sha256(stdout + stderr)`. The
`replay` auditor recomputes it from the recorded bytes, so a
fingerprint that could not have come from that output is detectable.

Where Python is available, the shipped script does the whole thing:
it runs the repro, captures the output, hashes it, writes the
finding, and rebuilds the report.

```bash
echo "$FINDING_JSON" | python3 skills/sstack/scripts/emit_findings.py \
  --workspace "$(pwd)" --fixture my-fixture
```

Where Python is absent, two shell commands produce the same evidence:

```bash
"$REPRO" > o.txt 2> e.txt; code=$?
fp=$(cat o.txt e.txt | sha256sum | cut -c1-16)   # macOS: shasum -a 256
```

Write the streams to files. A `$(...)` substitution strips trailing
newlines, so the hash would cover different bytes than the evidence
records, and every fingerprint would read as fabricated.

## Languages

The process is language-agnostic. The evidence is not. Python,
TypeScript, JavaScript, Java, and C++ each have a seeded repo under
`evals/` with a happy-path baseline, and the table below shows how
far each one has been carried.

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
nothing else. Start a fresh agent session with no memory of this
repository, point it at that directory, and let it work:

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
| seeded-py | 7 | PASS; 5/5 seeds content-matched (ColdPy-5), 12/12 evidence replay intact. The state and ownership seeds have not had a full cold pass yet |
| seeded-ts | 5 | PASS; 5/5 seeds content-matched, 19/19 evidence replay intact (rerun) |
| seeded-js | 5 | PASS; 5/5 seeds content-matched, 12/12 evidence replay intact (rerun) |
| seeded-java | 5 | PASS; 3/5 seeds content-matched, 7/7 evidence replay intact (rerun on current text) |
| seeded-cpp | 5 | PASS; 3/5 seeds content-matched, 13/13 evidence replay intact (rerun) |

Each row is the most recent cold pass for that fixture, and only the
seeded-py one has been re-run since the current lens set landed.
Earlier waves' failures, including fabricated fingerprints and
regressions that never landed, are in the run histories.

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
