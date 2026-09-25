# Seeded bugs (KEEP OUT OF ACCEPTANCE RUNS)

| id | module | lens | trigger | buggy behavior | oracle |
|---|---|---|---|---|---|
| cpp-1 | pagination | boundaries | `paginate(items, 0, 2)` | iterator arithmetic invalid | throw domain error naming page |
| cpp-2 | pagination | boundaries | page beyond end | iterator out of range / undefined behavior | explicit named error or empty page per contract |
| cpp-3 | pricing | boundaries | negative qty | accepts negative total | throw `qty must be positive` |
| cpp-4 | cart | boundaries | `max_quantity({})` | dereferences end iterator | throw `lines must not be empty` |
| cpp-5 | cart | malformed | very large integer input | overflow wraps silently | checked arithmetic or domain error |
