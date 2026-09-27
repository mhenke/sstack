# Negative Testing: State Lens

Research on negative testing for lifecycle state machines, invalid transitions, shared mutable state, race conditions, concurrency bugs, and out-of-order events.

## Overview & Definition

Negative testing for state evaluates how software behaves across sequences of operations: when commands execute out of order, during incompatible lifecycle states, concurrently across race windows, or against shared mutable memory.

While other lenses test a single invocation in isolation, the state lens attacks the sequence around it. A robust state model must enforce strict transition invariants, reject commands invalid in the current lifecycle state, isolate in-memory mutable data against caller pollution, invalidate derived caches on mutation, guarantee all-or-nothing rollback on partial failures, and serialize concurrent mutations without double-spending or split-brain inconsistencies.

## Core Concepts & Failure Modes

1. **Illegal Lifecycle Transitions & Post-Disposal Operations (CWE-672):**
   - Attempting operations valid only in state $S_1$ while in state $S_2$ (e.g., paying for an already cancelled order, capturing an unapproved authorization, archiving an active subscription).
   - Re-initializing an already initialized object, connection, or singleton.
   - Invoking methods or sending commands to closed, disposed, aborted, or shut-down instances.
2. **Escaped Mutable References & Live View Exposure (CWE-375):**
   - Accessors/getters returning references to internal mutable collections, dictionaries, or objects without defensive copying or read-only wrapping.
   - External callers mutating the returned reference, silently corrupting the owner's internal invariants without traversing validation methods.
3. **Parameter Mutation & Write-Through Hazards (CWE-374):**
   - Functions mutating caller-owned arguments (in-place sorting, popping, clearing, or modifying nested fields) when the contract specifies an immutable calculation or pure transformation.
   - Callers experiencing unexpected side effects in subsequent operations on their own data.
4. **Stale Derived State & Broken Cache Invalidation:**
   - Reading cached, memoized, or precomputed derived fields (balances, aggregates, totals, flags) after underlying state has mutated without cache eviction or invalidation.
   - Performing writes based on stale version tokens without optimistic concurrency checks.
5. **Partial Updates & Broken Failure Atomicity (CWE-366):**
   - Multi-step or batch operations encountering an error halfway through execution (e.g., failure on step 3 of 5) and leaving the system in a half-applied, inconsistent state instead of rolling back to the pre-call baseline.
6. **Race Conditions & Time-of-Check to Time-of-Use (TOCTOU) (CWE-362, CWE-367):**
   - Concurrent requests executing against a shared balance, quota, or inventory count before the deduction lock is acquired (limit overrun, double-spend).
   - Simultaneous registration of the same unique slug, resource, or identifier bypassing validation before transaction commit.
7. **Out-of-Order & Replay Events:**
   - Asynchronous event delivery where message $N+1$ (e.g., `ShipmentCompleted`) arrives before message $N$ (`OrderCreated`).
   - Duplicate delivery of webhooks or payment notifications without idempotent deduplication keys.

## Real-World Examples & Test Scenarios

### Scenario 1: Illegal State Machine Transition
- **Contract:** Order states: `Created` -> `Paid` -> `Shipped` -> `Delivered` or `Cancelled`.
- **Negative Action:** Client invokes `POST /orders/{id}/cancel` on an order already marked `Shipped`.
- **Expected Oracle:** HTTP 409 Conflict or `IllegalStateError: Cannot cancel an order that has already shipped`. State remains strictly `Shipped`.

### Scenario 2: Escaped Internal Collection Reference
- **Contract:** An `AccountGroup` maintains a private list of authorized member IDs; additions must pass validation.
- **Negative Action:** Caller invokes `group.get_members()`, receives the internal mutable list reference, and executes `list.append(unauthorized_id)`.
- **Expected Oracle:** Calling `group.get_members()` returns an immutable view or defensive copy. In-place modification of the returned structure has zero effect on the internal group roster or subsequent `group.is_authorized(...)` checks.

### Scenario 3: Callee Parameter Write-Through Mutation
- **Contract:** A formatting function `format_schedule(events)` formats and returns a display string.
- **Negative Action:** Function performs in-place sorting on the passed `events` list (`events.sort(...)`).
- **Expected Oracle:** Caller's original `events` list maintains its exact original ordering and identity after the function returns; the function sorts an internal copy or uses non-mutating sort.

