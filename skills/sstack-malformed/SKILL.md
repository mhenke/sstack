---
name: sstack-malformed
description: "Malformed lens rubric. Case-generation heuristics, oracle patterns, and worked examples for wrong types, corrupt structures, encoding issues, and unvalidated parsing. Loaded by the sstack-malformed-attacker agent."
---

# Malformed lens

Attacks every mapped surface through the malformed lens: that data
arriving from outside has the shape the type signature or docstring
promises. Strings parse, JSON is well-formed, runtime types match
compile-time types (types are erased at runtime in TS/Python
annotations).

## Case-generation heuristics

- Strings that get parsed: non-numeric where a number is expected
  (`"abc"` into `float()`/`Number()`), empty string, whitespace,
  thousands separators, locale decimals.
- Raw JSON entry points: truncated payloads, wrong top-level type
  (array where object expected).
- Runtime type confusion: string where number expected (`"2"` from a
  form or JSON without strict schema) flowing into arithmetic. Watch
  silent coercion (`0 + "2" === "02"`).
- Encodings: invalid UTF-8 bytes, embedded NULs, control chars.

## Oracle patterns

- Clean, typed validation error at the boundary
  (`ValueError: unit_price must be numeric`), not a raw leak from deep
  inside (`ValueError: could not convert string to float: 'abc'`).
- Reject-or-parse-completely: parser either returns a fully validated
  value or raises a domain error. Never a partially parsed result.
- Arithmetic never silently changes type (result stays numeric).

Worked example — Python `line_total(item)` calling
`float(item["unit_price"])`: case `unit_price="abc"`, oracle
`ValueError("unit_price must be numeric")`, observed (bug) raw
ValueError could-not-convert leaks. TypeScript `readConfig(raw)`
calling `JSON.parse(raw)`: case `raw = "{invalid"`, oracle throws
`Error("config is not valid JSON")`, observed (bug) raw SyntaxError
with position internals leaks.

## Language notes

### Java

- `Integer.parseInt("abc")` throws `NumberFormatException` (raw leak
  unless wrapped in a domain error).
- Unchecked casts compile but throw `ClassCastException` at runtime.
- Autoboxing a null `String` into `int` throws `NullPointerException`.

### C++

- `std::stoi("abc")` throws `std::invalid_argument` (raw leak unless
  wrapped).
- `reinterpret_cast` compiles for anything, crashes at runtime.
- Format string mismatches (`%s` with an `int`) are undefined
  behavior.

### JavaScript

- `"2" + 2` returns `"22"` (string concatenation, no error). The
  result type silently changes from number to string.
- `parseInt("abc")` returns `NaN`, not an error. `NaN` propagates
  through subsequent arithmetic.
- `JSON.parse` throws raw `SyntaxError` with position internals.

## When not to apply

Input already passes through a strict schema validator (zod, pydantic)
at a boundary you can point to. Attack the schema itself instead.
