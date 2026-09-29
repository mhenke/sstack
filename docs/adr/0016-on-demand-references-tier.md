# ADR-0016: Subcommand bodies live in an on-demand references tier

**Status**: Accepted
**Date**: 2026-09-28
**Deciders**: Mike Henke

## Context

SKILL.md carries a 540-line ceiling and sat at 527 when the harden
mode was designed. A mode body of any depth cannot fit in the entry
skill, and harden is not a stage — the seven stages are fixed — so it
could not live in the Stages section regardless of length.

[impeccable](https://github.com/pbakaus/impeccable)'s prior art (cited in this repo since v0) ships one skill
with `references/` per command, loaded on demand. The eight
definitions named Skill "the methodology for a stage," which left a
subcommand's methodology no noun and no loading tier.

## Decision

We will add a `references/` tier under `skills/sstack/`: plain
markdown bodies, no frontmatter, loaded inline by routing only when
their subcommand is invoked. The Skill definition becomes "the
methodology for a stage or subcommand."

## Consequences

**Good**: the line ceiling stops binding feature design; a new
subcommand adds a file, not a section; cold agents load harden text
only when running harden.

**Bad**: a second place where pack behavior lives; a routing bullet
naming a missing file is a broken subcommand with no load-time check.

**Risks**: if the tier grows past a few files, the entry skill stops
being the map of what sstack does. Revisit when a fourth reference
file is proposed.
