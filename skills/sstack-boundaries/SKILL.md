---
name: sstack-boundaries
description: "Boundaries lens rubric. Case-generation heuristics, oracle patterns, and worked examples for numeric, size, index, collection, pagination, precision, and time edge cases. Loaded inline under ### Lens rubric."
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

- Paired boundary probes: probe the exact threshold $N$ (valid or
  boundary-valid) alongside $N \pm 1$ (the invalid/violating mutation).
  Probing only the violating side misses off-by-one errors and accepts
  guards that reject valid boundary values.
- Numeric arguments: `0`, `1`, `-1`, `-N`, max int, just-over any
  threshold the code compares against. Float extremes: IEEE 754 `-0.0`
  (negative zero), `NaN`, `Infinity`, denormals (`5e-324`).
- Integer wrap: past `MAX_SAFE_INTEGER` (`2**53`), 32-bit signed wrap
  (`2147483647`, `2147483648`, `-2147483649`).
- String and text bounds: empty `""`, single space `" "`, lone surrogates
  (`\uD800`), RTL overrides (`\u202E`), zero-width characters (`\u200B`, `\u200D`).
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
- Numeric precision and scale: money or measured quantities needing
  more decimal places than the type holds, floats where the contract
  implies exactness, integers just past `MAX_SAFE_INTEGER`/`sys.maxsize`.
  Truncation and rounding are boundary violations even when the input
  is in range.
- Time and durations: `0` or negative durations, interval arithmetic
  (`end - start`), month/year edges where off-by-one lands wrong
  (`(page - 1)` has a time twin: `month - 1` into a 0-based index).

## Oracle patterns

- Explicit validation error naming the argument
  (`ValueError: lo must be <= hi`).
- Well-defined empty result (`[]`, `0`) documented as correct.
- Invariant preserved (total never negative; sum always a number;
  large-but-legitimate input still returns a value).
- Boundary sensitivity: verify admission at $N$ and rejection at $N+1$
  (or vice versa); an oracle that accepts both or rejects both at the
  boundary has missed the state transition.
- No silent truncation, precision loss, or rounding where the
  contract implies exactness (2.675 stored as 2.67 is a boundary bug
  even though 2.675 is in range).

Watch for the negative-index trap: when a 1-based index goes to zero,
the derived start goes negative, and Python `items[-3:0]` and JS
`slice(-3, 0)` both silently return `[]` (the clamped start outranks
stop) instead of erroring. A silent empty or wrong page is worse than
a crash.

Worked example — Python `format_amount(cents)` computing
`round(amount, 2)`: case `amount = 2.675`, oracle returns `"2.68"`
(or better, computes in integer cents), observed (bug) `"2.67"`
(IEEE 754 cannot represent 2.675; `round` applies banker's rounding
to a binary approximation). BVA canon: ISO/IEC/IEEE 29119-4 and
Myers, *The Art of Software Testing* — the method is $Min - 1$ and
$Max + 1$ around every declared threshold, plus structural extremes
(empty, one past the end, capacity + 1).

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

## Failure modes to watch for

- Numeric range violations (CWE-190): inputs exceeding integer limits or falling
  below minimum thresholds.
- Collection & buffer extremes (CWE-125, CWE-787): empty collections passed to
  aggregators, or single-element inputs where pairwise operations assume N >= 2.
- Index off-by-one and slicing traps: negative indices silently clamping or
  returning empty slices instead of raising errors.
- Float precision loss and rounding drift (CWE-682): binary IEEE 754 precision
  loss and banker's rounding on currency or exact measurements.
- Temporal boundary inversion: negative or zero durations and inverted intervals.

## Language notes

### Python

- Negative slicing: `items[-3:0]` silently returns `[]` without erroring.
- Rounding: `round()` uses banker's rounding (round-half-to-even); use `decimal.Decimal`
  for exact currency calculations.
- Integers: Python integers have arbitrary precision, but C-extensions and
  interfaces may overflow `sys.maxsize`.

### JavaScript / TypeScript

- Slicing: `array.slice(-3, 0)` returns `[]` silently due to negative index clamp.
- Spread limits: `Math.min(...largeArray)` throws unhandled `RangeError: Maximum call
  stack size exceeded` on large inputs.
- Safe integers: integers exceeding `Number.MAX_SAFE_INTEGER` ($2^{53}-1$) silently
  lose precision without errors.

### Java

- Out of bounds: indexing beyond list/array bounds throws `IndexOutOfBoundsException`.
- Overflow: primitive integer arithmetic wraps silently without errors unless using
  `Math.addExact()` or `Math.multiplyExact()`.
- Precision: binary floating-point types (`float`, `double`) drift; use `BigDecimal`
  with explicit `RoundingMode`.

### C++

- Subscripting: `std::vector::operator[]` does no bounds checking (undefined behavior);
  use `.at()` or checked boundaries.
- Overflow: signed integer overflow is undefined behavior under ISO C++.
- Iterators: arithmetic advancing past `end()` causes memory faults.

## When not to apply

No numbers, sizes, indexes, or collections in the surface's contract;
values are already validated upstream at a boundary you can point to.
