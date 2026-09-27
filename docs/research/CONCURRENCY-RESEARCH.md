# Concurrency lens: what a `concurrency` lens would own

Every claim below was read from the primary source named beside it. Where a
source does not say something, this file says so rather than filling the gap.
Research date: 2026-09-27. Linked from [`RESEARCH.md`](RESEARCH.md).

The `concurrency` row in the lens index reads "race conditions, parallel access"
and is unbuilt. This note exists to decide whether shipping it would duplicate
`state`, which already mentions race windows and shared mutable memory, and how
an automated agent can reliably reproduce and verify race conditions.

## The overlap, settled

`state` owns object lifetime and sequential state transitions. `concurrency`
owns simultaneous or interleaved access from multiple threads, fibers, or
network requests competing for the same resource:

| Case | Shipped owner | Notes |
|---|---|---|
| Single-threaded invalid transition | `state` | Sequence of 1 client |
| Escaped mutable reference | `state` | Single-threaded memory aliasing |
| Stale cache read after sequential write | `state` | Sequential cache invalidation |
| Lost update (concurrent read-modify-write) | `concurrency` | Two concurrent clients overwrite |
| Time-of-check to time-of-use (TOCTOU) | `concurrency` | State changes between check and act |
| Deadlock / livelock under load | `concurrency` | Lock ordering between resources |
| Double-spend / balance overdraft | `concurrency` | Parallel debits exceeding limit |

While `state` verifies that optimistic locking tokens are supported, `concurrency`
executes parallel interleaved probes to prove that uncoordinated concurrent
requests cannot corrupt data or double-spend balances.

## What standards and specifications prove

### RFC 7232 & RFC 9110: Conditional Requests and Lost Update Prevention

RFC 9110 §13.1.1 and RFC 7232 define the standard HTTP mechanism for preventing
the "Lost Update" problem:
- Clients include `If-Match: <entity-tag>` or `If-Unmodified-Since`.
- Per RFC 7232 §3.1: If the condition evaluates to false, the server MUST NOT
  perform the requested method and MUST return a 412 (Precondition Failed)
  response.
- When an API does not support conditional headers or version checks, concurrent
  `PUT` or `PATCH` requests result in silent lost updates where the last write
  wins, discarding intermediate modifications without diagnostic warning.

### CWE-362 and CWE-367: Race Conditions and TOCTOU

MITRE CWE-362 defines race conditions:
> "The software performs concurrent operations on a shared resource that may
> alter the resource's state, but it does not perform adequate synchronization,
> which may result in unexpected or insecure behavior."

MITRE CWE-367 defines Time-of-Check to Time-of-Use (TOCTOU):
> "The software checks the state of a resource before using that resource, but
> the resource's state can change between the check and the use in a way that
> invalidates the results of the check."
Classic examples: checking file existence or user balance before writing/withdrawing,
where parallel threads pass the check before either decrements the balance.

### ANSI SQL Isolation Levels and Phenomena

ANSI/ISO SQL-92 and Berenson et al. (1995, "A Critique of ANSI SQL Isolation Levels"):
- Read Committed prevents Dirty Reads (P1) but permits Non-repeatable Reads (P2)
  and Phantom Reads (P3).
- Lost Update (P4): Transaction 1 reads $x$, Transaction 2 reads $x$, Transaction
  1 writes $x$, Transaction 2 writes $x$ based on its original read.
- To prevent Lost Update in relational databases, applications must use either:
  1. `SELECT ... FOR UPDATE` (pessimistic row locking)
  2. Version columns / timestamps with CAS (optimistic locking)
  3. Serializable isolation level.

## The observable oracle, checked at the source

Under negative concurrency attacks:
1. **No Lost Updates:** Given $N$ concurrent updates to an entity, the final
   state must reflect either all $N$ updates or exactly $K$ successful updates
   with $N-K$ explicit conflict errors (HTTP 409 or 412).
2. **Strict Invariant Bounds (No Double-Spend):** Given initial balance $B$
   and $M$ parallel requests each requesting $D$ where $M \times D > B$ but
   $D \le B$, the sum of approved debits must never exceed $B$, and final
   balance must satisfy $B_{final} \ge 0$.
3. **Deadlock Free / Fast Fail:** When two transactions acquire locks in
   opposing order, the system must detect deadlock and abort one transaction
   with a transient retryable error (e.g., PostgreSQL error code `40P01` or
   HTTP 503/409), never hanging indefinitely.

## What the lens should own

1. **Concurrent Read-Modify-Write (Lost Update):** Firing parallel update
   requests with identical base versions to verify optimistic locking.
2. **Check-Then-Act Race Exploitation (Double-Spend / Over-Allocation):**
   Firing simultaneous depletion requests against limited quotas, balances,
   or inventory.
3. **Thread Safety of Shared In-Memory Data Structures:** Probing global singletons,
   in-memory caches, or connection pools with concurrent worker threads.

## Recommendation: Proceed with standalone lens

**Verdict: Recommended.**
Concurrency bugs cannot be caught by single-invocation or sequential tests.
They represent critical financial, inventory, and data-integrity vulnerabilities.
A standalone `concurrency` lens with parallel probe tooling (e.g. `asyncio.gather`,
`threading`, or `Promise.all`) provides distinct, machine-verifiable oracles.

## Open questions

- Flakiness & Non-determinism: Race conditions depend on CPU scheduling. Probes
  must use barrier synchronization (`threading.Barrier`, `asyncio.Event`) to
  release requests simultaneously to maximize collision probability.
