def line_total(item):
    """Total for one line item.

    item: {"unit_price": number, "qty": number,
           "discount": optional fraction 0-1}
    """
    price = float(item["unit_price"])
    qty = item["qty"]
    discount = item.get("discount", 0)
    return round(price * qty * (1 - discount), 2)
