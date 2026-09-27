# Negative Testing: Concurrency Lens

Research on negative testing for race conditions, concurrent read-modify-write conflicts, TOCTOU vulnerabilities, lost updates, double-spend anomalies, deadlock detection, and thread-safety invariants.

## Overview & Definition

Negative testing for concurrency attacks software under simultaneous, parallel, or interleaved operations competing for shared state, memory, or external resources.

While functional testing executes operations sequentially, concurrency negative testing deliberately synchronizes parallel requests to collide inside critical sections. A resilient system must maintain strict ACID consistency, eliminate Time-of-Check to Time-of-Use (TOCTOU) windows, prevent lost updates through atomic compare-and-swap or optimistic locking (RFC 7232 / 412 Precondition Failed), and ensure that parallel operations cannot exceed balances, quotas, or inventory ceilings.

## Core Concepts & Failure Modes

1. **Lost Updates in Concurrent Read-Modify-Write (CWE-362):**
   - Two or more processes read record version $V$, compute new values independently, and write back. The second write silently overwrites the first, discarding modifications.
   - Failure to use conditional HTTP headers (`If-Match: ETag`) or SQL optimistic concurrency controls (`WHERE version = :expected`).
2. **Time-of-Check to Time-of-Use (TOCTOU) Exploitation (CWE-367):**
   - Checking balance, permission, or coupon validity in one step, then executing the action in a subsequent step without an atomic lock.
   - Parallel requests passing the check concurrently before any debit occurs, resulting in double-spending or unauthorized actions.
3. **Double-Spend & Quota Oversubscription:**
   - Account balance has $100. Two parallel requests for $100 arrive simultaneously.
   - If withdrawal logic executes as `if balance >= amount: balance -= amount` without row locks or atomic constraints, both withdrawals succeed, driving the balance to -$100.
4. **Deadlocks and Lock Ordering Inversions (CWE-833):**
   - Transaction $A$ locks Resource 1 then requests Resource 2; Transaction $B$ locks Resource 2 then requests Resource 1.
   - Failure to acquire locks in a globally deterministic order, leading to hung threads or worker pool starvation.
5. **Non-Thread-Safe Shared Collections & In-Memory State:**
   - Concurrent appends, reads, or mutations on standard dictionaries, hash maps, or lists in multi-threaded runtimes without mutex synchronization.
   - Resulting in memory corruption, infinite loops (e.g. Java `HashMap` rehashing race), or corrupted array lengths.

## Real-World Examples & Test Scenarios

### Scenario 1: Parallel Double-Withdrawal (Double-Spend)
- **Contract:** Account balance is $50. Minimum allowed balance is $0.
- **Negative Inputs:**
  - Two parallel requests simultaneously call `POST /accounts/123/withdraw` with `{"amount": 50}` released via synchronization barrier.
- **Expected Oracle:** Exactly one request succeeds with HTTP 200/204; the other fails with HTTP 409 Conflict or 422 Unprocessable Content (`{"error": "insufficient_funds"}`). Final account balance is exactly $0, never -$50.

### Scenario 2: Concurrent Lost Update on Profile Resource
- **Contract:** Endpoint `PUT /api/v1/users/456` updates contact details using conditional header `If-Match: "etag_v1"`.
- **Negative Inputs:**
  - Client A submits update with `If-Match: "etag_v1"`. Client B simultaneously submits update with `If-Match: "etag_v1"`.
- **Expected Oracle:** First client receives HTTP 200 and increments ETag to `"etag_v2"`. Second client receives HTTP 412 Precondition Failed. Client B's update is rejected rather than overwriting Client A's changes.

### Scenario 3: Single-Use Promo Code Race Condition
- **Contract:** A promotional code has usage limit = 1 across the entire platform.
- **Negative Inputs:**
  - 10 parallel threads simultaneously submit checkout requests with the same promo code for 10 distinct users.
- **Expected Oracle:** Exactly 1 checkout completes with the discount applied; 9 checkouts fail the discount check with HTTP 409 Conflict. Total discount applied is $1\times$, never $10\times$.

### Scenario 4: Concurrent Inventory Allocation
- **Contract:** Flash sale item has remaining inventory = 1.
- **Negative Inputs:**
  - 5 parallel requests attempt to reserve the final item simultaneously.
- **Expected Oracle:** Exactly 1 reservation is granted. 4 requests receive HTTP 409 Conflict (`{"error": "item_out_of_stock"}`). Stock count remains 0, never negative.

### Scenario 5: Cyclic Lock Ordering Deadlock Detection
- **Contract:** Transfer funds between Account $X$ and Account $Y$ locks both accounts.
- **Negative Inputs:**
  - Thread 1 transfers $X \to Y$ (locks $X$, then $Y$). Thread 2 transfers $Y \to X$ (locks $Y$, then $X$).
- **Expected Oracle:** Either deterministic lock ordering prevents deadlock entirely, or database deadlock detector immediately kills one transaction with retryable error (HTTP 409 or 503) within milliseconds. Neither thread hangs indefinitely.

## Key Oracle Patterns

- **Conservation Invariant:** Consumable quantities (money, inventory, quotas, seat counts) must sum to exactly the initial total minus successful consumed units. No phantom creation or negative balances.
- **Deterministic Conditional Rejection:** At least $N-1$ conflicting parallel requests receive HTTP 412 (Precondition Failed) or HTTP 409 (Conflict).
- **Fast Lock Failover:** Contested locks fail with immediate timeout or explicit rollback error rather than hanging workers or exhausting connection pools.
- **Atomic Read-Modify-Write:** All state checks and mutations occur within an atomic database transaction or synchronization primitive (`CAS`, mutex, `SELECT FOR UPDATE`).

## Primary Sources & References

- RFC 7232: Hypertext Transfer Protocol (HTTP/1.1): Conditional Requests (§3.1 If-Match, §3.2 If-None-Match, §4.2 412 Precondition Failed)
- RFC 9110: HTTP Semantics §13.1.1 (Conditional Requests), §15.5.13 (412 Precondition Failed)
- CWE-362: Concurrent Execution using Shared Resource with Improper Synchronization ('Race Condition')
- CWE-367: Time-of-check Time-of-use (TOCTOU) Race Condition
- CWE-833: Deadlock
- Hal Berenson et al., "A Critique of ANSI SQL Isolation Levels" (ACM SIGMOD, 1995)
- OWASP API Security Top 10: API6:2023 (Business Logic Vulnerabilities / Race Conditions)