### Scenario 4: Broken Atomicity on Mid-Operation Failure
- **Contract:** `batch_transfer(source_account, transfers)` processes multiple deductions as an atomic transaction.
- **Negative Action:** Third transfer in a list of five triggers an invalid routing code error.
- **Expected Oracle:** Transaction aborts and rolls back all mutations; deductions 1 and 2 are reverted. `source_account.balance` matches its pre-operation value exactly.

### Scenario 5: Concurrent Double-Spend / Limit Overrun
- **Contract:** A promotional coupon or gift balance can only be redeemed once per account.
- **Negative Action:** Client fires 10 simultaneous requests with the same coupon code within a 5-millisecond window.
- **Expected Oracle:** Exactly 1 request succeeds (HTTP 200); remaining 9 requests fail with HTTP 409 Conflict / 400 (`Coupon already redeemed`). The discount is applied exactly once to the ledger.

### Scenario 6: Stale Version Replay (Optimistic Concurrency)
- **Contract:** Updating resource requires passing current version token (`ETag` or `version_id`).
- **Negative Action:** Client passes `version_id = 1` when state has already advanced to `version_id = 2`.
- **Expected Oracle:** Request rejected with HTTP 412 Precondition Failed or `StaleObjectStateException`. Database record is not overwritten.

## Key Oracle Patterns

- **Explicit State & Transition Rejection (409 Conflict):** Illegal transitions return structured errors explicitly naming the current state and why the action is disallowed.
- **State Invariant & Rollback Preservation:** If any operation fails midway, internal state cleanly rolls back to its exact pre-operation baseline with no orphaned side effects.
- **Defensive Copying & Reference Encapsulation:** Internal mutable structures handed to callers are immutable views or isolated copies; mutating them never mutates the owner.
- **Parameter Non-Interference:** Callee functions never mutate caller-owned input structures in-place unless explicitly contracted as a mutating method.
- **Immediate Derived Cache Invalidation:** Derived reads (counts, totals, flags) reflect underlying mutations immediately, or staleness is explicitly documented and bounded.
- **Deterministic Concurrency Serialization:** Critical mutation paths enforce atomic check-and-set semantics or optimistic version checks (`If-Match` / 412); concurrent attempts yield a single deterministic winner.

## Interaction with Other Lenses

In the sstack taxonomy (`docs/ARCHITECTURE.md`), the `Behavior` category splits into four lenses:

- **`state` (shipped):** Owns an object or entity's lifetime and shared mutable state—stale derived views, escaping internal collections, parameter write-through, mid-operation rollback failure, and invalid state machine transitions.
- **`ordering` (custom/future):** Owns operations applied out of sequence across separate endpoints or pipeline stages (e.g. delivery before payment).
- **`concurrency` (custom/future):** Owns parallel multi-threaded/multi-process race windows, thread synchronization primitives, and distributed lock contention.
- **`idempotency` (custom/future):** Owns identical requests applied multiple times across network retries diverging or executing redundant side effects.

Where `concurrency` or `idempotency` are not configured as active custom lenses, `state` verifies that single-winner semantics, optimistic concurrency version checks, and basic duplicate rejections preserve state integrity.

## Primary Sources & References

- Martin Fowler, *Patterns of Enterprise Application Architecture* (Optimistic Offline Lock, Pessimistic Offline Lock, State Pattern)
- Joshua Bloch, *Effective Java* (Item 50: Make defensive copies when needed)
- OWASP Web Security Testing Guide: Testing for Race Conditions (WSTG-ATHN-09)
- PortSwigger Web Security Academy: Race Conditions & Limit Overrun Vulnerabilities
- CWE-362: Concurrent Execution using Shared Resource with Improper Synchronization ('Race Condition')
- CWE-367: Time-of-check Time-of-use (TOCTOU) Race Condition
- CWE-374: Passing Mutable Objects to an Untrusted Method
- CWE-375: Returning a Mutable Object to an Untrusted Caller
- CWE-672: Operation on Resource After Expiration or Release
- CWE-366: Race Condition within a Thread / Incomplete Multi-step Operations
- RFC 9110 §15.5.13 / RFC 7232: HTTP Semantics – 412 Precondition Failed & Conditional Requests
