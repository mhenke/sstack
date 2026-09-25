---
name: sstack-missing
description: "Missing lens rubric. Case-generation heuristics, oracle patterns, and worked examples for absent fields, null/None/undefined, and empty inputs. Loaded inline under ### Lens rubric."
disable-model-invocation: true
---

# Missing lens

Attacks every mapped surface through the missing lens: that fields,
keys, and inputs are present. Required dict/record keys exist, optional
values are `None`/`undefined`-aware, empty inputs are handled, and
absent data is distinguished from default data.

## Case-generation heuristics

- Required keys deleted one at a time from every record the code
  indexes into.
- Optional field explicitly null (`None` / `null` / `undefined`) —
  different from absent; `dict.get(k, default)` and `??` treat them
  differently than `d[k]` does.
- Empty inputs: `''`, `[]`, `{}`, missing file, absent query param.
- Whole argument omitted where the language allows (default args,
  optional params).

## Oracle patterns

- Missing REQUIRED field → explicit error naming the field, at the
  boundary.
- Explicit null on OPTIONAL field → documented policy: treated as
  absent (default applies) or rejected. Either is fine; silence and
  `NaN`/`TypeError` deep inside are not.
- Result never silently degrades: no `NaN` totals, no `None`
  propagated into arithmetic.

Worked example — Python `fare_for(trip)` indexing `trip["distance_km"]`
and `trip.get("discount", 0)`: case A `{}` (distance absent), oracle
`ValueError("distance_km is required")`, observed (bug) `KeyError`
leaks. Case B `discount=None` (explicit null), oracle treated as absent
so discount 0 applies, observed (bug) `TypeError` on `1 - None`.

TypeScript `priceFor({weightKg, zone, discount?})` reading
`order.discount ?? 0`: case `{zone: 2}` (weightKg absent, type erased at
runtime), oracle throws `Error("weightKg is required")`, observed (bug)
returns `NaN` silently.

## When not to apply

The record type makes the field structurally impossible to omit and
the value comes from code you control, not external data.
