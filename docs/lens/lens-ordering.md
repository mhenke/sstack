# Negative Testing: Ordering Lens

Research on negative testing for operation ordering, multi-step workflow bypasses, inverted execution sequences, step skipping, out-of-order event consumption, and pipeline sequence invariants.

## Overview & Definition

Negative testing for ordering evaluates how software behaves when operations, API requests, method calls, or asynchronous messages arrive in an unexpected, out-of-sequence, or inverted order.

While single-surface validation checks the payload of an individual call, ordering negative testing targets the sequence dependency graph. A resilient system must strictly enforce prerequisites between workflow steps, reject out-of-sequence invocations with explicit conflict diagnostics (e.g., HTTP 409 Conflict), and maintain transactional consistency without allowing users or external consumers to bypass intermediary validation, payment, or authorization stages.

## Core Concepts & Failure Modes

1. **Workflow Step Skipping & Stage Bypassing (CWE-841):**
   - Directly invoking finalization steps (e.g., `POST /checkout/confirm`) without completing intermediate payment verification or address confirmation.
   - Accessing multi-stage registration/onboarding steps out of order to evade identity verification or required disclosures.
2. **Inverted Protocol & Pipeline Sequences (CWE-696):**
   - Calling dependent lifecycle operations before initialization (e.g., calling `read()` or `write()` before `handshake()` / `open()`).
   - Triggering `commit()` before `prepare()`, or `close()` before `flush()`.
   - Data pipeline stages executed backwards (e.g., attempting decompression before decryption when the wire format is compressed-then-encrypted).
3. **Out-of-Order Asynchronous Event Processing:**
   - Distributed event streams where an update event (e.g., `EntityUpdated`, sequence 2) arrives before creation (`EntityCreated`, sequence 1).
   - Deletion events arriving before creation events, leading to resurrection bugs (creating the entity after it was marked deleted).
4. **Premature Completion & Premature Settlement:**
   - Attempting to complete or fulfill an order, task, or contract while dependent background jobs (e.g., fraud check, inventory reservation) are still pending.
5. **Reversed Teardown / Resource Deallocation:**
   - Closing database connection pools or parent context objects before active child transactions complete.
   - Deallocating memory or file handles while dependent processing queues still hold references.

## Real-World Examples & Test Scenarios

### Scenario 1: Multi-Step E-Commerce Checkout Step Skipping
- **Contract:** Checkout requires `POST /cart/shipping` $\to$ `POST /cart/payment` $\to$ `POST /cart/confirm`.
- **Negative Inputs:**
  - Client creates cart, then directly calls `POST /cart/confirm` with cart ID, skipping shipping and payment endpoints entirely.
- **Expected Oracle:** HTTP 409 Conflict or 400 Bad Request (`{"error": "precondition_failed", "missing_step": "payment"}`). The order is not created; no inventory is decremented or shipment booked.

### Scenario 2: Account Onboarding Prerequisite Bypass
- **Contract:** User creation flow requires `POST /users/register` $\to$ `POST /users/verify-email` $\to$ `POST /users/activate`.
- **Negative Inputs:**
  - Client calls `POST /users/activate` immediately after registration without having submitted a valid email verification token.
- **Expected Oracle:** HTTP 409 Conflict or 403 Forbidden with diagnostic (`{"error": "email_unverified"}`). Account status remains `pending_verification`.

### Scenario 3: Inverted Data Pipeline Call Sequence
- **Contract:** Stream cipher wrapper requires `cipher.init(key)` $\to$ `cipher.update(data)` $\to$ `cipher.final()`.
- **Negative Inputs:**
  - Caller invokes `cipher.update(chunk)` before calling `cipher.init(key)`.
- **Expected Oracle:** Throws explicit domain exception (`InvalidOperationError: Cipher must be initialized before processing data`) instead of unhandled null pointer dereference, segfault, or emitting raw unencrypted plaintext.

### Scenario 4: Out-of-Order Message Processing in Event Consumer
- **Contract:** Consumer receives CDC (Change Data Capture) messages with monotonic sequence numbers.
- **Negative Inputs:**
  - Ingestion receives sequence #5 (`CustomerAddressUpdated`) before sequence #1 (`CustomerCreated`).
- **Expected Oracle:** Consumer either buffers sequence #5 in a dead-letter/hold queue or returns an explicit sequencing nack/retry error. It never inserts a orphaned record with null primary attributes.

### Scenario 5: Database Transaction Savepoint Inversion
- **Contract:** Transactional flow requires `BEGIN` $\to$ `SAVEPOINT sp1` $\to$ `RELEASE SAVEPOINT sp1` $\to$ `COMMIT`.
- **Negative Inputs:**
  - Application code calls `ROLLBACK TO SAVEPOINT sp2` where `sp2` was never declared or was already released.
- **Expected Oracle:** Clean transaction abort with specific error indicating non-existent savepoint. The outer transaction does not silently continue into a partially committed state.

## Key Oracle Patterns

- **Explicit Sequencing Errors:** Rejections identify exactly which prerequisite step or sequence condition was unfulfilled (HTTP 409 Conflict, RFC 9110 §15.5.10).
- **Zero Partial State Mutations:** An out-of-order operation causes zero database mutations, external API calls, or side effects.
- **Enforced Step Invariants:** Every stage validates cryptographically signed session tokens, database-backed state flags, or monotonic sequence counters before proceeding.
- **No Unhandled Pointer / Key Crashes:** Calling methods out of sequence fails with clean domain error types rather than raw runtime crashes (`AttributeError: 'NoneType' object has no attribute 'session'`).
- **Idempotent Precondition Guards:** Verifying prerequisites produces no state changes of its own if the condition is not met.

## Primary Sources & References

- RFC 9110: HTTP Semantics §15.5.10 (409 Conflict), §15.5.23 (428 Precondition Required)
- RFC 7231: Hypertext Transfer Protocol (HTTP/1.1): Semantics and Content
- CWE-841: User-Controlled Critical Execution Sequence
- CWE-696: Incorrect Behavior Order
- OWASP API Security Top 10: API6:2023 (Unrestricted Access to Sensitive Business Flows)
- Leslie Lamport, "Time, Clocks, and the Ordering of Events in a Distributed System" (CACM, 1978)
- Enterprise Integration Patterns: Resequencer / Message Ordering Patterns
