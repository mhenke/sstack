# ADR-0004: Lenses delegate to the target's existing tools

**Status**: Accepted
**Date**: 2026-09-23
**Deciders**: Mike Henke

## Context

sstack's Attack stage asks an agent to hand-design a case per surface per
lens, and its Minimize stage asks the agent to strip a case down to the
smallest input that still violates the oracle. Both are reasonable
approaches and both are now behind the field.

Across Python, JavaScript/TypeScript, and Java, the answer to "which
inputs break this" is moving toward declared properties plus generated
inputs plus automatic counterexample shrinking: Hypothesis, fast-check,
and jqwik respectively, with RapidCheck and Google FuzzTest in C++. jqwik
landed in Java partly because it ships as a JUnit 5 engine rather than a
standalone framework, so teams inherit their existing IDE and build
integration.

Sources split on whether PBT replaces or complements hand-written
cases. The library docs frame PBT as an alternative to example-based
testing; practitioner threads treat them as complementary. Both
positions agree the generator-and-shrinker catches cases hand-design
misses, which is the part sstack should delegate.

Mutation testing is in the same position. PIT for the JVM, Stryker for
JS/TS, and mutmut for Python are mature, and mutation score is now a
common answer to "are my tests even asserting anything", which is
precisely the question sstack asks.

Hand-designing a case a generator would produce is wasted effort, and
hand-minimizing a case a shrinker would shrink is worse than wasted
effort: it is slower and less complete.

This ADR does not change ADR-0001, which scoped mutation as a
verification strategy rather than the product's identity. That stands.
What changes is that sstack should reach for the target's own tooling
before falling back to its own method.

## Decision

Where the host repo already has a property-based testing library, a
mutation tool, or a fuzzer, sstack delegates to it and says so in the
run's artifacts. The skill's own case-design and hand-minimization are
the fallback for repos that have none.

sstack keeps oracle-first ordering, which the libraries do not have: the
expected behavior is declared before the attack runs, not discovered by
hitting the bug first. A property-based test tells you an input exists
that breaks an assumption; sstack's oracle tells you what the system
should have done instead. Both halves are needed.

## Consequences

**Good**

- sstack stops reinventing shrinking. A run against a Hypothesis repo
  gets better minimization for free.
- The resulting regressions match the repo's own idiom, so they survive
  review and keep running under the existing toolchain.
- The tool stays small. Delegation is prose in the skill, not code in
  the pack, so ADR-0002's no-runtime constraint survives.
- Mutation becomes cheap to offer: the agent invokes PIT or Stryker
  rather than implementing anything.

**Bad**

- Two verification styles in one report. A run that mixes property-based
  and example-based findings needs a field saying which produced each.
- Delegation is only as good as the target's tooling. A repo with a
  barely-configured fuzz target gains little.
- The skill grows instructions for tools it cannot test. A delegation
  instruction naming Hypothesis is only as correct as that sentence.

**Risks**

- Over-delegation. An agent that finds a property-based library may
  stop reading surfaces, trading breadth for generator convenience. The
  per-surface coverage rule stays mandatory regardless of tooling.
- If C++ sanitizer-driven fuzzing needs a second verification mode
  rather than a lens addendum, that is a design question this ADR does
  not settle. See ROADMAP.md.
