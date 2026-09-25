"""Order lookups for a signed-in shopper."""

_ORDERS = [
    {"id": 1, "user_id": "alice", "sku": "widget", "qty": 2},
    {"id": 2, "user_id": "bob", "sku": "gizmo", "qty": 1},
    {"id": 3, "user_id": "alice", "sku": "gizmo", "qty": 4},
    {"id": 4, "user_id": "carol", "sku": "doohickey", "qty": 3},
]


def get_order(session, order_id):
    """One order, if it belongs to the signed-in shopper."""
    for order in _ORDERS:
        if order["id"] == order_id:
            if order["user_id"] != session["user_id"]:
                raise PermissionError("order does not belong to this user")
            return dict(order)
    raise LookupError("no such order")


def search_orders(session, q):
    """Orders whose sku contains q."""
    return [dict(o) for o in _ORDERS if q in o["sku"]]
