# Mutation lens: what a `mutation` lens would own

Every claim below was read from the primary source named beside it. Where a
source does not say something, this file says so rather than filling the gap.
Research date: 2026-09-27. Linked from [`RESEARCH.md`](RESEARCH.md).

The `mutation` row in the lens index reads "proof that tests detect injected
faults" and is unbuilt. This note exists to resolve an architectural ambiguity:
is mutation a *lens* (a failure class attacking software under test) or an
*evidence verification strategy* (a meta-test evaluating test suite quality)?

## The overlap and category error, settled

In sstack's architecture, a lens is defined as:
> "A lens is a failure class the pack attacks. The oracle — expected behavior
> under the adverse condition — is written before the attack runs." (`docs/LENS.md`)

Every shipped lens attacks a target software surface with adverse inputs or
conditions:
- `boundaries`: adverse extreme values
- `malformed`: adverse byte sequences and syntax
- `missing`: adverse omission of required fields
- `ownership`: adverse subject/action combinations
- `exceptional-conditions`: adverse runtime exceptions
- `resource-exhaustion`: adverse volume and resource saturation
- `state`: adverse sequences of lifecycle operations

Mutation does not fit this definition:

| Concept | Lens (Attacker) | Mutation Testing |
|---|---|---|
| Target | Target application code | Target test suite |
| Input | Adverse client inputs / requests | Synthetic syntactic source mutations |
| Oracle | Desired system behavior / error code | Test suite fails on mutant (mutant killed) |
| Output | Finding: application defect | Metric: Mutation score ($\frac{\text{killed}}{\text{total}}$) |
| Sstack Noun | Lens / Agent | Evidence / Runner |

Classifying mutation as a lens is a category error. Mutation testing does not
attack the target's API or business logic; it alters the target's source code
to prove that tests detect injected faults.

## What standards and primary sources prove

### DeMillo, Lipton & Sayward (1978): The Foundations of Mutation Testing

In "Hints on Test Data Selection: Help for the Practicing Programmer" (IEEE
Computer 11(4), 1978), DeMillo et al. established mutation testing based on two
hypotheses:
1. **The Competent Programmer Hypothesis:** Programmers generally create programs
   close to correct; faults are small syntactic variations (e.g., `<` vs `<=`,
   `+` vs `-`).
2. **The Coupling Effect:** Test data that distinguishes all small mutations
   is sensitive enough to distinguish complex, compound faults.

Mutation testing introduces syntactic mutations into the source tree:
- Relational Operator Replacement (ROR): `<` $\to$ `<=`, `==` $\to$ `!=`
- Arithmetic Operator Replacement (AOR): `+` $\to$ `-`
- Statement Deletion (SDL): Removing statements or early returns.

If the test suite passes against a mutant, the mutant **survives** (test suite
deficiency). If at least one test fails, the mutant is **killed** (test suite
strength).

### Tool Ecosystem (PIT, Mutmut, Stryker)

Primary documentation from production mutation tools confirms their nature:
- **PIT (pitest.org):** A fast bytecode mutation testing system for Java. Runs
  against unit tests to evaluate test coverage and effectiveness.
- **Stryker (stryker-mutator.io):** Mutation testing for JavaScript, TypeScript,
  C#, and Scala. Operates on AST nodes to compute Mutation Score Indicator (MSI).
- **Mutmut:** Python mutation testing tool.

None of these tools act as client-facing negative attackers or fuzzers. They
are test suite quality auditors.

## Where mutation belongs in sstack

`docs/ARCHITECTURE.md` already places mutation in its proper architectural tier:

1. **Section "Taxonomy", line 89:**
   `| Evidence | mutation | future |`
   Notice the category is **Evidence**, not Behavior, Access, or Environment.
2. **Section "Verification strategies", line 123:**
   `4. mutation — test fails against a mutant (v1)`
3. **`skills/sstack/SKILL.md`, line 429:**
   `If the target repo has a mutation testing tool installed, run it scoped to
   the surfaces you attacked and record the mutation score.`

Mutation is an **Evidence Verification Gate** in Stage 5 (Test) and Stage 6
(Fix):
- When sstack adds a regression test for a confirmed finding, a mutant applied
  to the fix MUST be killed by the new test.
- If the mutant survives, the regression test pinned the wrong behavior.

## Recommendation: Do NOT proceed as an attacker lens

**Verdict: Not recommended as a lens. Retain as an Evidence Runner.**
Shipping `sstack-mutation-attacker.md` or `skills/sstack-mutation/SKILL.md`
would break sstack's core contract (a lens takes a surface from `map.md`,
designs adverse inputs, writes an oracle, and executes a repro command).
Mutation testing does not take input parameters or return HTTP/domain errors.

Instead, mutation belongs in the v1 roadmap as a **Runner/Evidence tool** that
gates regression tests during Stage 5 (Test), verifying that new tests kill
injected faults before claiming victory.

## Open questions

- Performance cost: Mutation testing is computationally expensive ($O(\text{mutants} \times \text{tests})$).
  Scoped AST mutation (mutating only the lines edited during Fix) is necessary
  to make this practical in fast agent loops.
