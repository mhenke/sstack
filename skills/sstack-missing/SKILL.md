---
name: sstack-missing
description: "Missing lens rubric. Case-generation heuristics, oracle patterns, and worked examples for absent fields, null/None/undefined, falsy traps, and empty inputs. Loaded inline under ### Lens rubric."
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
- Falsy collisions: pass `0`, `false`, or `""` where defaulting logic
  (`val or default`, `val || default`) may mistakenly treat valid zero
  or boolean false as absent.
- Empty inputs: `''`, `[]`, `{}`, missing file, absent query param.
- Protocol context: omit mandatory HTTP headers (`Content-Type`,
  `Authorization`, routing headers) on exposed endpoints.
- Partial updates (PATCH): probe omitted fields vs explicit `null` to
  verify omission preserves existing state while null clears it.
- Whole argument omitted where the language allows (default args,
  optional params).
- Startup config: unset mandatory environment variables or secrets to
  verify boot-time fail-fast.

## Oracle patterns

- Missing REQUIRED field → explicit error naming the field, at the
  boundary.
- Missing or null inputs never leak past validation to cause raw
  `KeyError`, `AttributeError`, or `TypeError` deep inside.
- Explicit null on OPTIONAL field → documented policy: treated as
  absent (default applies) or rejected. Either is fine; silence and
  `NaN`/`TypeError` deep inside are not.
- Partial update contract: omitted fields remain untouched; explicit
  `null` clears or resets the field.
- Critical configuration: missing environment variables abort startup
  immediately naming the missing variable, never falling back to
  insecure defaults.
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

## Failure modes to watch for

- Omitted mandatory parameters (CWE-476, CWE-252): missing dictionary keys or
  omitted function arguments crashing with unhandled KeyError or NullPointerException.
- Null vs absent confusion (RFC 7396): conflating omitted partial-update fields
  with explicit null clearing directives.
- Falsy coercion traps: Python `dict.get(k, default)` returning `None` instead of
  default, or JavaScript `||` clobbering valid `0`, `false`, or `""`.
- Missing protocol headers: requests lacking required `Authorization`, `Content-Type`,
  or tenant identifiers.
- Unsafe attribute traversal: chained attribute or property lookups across unvalidated
  null or undefined parents.
- Boot-time configuration absence (CWE-457): unconfigured secrets or environment variables
  falling back to insecure defaults.

## Language notes

### Python

- `dict.get(k, default)` returns `None` (not `default`) when key `k`
  exists with value `None`. Subsequent arithmetic or string calls raise
  deferred `TypeError` / `AttributeError`.
- Direct indexing `d[k]` raises raw `KeyError: 'k'` instead of domain
  validation naming the missing field.
- Falsy evaluation (`if not val:`) conflates valid `0`, `False`, `[]`,
  and `""` with missing.

### JavaScript / TypeScript

- TypeScript interfaces and type assertions are erased at runtime;
  unvalidated inputs omitting fields silently produce `undefined`.
- Logical OR (`val || default`) treats valid `0`, `false`, and `""` as
  missing, clobbering them with the fallback. Use nullish coalescing
  `??` when absence is the criterion.
- Arithmetic on `undefined` silently yields `NaN` without throwing,
  propagating corrupted values into downstream state.
- Unchecked nested access (`obj.a.b`) throws raw `TypeError` when
  `obj.a` is undefined.

### Java

- `Map.get("key")` returns `null` on missing key; unboxing to a
  primitive (`int`, `boolean`) throws raw `NullPointerException`.
- `Optional.get()` on an empty `Optional` throws raw
  `NoSuchElementException` instead of a domain validation error.

### C++

- `std::map::operator[]` silently default-constructs an entry on missing
  key (e.g. inserting 0), masking omission and corrupting state.
- `std::map::at(k)` throws raw `std::out_of_range`.
- Dereferencing an unengaged `std::optional` (`*opt`) is undefined
  behavior; `.value()` throws `std::bad_optional_access`.

## When not to apply

The record type makes the field structurally impossible to omit and
the value comes from code you control, not external data.
