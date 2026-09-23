# Lens: malformed

## What assumptions this lens attacks

That data arriving from outside has the shape the type signature
or docstring promises: strings parse, JSON is well-formed,
runtime types match compile-time types (types are erased at
runtime in TS/Python annotations).

## Case-generation heuristics

- Strings that get parsed: non-numeric where a number is expected
  (`"abc"` into `float()`/`Number()`), empty string, whitespace,
  thousands separators, locale decimals.
- Raw JSON entry points: truncated payloads, `{oops`, wrong top-level
  type (array where object expected).
- Runtime type confusion: string where number expected
  (`"2"` from a form or JSON without strict schema) flowing into
  arithmetic — watch silent coercion (`0 + "2" === "02"`).
- Encodings: invalid UTF-8 bytes, embedded NULs, control chars.

## Oracle patterns

- Clean, typed validation error at the boundary (`ValueError:
  unit_price must be numeric`), not a raw leak from deep inside
  (`ValueError: could not convert string to float: 'abc'`).
- Reject-or-parse-completely: parser either returns a fully
  validated value or raises a domain error — never a partially
  parsed result.
- Arithmetic never silently changes type (result stays numeric).

## Worked examples

Python — `line_total(item)` calling `float(item["unit_price"])`:

```python
# case: unit_price="abc"
# oracle: ValueError("unit_price must be numeric")
# observed (bug): raw ValueError could-not-convert leaks
```

TypeScript — `parseOrder(raw)` calling `JSON.parse` directly:

```ts
// case: raw = "{oops"
// oracle: throws Error("invalid order JSON")
// observed (bug): raw SyntaxError with position internals leaks
```

## When not to apply

Input already passes through a strict schema validator (zod,
pydantic) at a boundary you can point to — attack the schema
itself instead.
