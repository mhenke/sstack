def paginate(items, page, size):
    """Return one page of items. `page` is 1-based, `size` items per page."""
    start = (page - 1) * size
    return items[start:start + size]
