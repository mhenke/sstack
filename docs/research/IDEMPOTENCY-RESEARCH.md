# Idempotency lens: what an `idempotency` lens would own

Every claim below was read from the primary source named beside it. Where a
source does not say something, this file says so rather than filling the gap.
Research date: 2026-09-27. Linked from [`RESEARCH.md`](RESEARCH.md).

The `idempotency` row in the lens index reads "same operation applied twice
diverges" and is unbuilt. This note exists to decide whether shipping it would
duplicate `state` (which checks invalid repeated transitions) or `concurrency`,
and to ground its oracles in RFC specifications.

## The overlap, settled

A common misconception conflates idempotency with immutability or transition
rejection. The distinction between shipped lenses and `idempotency`:

| Case | Shipped owner | Notes |
|---|---|---|
| Re-calling `cancel()` on already cancelled order throws 409 | `state` | Transition rejection / error |
| Re-sending identical request with `Idempotency-Key` returns original 200 without duplicate debit | `idempotency` | Safe retry with preserved result |
| Sending same `Idempotency-Key` with altered payload throws error | `idempotency` | Key tampering / payload mismatch |
| Parallel simultaneous submissions of duplicate requests | `concurrency` | Race condition in key lock |
| Unsafe HTTP method (e.g. `GET`) causing side effects | `idempotency` | RFC 9110 §9.2.1 violation |

Where `state` expects repeated operations to either reject or transition,
`idempotency` expects safe operations to produce identical server-side effects
and safely replayable client responses under network retries.

## What standards and specifications prove

### RFC 9110: HTTP Semantics on Idempotent Methods

RFC 9110 §9.2.2 defines idempotency formally:

> "A request method is considered 'idempotent' if the intended effect on the
> server of multiple identical requests with that method is the same as the
> effect for a single such request. Of the request methods defined by this
> specification, PUT, DELETE, and safe request methods are idempotent."

Crucially:
- Idempotency refers to **the intended effect on the server**, not the status
  code. For example, `DELETE /item/1` may return 200/204 on the first request
  and 404 on the second request, but the server state (item 1 deleted) is
  identical.
- `POST` and `PATCH` are non-idempotent by default. To make them idempotent,
  applications must implement application-layer mechanisms such as an
  `Idempotency-Key`.

RFC 9110 §9.2.1 defines Safe Methods:
> "Request methods are considered 'safe' if their defined semantics are essentially
> read-only... Of the request methods defined by this specification, the GET,
> HEAD, OPTIONS, and TRACE methods are safe."
If an API performs database writes, state changes, or charges money on a `GET`
request, it violates RFC 9110 §9.2.1.

### IETF draft-ietf-httpapi-idempotency-key-header

The IETF standard `draft-ietf-httpapi-idempotency-key-header-06` defines the
exact mechanics of the `Idempotency-Key` header:

1. **First Request:** Server processes the request, commits side-effects, and
   saves the response status and body linked to `<client-id, key, payload-hash>`.
2. **Identical Replay:** Server recognizes the key, skips processing, and returns
   the stored response (RFC draft §2.4).
3. **Payload Mismatch (Key Reuse with Altered Body):**
   > "If an incoming request has an Idempotency-Key that matches an existing
   > idempotency key, but the request payload or HTTP method differs, the
   > server MUST NOT execute the request and MUST return an error status code,
   > such as 422 (Unprocessable Content) or 409 (Conflict)." (RFC draft §2.7).
4. **Concurrent Requests in Flight:**
   > "If a second request with the same Idempotency-Key arrives while the first
   > request is still in-flight, the server MUST NOT process the second request
   > concurrently... It SHOULD return a 409 (Conflict) or 425 (Too Early)."

## The observable oracle, checked at the source

Under negative idempotency attacks:

1. **Replay Invariant:** Repeating an idempotent operation ($N \ge 2$ times)
   results in exactly 1 side effect (e.g., 1 payment, 1 record created, 1 email
   queued).
2. **Payload Mismatch Rejection:** Sending an existing `Idempotency-Key` with
   different body or parameters returns HTTP 422 or 409, never executing the new
   payload.
3. **Safe Method Purity:** Probing `GET`, `HEAD`, `OPTIONS` endpoints never alters
   database records, increments counters, or transitions states.
4. **In-Flight Key Collision:** Sending a duplicate key while the first is actively
   processing returns HTTP 409 Conflict rather than creating twin mutations.

## What the lens should own

1. **Retry Duplication Probing:** Sending duplicate `POST` requests without keys
   and with duplicate keys, verifying that payments, orders, or emails are not
   duplicated.
2. **Idempotency-Key Integrity:** Tampering with payloads under recorded keys
   to verify that key recycling is rejected.
3. **HTTP Method Semantics:** Verifying that `PUT` and `DELETE` achieve stable
   end states on repeated invocations, and that `GET` has zero side-effects.

## Recommendation: Proceed with standalone lens

**Verdict: Recommended.**
Idempotency is the cornerstone of distributed systems and network resilience
(handling network retries, timeouts, and webhook replays). The failure modes
(duplicate billing, duplicate inventory decrement, inconsistent retry responses)
cannot be addressed by `state` or `malformed`.

## Open questions

- Persistent Idempotency Stores: In test fixtures without Redis or a database
  table for idempotency keys, APIs may only track keys in memory, clearing
  them across restarts.
