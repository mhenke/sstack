---
name: sstack-idempotency
description: "Idempotency lens rubric. Case-generation heuristics, oracle patterns, and worked examples for retried operations, duplicate requests, Idempotency-Key collisions and payload tampering, and safe method purity. Loaded inline under ### Lens rubric."
disable-model-invocation: true
---

# Idempotency lens

Attacks every mapped surface through the idempotency lens: that
repeating an identical operation produces the same server-side state
as a single invocation. While other lenses attack payloads or single-call
lifecycles, this lens attacks network retries, duplicate submissions,
and at-least-once message processing.

## Case-generation heuristics

- Mutation replay: execute a state-changing mutation ($POST$, method call),
  capture the response, and replay the identical request multiple times
  ($N \ge 2$) with and without idempotency keys.
- Payload divergence mutation (IETF draft §2.7): execute a request with an
  `Idempotency-Key` and valid payload $P$. Then submit a second request
  reusing that exact key with a minimal single-field mutation $P'$
  (e.g. modified amount, recipient, or action). Verifies the key binds to
  a cryptographic digest of the payload rather than caching blindly.
- In-flight duplicate submission: send parallel requests with the same
  idempotency key simultaneously before the first request finishes.
- Safe method side-effect verification: execute `GET`, `HEAD`, or `OPTIONS`
  requests and verify zero state mutations, zero counter increments, and
  zero database updates.
- Repeated deletion stability: invoke `DELETE` or cleanup operations
  repeatedly to verify stable end-states without leaking unhandled 500 errors.

## Oracle patterns

- Effect conservation: for $N$ identical invocations, total server-side
  state mutation equals exactly 1 invocation (no duplicate debits, orders,
  or emails).
- Replay fidelity: subsequent retries under matching idempotency keys
  return the original response without re-executing business logic.
- Payload divergence rejection: reusing an existing key with altered parameters
  ($P \neq P'$) returns RFC 9110 HTTP 409 Conflict (or 422 Unprocessable Content)
  naming the payload mismatch; the server never returns the cached 200 response
  for $P$ and never executes the mutated action $P'$.
- In-flight collision protection: concurrent requests sharing an active key
  reject with 409 Conflict or 425 Too Early.

Worked example — Python `BillingService.charge_customer(customer_id, amount, idempotency_key)`:
re-submitting identical charge with same key returns original receipt, oracle
charges customer exactly once and returns existing receipt ID `rec_100`,
observed (bug) executes a second charge and generates twin receipt `rec_101`.

TypeScript `publishWebhook(eventId, payload)`: delivering the same webhook
payload twice, oracle recipient processes payload once and acknowledges second
delivery as duplicate, observed (bug) fulfills shipment twice.

## Failure modes to watch for

- Double-billing / duplicate record creation: failing to deduplicate client retries.
- Key recycling without payload hash binding (RFC draft §2.7): executing new actions
  under recycled idempotency keys.
- Safe method mutation (RFC 9110 §9.2.1): modifying state on `GET` requests.
- DELETE non-idempotence: crashing with unhandled exceptions on repeat deletions.

## Language notes

### Python

- Dictionaries as caches: in-memory key stores must be scoped with TTLs
  or persisted in shared backends (Redis/PostgreSQL) to survive worker restarts.
- Flask/FastAPI middleware: decorators checking idempotency headers must
  verify payload hashes (`hashlib.sha256(request.get_data()).hexdigest()`).

### JavaScript / TypeScript

- Express/NestJS: middleware intercepting `Idempotency-Key` headers must store
  cached responses before sending headers and return cached bytes directly.
- MongoDB / SQL upserts: prefer `ON CONFLICT DO UPDATE` or atomic `$setOnInsert`.

### Java

- Spring `@Retryable`: retried operations must explicitly bind to transaction
  identifiers or idempotency tokens.
- JAX-RS / Spring MVC: filter filters duplicate requests before controller
  invocation.

### C++

- Network protocol servers: RPC sequence IDs must deduplicate duplicate packet
  deliveries at the transport session layer.

## When not to apply

The surface is an inherently non-idempotent event logger where every event
must record a unique timestamped occurrence (e.g. append-only audit trail
or physical sensor tick stream).

## Interaction with other lenses

`idempotency` owns duplicate retries and replay fidelity. Single-threaded
lifecycle progression belongs to `state`. Workflow stage skipping belongs to
`ordering`. Parallel collision races belong to `concurrency`.
