# sstack MVP Design

Date: 2026-09-23
Status: Approved (brainstorming complete; pre-implementation)

## Problem

LLM-generated tests cluster on the happy path. sstack is a structured
negative-testing skill pack for AI coding agents: it discovers failure
surfaces, attacks them through specialist lenses, verifies observed behavior
against a declared oracle, minimizes confirmed failures, and converts them
into permanent regression tests.

Conceptual center, locked during brainstorming:

- **Negative testing is the domain.** Testing techniques (mutation, fuzzing,
  fault injection) are lenses/evidence mechanisms, not the product identity.
- Security is one lens, never the identity.
- The general principle is **oracle-first**, not controlled-failure: a
  negative test defines explicit expected behavior under an adverse condition
  (error, degradation, retry bound, invariant, rejection) and produces
  observable evidence of satisfaction or violation.

## Prior art and what was borrowed

| Source | Borrowed | Rejected |
|---|---|---|
| gstack (garrytan/gstack) | Process model: discrete, artifact-producing, resumable stages; root `ETHOS.md`/`ARCHITECTURE.md` | Bun binaries, browser daemon, runtime infrastructure |
| pstack (cursor/plugins/pstack) | One launcher skill + on-demand content files + inline index | 23-skill sprawl, model-role routing |
| impeccable (pbakaus/impeccable) | One skill + `references/` per subcommand; `scripts/` evidence layer addable later without restructuring; audit-not-fix stance | (see mechanics below) |

Impeccable mechanics explicitly **not** borrowed in v0 (user decision):
isolated verify subagent, degraded-run banner, ignore file, severity
tags + trend tracking. Report-then-persist delivery order is kept (costs
nothing; it is prose discipline).

## User-locked decisions

| Decision | Choice |
|---|---|
| Host | Agent-agnostic skills (agent-skills SKILL.md format). No plugin packaging. |
| CLI / runners | None in v0. The agent runs real commands itself and quotes real output. |
| Evidence | Process-only: loose markdown artifacts under `.sstack/`. Strict schema, fingerprints deferred to v1. |
| v0 slice | `ARCHITECTURE.md` + `ETHOS.md` + one orchestrator skill + 3 input lenses |
| Demo target | Seeded-bug repos in **both** Python/pytest and TypeScript/vitest |
| Structure | Skill + lens reference files (impeccable/pstack shape) |

## Repo layout

```text
sstack/
├── skills/sstack/
│   ├── SKILL.md                     # entry: routing, lifecycle, rules, lens index
│   └── references/
│       ├── lens-boundaries.md
│       ├── lens-malformed.md
│       └── lens-missing.md
├── docs/
│   ├── ARCHITECTURE.md              # lifecycle, six definitions, taxonomy, v0 scope
│   └── ETHOS.md                     # motto + four rules
├── evals/
│   ├── seeded-py/                   # Python + pytest, 4–5 seeded bugs
│   └── seeded-ts/                   # TypeScript + vitest, 4–5 seeded bugs
└── README.md                        # what/why/install-as-skill
```

## docs/ARCHITECTURE.md

- **Canonical lifecycle**: Discover → Model → Attack → Observe → Verify →
  Minimize → Regress → Learn. v0 implements Discover→Regress inline in the
  skill; Learn is documented but deferred. Model = recording expected
  behavior/contracts (the oracle material). Observe = capturing what the
  attack actually produced.
- **Six definitions** (drift prevention):
  - **Skill** — methodology for a stage.
  - **Lens** — an attack strategy over a failure class (content, not machinery).
  - **Agent** — a reasoning role; in v0, roles the one agent adopts per stage,
    not separate files.
  - **Runner** — deterministic execution of generated cases; deferred (v0:
    agent runs real commands and quotes real output).
  - **Oracle** — the expected-behavior declaration written before the attack.
  - **Evidence** — observed output vs. oracle; v0 loose markdown, v1
    structured.
- **Taxonomy**: Input / Behavior / Environment / Contracts / AI-Agent /
  Security. All 13 lenses listed; boundaries, malformed, missing marked v0;
  the other 10 marked future (state, ordering, concurrency, idempotency,
  dependency-failure, resource-exhaustion, contract, mutation, agent,
  security).
- **Verification strategies catalog**: controlled fault, mutation, known-bad
  fixture, differential comparison, invariant violation, contract violation,
  expected-error assertion, reproducibility. v0 uses expected-error assertion
  + reproduction; the rest documented as the v1 proof-gate menu.

