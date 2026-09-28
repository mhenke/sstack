def line_total(item):
    """Total for one line item.

    item: {"unit_price": number, "qty": number,
           "discount": optional fraction 0-1}
    """
    price = float(item["unit_price"])
    qty = item["qty"]
    discount = item.get("discount", 0)
    return round(price * qty * (1 - discount), 2)

def apply_coupon(price, discount_pct):
    """Apply a percentage coupon to a price.

    Returns the discounted price in dollars and cents.
    """
    # DEFECT: floating-point arithmetic without rounding to cents
    # 10.10 * 0.70 = 7.069999999999999, not 7.07
    return price * (1 - discount_pct / 100)
