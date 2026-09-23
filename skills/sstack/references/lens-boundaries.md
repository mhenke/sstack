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
- Pagination math: `page=0` (off-by-one into negative slice),
  `size=0`, page beyond data.
- Aggregation over collections: empty input (reduce/fold without
  initial value), single element.

## Oracle patterns

- Explicit validation error naming the argument
  (`ValueError: page must be >= 1`).
- Well-defined empty result (`[]`, `0`) documented as correct.
- Invariant preserved (total never negative; sum always a number).

Watch for the negative-index trap: `page=0` makes start negative,
and Python `items[-3:0]` and JS `slice(-3, 0)` both silently
return `[]` (the clamped start outranks stop) instead of erroring.
A silent empty/wrong page is worse than a crash.

## Worked examples

Python — `paginate(items, page, size)` with 1-based `page`:

```python
# case: page=0, size=3, items=[1..10]
# oracle: raises ValueError("page must be >= 1")
# observed (bug): returns []  (start = -3 clamps past stop, silent empty)
```

TypeScript — `maxQuantity(lines)` via `Math.max(...map)`:

```ts
// case: lines = []
// oracle: throws Error("lines must not be empty")
// observed (bug): returns -Infinity  (Math.max of nothing)
```

## When not to apply

No numbers, sizes, indexes, or collections in the surface's
contract; values are already validated upstream at a boundary you
can point to.
