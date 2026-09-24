# What the research said

Source: a 30-day community scan (Reddit, Hacker News, GitHub, YouTube,
web) on negative testing across Python, JavaScript/TypeScript, Java, and
C++, run on 2026-09-23. This is the raw synthesis that fed
[ADR-0004](adr/0004-delegate-to-target-existing-tools.md) and the
property-based and mutation-testing items in the roadmap. Kept as the
record of what the field looked like at that date.

## Terminology is unsettled

The QA field uses "edge case" and "negative case" interchangeably more
often than not, but TestinGil's framing draws the line on intent: edge
cases sit at extreme parameters, negative cases are about unexpected
input and user behavior. The practical consequence for tooling is that
"edge case" is a location on a number line while "negative case" is a
class of bad input, and a taxonomy that conflates them will miss cases.

This became the Vocabulary block in
[ARCHITECTURE.md](ARCHITECTURE.md) and the boundaries-lens oracle note.

## Property-based testing is displacing hand-written edge cases

Consistent across all four managed languages. Instead of hand-writing
cases for `0`, `-1`, and `max`, you declare a property and let a
generator with counterexample shrinking find the input that breaks it.
Hypothesis covers Python, fast-check covers TypeScript and JavaScript,
and jqwik covers Java.

jqwik's design is the tell for why the shift took off in Java
specifically: it ships as a JUnit 5 test engine rather than a standalone
framework, so teams inherit IDE support and existing build integration
for free.

## Mutation score is the emerging measure of assertion strength

Stryker for JS/TS and PIT for the JVM are the two tools that come up,
and the pitch is identical: line coverage measures execution, mutation
score measures assertion strength. A 2026 survey puts roughly 80% as
the practical target for critical modules, with the workflow being
incremental: mutate only what changed, inspect survived mutants, write
the assertion that kills each one. PIT advises running on changed code
rather than whole-repo sweeps, which is what makes it survivable in CI.

## C++ runs on a different proof model

Google's FuzzTest fuses property-based testing with coverage-guided
fuzzing, so a C++ fuzz target is written as an ordinary unit test via a
`FUZZ_TEST` macro. libFuzzer underneath catches undefined behavior
through sanitizers with no assertions at all, which is a fundamentally
different proof model from every other language here: you are not
asserting expected behavior, you are asserting the absence of UB.

FuzzTest's own docs make the split explicit: sanitizer-driven detection
with no assertions, versus explicit correctness properties. Round-trip
invariants like escape/unescape catch what sanitizers structurally
cannot.

This became the C++ second-verification-mode item on the roadmap.

## Weak assertions in generated tests are a named, current problem

Augment Code's guide on mutation testing for AI-generated code frames
weak assertions as the dominant failure mode in generated suites, which
is the same failure mode this project keeps rediscovering. A generated
test that passes tells you nothing; a generated test that goes red
against a mutant proves it was asserting something.

## Key patterns

1. Property-based testing is displacing hand-written edge cases across
   Python, JS/TS, and Java, per the jqwik, fast-check, and Hypothesis
   docs
2. Mutation score is the emerging measure of assertion strength rather
   than line coverage, per PIT and Stryker
3. C++ negative testing runs on sanitizers and fuzzing rather than
   assertions, per libFuzzer and FuzzTest
4. The edge-case versus negative-case split is real but inconsistently
   applied, per TestinGil
5. Weak assertions in generated tests are a named, current problem, per
   Augment Code
