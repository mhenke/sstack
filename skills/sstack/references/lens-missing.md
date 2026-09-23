# Lens: missing

## What assumptions this lens attacks

That fields, keys, and inputs are present: required dict/record
keys exist, optional values are `None`/`undefined`-aware, empty
inputs are handled, and absent data is distinguished from default
data.

## Case-generation heuristics

- Required keys deleted one at a time from every record the code
  indexes into.
- Optional field explicitly null (`None` / `null` / `undefined`)
  — different from absent; `dict.get(k, default)` and `??` treat
  them differently than `d[k]` does.
- Empty inputs: `''`, `[]`, `{}`, missing file, absent query param.
- Whole argument omitted where the language allows (default args,
  optional params).

## Oracle patterns

- Missing REQUIRED field → explicit error naming the field, at
  the boundary.
- Explicit null on OPTIONAL field → documented policy: treated as
  absent (default applies) or rejected — either is fine, silence
  and `NaN`/`TypeError` deep inside are not.
- Result never silently degrades: no `NaN` totals, no `None`
  propagated into arithmetic.

## Worked examples

Python — `UserProfile.getName(profile)` indexing `profile["id"]` and
`profile.get("email", "unknown@example.com")`:

```python
# case A: {} (id absent)
# oracle: ValueError("id is required")
# observed (bug): KeyError 'id' leaks
# case B: email=None (explicit null)
# oracle: treated as absent → email "unknown@example.com"
# observed (bug): TypeError on "unknown" + None
```

TypeScript — `UserProfile.getAge(profile)` with
`profile.age ??= 18`:

```ts
// case: {name: "Alice"} — age absent (type erased at runtime)
// oracle: throws Error("age is required")
// observed (bug): returns NaN silently
```

## When not to apply

The record type makes the field structurally impossible to omit
and the value comes from code you control, not external data.