# Negative Testing: Idempotency Lens

Research on negative testing for operation replays, network retries, duplicate submissions, `Idempotency-Key` collisions and payload tampering, HTTP method safety invariants, and at-least-once message processing.

## Overview & Definition

Negative testing for idempotency evaluates how systems respond when the same request or mutation is submitted multiple times—due to network timeouts, automated client retries, user double-clicks, or distributed queue re-deliveries.

In a resilient architecture, repeating an idempotent request must yield the same server-side outcome as a single execution. Under negative idempotency attacks, systems must prevent duplicate financial charges, duplicate database entity creation, and race conditions during in-flight retries. Furthermore, systems supporting `Idempotency-Key` headers must strictly reject attempts to reuse an existing key with altered request parameters (RFC draft §2.7).

## Core Concepts & Failure Modes

1. **Duplicate Mutation on Retry (Double-Billing / Double-Creation):**
   - Resending a `POST /payments` or `POST /orders` request when a prior call timed out on the network.
   - Server creates a second charge or duplicate order instead of recognizing the duplicate transaction.
2. **Idempotency-Key Payload Mismatch / Key Recycling:**
   - Client sends Request 1 with `Idempotency-Key: "k-100"` and payload `{"amount": 10}`.
   - Client subsequently sends Request 2 with `Idempotency-Key: "k-100"` but payload `{"amount": 50}`.
   - Conforming systems must reject Request 2 with HTTP 422 or 409. Vulnerable systems either execute the second charge or silently return the original response with the wrong amount.
3. **In-Flight Concurrent Idempotency Key Collisions:**
   - Multiple identical requests with the same `Idempotency-Key` arrive simultaneously while the first request is actively executing.
   - Systems lacking distributed key locks (e.g. Redis mutex) execute both concurrently, defeating the idempotency guarantee.
4. **Unsafe HTTP Method Side Effects (RFC 9110 §9.2.1):**
   - Endpoints using `GET` or `HEAD` methods that trigger database mutations, balance deductions, or state transitions.
   - Web crawlers, pre-fetchers, or caching proxies unintentionally triggering financial or business mutations.
5. **PUT / DELETE Divergence & State Drift (RFC 9110 §9.2.2):**
   - Calling `PUT /resource` multiple times with identical payloads causing incremental side effects (e.g., re-triggering webhook dispatch loops or appending duplicate audit log entries per call).
   - Calling `DELETE /resource` failing with an unhandled 500 error on the second call instead of returning a clean 204 or 404.

## Real-World Examples & Test Scenarios

### Scenario 1: Retried Payment with Same Idempotency Key
- **Contract:** `POST /api/v1/charges` accepts `Idempotency-Key: <uuid>`.
- **Negative Inputs:**
  - Client sends `POST /api/v1/charges` with `Idempotency-Key: "uuid-123"` and body `{"amount": 25.00}`.
  - Client repeats the identical call 3 times.
- **Expected Oracle:** First call returns HTTP 201 with charge ID `ch_abc`. Subsequent 2 calls return HTTP 200/201 with the exact same charge ID `ch_abc` and payload. The underlying payment processor is charged exactly once ($25.00 total debit).

### Scenario 2: Idempotency Key Reused with Altered Payload
- **Contract:** Endpoint verifies that an `Idempotency-Key` strictly binds to the request body hash.
- **Negative Inputs:**
  - Request 1: `POST /orders` (`Idempotency-Key: "order-999"`, body: `{"item": "laptop", "qty": 1}`).
  - Request 2: `POST /orders` (`Idempotency-Key: "order-999"`, body: `{"item": "mouse", "qty": 5}`).
- **Expected Oracle:** Request 2 is rejected with HTTP 422 Unprocessable Content or 409 Conflict (`{"error": "idempotency_payload_mismatch"}`). No mouse order is created; original laptop order remains unaffected.

### Scenario 3: Simultaneous Duplicate Requests in Flight
- **Contract:** Endpoint handles concurrent duplicate submissions gracefully.
- **Negative Inputs:**
  - Two parallel threads submit `POST /transfers` with the identical `Idempotency-Key: "tx-456"` at the exact same millisecond.
- **Expected Oracle:** Exactly one request executes the transfer. The second request either blocks until the first completes (returning the same result) or immediately returns HTTP 409 Conflict / 425 Too Early. Under no circumstance are two transfers initiated.

### Scenario 4: Side Effects on Safe HTTP Methods
- **Contract:** RFC 9110 §9.2.1 mandates `GET /users/1/unsubscribe` must be read-only.
- **Negative Inputs:**
  - Automated scanner sends repeated `GET /reports/generate` or `GET /accounts/1/toggle-status`.
- **Expected Oracle:** Request fails with HTTP 405 Method Not Allowed if state modification is intended, or GET is purely idempotent and read-only without toggling account status.

### Scenario 5: Webhook Replay Protection
- **Contract:** Webhook receiver at `/webhooks/stripe` processes incoming event notifications.
- **Negative Inputs:**
  - The same webhook event payload with `event_id: "evt_789"` is delivered 5 times.
- **Expected Oracle:** Receiver returns HTTP 200 on all 5 deliveries, but only performs the database order fulfillment on delivery #1. Deliveries 2–5 log duplicate receipt and short-circuit immediately.

## Key Oracle Patterns

- **Server-Side Effect Conservation:** For $N$ identical invocations, total state mutation equals exactly 1 invocation.
- **Replay Fidelity:** Subsequent retries with matching idempotency keys return identical response bodies, headers, and status codes without re-running business logic.
- **Tampering Detection:** Any modification to HTTP method, URL path, or request payload under an existing idempotency key fails with HTTP 422 / 409.
- **Clean Deletion Idempotence:** Multiple identical `DELETE` requests leave the system in the same final state (resource deleted) without leaking unhandled exceptions on repeat.

## Primary Sources & References

- RFC 9110: HTTP Semantics §9.2.1 (Safe Methods), §9.2.2 (Idempotent Methods)
- IETF Internet-Draft: draft-ietf-httpapi-idempotency-key-header-06 (The Idempotency-Key HTTP Header Field)
- Stripe API Reference: Idempotent Requests
- AWS Architecture Center: "Making retries safe with idempotent APIs"
- Enterprise Integration Patterns: Idempotent Receiver Pattern
