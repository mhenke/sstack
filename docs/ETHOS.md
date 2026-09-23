# sstack ethos

> Don't ask the agent to say whether the software is robust.
> Make it exercise the failure condition and collect evidence.

sstack is structured negative testing for AI coding agents: it
systematically explores how software behaves outside the happy path,
verifies observed behavior against a declared oracle, and turns
confirmed failures into permanent regression tests.

## The four rules

1. **Attack assumptions.** Every input, state, and dependency an
   implementation assumes is a surface to probe.
2. **Define the oracle before the attack.** Write down the expected
   behavior under the adverse condition — error, degradation, retry
   bound, invariant, rejection — before running anything. "It
   crashes" is not an oracle; "it raises a validation error naming
   the field" is.
3. **Never accept an agent's claim as evidence.** Run the real
   command, quote the real output. The agent interprets evidence;
   it does not manufacture it.
4. **Turn confirmed failures into permanent regressions.** A
   finding that is not a test in the host repo's suite will be
   reintroduced.

## What sstack is not

- Not a security product. Security is one lens among many.
- Not a mutation-testing product. Mutation is one verification
  strategy, deferred past v0.
- Not a happy-path test generator. Happy-path coverage is the host
  repo's business.
- Not adversarial-only. A timeout, null, or clock rollover is not
  an attack; it is still a negative condition worth an oracle.
