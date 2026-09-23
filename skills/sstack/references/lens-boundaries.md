# Lens: boundaries

## What assumptions this lens attacks

That numbers stay in sane ranges, indexes exist, collections are
non-empty, and arithmetic lands inside the value domain the code
was written for.

## Case-generation heuristics

- Numeric arguments: `0`, `1`, `-1`, `-N`, max int, just-over any
  threshold the code compares against.
- Sizes/limits: `0`, negative, huge (memory-relevant), and
  `len(x)` and `len(x)±1`.
- Indexes/slices: first, last, `len` (one past end), negative
  index (language-specific wraparound!), empty collection.
- Email validation: empty string, malformed, missing local part, missing domain.
- Aggregation over collections: empty input (reduce/fold without
  initial value), single element.

## Oracle patterns

- Explicit validation error naming the argument
  (`ValueError: age must be >= 0`).
- Well-defined empty result (`[]`, `0`) documented as correct.
- Invariant preserved (total never negative; sum always a number).

Watch for the negative-index trap: `age=0` makes start negative,
and `items[-3:0]` and `slice(-3, 0)` both silently
return `[]` (the clamped start outranks stop) instead of erroring.
A silent empty/wrong value is worse than a crash.

## Worked examples

Python — `UserProfile.getAge(profile)` with 1-based `age`:

```python
# case: profile={"age": -1}, data=[1..10]
# oracle: raises ValueError("age must be >= 0")
# observed (bug): returns []  (start = -3 clamps past stop, silent empty)
```

TypeScript — `UserProfile.getScore(profile)` via `Math.max(...scores)`:

```ts
// case: profile = {name: "Alice"}
// oracle: throws Error("profile must have scores")
// observed (bug): returns -Infinity  (Math.max of nothing)
```

## When not to apply

No numbers, sizes, indexes, or collections in the surface's
contract; values are already validated upstream at a boundary you
can point to.