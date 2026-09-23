# sstack MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the sstack v0 negative-testing skill pack (docs + one skill + 3 lens references) and prove it with cold acceptance runs against two seeded-bug repos (Python/pytest and TypeScript/vitest).

**Architecture:** Agent-agnostic SKILL.md entry skill with on-demand `references/` lens files (impeccable/pstack shape); concept freeze in `docs/ARCHITECTURE.md` + `docs/ETHOS.md`; evals prove the skill end-to-end with a cold subagent that finds seeded bugs and lands regression tests.

**Tech Stack:** Markdown (agent-skills format), Python 3.10+ / pytest, TypeScript / vitest (run with bun). No other dependencies.

**Spec:** `docs/superpowers/specs/2026-09-23-sstack-mvp-design.md` (commit `31f4021`).

## Global Constraints

- Skills follow the agent-skills format: `SKILL.md` starts with YAML frontmatter containing exactly `name` and `description`.
- `skills/sstack/SKILL.md` must stay ≤ 500 lines.
- No CLI, no scripts, no runner code in the skill pack. The skill instructs the agent to run real commands and quote real output.
- Every seeded bug maps to exactly one v0 lens: `boundaries`, `malformed`, or `missing`.
- `BUGS.md` must never be visible to the agent during acceptance runs (the acceptance script strips it).
- The skill never edits source code — findings and tests only.
- Commits use conventional messages (`docs:`, `feat:`, `test:`, `chore:`).

---

### Task 1: Foundation docs — ETHOS.md and ARCHITECTURE.md

**Files:**
- Create: `docs/ETHOS.md`
- Create: `docs/ARCHITECTURE.md`

**Interfaces:**
- Produces: the canonical lifecycle stage names `Discover → Model → Attack → Observe → Verify → Minimize → Regress → Learn`; the six definitions `Skill, Lens, Agent, Runner, Oracle, Evidence`; the 13 lens names `boundaries, malformed, missing, state, ordering, concurrency, idempotency, dependency-failure, resource-exhaustion, contract, mutation, agent, security`. Task 2's SKILL.md must use these names verbatim.

- [ ] **Step 1: Write `docs/ETHOS.md`** — full content:

```markdown
# sstack ethos

> Don't ask the agent to say whether the software is robust.
> Make it exercise the failure condition and collect evidence.

sstack is structured negative testing for AI coding agents: it
systematically explores how software behaves outside the happy path,
verifies observed behavior against a declared oracle, and turns
confirmed failures into permanent regression tests.

## The four rules

1. **Attack assumptions.** Every input, state, and dependency an
   implementation assumes is a surface to probe.
2. **Define the oracle before the attack.** Write down the expected
   behavior under the adverse condition — error, degradation, retry
   bound, invariant, rejection — before running anything. "It
   crashes" is not an oracle; "it raises a validation error naming
   the field" is.
3. **Never accept an agent's claim as evidence.** Run the real
   command, quote the real output. The agent interprets evidence;
   it does not manufacture it.
4. **Turn confirmed failures into permanent regressions.** A
   finding that is not a test in the host repo's suite will be
   reintroduced.

## What sstack is not

- Not a security product. Security is one lens among many.
- Not a mutation-testing product. Mutation is one verification
  strategy, deferred past v0.
- Not a happy-path test generator. Happy-path coverage is the host
  repo's business.
- Not adversarial-only. A timeout, null, or clock rollover is not
  an attack; it is still a negative condition worth an oracle.
```

- [ ] **Step 2: Write `docs/ARCHITECTURE.md`** — full content:

