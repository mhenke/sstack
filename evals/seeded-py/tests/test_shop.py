from shop.pagination import paginate
from shop.pricing import line_total
from shop.cart import add_item, total_items


def test_paginate_returns_requested_page():
    items = list(range(1, 11))
    assert paginate(items, 2, 3) == [4, 5, 6]


def test_paginate_last_partial_page():
    items = list(range(1, 11))
    assert paginate(items, 4, 3) == [10]


def test_line_total_with_discount():
    assert line_total({"unit_price": 10, "qty": 2, "discount": 0.5}) == 10.0


def test_line_total_without_discount():
    assert line_total({"unit_price": "9.99", "qty": 3}) == 29.97


def test_cart_accumulates():
    cart = {}
    add_item(cart, "a", 2)
    add_item(cart, "a", 1)
    add_item(cart, "b", 4)
    assert total_items(cart) == 7
