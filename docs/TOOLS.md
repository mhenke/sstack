# Negative testing tools

What the 2026-09-23 community scan named, by category and language.
Companion to [`RESEARCH.md`](RESEARCH.md) and the roadmap's mutation
and property-based items.

## Property-based testing

Generates inputs, asserts a property, shrinks failures to minimal
counterexamples.

| Language | Tool | Notes |
|---|---|---|
| Python | [Hypothesis](https://hypothesis.readthedocs.io/) | The reference implementation. Seeded RNG for reproducibility. |
| Python | [Atheris](https://github.com/google/atheris) | Coverage-guided fuzzing for Python, built on libFuzzer. Catches crashes, hangs, and sanitizer failures. |
| TypeScript / JS | [fast-check](https://fast-check.dev/) | ~100 runs per property by default. Arbitraries compose. Seeded RNG. |
| Java / Kotlin | [jqwik](https://jqwik.net/) | Ships as a JUnit 5 engine, so it inherits IDE and build support. |
| C++ | [RapidCheck](https://github.com/emil-e/rapidcheck) | QuickCheck-style. Works with GoogleTest. |
| C++ | [Google FuzzTest](https://github.com/google/fuzztest) | Property-based testing fused with coverage-guided fuzzing. `FUZZ_TEST` macro. |
| C++ | [Hegel](https://github.com/hegeldev/hegel-cpp) | Hypothesis-inspired, beta. |
| C++ | [reflect_arbitrary](https://wrocpp.github.io/posts/reflect-arbitrary/) | Reflection-based Arbitrary generation. Adapters for RapidCheck and FuzzTest. |
| Haskell | [QuickCheck](https://hackage.haskell.org/package/QuickCheck) | The original. Everything above descends from it. |

## Mutation testing

Seeds mutants into source, runs the suite, measures kill rate.
Assertion-strength signal that line coverage cannot provide.

| Language | Tool | Notes |
|---|---|---|
| Java / JVM | [PIT](https://pitest.org/) | The standard. Incremental (changed code only). arcmutate Pro adds Kotlin, Spring, Git. |
| JS / TS | [Stryker Mutator](https://stryker-mutator.io/) | Supports Jest, Vitest, Mocha. Per-mutant clear-text reports. |
| Python | [mutmut](https://github.com/boxed/mutmut) | Simplest Python option. |
| Python | [MutPy](https://github.com/mutpy/mutpy) | Alternative. Mentioned but less active. |

Practical bar: one 2026 survey puts ~80% mutation score on critical
modules. PIT and Stryker publish no target number themselves. Run on
changed code, not whole-repo sweeps.

## Fuzzing and sanitizers (C++)

Asserts the absence of UB rather than expected behavior. A different
proof model from every other language here.

| Tool | What it does |
|---|---|
| [libFuzzer](https://llvm.org/docs/LibFuzzer.html) | In-process coverage-guided fuzzing. Compile with `-fsanitize=fuzzer`. Crashing inputs saved for replay. |
| AddressSanitizer (ASan) | Memory errors: buffer overflow, use-after-free. |
| UndefinedBehaviorSanitizer (UBSan) | UB: signed overflow, misaligned access, null deref. |
| [Google FuzzTest](https://github.com/google/fuzztest) | Fuzzing + property-based testing in one framework. Bridges both models. |
| [Catch2](https://github.com/catchorg/Catch2) | BDD-style test framework for C++. Sections, generators, and matchers for negative test cases. Pairs with libFuzzer or ASan for UB detection. |

Sanitizer-driven detection needs no assertions in the test; explicit
correctness properties (round-trip invariants, pre/post-conditions)
catch what sanitizers cannot. FuzzTest's docs treat these as two
complementary strategies.

## Scan sources, non-tool

Guides and threads the scan surfaced. Context, not tooling.

- [TestinGil](https://www.youtube.com/@TestinGil) — edge case vs
  negative case distinction
- [Ministry of Testing](https://club.ministryoftesting.com/) — how much
  negative testing is acceptable
- [Tricentis](https://www.tricentis.com/learn/negative-testing) —
  includes boundary values under negative testing (disagrees with
  TestinGil's split)
- [BrowserStack](https://www.browserstack.com/guide/negative-testing) —
  practical guide
- [Augment Code](https://www.augmentcode.com/guides/mutation-testing-ai-generated-code)
  — mutation testing aimed at AI-generated code
- [jmid/pbt-frameworks](https://github.com/jmid/pbt-frameworks) —
  cross-language PBT framework comparison matrix