```markdown
# sstack architecture

> sstack is a structured negative-testing skill pack for AI coding
> agents: it discovers failure surfaces, attacks them through
> specialist lenses, verifies observed behavior against a declared
> oracle, minimizes confirmed failures, and converts them into
> permanent regression tests.

## Lifecycle

Canonical, in order. Each stage is discrete, artifact-producing, and
resumable from its artifact (gstack's process lesson).

| Stage | Produces | v0 |
|---|---|---|
| Discover | `.sstack/map.md` — surfaces + assumed contracts | yes |
| Model | expected behavior per surface (folded into `map.md`) | yes |
| Attack | executed cases + verbatim observed output | yes |
| Observe | captured actual behavior (folded into Attack) | yes |
| Verify | verdict per case: confirmed / refuted / inconclusive | yes |
| Minimize | minimal repro per confirmed finding | yes |
| Regress | permanent test in the host repo's suite | yes |
| Learn | `.sstack/learn/` failure classes feeding future planning | deferred |

## Six definitions

These prevent drift back into "a big bag of negative-testing
skills". If a new file does not fit one of these nouns, it does not
belong in the pack.

- **Skill** — the methodology for a stage. One entry skill owns
  routing and rules (`skills/sstack/SKILL.md`).
- **Lens** — an attack strategy over a failure class. Content
  (`references/lens-*.md`), not machinery. Selected per target by
  the Attack stage.
- **Agent** — a reasoning role (scout, attacker, oracle,
  reproducer). In v0 these are roles the one agent adopts per
  stage, not separate files.
- **Runner** — deterministic execution of generated cases. Deferred:
  v0 has the agent run real commands itself and quote real output.
- **Oracle** — the expected-behavior declaration written *before*
  the attack. Errors, degradation, retry bounds, invariants,
  rejections — not only crashes.
- **Evidence** — observed output vs. oracle. v0: loose markdown in
  `.sstack/findings/`. v1: structured schema + fingerprints.

## Taxonomy

Negative testing is the domain; lenses explore it. Security is a
lens, never the identity.

| Category | Lens | v0 |
|---|---|---|
| Input | boundaries | ✅ |
| Input | malformed | ✅ |
| Input | missing | ✅ |
| Behavior | state | future |
| Behavior | ordering | future |
| Behavior | concurrency | future |
| Behavior | idempotency | future |
| Environment | dependency-failure | future |
| Environment | resource-exhaustion | future |
| Contracts | contract | future |
| Evidence | mutation | future |
| AI / Agent | agent | future |
| Security | security | future |

## Verification strategies

How a verified finding earns its verdict. v0 uses the first two;
the rest are the v1 proof-gate menu.

1. expected-error assertion (v0)
2. reproducibility — a confirmed finding must reproduce (v0)
3. controlled fault injection (v1)
4. mutation — test fails against a mutant (v1)
5. known-bad fixture (v1)
6. differential comparison (v1)
7. invariant violation (v1)
8. contract violation (v1)

## v0 scope

`skills/sstack/SKILL.md` + 3 lens references + this docs pair +
two seeded eval repos. Everything else (agents-as-files, runners,
evidence schema, learn loop, 10 lenses, host packaging) is additive
later via new `references/` files or a `scripts/` dir — no
restructuring.

## Prior art

- **gstack** — process model: discrete, artifact-producing,
  resumable stages. Infra (binaries, daemon) deliberately not
  copied.
- **pstack** — one launcher skill + on-demand content files.
- **impeccable** — `references/` per subcommand; `scripts/`
  evidence layer addable later; audit-not-fix stance.
```

- [ ] **Step 3: Verify content**

Run: `sed -n '/## Six definitions/,/## Taxonomy/p' docs/ARCHITECTURE.md | grep -c "^- \*\*"` → Expected: 6 (six definitions).
Run: `sed -n '/## Taxonomy/,/## Verification strategies/p' docs/ARCHITECTURE.md | grep -c "future"` → Expected: 10 (future lenses).
Run: `grep -o "Discover\|Model\|Attack\|Observe\|Verify\|Minimize\|Regress\|Learn" docs/ARCHITECTURE.md | sort -u | wc -l` → Expected: 8.

- [ ] **Step 4: Commit**

```bash
git add docs/ETHOS.md docs/ARCHITECTURE.md
git commit -m "docs: sstack ethos and architecture freeze"
```

---

### Task 2: Orchestrator skill — SKILL.md

**Files:**
- Create: `skills/sstack/SKILL.md`

**Interfaces:**
- Consumes: stage names, lens names, and definitions from Task 1 (verbatim).
- Produces: the routing table and `.sstack/` workspace contract that Tasks 3–5 and the Task 7 acceptance prompt rely on. Finding-file fields: `lens, surface, case, oracle, observed, verdict, repro, regression`.

- [ ] **Step 1: Write `skills/sstack/SKILL.md`** — full content:

````markdown
---
name: sstack
description: Use when the user wants negative testing, edge-case coverage, failure-mode analysis, robustness checks, hostile or unexpected input handling, "what happens if" questions about code, or to harden a module or API against bad input before shipping. Discovers failure surfaces, attacks them through lenses (boundaries, malformed, missing), verifies observed behavior against a pre-declared oracle, and turns confirmed failures into permanent regression tests. Not for happy-path feature work.
---

# sstack — structured negative testing

> Don't ask whether the software is robust. Exercise the failure
> condition and collect evidence.

## The four rules

1. Attack assumptions.
2. Define the oracle before the attack. Expected behavior under the
   adverse condition — error, degradation, retry bound, invariant,
   rejection. "It crashes" is not an oracle; "it raises a
   validation error naming the field" is.
3. Never accept an agent's claim as evidence. Run the real command,
   quote the real output.
4. Turn confirmed failures into permanent regressions.

## Routing

- `/sstack <target>` — run the full lifecycle on a module, file,
  directory, or function.
- `/sstack` (bare) — infer the target from recent changes
  (`git status`, `git diff --stat`); ask only if nothing is
  inferable.
- `/sstack <stage>` (discover | attack | verify | minimize |
  regress) — enter that stage using existing `.sstack/` state.
- `/sstack lenses` — print the lens index below.

## Workspace

All artifacts live under `.sstack/` in the host repo:

- `map.md` — surfaces + assumed contracts (Discover output)
- `plan.md` — scoped run plan: selected lenses, cases, oracles
- `findings/<slug>.md` — one per finding, fields:
  `lens, surface, case, oracle, observed (verbatim), verdict
  (confirmed | refuted | inconclusive), repro (command),
  regression (test file + name + fail|pass)`
- `scratch/` — throwaway scripts; delete at run end

## Stages

### 1. Discover

Map the target's failure surfaces: public functions and classes,
API routes, anything that parses external input, loops over
collections, or indexes/slices. For each surface, record its
assumed contract — types, ranges, preconditions gleaned from
docstrings, types, and call sites. Write `.sstack/map.md`.

### 2. Attack

Pick applicable lenses from the index. Read each selected
`references/lens-*.md` before designing cases. For each
surface × lens:

1. Design the case (concrete input and action).
2. Write its oracle in `plan.md` FIRST — the expected behavior
   under this adverse condition.
3. Execute for real: a scratch script under `.sstack/scratch/`,
   or a direct call through the repo's test framework.
4. Record the actual output verbatim.

Never design the oracle after seeing the result.

### 3. Verify

Per case, compare oracle vs. observed:

- **confirmed** — observed violates the oracle, and the case
  reproduces on a second run.
- **refuted** — system satisfies the oracle.
- **inconclusive** — oracle unclear or execution unreliable.
  Inconclusive findings are never promoted to regressions.

### 4. Minimize

For each confirmed finding, strip the case to the smallest input
that still violates the oracle. Update the repro command.

### 5. Regress

Write a permanent test in the host repo's real suite — same
directory and assert style as existing tests, asserting the
oracle, not the bug:

- Test FAILS against current code → live bug; note it.
- Test PASSES → already handled; keep it as a characterization
  test and mark the finding accordingly.

Run the new tests. Then deliver the report in chat FIRST;
persisting `findings/` files is bookkeeping that follows.

## Lens index

| Lens | Applies when | Reference |
|---|---|---|
| boundaries | numbers, sizes, indexes, slices, collections, pagination, loops | references/lens-boundaries.md |
| malformed | strings parsed from outside, JSON, encodings, dynamic types | references/lens-malformed.md |
| missing | optional fields, records from external data, null/None/undefined | references/lens-missing.md |

## Safety

- Read-only toward source, config, and secrets. Write only tests
  and `.sstack/`.
- Never mutate source to demonstrate a bug. Reproduce in scratch
  space.
- No test framework detected → ask before scaffolding one.
- Respect the repo's test conventions exactly.

## Report format

One line per finding: `id | lens | surface | verdict | regression
(file::test, fail|pass)`. Then per confirmed finding the full
field set, with observed output quoted verbatim. End with counts:
confirmed / refuted / inconclusive, regressions landed.
````

- [ ] **Step 2: Verify frontmatter and size**

Run: `python3 -c "import yaml,sys; t=open('skills/sstack/SKILL.md').read(); fm=t.split('---')[1]; d=yaml.safe_load(fm); assert d['name']=='sstack' and 'negative testing' in d['description']; print('frontmatter ok')"`
Run: `wc -l skills/sstack/SKILL.md` → Expected: ≤ 500.

