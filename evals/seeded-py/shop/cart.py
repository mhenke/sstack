def add_item(cart, item_id, qty):
    """Add qty of item_id to the cart (dict)."""
    cart[item_id] = cart.get(item_id, 0) + qty


def total_items(cart):
    """Total number of items in the cart."""
    return sum(cart.values())
