# Seeded bugs (KEEP OUT OF ACCEPTANCE RUNS)

| id | module | lens | trigger | buggy behavior | oracle |
|---|---|---|---|---|---|
| java-1 | pagination | boundaries | `paginate(items, 0, 2)` | IndexOutOfBoundsException leaks | throw domain error naming page |
| java-2 | pagination | boundaries | empty list | subList bounds error | return empty list or named error |
| java-3 | pricing | missing | null discount | treated as zero silently | documented policy, explicit |
| java-4 | cart | boundaries | `maxQuantity(List.of())` | returns Integer.MIN_VALUE | throw `lines must not be empty` |
| java-5 | cart | malformed | negative quantity | accepts negative max | throw `qty must be positive` |
| java-6 | orders | state | `new CartSession().track("widget", 3)` then `.count()` | returns 0; count snapshot never invalidated | `count()` returns 3; derived read reflects state |
| java-7 | orders | ownership | `searchOrders(sessionAlice, "gizmo")` | returns bob's and alice's orders; session accepted but unapplied | only alice's orders; collection never leaks other users' rows |
| java-8 | orders | ordering | `completeCheckout(cid)` before `payCheckout(cid)` | creates order without payment; pay step skipped | throw `checkout must be paid before completion` |
| java-9 | orders | exceptional-conditions | `refundOrder(sessionAlice, 1, failingGateway)` | returns `{"refunded": true}`; swallows gateway error | throw `refund failed; gateway failure must not be silently swallowed` |
| java-10 | orders | resource-exhaustion | `batchLookupOrders(session, orderIds)` | processes unbounded batch without ceiling | throw `batch size exceeds maximum limit of 100` |
| java-11 | orders | concurrency | `reserveStock(sku, qty)` | two workers both succeed; stock double-reserved | throw `insufficient stock; concurrent requests must not double-reserve` |
| java-12 | orders | idempotency | `processPayment(orderId, amount, idempotencyKey)` | duplicate payment created on replay | return original payment; duplicate charge not created |
| java-13 | orders | dependency-failure | `getOrderRecommendations(session, orderId, recommender)` | throws unhandled error; upstream failure crashes | return `[]`; graceful degradation on recommender failure |
| java-14 | orders | contract | `exportOrderSummary(orderId)` | leaks internal fields `internalCost` and `gatewayRef` | return public schema fields only; internal fields stripped |
| java-15 | orders | security | `resolveReceiptPath(orderId, filename)` | returns unconstrained path escaping receipts dir | throw `path traversal outside receipts directory` |
| java-16 | orders | agent | `dispatchAgentTool("lookupOrder", {"orderId": "invalid"})` | raw ClassCastException leaks, crashing agent loop | return `{"isError": true, "error": ...}`; errors encapsulated |
