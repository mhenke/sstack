# ADR-0010: Cross-language fixture parity

**Status**: Accepted
**Date**: 2026-09-27
**Deciders**: Mike Henke

**Implementation status (2026-09-27)**: Complete across all four phases
(`seeded-ts`, `seeded-js`, `seeded-java`, `seeded-cpp`). Full 16-seed parity
across all 14 lenses achieved for all 5 fixtures.
- `seeded-ts`: seeds ts-6..ts-16 in `evals/seeded-ts/src/orders.ts`, 16 goldens;
  ColdTs-5 verified 11/11 parity seeds (11 confirmed red→green regressions in
  workspace `.sstack/scratch/sstack-seeded-ts-o10hxv94`, 17/17 tests green, 11/11 evidence
  replay intact, 0 drift).
- `seeded-js`: seeds js-6..js-16 in `evals/seeded-js/src/orders.js`, 16 goldens;
  ColdJs-3 verified 11/11 parity seeds (11 confirmed red→green regressions in
  workspace `.sstack/scratch/sstack-seeded-js-xia4pr3h`, 12/12 tests green, 11/11 evidence
  replay intact, 0 drift).
- `seeded-java`: seeds java-6..java-16 in `evals/seeded-java/src/main/java/com/sstack/Orders.java`, 16 goldens;
  ColdJava-4 verified 11/11 parity seeds (11 confirmed red→green regressions in
  workspace `.sstack/scratch/sstack-seeded-java-x4aqw2kh`, 14/14 tests green, 11/11 evidence
  replay intact, 0 drift).
- `seeded-cpp`: seeds cpp-6..cpp-16 in `evals/seeded-cpp/src/orders.hpp`, 16 goldens;
  ColdCpp-3 verified 11/11 parity seeds (11 confirmed red→green regressions in
  workspace `.sstack/scratch/sstack-seeded-cpp-s8t5nzeu`, 2/2 ctest targets / 12 test assertions green,
  11/11 evidence replay intact, 0 drift).

## Context

sstack evaluates agent capabilities against deliberately broken fixtures in
`evals/`. In v0, `evals/seeded-py` was used as the fast development vehicle
to validate lenses 7 through 14 (`state` through `agent`), growing to 16
seeded defects (`py-1` through `py-16`) with verified cold passes in
`evals/ACCEPTANCE.md`.

However, the non-Python fixtures (`seeded-ts`, `seeded-js`, `seeded-java`,
`seeded-cpp`) remained frozen at their initial 5 baseline seeds, covering only
the three initial input lenses (`boundaries`, `missing`, `malformed`). This
produced an architectural gap: while sstack claims 14 lenses and multi-language
support, only Python has end-to-end acceptance evidence across all 14 lenses.
A roadmap item without acceptance evidence is not done, however good the prose is.

## Decision

We will achieve full cross-language fixture parity by extending each non-Python
fixture (`seeded-ts`, `seeded-js`, `seeded-java`, `seeded-cpp`) to cover all
14 shipped lenses, adhering to the frozen-seed principle of ADR-0003:

1. Existing seeds (`ts-1..5`, `js-1..5`, `java-1..5`, `cpp-1..5`) remain
   frozen and immutable.
2. Each fixture will implement an `orders` domain module (e.g. `src/orders.ts`,
   `orders.js`, `Orders.java`, `orders.cpp`) hosting seeds 6 through 16
   corresponding to the 11 extended lenses (`state`, `ownership`, `ordering`,
   `exceptional-conditions`, `resource-exhaustion`, `concurrency`,
   `idempotency`, `dependency-failure`, `contract`, `security`, `agent`).
3. Fixture parity will be phased by language, each gated by cold acceptance
   runs proving negative-control flips (red→green) and out-of-loop replay
   integrity before claiming coverage in `evals/ACCEPTANCE.md`.

## Consequences

**Good**:
- Closes the verification gap between Python and other supported host languages.
- Proves lens rubrics function effectively across diverse type systems and
  runtime semantics (static vs dynamic, compiled vs interpreted).
- Maintains strict integrity: acceptance claims remain backed by executed
  cold-agent evidence, never assumed by extrapolation.

**Bad**:
- Substantial implementation effort: requires authoring 11 idiomatic seeded
  defects and corresponding baseline test suites across four additional
  programming languages (TypeScript, JavaScript, Java, C++).
- Significant eval execution time required to execute and record cold
  acceptance runs across all fixtures.

**Risks**:
- Language-specific concurrency and dependency ecosystems (e.g. thread pools
  in C++ vs async event loops in Node.js) require careful defect design so that
  bugs represent fundamental lens invariants rather than framework quirks.
