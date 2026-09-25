---
name: sstack-state
description: "State lens rubric. Case-generation heuristics, oracle patterns, and worked examples for shared mutable state: stale cached views, write-through to caller data, partial updates after failure, live views returned as results. Loaded inline under ### Lens rubric."
disable-model-invocation: true
---

# State lens

Attacks every mapped surface through the state lens: that a value
computed from, or a structure handed out by, an object with mutable
state stays true while that state changes. Other lenses attack one
call; this lens attacks the sequence around it.

## Case-generation heuristics

- Read-then-mutate-then-read: read a derived value, mutate the
  underlying collection, re-read. A cached or derived value that
  never invalidates serves the stale first read forever.
- Hand-out-then-mutate: take any collection a surface returns,
  mutate it, then inspect the owner through a second call. An
  escaped internal reference means callers can edit your data.
- Write-through: pass a caller-owned list/dict into a surface,
  mutate inside (sort, append, clear), check the caller's object
  afterward. Input objects come back changed.
- Interleave shared accumulators: two operations on one object,
  second reads what the first wrote (totals, counts, indices).
  Ordering is part of the contract; test the contract, not one call.
- Failure mid-update: trigger an error after a surface has already
  changed part of its state (raise on the second item of a batch).
  Compare the whole object before and after the failed call.

## Oracle patterns

- Derived reads reflect current state, or staleness is documented
  and bounded. A silent stale read is a bug.
- Collections handed to callers are copies or immutable views:
  mutating them never changes the owner.
- Input objects are never written through: same object in,
  unmutated out, unless the signature documents mutation.
- A failed update leaves the object exactly as it was, or the
  partial state is documented. Half-applied with no note is a bug.

Worked example — Python `Cart.total()` caching a running sum while
`add_item()` appends to the dict without invalidating the cache: case
`total()` then `add_item(...)` then `total()` again, oracle the second
read includes the new line, observed (bug) the first cached number is
served forever.

TypeScript `topDiscount(lines)` calling `lines.sort()` before picking:
oracle the caller's array is untouched and a sorted copy is returned,
observed (bug) the input array arrives reordered at the next call
site — write-through through a parameter.

## When not to apply

The surface is pure: it reads nothing beyond its arguments, mutates
nothing, caches nothing, and returns freshly built values. No object
lifetime, no state to go stale.