## docs/ETHOS.md

> Don't ask the agent to say whether the software is robust. Make it
> exercise the failure condition and collect evidence.

1. Attack assumptions.
2. Define the oracle before the attack.
3. Never accept an agent's claim as evidence — run the real command, quote
   the real output.
4. Turn confirmed failures into permanent regressions.

## skills/sstack/SKILL.md

Frontmatter: `name: sstack`; description loaded with negative-testing trigger
phrases (edge cases, "what happens if", robustness, failure modes, negative
tests, hostile input).

1. **Routing** — `/sstack [target]` runs the full lifecycle; bare `/sstack`
   infers target from recent changes; explicit stage request (`/sstack
   verify`) enters that stage using existing `.sstack/` state.
2. **Stage instructions**:
   - **Discover**: map entry points, public functions, API routes, parsed
     inputs; write `.sstack/map.md` (surfaces + assumed contracts — the
     Model output).
   - **Attack**: pick applicable lenses from the index, read those reference
     files, design cases. Each case records its oracle first. Execute for
     real (scratch script, endpoint call, test run). Quote actual output.
   - **Verify**: expected vs. observed → confirmed / refuted / inconclusive.
     A finding is confirmed only if it reproduces.
   - **Minimize**: strip the confirmed case to the smallest repro.
   - **Regress**: write a permanent test in the host repo's real test suite
     (correct directory, existing framework), asserting the oracle. Test must
     fail against current code (bug live) or pass (already-handled —
     characterization, noted as such).
3. **`.sstack/` workspace**: `map.md`; `plan.md` when a run is scoped;
   `findings/<slug>.md` (lens, case, oracle, observed, verdict, repro,
   regression location); `scratch/` for throwaway execution, cleaned after.
   Report delivered in chat first; files are bookkeeping.
4. **Lens index**: table of lens → when it applies → reference file.
5. **Safety rules**: read-only toward prod config/secrets; writes only tests
   and `.sstack/`; never mutate source to prove a bug (repro happens in
   scratch space); respect the repo's test conventions.

## Lens reference files

Shared template: what assumptions the lens attacks · case-generation
heuristics · oracle patterns · worked examples in Python and TypeScript ·
when not to apply.

- `lens-boundaries.md` — numeric/size/index/collection edges: 0, -1, max,
  empty, off-by-one, first/last, just-over threshold.
- `lens-malformed.md` — wrong types, corrupt structures, garbage encodings.
- `lens-missing.md` — absent fields, null/None/undefined, empty inputs,
  dropped keys.

## evals/ — acceptance

Two seeded repos, each a tiny realistic module set (~3 files, plain
functions, no framework beyond pytest/vitest):

- `seeded-py`: `pagination.py` (page=0 / size=0 / huge page), `pricing.py`
  (None field, non-numeric string, missing discount key), `cart.py`
  (negative quantity, duplicate item id).
- `seeded-ts`: same bug classes (NaN propagation from undefined, JSON.parse
  throw, slice off-by-one, reduce without initial on empty array,
  string+number coercion).
- Every seeded bug maps to exactly one v0 lens; `BUGS.md` in each eval
  records the seed list and is withheld from the skill during acceptance
  runs.

**Acceptance criteria** (the MVP demo):

1. A cold subagent given only the skill + repo path, run on each seeded
   repo, confirms at least 1 seeded bug per repo.
2. Each confirmed finding lands a regression test in the repo's real test
   suite that (a) fails on the seeded code and (b) passes after the seed
   fix. Stretch: majority of seeds found per repo.
3. Negative control: fixing a seed flips its regression test from fail to
   pass (no test pins the buggy behavior).

## Error handling and edge behavior

- No test framework detected → skill asks before scaffolding one;
  characterization tests only with consent.
- Library without runnable entry → attacks run via scratch scripts in
  `.sstack/scratch/`, cleaned up after.
- Inconclusive findings stay in `findings/` marked inconclusive; never
  promoted to regressions.
- The skill never edits source code — findings and tests only. Fixing is a
  separate task (audit-not-fix).

## Deferred (v1+)

Agents-as-files; runners/CLI; evidence schema + fingerprints; learn loop
(`.sstack/learn`); 10 additional lenses; mutation/proof gate; impeccable
mechanics (isolated verify, degraded banner, ignore file, severity/trend);
host packaging (Cursor/OpenCode plugins); host adapters. All additive via
new `references/` files or a `scripts/` dir — no restructuring.