- [ ] **Step 3: Commit**

```bash
git add skills/sstack/SKILL.md
git commit -m "feat: sstack orchestrator skill"
```

---

### Task 3: Lens reference files

**Files:**
- Create: `skills/sstack/references/lens-boundaries.md`
- Create: `skills/sstack/references/lens-malformed.md`
- Create: `skills/sstack/references/lens-missing.md`

**Interfaces:**
- Consumes: reference paths exactly as listed in Task 2's lens index.
- Produces: the oracle-first case design method the Attack stage uses; the bug classes the Task 4/5 seeds instantiate.

Shared template (every lens file has these five sections, in order): **What assumptions this lens attacks** · **Case-generation heuristics** · **Oracle patterns** · **Worked examples** (one Python, one TypeScript) · **When not to apply**.

- [ ] **Step 1: Write `lens-boundaries.md`** — full content:

````markdown
# Lens: boundaries

## What assumptions this lens attacks

That numbers stay in sane ranges, indexes exist, collections are
non-empty, and arithmetic lands inside the value domain the code
was written for.

## Case-generation heuristics

- Numeric arguments: `0`, `1`, `-1`, `-N`, max int, just-over any
  threshold the code compares against.
- Sizes/limits: `0`, negative, huge (memory-relevant), and
  `len(x)` and `len(x)±1`.
- Indexes/slices: first, last, `len` (one past end), negative
  index (language-specific wraparound!), empty collection.
- Pagination math: `page=0` (off-by-one into negative slice),
  `size=0`, page beyond data.
- Aggregation over collections: empty input (reduce/fold without
  initial value), single element.

## Oracle patterns

- Explicit validation error naming the argument
  (`ValueError: page must be >= 1`).
- Well-defined empty result (`[]`, `0`) documented as correct.
- Invariant preserved (total never negative; sum always a number).

Watch for the negative-index trap: `page=0` makes start negative, and
Python `items[-3:0]` and JS `slice(-3, 0)` both silently return `[]`
(the clamped start outranks stop) instead of erroring. A silent
empty/wrong page is worse than a crash.

## Worked examples

Python — `paginate(items, page, size)` with 1-based `page`:

```python
# case: page=0, size=3, items=[1..10]
# observed (bug): returns []  (start = -3 clamps past stop, silent empty)
```

TypeScript — `totalQuantity(lines)` via reduce:

```ts
// case: lines = []
// oracle: returns 0
// observed (bug): TypeError: Reduce of empty array with no initial value
```

## When not to apply

No numbers, sizes, indexes, or collections in the surface's
contract; values are already validated upstream at a boundary you
can point to.
````

- [ ] **Step 2: Write `lens-malformed.md`** — full content:

````markdown
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
````

- [ ] **Step 3: Write `lens-missing.md`** — full content:

````markdown
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

Python — `line_total(item)` indexing `item["unit_price"]` and
`item.get("discount", 0)`:

```python
# case A: {} (unit_price absent)
# oracle: ValueError("unit_price is required")
# observed (bug): KeyError 'unit_price' leaks
# case B: discount=None (explicit null)
# oracle: treated as absent → discount 0
# observed (bug): TypeError on 1 - None
```

TypeScript — `lineTotal({unitPrice, qty, discount?})` with
`item.discount ?? 0`:

```ts
// case: {qty: 2} — unitPrice absent (type erased at runtime)
// oracle: throws Error("unitPrice is required")
// observed (bug): returns NaN silently
```

## When not to apply

The record type makes the field structurally impossible to omit
and the value comes from code you control, not external data.
````

- [ ] **Step 4: Verify template compliance**

Run: `for f in skills/sstack/references/lens-*.md; do grep -c "^## " $f; done` → Expected: 5 per file.
Run: `grep -L "python" skills/sstack/references/lens-*.md; grep -L "typescript\|```ts" skills/sstack/references/lens-*.md` → Expected: no output (both languages in every file).

- [ ] **Step 5: Commit**

```bash
git add skills/sstack/references/
git commit -m "feat: boundaries, malformed, missing lens references"
```

---

### Task 4: Python seeded eval repo

