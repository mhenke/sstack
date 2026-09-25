# Roadmap

Where sstack goes after v0.1.0. Each item names the evidence that put it
here; nothing on this list is speculative. The decisions behind the
shape of v0 live in [`docs/adr/`](docs/adr/README.md).

The organizing rule: every item must either raise proof quality or
lower the cost of a run. Anything that does neither is out.

## What v0 left open

v0 is a content-only skill pack with a process-only evidence layer
(ADR-0002). Current consequences:

- Cold-agent compliance is the weak axis. Acceptance runs have each
  exposed a prose-compliance failure, and the guardrails now cover
  the observed classes, but the current five-language fixture set has
  no fresh cold-run evidence.
- No deterministic evidence schema, so a finding is only as
  reproducible as the agent's transcript.

## v1: raise proof quality

### Structured evidence with fingerprints

- **Why**: the deferred half of ADR-0002. A confirmed finding should
  be re-checkable without re-reading a chat transcript.
- **What**: a small JSON schema for `findings/`: command, exit code,
  stdout/stderr, input fingerprint, oracle, verdict, regression
  pointer. Loose markdown stays the human view; the JSON is the
  machine view.
- **Done when**: a cold run's finding can be re-verified from its
  evidence file alone, with the agent out of the loop.
- **Add**: a thin `scripts/` verifier under the skill. First code in
  the pack, and still no CLI or daemon. This is the item ADR-0002
  named as its own revisit trigger.

### Mutation as a verification strategy

- **Status**: skill text shipped (`5de75b3`); the dedicated mutation
  lens and acceptance evidence remain open.
- **What**: add the `mutation` lens and the mutation entry in the v1
  proof-gate menu. Only after structured evidence exists, so a
  mutation result is itself recorded as evidence.
- **Tooling per language**, researched rather than guessed: PIT for
  Java, Stryker for JS/TS, mutmut for Python, RapidCheck or Google
  FuzzTest for C++. One 2026 survey (softwaretestingbasics.io) puts
  ~80% mutation score on critical modules as the practical bar;
  PIT and Stryker publish no number. All advise running on changed
  code rather than whole-repo sweeps.
- **Done when**: a regression test can be shown to go red against a
  seeded mutant, not only against the original bug.

### Property-based testing as the Attack default

- **Status**: SHIPPED in skill text (`5de75b3`). Pending acceptance
  evidence.
- **What**: an Attack-stage rule that checks for an installed
  property-based library and writes a property before hand-designing
  cases, plus a Minimize rule that delegates shrinking. Oracle-first
  ordering stays sstack's and is not delegated. A library finds an
  input that breaks an assumption; sstack declares what should have
  happened instead.
- **Done when**: a run against a seeded repo with Hypothesis or
  fast-check installed lands property-based regressions, and the
  coverage rule still forces every mapped surface to be attacked.
- **Risk**: over-delegation. An agent that finds a library may stop
  reading surfaces, so the per-surface coverage rule stays mandatory.

### Remaining input and behavior lenses

- **What**: `state`, `ordering`, `concurrency`, `idempotency` next.
  The behavior lenses catch more real defects than more input lenses.
  Then `dependency-failure`, `contract`. (`resource-exhaustion`
  already shipped as a peer skill + agent.)
- **Done when**: the seeded repos carry at least one seed per shipped
  lens, and a clean run reaches a majority on each supported fixture.
- **Note**: additive only. A lens is an
  `agents/sstack-<name>-attacker.md` wrapper plus a
  `skills/sstack-<name>/SKILL.md` rubric plus one row in
  SKILL.md's lens index (ADR-0002).

### Run-end checklist

- **Status**: skill text shipped (`5de75b3`); current acceptance
  evidence remains pending.
- **What**: before the report, the skill verifies every confirmed
  finding has a red test and a green post-fix test, every refuted
  finding on external input has a green hardening test, every fix is
  minimal, and the full suite passes.
- **Done when**: the checklist appears in the shipped skill and a
  deliberately-defective cold run is caught by it.

## v2: lower the cost of a run

### Containment that survives a curious agent

- **Status**: harness-backed containment. `python3 evals/acceptance.py
  prepare <fixture>` builds one temp workspace containing the skill,
  all four lens skills, the four agents, and the decontaminated
  fixture. The caller dispatches the cold agent into that workspace.
  The skill resolves all paths via the `.sstack-host-repo` marker.
