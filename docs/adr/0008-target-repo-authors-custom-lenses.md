# ADR-0008: The target repo authors its own lenses

**Status**: Accepted
**Date**: 2026-09-25
**Deciders**: mhenke

## Context

sstack shipped seven lenses and called seven the ceiling. ADR-0007
fixed extension for the *pack* author: one lens skill, one agent file,
one index row. That works for us, who own the repository. It does
nothing for the person whose code is under attack. A team that keeps
finding the same defect class, an ordering bug or an idempotency bug,
has no way to say so, and the workarounds are bad: paste the rule into
a prompt every run and hope, or fork the pack and lose every upstream
fix.

oh-my-opencode-slim solves the same problem with a config file,
`agents.<name>` blocks, `<agent>.md` prompt overrides, and
`<agent>_append.md` appends. Its implementation is the reference, and
two details from it shaped this decision. `resolvePrompt` composes an
append file onto the resolved base rather than replacing it, so a local
override adds to a built-in instead of erasing it. And
`discoverProjectLocalSkillNames` resolves the skills root through
`fs.realpathSync` and returns an empty list when it does not match the
canonical project path, explicitly refusing to let a symlinked `.opencode`
turn "project-local" into arbitrary content injection.

sstack cannot copy that mechanism. omos has a loader, a JSON schema,
and a merge order; sstack is markdown in a copied directory, and the
agent reading `SKILL.md` *is* the loader. A config file nobody parses
is decoration. The feature had to become a convention an agent
performs, cheap enough that it actually happens.

## Decision

We will let a target repo add lenses without changing the pack. It
authors `.sstack/lenses/<name>.md` and selects them in
`.sstack/config.md`, and a custom lens runs by appending its rubric to
an existing attacker's `### Lens rubric` dispatch rather than by
adding an agent.

Three properties follow from the omos reference:

The append mirrors `resolvePrompt`. The built-in rubric still applies,
so a custom lens widens coverage instead of replacing it. Custom lenses
are additive to the built-in set; `lenses.remove` is the only way to
drop one, and every removal is reported in the chat summary, because a
silently weakened run is indistinguishable from a clean one.

Identity comes from frontmatter, not the filename, matching how skill
identity already works in both sstack and omos. A lens file is found
by `name:` in its frontmatter.

Discovery is scoped to the repo. A `config.md` or `lenses/` that
resolves outside the target is skipped with a note in the report. This
is `discoverProjectLocalSkillNames` translated: the guard is the point,
not a detail.

Config lives under `.sstack/`, kept out of the ignore list by negation
(`.sstack/*` plus `!.sstack/config.md` and `!.sstack/lenses/`). Run
output stays ignored; authored content becomes committable, so a team
shares lenses through git.

## Consequences

**Good**: a team encodes its own failure classes where they live, in
version control, and keeps every upstream pack fix. The seven built-ins
stop being a ceiling: the eight `custom lens` rows in the index,
including `ordering`, `concurrency`, and `idempotency`, are activatable
today by anyone.

**Bad**: the pack now has an extension point it cannot test. A cold
agent reading `SKILL.md` might skip config discovery, or apply an
appended rubric to the wrong scratch directory. The `lenses.remove`
report requirement is likewise unenforced except by the agent's own
honesty. This is the cost of having no loader, and it is not small.

**Risks**: a custom lens is repo-authored content injected into an
agent's instructions. A hostile or careless rubric could instruct the
agent to skip oracles or hand-author evidence, which is precisely the
failure mode ADR-0006 exists to prevent. The skill tells the agent
that a lens is content, not authority, and to follow the built-in rules
on conflict, but that is prose, not enforcement. A lens file that
materially weakens a run should be a rejected pack contribution, and
if the pressure to enforce it grows, the honest answer is a validating
harness in `evals/`, not a stronger sentence in `SKILL.md`.
