# ADR-0009: Uniform six-part lens anatomy

**Status**: Accepted
**Date**: 2026-09-27
**Deciders**: Mike Henke

## Context

sstack grew from 3 lenses to 14 lenses across v0 development. Early lenses
(`boundaries`, `malformed`, `missing`, `ownership`) focused strictly on
case-generation heuristics and oracle patterns, but lacked structured
CWE/OWASP failure-mode taxonomies and language-specific implementation
notes for all supported tiers (Python, JavaScript/TypeScript, Java, C++).
Meanwhile, newer lenses (`concurrency`, `idempotency`, `contract`, `security`,
`agent`) included explicit failure-mode mappings and 4-language notes.

This created an inconsistency across the pack: a cold agent attacking a
boundary or missing field in Java or C++ received less language-specific
attack guidance than one attacking SQL injection or tool dispatch failures.
Furthermore, research specifications in `docs/lens/` had identified critical
language traps (such as Python slice clamping, C++ undefined iterator
overflow, and Java unboxing NullPointerExceptions) that were documented in
research but omitted from older skill rubrics.

## Decision

We will require every shipped lens skill (`skills/sstack-<lens>/SKILL.md`)
to implement a uniform six-part anatomy:
1. Case-generation heuristics
2. Oracle patterns
3. Inline worked examples (one Python, one TS/JS, with `observed (bug)` marking the defect)
4. Failure modes to watch for (mapped to formal CWE / OWASP / RFC taxonomies)
5. Language notes across all four tier languages (Python, JavaScript/TypeScript, Java, C++)
6. When-not-to-apply boundaries

All existing lenses are brought into compliance with this standard.

## Consequences

**Good**:
- Parity of guidance across all 14 lenses: an agent receives actionable,
  language-specific attack vectors regardless of which lens is dispatched.
- Research specifications in `docs/lens/` are fully reflected in production
  skills rather than remaining dead research documentation.
- Rigorous answer-key decontamination check is maintained across all sections.

**Bad**:
- Lens skill files are larger, consuming marginally more prompt context
  when pasted inline to subagents.
- Adding a new lens in the future requires authoring all six sections
  including four-language implementation notes.

**Risks**:
- Language notes could drift as language runtimes evolve. Revisit if new
  major language targets (e.g. Go, Rust) are added to the pack.
