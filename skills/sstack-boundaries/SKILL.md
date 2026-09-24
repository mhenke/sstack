---
name: sstack-boundaries
description: "Boundaries lens rubric. Case-generation heuristics, oracle patterns, and worked examples for numeric, size, index, collection, and pagination edge cases. Loaded by the sstack-boundaries-attacker agent."
disable-model-invocation: true
---

# Boundaries lens

Attacks every mapped surface through the boundaries lens: that numbers
stay in sane ranges, indexes exist, collections are non-empty, and
arithmetic lands inside the value domain the code was written for.

A boundary input is a *location*, not a verdict. `page=999` on a
three-item list is a boundary the contract may well answer with a short
page; `page=0` is a boundary the contract almost certainly rejects.
Declare the oracle from the surface's contract, never from the fact
that the value sits at an extreme.

## Case-generation heuristics

- Numeric arguments: `0`, `1`, `-1`, `-N`, max int, just-over any
  threshold the code compares against.
- Sizes/limits: `0`, negative, huge (memory-relevant), and `len(x)`
  and `len(x)±1`.
- Indexes/slices: first, last, `len` (one past end), negative index
  (language-specific behavior!), empty collection.
- 1-based vs 0-based conventions: any arithmetic that derives an index
  (`start = (page - 1) * size`) flips sign one step below the declared
  minimum.
- Aggregation over collections: empty input (reduce/fold without
  initial value, `Math.max()` of nothing), single element, arrays
  large enough to hit spread-argument stack limits.

## Oracle patterns

- Explicit validation error naming the argument
  (`ValueError: lo must be <= hi`).
- Well-defined empty result (`[]`, `0`) documented as correct.
- Invariant preserved (total never negative; sum always a number;
  large-but-legitimate input still returns a value).

Watch for the negative-index trap: when a 1-based index goes to zero,
the derived start goes negative, and Python `items[-3:0]` and JS
`slice(-3, 0)` both silently return `[]` (the clamped start outranks
stop) instead of erroring. A silent empty or wrong page is worse than
a crash.

Worked examples — Python `clamp(value, lo, hi)` with `lo > hi`:
case `clamp(5, 10, 1)`, oracle `raises ValueError("lo must be <= hi")`,
observed (bug) returns 1. TypeScript `windowFrom(items, start, count)`
with `start = -1`: oracle throws `Error("start must be >= 0")`,
observed (bug) returns `[]`.

## Operating limits

Operating limits are boundary cases too. Max connections, rate
limits, memory ceilings, request timeouts, and concurrent-request
caps all have a "just-over" value where the system transitions from
accepting to rejecting. Attack them the same way: find the limit,
go one past it, and check that the system returns a clean error
naming the limit rather than hanging, leaking, or silently degrading.
BrowserStack's negative testing guide calls these "operating limits";
the `resource-exhaustion` lens covers them when they land.

## When not to apply

No numbers, sizes, indexes, or collections in the surface's contract;
values are already validated upstream at a boundary you can point to.
