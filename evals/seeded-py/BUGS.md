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
