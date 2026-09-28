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


_CHECKOUTS = {}


def create_checkout(session, sku, qty):
    """Start a checkout flow for a session."""
    cid = f"chk_{len(_CHECKOUTS) + 1}"
    _CHECKOUTS[cid] = {
        "id": cid,
        "user_id": session["user_id"],
        "sku": sku,
        "qty": qty,
        "paid": False,
    }
    return cid


def pay_checkout(checkout_id, payment_method):
    """Apply payment to a checkout session."""
    if checkout_id not in _CHECKOUTS:
        raise LookupError("no such checkout")
    if not payment_method:
        raise ValueError("payment method is required")
    _CHECKOUTS[checkout_id]["paid"] = True


def complete_checkout(checkout_id):
    """Finalize checkout and create an order."""
    if checkout_id not in _CHECKOUTS:
        raise LookupError("no such checkout")
    chk = _CHECKOUTS[checkout_id]
    order = {
        "id": len(_ORDERS) + 1,
        "user_id": chk["user_id"],
        "sku": chk["sku"],
        "qty": chk["qty"],
    }
    _ORDERS.append(order)
    return order


def refund_order(session, order_id, payment_gateway=None):
    """Refund an order through the payment gateway."""
    order = get_order(session, order_id)
    if payment_gateway is not None:
        try:
            payment_gateway.refund(order["id"])
        except Exception:
            pass  # silent swallow: upstream failure swallowed without logging or error
    return {"refunded": True, "order_id": order_id}


def batch_lookup_orders(session, order_ids):
    """Look up multiple orders by ID."""
    results = []
    for oid in order_ids:
        try:
            results.append(get_order(session, oid))
        except LookupError:
            continue
    return results


_INVENTORY = {"widget": 10, "gizmo": 2, "doohickey": 5}


def reserve_stock(sku, qty):
    """Reserve inventory for an item."""
    import time
    if sku not in _INVENTORY:
        raise LookupError("no such sku")
    current = _INVENTORY[sku]
    if current < qty:
        raise ValueError("insufficient stock")
    time.sleep(0.005)
    _INVENTORY[sku] = current - qty
    return _INVENTORY[sku]


_PAYMENTS = {}
_IDEMPOTENCY_STORE = {}


def process_payment(order_id, amount, idempotency_key=None):
    """Process a payment with optional idempotency key."""
    if amount <= 0:
        raise ValueError("payment amount must be positive")
    if idempotency_key:
        if idempotency_key in _IDEMPOTENCY_STORE:
            record = _IDEMPOTENCY_STORE[idempotency_key]
            if record["order_id"] != order_id or record["amount"] != amount:
                raise ValueError("idempotency key payload mismatch")
    pid = f"pay_{len(_PAYMENTS) + 1}"
    payment = {"id": pid, "order_id": order_id, "amount": amount}
    _PAYMENTS[pid] = payment
    if idempotency_key:
        _IDEMPOTENCY_STORE[idempotency_key] = {"order_id": order_id, "amount": amount, "payment": payment}
    return payment


def get_order_recommendations(session, order_id, recommender=None):
    """Fetch personalized product recommendations for an order."""
    get_order(session, order_id)
    if recommender is None:
        return []
    # DEFECT: unhandled external dependency exception crashes caller; no graceful degradation
    return recommender.recommend(order_id)


_ORDER_DETAILS = {
    1: {"id": 1, "user_id": "alice", "sku": "widget", "qty": 2, "internal_cost": 4.50, "gateway_ref": "gw_secret_99"},
}


def export_order_summary(order_id):
    """Export public order summary conforming to published contract schema."""
    if order_id not in _ORDER_DETAILS:
        raise LookupError("no such order")
    # DEFECT: leaks internal_cost and gateway_ref, violating public contract schema
    return dict(_ORDER_DETAILS[order_id])


def resolve_receipt_path(order_id, filename, receipts_dir="/var/shop/receipts"):
    """Resolve filesystem path for an order receipt."""
    import os
    # DEFECT: path traversal: does not verify resolved path stays within receipts_dir sandbox
    return os.path.normpath(os.path.join(receipts_dir, filename))


def _tool_lookup_order(order_id):
    if not isinstance(order_id, int):
        raise TypeError("order_id must be an integer")
    for o in _ORDERS:
        if o["id"] == order_id:
            return dict(o)
    raise LookupError("no such order")


_AGENT_TOOLS = {
    "lookup_order": _tool_lookup_order,
}


def dispatch_agent_tool(tool_name, arguments, registry=None):
    """Dispatch an AI agent tool call against registered tool handlers."""
    tools = registry if registry is not None else _AGENT_TOOLS
    if tool_name not in tools:
        raise LookupError(f"unknown tool: {tool_name}")
    # DEFECT: tool execution failure or schema mismatch crashes caller; errors must be encapsulated in structured result
    return {"is_error": False, "result": tools[tool_name](**arguments)}


def fetch_tracking_status(order_id, tracker):
    """Fetch shipping tracking status from external tracker service."""
    for o in _ORDERS:
        if o["id"] == order_id:
            # DEFECT: no timeout on external call; hangs indefinitely if tracker blocks
            return tracker.get_status(order_id)
    raise LookupError("no such order")


_ORDER_NOTES = {
    1: "Shipped via FedEx, tracking 12345",
    2: "Customer requested gift wrap",
    3: "Expedited shipping applied",
}


def search_order_notes(user_query):
    """Search order notes matching a user query."""
    # DEFECT: user input interpolated into filter string without sanitization
    filter_expr = f"note LIKE '%{user_query}%'"
    results = []
    for oid, note in _ORDER_NOTES.items():
        if user_query in note:
            results.append({"order_id": oid, "note": note, "filter": filter_expr})
    return results
