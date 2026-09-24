# ADR-0001: Negative testing is the product domain

**Status**: Accepted
**Date**: 2026-09-23
**Deciders**: Mike Henke

## Context

The first framing of this project was "proof-gated generated tests":
generate a test, prove it has signal by watching it fail against a
mutant. That is a mutation-testing product wearing a testing hat, and
it would have quietly become the thing sstack is. The pasted analysis
that prompted the build made the correction itself: negative testing
is the domain, and techniques like mutation, fuzzing, and fault
injection are lenses or evidence mechanisms that explore that domain.

Three concepts had to be kept apart:

1. negative testing as the product question (what happens when the
   system gets something it did not expect)
2. gstack's process model (discrete, artifact-producing, resumable
   stages)
3. mutation/proof tooling as one way to earn a verdict

sstack is (1), shaped by (2), and treats (3) as optional.

The adjacent question was whether "negative" means "adversarial."
It does not. A `null`, an empty file, a duplicate event, a timeout,
and a clock rollover are not attacks, and they still deserve an
oracle. Anchoring the identity on "security" or "adversarial" would
have excluded most of the domain and invited a different product.

## Decision

sstack's product question is "what happens when the system gets
something it wasn't expecting?" Every technique is a lens that
explores that one question, and the generic principle is
**oracle-first**: a negative test declares the expected behavior
under the adverse condition before running anything, and produces
observable evidence that the expectation held or broke.

Security is one lens among many. Mutation is one verification
strategy, deferred past v0. The lifecycle borrows gstack's process
shape; gstack's runtime infrastructure (binaries, daemon, browser
service) is explicitly not copied.

## Consequences

**Good**

- The product cannot drift into mutation-testing or security-testing
  by feature creep; those are scoped as components, not identity.
- "Not adversarial" keeps timeouts, nulls, and rollovers in scope,
  which is most of the interesting surface for ordinary software.
- The oracle-first rule gives every finding a checkable shape
  regardless of which lens found it.

**Bad**

- Slower to explain than "AI security testing." The positioning costs
  a paragraph every time.
- Mutation, the strongest proof technique, is not in v0, so a v0
  finding rests on expected-error assertion plus reproducibility
  alone.
- The taxonomy (13 lenses) is large enough to look like a sprawl
  risk, mitigated by shipping three lenses and disclosing the rest.

**Risks**

- If cold agents keep missing the malformed/missing lenses in
  practice, the per-surface coverage rule in the skill may need to
  be enforced harder than prose. Revisit if a second clean run fails
  to reach record-shaped surfaces.
