# Seeded bugs (KEEP OUT OF ACCEPTANCE RUNS)

This file is the answer key. `evals/acceptance.py` strips it when
copying the repo for a cold run. Fixes below are the canonical
negative-control fixes.

| id | module | lens | trigger | buggy behavior | oracle | fix note |
|---|---|---|---|---|---|---|
| ts-1 | pagination | boundaries | `paginate(items, 0, 3)` | returns `[]` silently (negative slice clamps; no validation) | `throw Error("page must be >= 1")` | validate page/size |
| ts-2 | pricing | missing | `lineTotal({qty: 2})` | returns `NaN` silently | `throw Error("unitPrice is required")` | `Number.isFinite` check |
| ts-3 | pricing | malformed | `parseOrder("{oops")` | raw `SyntaxError` leaks | `throw Error("invalid order JSON")` | try/catch, rethrow domain error |
| ts-4 | cart | boundaries | `maxQuantity([])` | returns `-Infinity` | `throw Error("lines must not be empty")` | length check before `Math.max` |
| ts-5 | cart | malformed | qty as string `"2"` in lines | returns `"023"` (string) | `throw Error("qty must be a number")` | `typeof l.qty === "number"` check |
| ts-6 | orders | state | `new CartSession().track("widget", 3)` then `.count()` | `0` — `_count` snapshotted in constructor, never invalidated by `track` | `count()` returns `3`; a derived read reflects current state | recompute in `count()`, or update `_count` in `track` |
| ts-7 | orders | ownership | `searchOrders(sessionAlice, "gizmo")` | returns bob's and alice's orders; `session` is accepted but never used to filter | only alice's order with that sku | filter on `session.userId` before the sku match |
| ts-8 | orders | ordering | `completeCheckout(cid)` before `payCheckout(cid, ...)` | creates order without payment; pay step skipped | `Error: checkout must be paid before completion` | check `chk.paid` in `completeCheckout` |
| ts-9 | orders | exceptional-conditions | `refundOrder(sessionAlice, 1, failingGateway)` | returns `{"refunded": true}`; swallows gateway exception | `Error: refund failed` | check gateway response or rethrow domain error |
| ts-10 | orders | resource-exhaustion | `batchLookupOrders(session, Array.from({length: 1000}, (_, i) => i))` | processes unbounded batch without ceiling | `Error: batch size exceeds maximum limit of 100` | validate `orderIds.length <= 100` before query loop |
| ts-11 | orders | concurrency | parallel `reserveStock("gizmo", 2)` | double-reservation; two workers both succeed reserving 2 of 2 | `Error: insufficient stock` on second worker | serialize reservation with lock or atomic check |
| ts-12 | orders | idempotency | `processPayment(1, 50.0, "key-1")` called twice | duplicate payment created on replay; new payment id allocated | return original payment; duplicate charge not created | check key in store and return cached payment |
| ts-13 | orders | dependency-failure | `getOrderRecommendations(sessionAlice, 1, failingRecommender)` | throws unhandled error; upstream failure crashes recommendations | return `[]`; graceful degradation when recommendation service fails | catch upstream exceptions and return empty array fallback |
| ts-14 | orders | contract | `exportOrderSummary(1)` | leaks internal database fields `internalCost` and `gatewayRef` | return public schema fields only; undeclared internal fields stripped | filter against public contract fields before returning |
| ts-15 | orders | security | `resolveReceiptPath(1, "../../etc/passwd")` | returns unconstrained traversal path escaping receipts directory | `Error: path traversal outside receipts directory` | verify canonical path starts with receiptsDir |
| ts-16 | orders | agent | `dispatchAgentTool("lookupOrder", {orderId: "invalid"})` | raw TypeError leaks, crashing agent loop | return `{"isError": true, "error": "orderId must be a number"}`; tool errors encapsulated as structured error result | wrap tool handler invocation in try/catch and return isError payload |

