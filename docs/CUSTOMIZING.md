# Customizing sstack

Everything sstack does is customizable the same way: drop a file in
your own tree, named with an `sstack-` prefix. The next run picks it
up. There is no config file to edit, no plugin to register, and no
file of ours to modify.

- [The one rule](#the-one-rule)
- [Where files go](#where-files-go)
- [Add a lens](#add-a-lens)
- [Add an agent](#add-an-agent)
- [Stages are not extensible](#stages-are-not-extensible)
- [Skip a shipped lens](#skip-a-shipped-lens)
- [When the two halves do not match](#when-the-two-halves-do-not-match)
- [What customization cannot do](#what-customization-cannot-do)

## The one rule

The `sstack-` prefix is the entire contract. sstack reads files
carrying it and ignores everything else in your tree.

| you want to | drop | it is read by |
|---|---|---|
| add an attack angle | `sstack-<lens>/SKILL.md` | Attack, at `### Lens rubric` |
| add a worker | `sstack-<lens>-attacker.md` | Attack, dispatched by name |

Two nouns, and they are not interchangeable:

- A **stage** is a step in the process. There are seven and they are
  fixed: Discover, Attack, Verify, Minimize, Test, Fix, Learn. Only
  Attack uses lenses.
- A **lens** is what you attack with. Seven ship: `boundaries`,
  `malformed`, `missing`, `ownership`, `exceptional-conditions`,
  `resource-exhaustion`, `state`. A lens and its agent ship paired,
  which is why they read as one thing. They are not: the lens is the
  strategy, the agent is the worker.
- An **agent** is the subprocess that runs one lens. It receives the
  surface map, the lens rubric, and the report format in its message.

## Where files go

Use the skills and agents directories your tools already scan. The
`.agents` convention is the portable one:

```
<your-repo>/.agents/skills/     your lenses
<your-repo>/.agents/agents/     your attackers
~/.agents/skills/               the same, for every repo you run
~/.agents/agents/
```

Project wins over global, the rule OpenCode, Claude Code, and VS Code
already apply to skills. A lens in the global tree is available
everywhere you run sstack; one in the project tree travels with the
code it protects and reaches a teammate by commit.

Other hosts use their own directories for the same files:

| host | agents | notes |
|---|---|---|
| `.agents` | `~/.agents/agents/`, `.agents/agents/` | portable default |
| Claude Code | `~/.claude/agents/`, `.claude/agents/` | |
| VS Code Copilot | `~/.copilot/agents/*.agent.md` | `.github/agents/` per repo |
| OpenCode | `~/.config/opencode/agent/`, `.opencode/agent/` | |

**Never put your files in `skills/` or `agents/` at the top of this
pack.** Those directories belong to sstack and are replaced wholesale
when you update, so anything you put there is lost.

## Add a lens

A lens is a skill. Write an ordinary `SKILL.md`:

```markdown
---
name: sstack-ordering
description: Operations applied out of sequence.
applies-when: two operations on one resource
disable-model-invocation: true
---

# Ordering lens rubric

## Case-generation heuristics

Call the subject twice in the reverse of its documented order...

## Oracle patterns

- The documented result, or a named error...

## Worked example

Python `reserve(seat)` then `release(seat)` then `reserve(seat)`.

## When not to apply

The surface is a pure query with no ordering guarantee.
```

Required:

1. `name: sstack-<lens>`, and a `description` naming the failure
   class it attacks.
2. `disable-model-invocation: true`, as all eight shipped skills
   carry. A lens is pasted into a dispatch by sstack, never
   auto-loaded by your tool matching its description, because a rubric
   with no target yet means nothing. Without the flag your tool may
   load it at the wrong moment.
3. A rubric body: case-generation heuristics, oracle patterns, worked
   examples, and when-not-to-apply guidance. The shipped lenses are
   the best reference.

`applies-when` is optional and narrows the lens to surfaces it is
for, so one about write ordering does not fire on a read-only
endpoint. Without it the lens runs on every mapped surface, which is
usually what you want.

The `<lens>` part of the name becomes a filename under
`.sstack/findings/`, so keep it to letters, digits, dot, dash, and
underscore. The emitter rejects anything else rather than writing
outside the workspace.

Your lens runs on the same surfaces as the built-ins, in the same
Report format, and inherits every rule in the skill: oracle before
attack, real execution, evidence through the emitter. Its findings
carry `lens: ordering` and its probes land in
`.sstack/scratch/ordering/`.

It needs no agent. It runs on a shipped attacker whose discipline fits,
usually `sstack-boundaries-attacker`, with your rubric appended after
the built-in one, so the lens widens coverage rather than replacing it.

## Add an agent

Only when the worker itself must behave differently, not just its
attack angle. Write `sstack-<lens>-attacker.md` into an agents
directory, paired 1:1 with a lens of the same name.

Copy the shape of a shipped one
(`agents/sstack-boundaries-attacker.md`): a `name` and `description`
in frontmatter, then the contract. The dispatch pastes `### Workspace
root`, `### Surface map`, `### Lens rubric`, and `### Report format`,
so your file is the fallback when no rubric arrives, not the carrier.

Keep it stateless about the repository. No repo names, no lens paths,
nothing correct for one target and wrong for another. Everything
repo-specific arrives pasted, which is what lets one global agent
serve every repo. The seven shipped attackers are stateless for
exactly this reason.

## Stages are not extensible

A stage is not a file. It is the orchestrator's own text, so there is
nothing to append to and no filename that could select one. The seven
stages are fixed: they can be neither added, removed, nor extended.

If a stage looks wrong for your repo, ship a **lens**. A lens runs
over every mapped surface at Attack, which covers the common case of
needing an angle of attack the built-ins miss, without pretending to
change the process itself.

## Skip a shipped lens

Name it in the chat, or put one directive per line in
`.sstack/config.md` in your repo:

```markdown
lenses.remove: ownership
```

Skipped lenses are reported in the run summary, because a quietly
weakened run is indistinguishable from a clean one. That file is run
input created by you, not pack content, so editing it costs no
updates.

## When the two halves do not match

A lens and an agent pair by name, and either half can appear alone.

| lens | agent | what runs |
|---|---|---|
| yes | yes | your agent, your rubric |
| yes | no | a shipped attacker, your rubric appended |
| no | yes | nothing — the run reports the unused file by name |
| no | no | nothing, which is the ordinary case |

An agent with no lens is the one to watch. It is not an error, but it
is reported, because a worker nobody called is a customization that
silently does nothing, and a quietly weaker run reads as a clean one.

## What customization cannot do

- **It cannot change the process.** The seven stages are fixed and not
  extensible. Use a lens to add an angle of attack instead.
- **It cannot weaken the contract.** Custom content is strategy, not
  authority. A lens that tells the agent to skip
  oracles, accept unexecuted cases, or hand-author evidence is
  ignored on conflict, and the conflict is reported.
- **It cannot reach outside the target repo.** A file that resolves
  elsewhere, including through a symlinked skills directory, is
  skipped with a note in the report. A run takes attack strategy only
  from paths scoped to the repo under test.
- **It cannot add an 8th shipped lens to the index.** The index in
  `skills/sstack/SKILL.md` lists what the pack provides. Your lens
  runs alongside it without an index row.

## Reference

- [`docs/adr/0008-user-extends-by-naming-a-file.md`](adr/0008-user-extends-by-naming-a-file.md)
  — why this design, and what it costs
- [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) — the eight definitions
- [`AGENTS.md`](../AGENTS.md) — contributor rules
