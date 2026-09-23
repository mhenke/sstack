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

Watch for the negative-index trap: Python `items[-3:0]` and JS
`slice(-3, 0)` silently return tail-window or empty results
instead of erroring. Silent wrong data is worse than a crash.

## Worked examples

Python — `paginate(items, page, size)` with 1-based `page`:

```python
# case: page=0, size=3, items=[1..10]
# oracle: raises ValueError("page must be >= 1")
# observed (bug): returns [8, 9, 10]  (start = -3 wraps)
```

TypeScript — `totalQuantity(lines)` via reduce:

```ts
// case: lines = []
// oracle: returns 0
// observed (bug): TypeError: Reduce of empty array with no initial value
```

## When not to apply

No numbers, sizes, indexes, or collections in the surface's
contract; values are already validated upstream at a boundary you
can point to.
