---
name: sstack-malformed
description: "Malformed lens rubric. Case-generation heuristics, oracle patterns, and worked examples for wrong types, corrupt structures, format violations, delimiter hazards, and unvalidated parsing. Loaded inline under ### Lens rubric."
disable-model-invocation: true
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
- Corrupted numeric and date formats: `"NaN"`, `"Infinity"`,
  currency strings (`"$100"`), multi-dot decimals (`"12.34.56"`),
  scientific notation (`"1e6"`), inverted or impossible dates
  (`"2024-31-12"`, `"2024-02-30"`).
- Structural mismatches: arrays/objects where scalars expected
  (`{"id": [1, 2]}`), scalar where collection expected, duplicate
  conflicting keys.
- Delimiter and injection hazards: unescaped quotes, delimiters,
  semicolons, embedded NULs (`\0`), syntax fragments that break
  parser layers.
- Raw JSON entry points: truncated payloads, wrong top-level type
  (array where object expected).
- Runtime type confusion: string where number expected (`"2"` from a
  form or JSON without strict schema) flowing into arithmetic. Watch
  silent coercion (`0 + "2" === "02"`).
- Encodings: invalid UTF-8 bytes, control chars.

## Oracle patterns

- Clean, typed validation error at the boundary
  (`ValueError: amount must be numeric`), not a raw leak from deep
  inside (`ValueError: could not convert string to float: 'abc'`).
- No unhandled runtime crashes or 500s: HTTP boundaries return 400
  Bad Request with structured error, never 500 or uncaught crash.
- No internal stack traces, file paths, or parser library internals
  leaked to callers.
- Reject-or-parse-completely: parser either returns a fully validated
  value or raises a domain error. Never a partially parsed result.
- Arithmetic never silently changes type (result stays numeric).

Worked example — Python `fare_for(trip)` calling
`float(trip["distance_km"])`: case `distance_km="far"`, oracle
`ValueError("distance_km must be numeric")`, observed (bug) raw
ValueError could-not-convert leaks. TypeScript `readConfig(raw)`
calling `JSON.parse(raw)`: case `raw = "{invalid"`, oracle throws
`Error("config is not valid JSON")`, observed (bug) raw SyntaxError
with position internals leaks.

## Failure modes to watch for

- Syntax and structural corruption (CWE-20, RFC 8259): truncated payloads,
  mismatched brackets, invalid byte escapes, and malformed encodings.
- Type violations and cast failures (CWE-1287, CWE-704): strings passed into
  numeric arithmetic or composite structures in scalar slots.
- Delimiter and separator hazards (CWE-158, CWE-74): unescaped delimiters,
  quotes, and embedded NUL bytes breaking downstream parsers.
- Conflicting duplicate keys (CWE-915): duplicate keys in object payloads
  triggering undefined deserializer precedence.
- Diagnostic information disclosure (CWE-209): leaking raw parser exception
  traces and library internals instead of structured boundary rejections.

## Language notes

### Python

- `json.loads("{")` throws raw `JSONDecodeError` with position internals.
- `float("abc")` or `int("abc")` throws raw `ValueError` leaking
  internal conversion text instead of naming the domain field.

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
