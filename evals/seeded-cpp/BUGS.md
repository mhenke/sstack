# Seeded bugs (KEEP OUT OF ACCEPTANCE RUNS)

| id | module | lens | trigger | buggy behavior | oracle |
|---|---|---|---|---|---|
| cpp-1 | pagination | boundaries | `paginate(items, 0, 2)` | iterator arithmetic invalid | throw domain error naming page |
| cpp-2 | pagination | boundaries | page beyond end | iterator out of range / undefined behavior | explicit named error or empty page per contract |
| cpp-3 | pricing | boundaries | negative qty | accepts negative total | throw `qty must be positive` |
| cpp-4 | cart | boundaries | `max_quantity({})` | dereferences end iterator | throw `lines must not be empty` |
| cpp-5 | cart | malformed | very large integer input | overflow wraps silently | checked arithmetic or domain error |
| cpp-6 | orders | state | `CartSession().track("widget", 3)` then `.count()` | returns 0; count snapshot never invalidated | `count()` returns 3; derived read reflects state |
| cpp-7 | orders | ownership | `search_orders(session_alice, "gizmo")` | returns bob's and alice's orders; session accepted but unapplied | only alice's orders; collection never leaks other users' rows |
| cpp-8 | orders | ordering | `complete_checkout(cid)` before `pay_checkout(cid)` | creates order without payment; pay step skipped | throw `checkout must be paid before completion` |
| cpp-9 | orders | exceptional-conditions | `refund_order(session_alice, 1, failing_gateway)` | returns true; swallows gateway error | throw `refund failed; gateway failure must not be silently swallowed` |
| cpp-10 | orders | resource-exhaustion | `batch_lookup_orders(session, order_ids)` | processes unbounded batch without ceiling | throw `batch size exceeds maximum limit of 100` |
| cpp-11 | orders | concurrency | `reserve_stock(sku, qty)` | two threads both succeed; stock double-reserved | throw `insufficient stock; concurrent requests must not double-reserve` |
| cpp-12 | orders | idempotency | `process_payment(order_id, amount, idempotency_key)` | duplicate payment created on replay | return original payment; duplicate charge not created |
| cpp-13 | orders | dependency-failure | `get_order_recommendations(session, order_id, recommender)` | throws unhandled error; upstream failure crashes | return `[]`; graceful degradation on recommender failure |
| cpp-14 | orders | contract | `export_order_summary(order_id)` | leaks internal database fields internal_cost and gateway_ref | return public schema fields only; internal fields stripped |
| cpp-15 | orders | security | `resolve_receipt_path(order_id, filename)` | returns unconstrained path escaping receipts dir | throw `path traversal outside receipts directory` |
| cpp-16 | orders | agent | `dispatch_agent_tool("lookup_order", {{"order_id", "invalid"}})` | raw exception leaks, crashing agent loop | return `{"is_error": "true", "error": ...}`; errors encapsulated |
| cpp-17 | shop | boundaries | `apply_coupon(10.10, 30)` | returns `7.069999999999999`; floating-point truncation error | `7.07`; price rounded to cents | `std::round(result * 100) / 100` |
| cpp-18 | orders | dependency-failure | `fetch_tracking_status(1, hanging_tracker)` | blocks indefinitely; no timeout on external call | throws timeout error after deadline | wrap with `std::future::wait_for` |
| cpp-19 | orders | security | `search_order_notes("'; DROP TABLE orders; --")` | filter string contains unsanitized SQL injection payload | reject or escape SQL metacharacters | sanitize or parameterize the query string |