- **What is enforced**: the harness strips `BUGS.md`, caches,
  `node_modules`, `target`, and `build`; the cold agent receives no
  answer key in its workspace.
- **Residual risk**: prompt-only containment. A cold agent that
  ignores the prompt can still reach the sstack repo. Compare
  `git status` before and after the run to detect it.

### Learn loop

- **Why**: ADR-0001 lists it deferred. A repo's failure classes
  ("retry duplicates webhook", "pagination loses last item") should
  feed the next run's planning.
- **What**: `.sstack/learn/` records confirmed failure classes; the
  Discover stage reads them and re-tests adjacent code.
- **Done when**: a second run on the same repo prioritizes a seed it
  missed the first time because a neighboring failure class pointed
  at it.
- **Risk**: the loop can overfit to a repo's history. Mitigate by
  treating learned classes as prioritization, never as proof.

### Specialised agents

- **Why**: ARCHITECTURE.md defers agents-as-files. v0 has one agent
  adopt roles per stage.
- **What**: only if separation earns it. An isolated oracle that
  cannot see the attacker's reasoning is the obvious candidate, and
  the eval is the judge.
- **Done when**: an isolated verifier measurably beats the inline
  oracle on the seeded repos. If it does not, it stays deferred.

### An isolated oracle, and what already landed

