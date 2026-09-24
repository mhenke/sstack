# ADR-0002: Content-only, agent-agnostic skill pack

**Status**: Accepted
**Date**: 2026-09-23
**Deciders**: Mike Henke

## Context

Three options were on the table for what sstack ships:

- a **host plugin** (Cursor, OpenCode, one vendor)
- a **CLI or runner** that executes evidence collection
- a **portable skill pack**: Markdown any agent can load, with the
  agent running real commands itself

The plugin route ties the product to one harness and its plugin
format. The CLI route reintroduces exactly the infrastructure gstack
carries (a Bun binary, a daemon, an evidence schema) that the whole
design was trying to avoid, and it is the thing that makes a
"deterministic helpers" layer expensive to maintain.

The deciding question was what "never accept an agent's claim as
evidence" actually requires. It requires the agent to run the real
command and quote the real output, not a bespoke binary that does it
for them. That is achievable in pure prose.

Prior art converged on the same shape: impeccable ships one skill
with `references/` per command and adds a `scripts/` evidence layer
only later, additively; pstack ships one launcher with on-demand
content files.

## Decision

sstack v0 is a portable skill pack: one entry `SKILL.md` plus
on-demand `references/` lens files, in the agent-skills format. No
CLI, no daemon, no binary, no runtime dependencies. The agent runs
real commands and quotes real output; evidence is loose markdown
under `.sstack/`. The pack is host-agnostic and copied into any
agent's skills directory.

sstack is an **audit, not a refactor**: it writes tests and `.sstack/`
artifacts and never the target's source, config, or secrets.

## Consequences

**Good**

- Zero install friction: copy a directory, type `/sstack`.
- Runs wherever the user already works; no harness lock-in.
- A later `scripts/` evidence layer can be added under the same
  skill without restructuring, because the reference layout
  already reserves the slot.
- The audit-not-fix contract is enforceable in prose because there
  is no code path the skill owns.

**Bad**

- No deterministic evidence schema in v0, so findings are only as
  reproducible as the agent's transcript. This is a real gap, and it
  is the main thing v1 buys.
- Cold-agent compliance is the weak axis. Every early run violated a
  rule in prose (bug-pinning regressions, fixing source, scoring
  broken harnesses as verdicts), and each violation had to be
  answered with another guardrail in the text.
- Host-agnostic means no forced update path; a stale copy of the
  skill can sit in a user's directory indefinitely.

**Risks**

- If the prose guardrails keep needing reinforcement, the content-only
  ceiling is real and v1 should revisit a thin `scripts/` runner.
  Trigger: a clean cold run still misreads a core contract after the
  text is unambiguous.
