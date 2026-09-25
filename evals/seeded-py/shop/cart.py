class Cart:
    """Cart of line quantities, with a running count."""

    def __init__(self, lines=None):
        self._lines = lines if lines is not None else {}
        self._count = sum(self._lines.values())

    def track(self, sku, qty):
        """Record qty of sku on this cart."""
        self._lines[sku] = self._lines.get(sku, 0) + qty

    def count(self):
        """Total quantity across all lines."""
        return self._count


def add_item(cart, item_id, qty):
    """Add qty of item_id to the cart (dict)."""
    cart[item_id] = cart.get(item_id, 0) + qty


def total_items(cart):
    """Total number of items in the cart."""
    return sum(cart.values())