The one defect that survived the v0 acceptance record was a verdict
the agent talked itself into: a disjunctive oracle ("throws TypeError
or returns NaN") encoded as a single `toBeNaN()` assertion. The
attack was sound and the regression was sound, so the failure sits in
the judging. That is the specialised-agent problem in miniature, and
the v1 response is prose rather than a subagent: Verify now requires
steel-manning the observed behavior before recording `confirmed`, and
naming the conditions that would break the verdict.

The steel-man step is portable, carries no host dependency, and
catches the disjunctive-oracle class directly. An isolated oracle
subagent stays deferred, because its packaging (`model:` pinning,
blocking gates) is host-specific and would break ADR-0002's
host-agnostic choice.

One observation is worth recording. A cold TypeScript run fanned out
into per-stage subagents on its own, without being told to, which
suggests the stage structure in the skill invites that shape. Whether
an explicit oracle subagent beats the fan-out the agent picks for
itself is measurable on the seeded repos, and the bar is beating both
the inline oracle and that self-selected fan-out.

### Specialised agents: Thermos pattern

The [Thermos](https://github.com/cursor/plugins/tree/main/thermos)
plugin demonstrates the architecture: an orchestrator dispatches N
specialised subagents in parallel, each carrying a single rubric, then
synthesizes. sstack's Attack stage maps directly onto this shape,
because the lenses are independent of each other and all depend on
Discover's output.

- **What**: at the Attack stage, dispatch one subagent per lens. Each
  loads its `sstack-<lens>` skill, receives the `map.md` path, and
  attacks every mapped surface through that lens alone. Results
  return to the orchestrator for Verify, Minimize, and Regress. The
  orchestrator deduplicates, steel-mans, and reports.
- **Why this over the current inline loop**: the per-lens attack is
  embarrassingly parallel. A cold run against 3 surfaces x 4 lenses
  currently runs 12 cases sequentially; the fan-out runs them
  concurrently. Each subagent also carries a narrower context (one
  lens, not four), which improves focus.
- **Evidence this works**: a cold TypeScript run fanned out into
  per-stage subagents on its own, without being told to. The stage
  structure in the skill invites that shape. Thermos formalizes the
  same pattern for review; sstack formalizes it for attack.
- **Constraint**: Discover still runs as a single agent (one map).
  Regress still runs as a single agent (test suite writes must be
  coordinated). The parallel fan-out is Attack-only.
- **Done when**: a per-lens fan-out cold run completes against a
  seeded repo, finds at least as many seeds as the inline loop, and
  completes in less wall clock.

### The ownership lens (next lens, highest priority)

Authorization-scope violations: user A's session returns user B's
entity. Valid request, wrong session. OWASP A01:2025 Broken Access
Control and API1:2023 BOLA. The check-number scenario: a user
searches by check number and sees only their own checks. A missing
authorization check means they see someone else's.

Discovery strategies from OWASP A01:2025:

- Swap entity IDs between sessions (`/api/user/101` to `/api/user/102`)
  and confirm the response denies access.
- Build a permission matrix mapping roles to permissions, and verify
  that low-privileged roles cannot reach high-privileged endpoints.
- Verify that every endpoint enforces centralized authorization
  (middleware, decorator, guard) rather than relying on the client to
  hide UI elements. sstack's Discover stage should flag any surface
  that lacks a visible auth check.

Remediation patterns that become oracle patterns:

- **Deny by default**: an endpoint with no explicit authorization
  should return 401/403, not 200. The absence of a check is itself
  the bug.
- **Indirect reference keys**: sequential database IDs in URLs are
  enumerable. GUIDs are the remediation, but sstack's job is to prove
  that sequential IDs are actually exposed, not to assume they aren't.

- **Why first**: authorization failures are the most exploitable class
  of bug and the least likely to be caught by input-generation lenses.
  The input is valid; the session is wrong.
- **Execution model**: unit tier works with sstack's scratch-script
  model: mock the user object, set the role, call the function, assert
  the rejection. No authenticated sessions needed at this tier.
  Integration tier needs real sessions, multiple test users, and a
  live router to catch framework-level bypasses (routing files that
  skip the handler entirely). sstack v0 covers the unit tier;
  integration tier needs the evidence schema's session/entity
  recording.
- **Interaction with verification skill**: the target's verification
  skill (pstack `/create-verification-skill` or equivalent) already
  knows the entities, the ownership model, and the auth flow. The
  ownership lens reads that map and attacks the boundaries between
  users.
- **Done when**: a seeded repo with an authorization-scope bug is
  confirmed by a cold run through the ownership lens, and the
  regression test proves the access-control check exists.

### The exceptional-conditions lens (A10:2025)

Fail-open scenarios, diagnostic leakage, cascading failures. OWASP
A10:2025 Mishandling of Exceptional Conditions. The `malformed` lens
tests input shape; this lens tests what the system does when
something fails, regardless of whether the trigger was malformed
input or a dying dependency.

- **Why second**: a fail-open auth service, a stack trace leaking
  database schema to the client, and a cascading cluster failure are
  more damaging than most input-validation bugs. They are also the
  least likely to be caught by happy-path tests, because they only
  fire when something else breaks.
- **Discovery strategies**:
  - Drop a dependency or inject a timeout mid-request. Does the
    system deny access (fail-safe) or grant access (fail-open)?
  - Search for empty or overly generic catch blocks
    (`catch (Exception e) { }`) that swallow errors silently.
  - Attack with malformed input and inspect the error response:
    does it leak stack traces, database schema, API keys, or
    internal hostnames to the end user?
- **Oracle patterns**:
  - Fail-safe: when an upstream dependency fails, the system denies
    access or degrades to a safe default, never grants access.
  - Sanitized errors: the client sees a generic message and a unique
    tracking ID. The detailed error goes to server-side logs only.
  - No cascading failures: one component's timeout does not propagate
    as a full-system outage.
- **Interaction with `malformed`**: the `malformed` lens triggers the
  error. This lens tests what the error handler does with it. The two
  are complementary, not overlapping.
- **Execution model**: unit tier works with sstack's scratch-script
  model: mock the failing dependency, call the function, assert that
  the raised exception is sanitized (no stack trace, no internal IP,
  no raw message). Integration tier needs a live server to catch
  framework-level routing bypasses and infrastructure cascades. sstack
  v0 covers the unit tier; integration tier needs the evidence
  schema's structured failure recording.
- **Done when**: a seeded repo with a fail-open path is confirmed by
  a cold run through this lens, and the regression test proves the
  fail-safe behavior exists.

### Host packaging

- **Why**: ADR-0002 chose host-agnostic for zero install friction. That
  costs a forced update path, so stale skill copies can linger.
- **What**: a thin installer per host (Cursor, OpenCode, Claude Code)
  that copies `skills/sstack/` and nothing else. No plugin API and no
  marketplace entry until a host needs one.
- **Done when**: install and update are one command per host.

## Language breadth: Python, JavaScript, TypeScript, Java, C++

The process is language-agnostic. v0 now carries one seeded fixture
per supported language. Each fixture has five seeds and its own
`BUGS.md` answer key; the answer key is stripped by the cold-run
harness.

| Language | Fixture | Baseline |
|---|---|---|
| Python | `evals/seeded-py` | `pytest -q` |
| TypeScript | `evals/seeded-ts` | `bun run test` |
| JavaScript | `evals/seeded-js` | `node --test` |
| Java | `evals/seeded-java` | `mvn test` |
| C++ | `evals/seeded-cpp` | `cmake` + `ctest` |

These are fixture baselines, not cold-run acceptance results. The
current acceptance record remains stale until a cold agent runs each
fixture against the current skill text.

### Per-language lens addenda

- **What**: a short section per language on how the three v0 lenses
  manifest there, saying so where the generic heuristic misleads. The
  `boundaries` lens currently says "negative index (language-specific
  behavior!)" and illustrates with Python and JS; in Go a negative
  index panics, in Rust it panics at the bounds check, and an agent
  working from the Python example will predict the wrong failure.
  `missing` has the same problem: Python `dict.get(k, default)` and
  TypeScript `??` treat explicit-null differently from `d[k]`, and a
  Java or C++ agent is looking at zero-value structs and err returns.
- **Done when**: every lens has an addendum for all five languages,
  and each addendum names at least one case where that language
  behaves differently from the Python example.
- **Note**: reference content, additive. One file per language under
  `references/languages/`, pointed at from the lens index.

### Seeded repos per language

- **Why**: the eval discipline caught every real defect so far
  because the seeds are language-specific. Without a repo, "we support
  it" is a claim.
- **What**: one seeded repo per new language, five bugs each, mapped
  one-to-one to the lenses, answer key in `BUGS.md`, verified by a
  clean cold run plus a negative control.
- **Done when**: a clean run on each new repo confirms seeds and
  flips them green under the canonical fixes.
- **Budget**: this is the expensive half. Three languages, three
  repos, three cold runs, three negative controls. Sequence it after
  the evidence schema lands, because a per-language run without
  structured evidence is a transcript nobody can re-check.

### Readme honesty line

- **Status**: LANDED in `150d6c2`. The README's Languages section
  states proven (Python, TypeScript) vs works-by-inference (JavaScript,
  Java, C++, others).

### The JavaScript shortcut, stated honestly

JavaScript is not really a new language for sstack. The `malformed` and
`missing` lenses already reason about erased runtime types, which is
the JavaScript condition; TypeScript just makes it visible at compile
time. A JavaScript addendum is mostly a note that the TypeScript
advice applies with the type checker removed, plus a seeded repo to
prove it. If the budget is tight, ship it as a TypeScript addendum
with the type-checker note rather than treating it as a peer
language.

### C++ needs a second verification mode, not a lens addendum

- **Why**: the items above file C++ as reference content, which
  understates it. C++ negative testing does not share sstack's proof
  model. libFuzzer and Google FuzzTest assert the *absence* of
  undefined behavior through sanitizers, often with no assertion in
  the test at all. sstack is oracle-first throughout, and every stage
  assumes a declared expected behavior. That assumption does not hold
  for the highest-value C++ negative testing.
- **What**: decide whether a sanitizer-driven mode is a second
  verification path alongside the oracle path, or whether C++ support
  stays inference-only. FuzzTest's own docs draw the line the decision
  has to make: UB detection with no assertions, versus explicit
  correctness properties.
- **Done when**: the decision is written down as an ADR and the
  language-breadth table above reflects it.
- **Note**: settle this before writing a C++ seeded repo, or the seeds
  encode an assumption that turns out wrong.

## Explicitly not planned

- **A hosted runtime.** sstack runs where the agent runs (ADR-0002).
- **A test-generation product.** Happy-path coverage is the host
  repo's business (ADR-0001).
- **A security scanner.** Security is one lens among many
  (ADR-0001).
- **Mutation as the identity.** It is a strategy under proof quality,
  never the frame (ADR-0001).

## Deferred

- **Acceptance re-runs.** Cold-run evidence for the current skill text
  is pending. The last clean evidence is at `9979718` (runs #6 and
  CleanTs). Re-run when tagging a release.
- **Evidence schema with fingerprints.** See v1 above.
- **Learn loop.** See v2 above.
- **Host packaging.** See v2 above.
- **Language breadth seeded repos.** See the language breadth section
  above.

## How a roadmap item ships

Every item lands the way v0 did: seeded bugs in `evals/`, a cold run
that finds them, a negative control that flips, and the result in
`evals/ACCEPTANCE.md`. A roadmap item without acceptance evidence is
not done, however good the prose is.