**Files:**
- Create: `evals/seeded-py/pyproject.toml`
- Create: `evals/seeded-py/shop/__init__.py` (empty)
- Create: `evals/seeded-py/shop/pagination.py`
- Create: `evals/seeded-py/shop/pricing.py`
- Create: `evals/seeded-py/shop/cart.py`
- Create: `evals/seeded-py/tests/test_shop.py`
- Create: `evals/seeded-py/BUGS.md`

**Interfaces:**
- Produces: `paginate(items, page, size)`, `line_total(item)`, `add_item(cart, item_id, qty)`, `total_items(cart)` — consumed by Task 7 acceptance and referenced by Task 3 lens examples.

Seeded bugs (5, one lens each; BUGS.md is the canonical record):

| id | module | lens | trigger | buggy behavior | oracle | fix note |
| py-1 | pagination | boundaries | `paginate(items, 0, 3)` | returns `[]` silently (negative slice clamps; no validation) | `ValueError: page must be >= 1` | validate `page >= 1`, `size >= 1` at top |
| py-2 | cart | boundaries | `add_item(c, "a", -5)` then `total_items(c)` | total `-5` | `ValueError: qty must be > 0` | validate qty in `add_item` |
| py-3 | pricing | missing | `line_total({})` | raw `KeyError: 'unit_price'` | `ValueError: unit_price is required` | check keys explicitly |
| py-4 | pricing | missing | `line_total({"unit_price": 10, "qty": 2, "discount": None})` | `TypeError: 1-None` | None treated as absent → 20.0 | `discount = item.get("discount") or 0` guard for None |
| py-5 | pricing | malformed | `line_total({"unit_price": "abc", "qty": 2})` | raw `ValueError: could not convert string to float` | `ValueError: unit_price must be numeric` | wrap float() with clean error |

- [ ] **Step 1: Verify toolchain**

Run: `python3 --version && python3 -m pytest --version` → Expected: Python ≥ 3.10, pytest present. If pytest missing: `python3 -m pip install pytest`.

- [ ] **Step 2: Write the modules**

`pyproject.toml`:

```toml
[project]
name = "seeded-py"
version = "0.1.0"
requires-python = ">=3.10"
```

`shop/pagination.py`:

```python
def paginate(items, page, size):
    """Return one page of items. `page` is 1-based, `size` items per page."""
    start = (page - 1) * size
    return items[start:start + size]
```

`shop/pricing.py`:

```python
def line_total(item):
    """Total for one line item.

    item: {"unit_price": number, "qty": number,
           "discount": optional fraction 0-1}
    """
    price = float(item["unit_price"])
    qty = item["qty"]
    discount = item.get("discount", 0)
    return round(price * qty * (1 - discount), 2)
```

`shop/cart.py`:

```python
def add_item(cart, item_id, qty):
    """Add qty of item_id to the cart (dict)."""
    cart[item_id] = cart.get(item_id, 0) + qty


def total_items(cart):
    """Total number of items in the cart."""
    return sum(cart.values())
```

- [ ] **Step 3: Write happy-path tests** — `tests/test_shop.py`:

```python
from shop.pagination import paginate
from shop.pricing import line_total
from shop.cart import add_item, total_items


def test_paginate_returns_requested_page():
    items = list(range(1, 11))
    assert paginate(items, 2, 3) == [4, 5, 6]


def test_paginate_last_partial_page():
    items = list(range(1, 11))
    assert paginate(items, 4, 3) == [10]


def test_line_total_with_discount():
    assert line_total({"unit_price": 10, "qty": 2, "discount": 0.5}) == 10.0


def test_line_total_without_discount():
    assert line_total({"unit_price": "9.99", "qty": 3}) == 29.97


def test_cart_accumulates():
    cart = {}
    add_item(cart, "a", 2)
    add_item(cart, "a", 1)
    add_item(cart, "b", 4)
    assert total_items(cart) == 7
```

- [ ] **Step 4: Run tests**

Run (cwd `evals/seeded-py`): `python3 -m pytest -q` → Expected: 5 passed.

- [ ] **Step 5: Probe every seeded bug (verify the seeds are live)**

Run each from `evals/seeded-py`, expect the documented buggy output:

