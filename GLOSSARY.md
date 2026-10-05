# sstack

Structured negative testing for AI coding agents. Discovers adverse failure surfaces, attacks them through specialist lenses, verifies observed outcomes against declared oracles, and converts confirmed failures into permanent regression tests.

## Language

**Surface**:
A function, parameter, state transition, or boundary where software encounters adverse or non-happy-path conditions.
_Avoid_: Target, endpoint, input

**Lens**:
An attack strategy specialized for a single failure class.
_Avoid_: Attack type, test category, scanner, inspection rule

**Oracle**:
The expected behavior under adverse conditions, written down before the attack is executed.
_Avoid_: Assertion, expectation, post-condition, test claim

**Finding**:
A verified divergence between observed behavior and the declared oracle, backed by machine-captured evidence.
_Avoid_: Bug, defect, issue, vulnerability (prior to verification)

**Regression Test**:
A test written for a confirmed finding that is red on the defect and turns green after the minimal fix.
_Avoid_: Repro script, verification test, bug test

**Hardening Test**:
A negative test confirming that a surface already handles an adverse condition correctly without code changes.
_Avoid_: Happy-path test, regression test, unit test

**Minimal Fix**:
The smallest source code change that satisfies the oracle and turns the regression test green.
_Avoid_: Patch, refactoring, architectural fix

**Evidence**:
Machine-captured execution output and fingerprint proving an observed result with no agent in the loop.
_Avoid_: Log snippet, agent claim, terminal quote

**Cold Agent**:
An AI coding agent evaluated in an isolated sandbox with zero conversation history, no memory, and no answer key.
_Avoid_: Benchmark agent, fresh session, blind agent
