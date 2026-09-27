# Seeded bugs (KEEP OUT OF ACCEPTANCE RUNS)

This file is the answer key. `evals/acceptance.py` strips it when
copying the repo for a cold run. Fixes below are the canonical
negative-control fixes.

| id | module | lens | trigger | buggy behavior | oracle | fix note |
|---|---|---|---|---|---|---|
| py-1 | pagination | boundaries | `paginate(items, 0, 3)` | returns [] silently (negative slice clamps; no validation) | `ValueError: page must be >= 1` | validate `page >= 1`, `size >= 1` at top |
| py-2 | cart | boundaries | `add_item(c, "a", -5)` then `total_items(c)` | total `-5` | `ValueError: qty must be > 0` | validate qty in `add_item` |
| py-3 | pricing | missing | `line_total({})` | raw `KeyError: 'unit_price'` | `ValueError: unit_price is required` | check keys explicitly |
| py-4 | pricing | missing | `line_total({"unit_price": 10, "qty": 2, "discount": None})` | `TypeError: 1-None` | None treated as absent → 20.0 | `discount = item.get("discount") or 0` guard for None |
| py-5 | pricing | malformed | `line_total({"unit_price": "abc", "qty": 2})` | raw `ValueError: could not convert string to float` | `ValueError: unit_price must be numeric` | wrap float() with clean error |
| py-6 | cart | state | `Cart().track("widget", 3)` then `Cart.count()` | `0` — `_count` snapshotted in `__init__`, never invalidated by `track` | `count()` returns `3`; a derived read reflects current state | recompute in `count()`, or update `_count` in `track` |
| py-7 | orders | ownership | `search_orders(session_alice, "gizmo")` | returns bob's and alice's orders; `session` is accepted but never used to filter | only alice's order with that sku | filter on `session["user_id"]` before the sku match |
| py-8 | orders | ordering | `complete_checkout(cid)` before `pay_checkout(cid, ...)` | creates order without payment; pay step skipped | `ValueError: checkout must be paid before completion` | check `chk.get("paid")` in `complete_checkout` |
| py-9 | orders | exceptional-conditions | `refund_order(session_alice, 1, failing_gateway)` | returns `{"refunded": True}`; swallows gateway exception | `RuntimeError: refund failed` | check gateway response or rethrow domain error |
| py-10 | orders | resource-exhaustion | `batch_lookup_orders(session, list(range(1000)))` | processes unbounded batch without ceiling | `ValueError: batch size exceeds maximum limit of 100` | validate `len(order_ids) <= 100` before query loop |
| py-11 | orders | concurrency | parallel `reserve_stock("gizmo", 2)` | double-reservation; two threads both succeed reserving 2 of 2 | `ValueError: insufficient stock` on second worker | guard check-then-act with threading.Lock |
| py-12 | orders | idempotency | `process_payment(1, 50.0, "key-1")` called twice | duplicate payment created on replay; new payment id allocated | return original payment; duplicate charge not created | check key in store and return cached payment |
| py-13 | orders | dependency-failure | `get_order_recommendations(session_alice, 1, failing_recommender)` | raises `ConnectionError`; upstream failure crashes recommendations | return `[]`; graceful degradation when recommendation service fails | catch upstream exceptions and return empty list fallback |
| py-14 | orders | contract | `export_order_summary(1)` | leaks internal database fields `internal_cost` and `gateway_ref` | return public schema fields only; undeclared internal fields stripped | filter against public contract fields before returning |
| py-15 | orders | security | `resolve_receipt_path(1, "../../etc/passwd")` | returns unconstrained traversal path escaping receipts directory | `PermissionError: path traversal outside receipts directory` | verify canonical path is contained in receipts_dir via commonpath |
| py-16 | orders | agent | `dispatch_agent_tool("lookup_order", {"order_id": "invalid"})` | raw TypeError leaks, crashing agent loop | return `{"is_error": True, "error": "order_id must be an integer"}`; tool errors encapsulated as structured error result | wrap tool handler invocation in try/except and return is_error payload |