```bash
python3 -c "from shop.pagination import paginate; print(paginate(list(range(1,11)), 0, 3))"
# expect: []
python3 -c "from shop.cart import add_item, total_items; c = {}; add_item(c, 'a', -5); print(total_items(c))"
# expect: -5
python3 -c "from shop.pricing import line_total; line_total({})"
# expect: KeyError: 'unit_price'
python3 -c "from shop.pricing import line_total; print(line_total({'unit_price': 10, 'qty': 2, 'discount': None}))"
# expect: TypeError: unsupported operand type(s) for -: 'int' and 'NoneType'
python3 -c "from shop.pricing import line_total; line_total({'unit_price': 'abc', 'qty': 2})"
# expect: ValueError: could not convert string to float: 'abc'
```

- [ ] **Step 6: Write `BUGS.md`** — copy the seeded-bug table above verbatim, prefaced with:

```markdown
# Seeded bugs (KEEP OUT OF ACCEPTANCE RUNS)

This file is the answer key. `evals/run-acceptance.sh` strips it
when copying the repo for a cold run. Fixes below are the canonical
negative-control fixes.
```

- [ ] **Step 7: Commit**

```bash
git add evals/seeded-py/
git commit -m "feat: python seeded eval repo (5 bugs across 3 lenses)"
```

---

### Task 5: TypeScript seeded eval repo

**Files:**
- Create: `evals/seeded-ts/package.json`
- Create: `evals/seeded-ts/tsconfig.json`
- Create: `evals/seeded-ts/src/pagination.ts`
- Create: `evals/seeded-ts/src/pricing.ts`
- Create: `evals/seeded-ts/src/cart.ts`
- Create: `evals/seeded-ts/tests/shop.test.ts`
- Create: `evals/seeded-ts/BUGS.md`

**Interfaces:**
- Produces: `paginate<T>(items, page, size)`, `lineTotal(item)`, `parseOrder(raw)`, `totalQuantity(lines)` — consumed by Task 7 acceptance.

Seeded bugs (5, one lens each):

| id | module | lens | trigger | buggy behavior | oracle | fix note |
| ts-1 | pagination | boundaries | `paginate(items, 0, 3)` | returns `[]` silently (negative slice clamps; no validation) | `throw Error("page must be >= 1")` | validate page/size |
| ts-2 | pricing | missing | `lineTotal({qty: 2})` | returns `NaN` silently | `throw Error("unitPrice is required")` | `Number.isFinite` check |
| ts-3 | pricing | malformed | `parseOrder("{oops")` | raw `SyntaxError` leaks | `throw Error("invalid order JSON")` | try/catch, rethrow domain error |
| ts-4 | cart | boundaries | `totalQuantity([])` | `TypeError: Reduce of empty array with no initial value` | returns `0` | `reduce(fn, 0)` |
| ts-5 | cart | malformed | qty as string `"2"` in lines | returns `"023"` (string) | `throw Error("qty must be a number")` | `typeof l.qty === "number"` check |

- [ ] **Step 1: Verify toolchain**

Run: `bun --version || node --version` → Expected: bun (preferred) or node ≥ 18.

- [ ] **Step 2: Write config and modules**

`package.json`:

```json
{
  "name": "seeded-ts",
  "private": true,
  "type": "module",
  "scripts": { "test": "vitest run" },
  "devDependencies": { "typescript": "^5.5.0", "vitest": "^2.0.0" }
}
```

`tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "bundler",
    "strict": true
  },
  "include": ["src", "tests"]
}
```

`src/pagination.ts`:

```ts
export function paginate<T>(items: T[], page: number, size: number): T[] {
  const start = (page - 1) * size;
  return items.slice(start, start + size);
}
```

`src/pricing.ts`:

```ts
export interface LineItem {
  unitPrice: number;
  qty: number;
  discount?: number;
}

export function lineTotal(item: LineItem): number {
  const discount = item.discount ?? 0;
  return Math.round(item.unitPrice * item.qty * (1 - discount) * 100) / 100;
}

export function parseOrder(raw: string): LineItem[] {
  return JSON.parse(raw) as LineItem[];
}
```

`src/cart.ts`:

```ts
export interface CartLine {
  id: string;
  qty: number;
}

export function totalQuantity(lines: CartLine[]): number {
  return lines.reduce((acc, l) => acc + l.qty);
}
```

