---
name: sstack-concurrency
description: "Concurrency lens rubric. Case-generation heuristics, oracle patterns, and worked examples for parallel access, race conditions, TOCTOU windows, lost updates, and double-spending. Loaded inline under ### Lens rubric."
disable-model-invocation: true
---

# Concurrency lens

Attacks every mapped surface through the concurrency lens: that
operations executed concurrently across multiple threads, async
tasks, or parallel requests maintain ACID guarantees and never corrupt
shared state. While other lenses execute calls sequentially, this
lens deliberately synchronizes parallel requests to collide inside
critical sections.

## Case-generation heuristics

- Concurrent depletion / double-spend: given a finite balance or quota
  $B$, fire $N$ simultaneous requests requesting $D$ where $N \times D > B$
  but $D \le B$, released simultaneously via a synchronization barrier.
- Concurrent read-modify-write (lost update): read an entity's current
  version token, spawn parallel update requests reusing that same base
  version token, and inspect the final persisted state.
- Time-of-check to time-of-use (TOCTOU): identify check-then-act pairs
  (checking item availability then reserving, checking promo code validity
  then applying discount), firing parallel workers across the check window.
- Parallel thread access to shared in-memory structures: fire concurrent
  reads and writes against global caches, connection pools, or collections
  without mutex guards.
- Interleaved lock acquisition: execute operations that acquire multiple
  locks in differing order to detect deadlocks or livelocks under load.

## Oracle patterns

- Balance and quota conservation: the sum of approved debits never
  exceeds initial funds; final state satisfies $B_{final} \ge 0$.
- Lost update prevention: concurrent updates with identical base version
  tokens must either merge cleanly or reject $N-1$ requests with HTTP
  412 Precondition Failed or 409 Conflict.
- Atomic check-then-act: operations verify and reserve resources
  atomically; at most one concurrent worker acquires single-use items.
- Deadlock-free failover: contested resource locks abort or time out
  with explicit retryable errors within milliseconds, never hanging
  worker threads indefinitely.

Worked example — Python `BankAccount.transfer(amount, recipient)` without
atomic locking: two concurrent threads both attempt to transfer $100 from
an account with balance $100, oracle raises `InsufficientFundsError` on the
second transfer and final balance is $0, observed (bug) both threads pass the
balance check before either decrements, resulting in a balance of -$100.

TypeScript `updateDocument(id, patch, expectedVersion)`: two concurrent
requests with version 1 submit updates, oracle rejects the second request
with `412 Precondition Failed`, observed (bug) the second write silently
overwrites the first, causing a lost update.

## Failure modes to watch for

- Race condition on shared resource (CWE-362): simultaneous operations
  mutating shared state without synchronization.
- Time-of-check time-of-use (CWE-367): state changing between verification
  and mutation.
- Deadlock (CWE-833): circular dependency between acquired resource locks.
- Non-atomic counter increments: using non-atomic `count += 1` in async
  handlers where context switches interrupt read and write phases.

## Language notes

### Python

- Global Interpreter Lock (GIL): the GIL serializes bytecode execution,
  but I/O switches and C-extensions yield the GIL, creating real race
  windows in multithreaded code.
- `asyncio`: single-threaded cooperative multitasking still suffers from
  race conditions whenever an `await` yields control between read and write.
- Use `threading.Lock`, `asyncio.Lock`, or atomic SQL `SELECT FOR UPDATE`.

### JavaScript / TypeScript

- Node.js event loop: while JS is single-threaded, `await` points yield
  execution to other tasks in the event loop; check-then-act logic across
  any `await` is vulnerable to TOCTOU races.
- In-memory objects shared across worker threads (`worker_threads`) require
  `SharedArrayBuffer` with `Atomics`.

### Java

- Standard collections (`HashMap`, `ArrayList`) are not thread-safe;
  concurrent writes can cause infinite loops during rehashing. Use
  `ConcurrentHashMap` or `AtomicInteger`.
- Synchronized blocks or `java.util.concurrent.locks.ReentrantLock` must
  be used to guard multi-step compound actions.

### C++

- Data races invoke Undefined Behavior in the C++ memory model (ISO C++11).
  All shared concurrent access requires `std::atomic` or `std::mutex`.
- Lock ordering must be strictly preserved or managed via `std::lock` /
  `std::scoped_lock` to prevent deadlocks.

## When not to apply

The surface operates entirely on thread-local, stack-allocated, or immutable
data with no shared database, cache, filesystem, or memory references.

## Interaction with other lenses

`concurrency` owns multi-worker parallel execution races and synchronization
barriers. Single-threaded sequence progression across time belongs to `ordering`
and `state`. Network retry replays belong to `idempotency`.
