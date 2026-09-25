# Seeded bugs (KEEP OUT OF ACCEPTANCE RUNS)

| id | module | lens | trigger | buggy behavior | oracle |
|---|---|---|---|---|---|
| js-1 | pagination | boundaries | `paginate(items, 0, 3)` | returns [] silently | throw `page must be >= 1` |
| js-2 | pricing | missing | `lineTotal({qty: 2})` | returns NaN | throw `unitPrice is required` |
| js-3 | pricing | malformed | `parseOrder("{oops")` | raw SyntaxError | throw `invalid order JSON` |
| js-4 | cart | boundaries | `maxQuantity([])` | returns -Infinity | throw `lines must not be empty` |
| js-5 | cart | malformed | qty as string `"2"` | returns string `"02"` | throw `qty must be a number` |