- [ ] **Step 3: Write happy-path tests** — `tests/shop.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { paginate } from "../src/pagination";
import { lineTotal, parseOrder } from "../src/pricing";
import { totalQuantity } from "../src/cart";

describe("paginate", () => {
  it("returns the requested page", () => {
    expect(paginate([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 2, 3)).toEqual([4, 5, 6]);
  });
  it("returns a partial last page", () => {
    expect(paginate([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 4, 3)).toEqual([10]);
  });
});

describe("pricing", () => {
  it("applies the discount", () => {
    expect(lineTotal({ unitPrice: 10, qty: 2, discount: 0.5 })).toBe(10);
  });
  it("parses a valid order", () => {
    expect(parseOrder('[{"unitPrice": 9.99, "qty": 3}]')).toEqual([
      { unitPrice: 9.99, qty: 3 },
    ]);
  });
});

describe("cart", () => {
  it("sums quantities", () => {
    expect(
      totalQuantity([
        { id: "a", qty: 2 },
        { id: "b", qty: 5 },
      ]),
    ).toBe(7);
  });
});
```

- [ ] **Step 4: Install and run tests**

Run (cwd `evals/seeded-ts`): `bun install && bun run test` (or `npm install && npx vitest run` if no bun) → Expected: 5 passed.

- [ ] **Step 5: Probe every seeded bug**

```bash
bun -e "import {paginate} from './src/pagination'; console.log(paginate([1,2,3,4,5,6,7,8,9,10], 0, 3))"
# expect: []
bun -e "import {lineTotal} from './src/pricing'; console.log(lineTotal({qty: 2} as any))"
# expect: NaN
bun -e "import {parseOrder} from './src/pricing'; parseOrder('{oops')"
# expect: SyntaxError (raw, leaks position internals)
bun -e "import {totalQuantity} from './src/cart'; console.log(totalQuantity([]))"
# expect: TypeError: Reduce of empty array with no initial value
bun -e "import {totalQuantity} from './src/cart'; console.log(totalQuantity([{id:'a',qty:'2'},{id:'b',qty:'3'}] as any))"
# expect: 023  (string accumulation)
```

- [ ] **Step 6: Write `BUGS.md`** — same preface as Task 4 Step 6, then the seeded-bug table above verbatim.

- [ ] **Step 7: Commit**

```bash
git add evals/seeded-ts/
git commit -m "feat: typescript seeded eval repo (5 bugs across 3 lenses)"
```

---

### Task 6: README + acceptance harness

**Files:**
- Create: `README.md`
- Create: `evals/run-acceptance.sh` (executable)
- Create: `evals/.gitignore` (`seeded-py/.venv`, `seeded-ts/node_modules`, `*/BUGS.md` NOT ignored — BUGS.md is committed)

**Interfaces:**
- Produces: `evals/run-acceptance.sh <seeded-py|seeded-ts>` → prints a temp dir path containing the repo copy WITHOUT `BUGS.md`; consumed by Task 7.

- [ ] **Step 1: Write `evals/run-acceptance.sh`**

```bash
#!/usr/bin/env sh
# Copy a seeded eval repo to a fresh temp dir without BUGS.md,
# for cold acceptance runs. Usage: run-acceptance.sh <seeded-py|seeded-ts>
set -eu
repo="${1:?usage: run-acceptance.sh <seeded-py|seeded-ts}"
case "$repo" in
  seeded-py | seeded-ts) ;;
  *) echo "unknown repo: $repo" >&2; exit 1 ;;
esac
dir=$(mktemp -d "${TMPDIR:-/tmp}/sstack-$repo-XXXXXX")
cd "$(dirname "$0")"
rsync -a --exclude BUGS.md "$repo/" "$dir/"
echo "$dir"
```


- [ ] **Step 2: Write `README.md`** — full content:

