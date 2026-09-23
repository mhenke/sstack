# Seeded bugs (KEEP OUT OF ACCEPTANCE RUNS)

This file is the answer key. `evals/run-acceptance.sh` strips it
when copying the repo for a cold run. Fixes below are the canonical
negative-control fixes.

| id | module | lens | trigger | buggy behavior | oracle | fix note |
|---|---|---|---|---|---|---|
| ts-1 | pagination | boundaries | `paginate(items, 0, 3)` | returns `[]` silently (negative slice clamps; no validation) | `throw Error("page must be >= 1")` | validate page/size |
| ts-2 | pricing | missing | `lineTotal({qty: 2})` | returns `NaN` silently | `throw Error("unitPrice is required")` | `Number.isFinite` check |
| ts-3 | pricing | malformed | `parseOrder("{oops")` | raw `SyntaxError` leaks | `throw Error("invalid order JSON")` | try/catch, rethrow domain error |
| ts-4 | cart | boundaries | `totalQuantity([])` | `TypeError: Reduce of empty array with no initial value` | returns `0` | `reduce(fn, 0)` |
| ts-5 | cart | malformed | qty as string `"2"` in lines | returns `"023"` (string) | `throw Error("qty must be a number")` | `typeof l.qty === "number"` check |
