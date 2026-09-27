---
name: sstack-state
description: "State lens rubric. Case-generation heuristics, oracle patterns, and worked examples for shared mutable state: stale cached views, write-through to caller data, partial updates after failure, live views returned as results, invalid lifecycle transitions. Loaded inline under ### Lens rubric."
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
- Lifecycle & post-disposal: invoke methods after an object or
  session is closed, disposed, aborted, or cancelled, or attempt
  transitions forbidden from the current lifecycle state.

## Oracle patterns

- Derived reads reflect current state, or staleness is documented
  and bounded. A silent stale read is a bug.
- Collections handed to callers are copies or immutable views:
  mutating them never changes the owner.
- Input objects are never written through: same object in,
  unmutated out, unless the signature documents mutation.
- A failed update leaves the object exactly as it was, or the
  partial state is documented. Half-applied with no note is a bug.
- Closed, disposed, or illegally transitioned objects reject
  subsequent operations with explicit domain or lifecycle errors
  (e.g. 409 Conflict, IllegalStateError); state remains valid.

Worked example — Python `Ledger.balance()` caching the summed total
while `record(entry)` appends to the entries list without invalidating
the cache: case `balance()` then `record(...)` then `balance()` again,
oracle the second read includes the new entry, observed (bug) the
first cached number is served forever.

TypeScript `sortByRank(rows)` calling `rows.sort()` before picking:
oracle the caller's array is untouched and a sorted copy is returned,
observed (bug) the input array arrives reordered at the next call
site — write-through through a parameter.

## Failure modes to watch for

- Escaped internal references (CWE-375): returning internal mutable
  collections or structures directly, allowing external callers to
  bypass validation and mutate owner state.
- Parameter write-through (CWE-374): modifying caller-owned arguments
  in-place during pure computations or transformations.
- Stale cached views: memoized or precomputed aggregates that fail to
  evict or recompute upon underlying state change.
- Broken failure atomicity (CWE-366): multi-step operations throwing
  midway without rolling back, leaving partial or corrupted state.
- Lifecycle invalidity & post-disposal invocation (CWE-672): operating
  on terminated, disposed, or closed instances without explicit
  rejection.

## Language notes

### JavaScript / TypeScript

- In-place array mutations (`Array.prototype.sort()`, `reverse()`,
  `splice()`, `pop()`, `shift()`) mutate caller inputs; prefer
  `toSorted()`, `toReversed()`, or copying with `slice()` before sorting.
- Object spread (`{...obj}`) and array spread (`[...arr]`) create
  shallow copies; nested collections remain shared mutable references.
- Returning internal objects without `Object.freeze()` or structured
  cloning exposes live mutable references to callers.

### Python

- Default mutable parameter values (`def append(item, target=[])`)
  persist mutations across all invocations of the function.
- In-place methods (`list.sort()`, `list.reverse()`, `list.extend()`,
  `dict.update()`) mutate arguments directly; prefer `sorted()`,
  defensive copies (`list(target)`), or copies before modification.
- Dictionary views (`dict.values()`, `dict.keys()`) reflect live
  mutations; snapshot explicitly with `list()` when detachment is required.

### Java

- Returning internal collections without `Collections.unmodifiableList()`
  or `List.copyOf()` violates encapsulation (Bloch *Effective Java*
  Item 50).
- Spring `@Transactional` rolls back on unchecked exceptions by default,
  but commits on checked exceptions unless `rollbackFor = Exception.class`
  is specified.

### C++

- Returning non-const references (`T&`) to internal member state allows
  external callers to bypass class invariants.
- Container iterator invalidation: modifying a collection (insertion,
  erasure, reallocation) while iterating through it causes undefined
  behavior or corrupted state.

## When not to apply

The surface is pure: it reads nothing beyond its arguments, mutates
nothing, caches nothing, and returns freshly built values. No object
lifetime, no state to go stale.

## Interaction with other lenses

`state` owns object lifetime, shared mutable memory, and transition
invariants. Parallel execution race conditions (`concurrency`), pipeline
call sequencing (`ordering`), and duplicate retry divergence (`idempotency`)
are distinct lenses in the taxonomy. When those custom lenses are absent,
`state` tests that atomic rollback, optimistic locking, and transition
rejections protect data integrity.