```markdown
# sstack

A structured negative-testing skill pack for AI coding agents.
sstack discovers failure surfaces, attacks them through specialist
lenses, verifies observed behavior against a pre-declared oracle,
minimizes confirmed failures, and turns them into permanent
regression tests.

> Don't ask whether the software is robust. Exercise the failure
> condition and collect evidence.

## Install (any agent that reads skills)

Copy or link `skills/sstack/` into your agent's skills directory
(e.g. `~/.claude/skills/`, `~/.config/opencode/skills/`,
`.cursor/skills/`). Then invoke `/sstack <target>`.

## What it does

1. **Discover** — map surfaces and assumed contracts
2. **Attack** — boundaries / malformed / missing lenses, oracle
   written before each case
3. **Verify** — confirmed / refuted / inconclusive; confirmed
   findings must reproduce
4. **Minimize** — smallest repro
5. **Regress** — permanent test in your repo's suite

Artifacts land in `.sstack/` (`map.md`, `plan.md`, `findings/`).
The skill never edits your source code.

## Docs

- `docs/ETHOS.md` — the four rules
- `docs/ARCHITECTURE.md` — lifecycle, six definitions, full lens
  taxonomy, v1 roadmap

## Evals

`evals/seeded-py` and `evals/seeded-ts` contain deliberately buggy
repos (answer keys in `BUGS.md`). Acceptance: a cold agent given
only the skill finds seeds and lands regression tests that fail on
the buggy code and pass after the canonical fix.

    evals/run-acceptance.sh seeded-py   # prints temp dir sans BUGS.md
```

- [ ] **Step 3: Verify harness**

Run: `chmod +x evals/run-acceptance.sh && d=$(evals/run-acceptance.sh seeded-py) && ls "$d" && test ! -f "$d/BUGS.md" && echo "BUGS.md stripped OK"`
Expected: listing without `BUGS.md`, then `BUGS.md stripped OK`.

- [ ] **Step 4: Commit**

```bash
git add README.md evals/run-acceptance.sh evals/.gitignore
git commit -m "feat: readme and cold-run acceptance harness"
```

---

### Task 7: Cold acceptance runs (orchestrator-executed)

**Files:**
- Create: `evals/ACCEPTANCE.md` (results record)

**Interfaces:**
- Consumes: skill (Task 2), lens refs (Task 3), seeded repos + BUGS.md canonical fixes (Tasks 4–5), harness (Task 6).

This task is executed by the coordinating agent (subagent dispatch + verification), not as a code-writing task.

- [ ] **Step 1: Cold run, Python**

`d=$(evals/run-acceptance.sh seeded-py)`; dispatch a fresh task subagent with exactly this prompt (fill `<abs-path>`):

```
Read <abs-sstack-repo>/skills/sstack/SKILL.md and follow it as if
invoked as /sstack on the repo at <d>. That repo is your target;
do not read anything else from the sstack repository. Work
entirely inside the target repo.
```

- [ ] **Step 2: Score the Python run**

In `<d>`: run the new regression tests the subagent wrote
(`python3 -m pytest -q`). For each test: FAIL = live-bug regression
(correct); PASS = characterization. Map found tests to the
`evals/seeded-py/BUGS.md` seed table. Acceptance: ≥ 1 seeded bug
confirmed with a failing regression.

- [ ] **Step 3: Negative control, Python**

Apply the canonical fixes from BUGS.md to the copy in `<d>`
(validate page/size; validate qty; explicit key checks; None
discount → 0; clean numeric error). Re-run the subagent's
regressions: every live-bug regression must now PASS. No test may
pin buggy behavior.

- [ ] **Step 4–6: Repeat Steps 1–3 for `seeded-ts`** (run tests with `bun run test` / `npx vitest run`).

- [ ] **Step 7: Record and commit**

Write `evals/ACCEPTANCE.md`: per repo — seeds found / total,
regressions landed, fail-then-pass verified per seed id, deviations
or inconclusives. Commit:

```bash
git add evals/ACCEPTANCE.md
git commit -m "test: record cold acceptance results"
```

---

## Plan self-review

1. **Spec coverage** — identity/lifecycle/six definitions/taxonomy → Task 1; SKILL.md routing/stages/workspace/safety/report → Task 2; 3 lenses with shared template + py/ts examples → Task 3; seeded-py (5 bugs, 3 lenses) → Task 4; seeded-ts (5 bugs, 3 lenses) → Task 5; README + acceptance harness + BUGS.md stripping → Tasks 4–6; acceptance criteria (≥1/repo, fail-then-pass, no bug-pinning) → Task 7. Spec's "stretch: majority of seeds" is recorded in Task 7 scoring. No gaps.
2. **Placeholder scan** — all file contents are given in full; probe commands carry expected outputs; no TBD/TODO.
3. **Type consistency** — function names match across Tasks 3–5 and Task 7 (`paginate`, `line_total`, `add_item`, `total_items` / `paginate`, `lineTotal`, `parseOrder`, `totalQuantity`); lens file paths match Task 2's index; finding fields match Task 2's workspace contract.
