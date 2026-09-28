# Seeded bugs (KEEP OUT OF ACCEPTANCE RUNS)

| id | module | lens | trigger | buggy behavior | oracle |
|---|---|---|---|---|---|
| js-1 | pagination | boundaries | `paginate(items, 0, 3)` | returns [] silently | throw `page must be >= 1` |
| js-2 | pricing | missing | `lineTotal({qty: 2})` | returns NaN | throw `unitPrice is required` |
| js-3 | pricing | malformed | `parseOrder("{oops")` | raw SyntaxError | throw `invalid order JSON` |
| js-4 | cart | boundaries | `maxQuantity([])` | returns -Infinity | throw `lines must not be empty` |
| js-5 | cart | malformed | qty as string `"2"` | returns string `"02"` | throw `qty must be a number` |
| js-6 | orders | state | `new CartSession().track('widget', 3)` then `.count()` | returns 0; #count snapshot never invalidated | `count()` returns 3; derived read reflects state |
| js-7 | orders | ownership | `searchOrders(sessionAlice, 'gizmo')` | returns bob's and alice's orders; session accepted but unapplied | only alice's orders; collection never leaks other users' rows |
| js-8 | orders | ordering | `completeCheckout(cid)` before `payCheckout(cid)` | creates order without payment; pay step skipped | throw `checkout must be paid before completion` |
| js-9 | orders | exceptional-conditions | `refundOrder(sessionAlice, 1, failingGateway)` | returns `{ refunded: true }`; swallows gateway error | throw `refund failed; gateway failure must not be silently swallowed` |
| js-10 | orders | resource-exhaustion | `batchLookupOrders(session, orderIds)` | processes unbounded batch without ceiling | throw `batch size exceeds maximum limit of 100` |
| js-11 | orders | concurrency | `reserveStock(sku, qty)` | two workers both succeed; stock double-reserved | throw `insufficient stock; concurrent requests must not double-reserve` |
| js-12 | orders | idempotency | `processPayment(orderId, amount, idempotencyKey)` | duplicate payment created on replay | return original payment; duplicate charge not created |
| js-13 | orders | dependency-failure | `getOrderRecommendations(session, orderId, recommender)` | throws unhandled error; upstream failure crashes | return `[]`; graceful degradation on recommender failure |
| js-14 | orders | contract | `exportOrderSummary(orderId)` | leaks internal fields `internalCost` and `gatewayRef` | return public schema fields only; internal fields stripped |
| js-15 | orders | security | `resolveReceiptPath(orderId, filename)` | returns unconstrained path escaping receipts dir | throw `path traversal outside receipts directory` |
| js-16 | orders | agent | `dispatchAgentTool('lookupOrder', {orderId: 'invalid'})` | raw TypeError leaks, crashing agent loop | return `{ isError: true, error: ... }`; errors encapsulated |

| js-17 | pricing | boundaries | `applyCoupon(10.10, 30)` | returns `7.069999999999999`; floating-point truncation error | `7.07`; price rounded to cents |
| js-18 | orders | dependency-failure | `fetchTrackingStatus(1, hangingTracker)` | blocks indefinitely; no timeout on external call | `Error: timeout` after reasonable deadline |
| js-19 | orders | security | `searchOrderNotes("'; DROP TABLE orders; --")` | filter string contains unsanitized SQL injection payload | reject or escape SQL metacharacters |
