# Roadmap

Where sstack goes after v0.1.0. Each item names the evidence that put
it here; nothing on this list is speculative. The decision behind the
shape of v0 lives in [`docs/adr/`](docs/adr/README.md).

The organizing rule: **every item must either raise proof quality or
lower the cost of a run.** Anything that does neither is out.

## The gap v0 left

v0 is a content-only skill pack with a process-only evidence layer
(ADR-0002). Two consequences, both real, both measured:

- **Cold-agent compliance is the weak axis.** Six acceptance runs each
  violated a rule in prose, and each violation forced a guardrail:
  bug-pinning regressions, source-fixing mid-run, a contaminated skill,
  and broken harnesses scored as verdicts. The guardrails worked; the
  pattern is the signal.
- **No deterministic evidence schema.** A finding is only as
  reproducible as the agent's transcript.

## v1 — raise proof quality

### Structured evidence with fingerprints

- **Why**: the deferred half of ADR-0002. A confirmed finding should
  be re-checkable without re-reading a chat transcript.
- **What**: a small JSON schema for `findings/` — command, exit code,
  stdout/stderr, input fingerprint, oracle, verdict, regression
  pointer. Loose markdown stays the human view; the JSON is the
  machine view.
- **Done when**: a cold run's finding can be re-verified from its
  evidence file alone, with the agent out of the loop.
- **Add**: a thin `scripts/` verifier under the skill. First code in
  the pack; still no CLI, still no daemon (ADR-0002 revisit trigger:
  this is it).

### Mutation as a verification strategy

- **Why**: ADR-0001 scoped mutation to "deferred, not the center."
  It is the strongest signal that a generated test has teeth.
- **What**: the `mutation` lens and the mutation entry in the v1
  proof-gate menu. Only after structured evidence exists, so a
  mutation result is itself recorded as evidence.
- **Done when**: a regression test can be shown to go red against a
  seeded mutant, not only against the original bug.

### Remaining input and behavior lenses

- **What**: `state`, `ordering`, `concurrency`, `idempotency` next —
  the behavior lenses catch more real defects than more input lenses.
  Then `dependency-failure`, `resource-exhaustion`, `contract`.
- **Done when**: the seeded repos carry at least one seed per shipped
  lens, and a clean run reaches a majority on both.
- **Note**: additive only. A lens is a `references/lens-<name>.md`
  file plus one index row (ADR-0002).

### Run-end checklist

- **Why**: the deferred hardening in ADR-0002. Prose guardrails have
  been load-bearing four times; a mechanical check catches the fifth
  without a new paragraph.
- **What**: before the report, the skill verifies source is unchanged
  (`git status` when available), every confirmed finding has a
  regression, and every regression's state is reported honestly.
- **Done when**: the checklist appears in the shipped skill and a
  deliberately-defective cold run is caught by it.

## v2 — lower the cost of a run

### Containment that survives a curious agent

- **Why**: two cold runs escaped their temp target, one editing the
  main repo's seeds. The current harness works because the prompt is
  strict, not because the boundary is hard.
- **What**: run the cold agent with its working directory *inside* the
  temp workspace, so the skill's relative `.sstack/` path cannot
  resolve outside it. The escape we saw was exactly that.
- **Done when**: an agent that ignores the prompt still cannot write
  to the sstack repo.

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
- **What**: only if separation earns it — an isolated oracle that
  cannot see the attacker's reasoning is the obvious candidate, and
  the eval is the judge.
- **Done when**: an isolated verifier measurably beats the inline
  oracle on the seeded repos. If it does not, it stays deferred.

### Host packaging

- **Why**: ADR-0002 chose host-agnostic for zero install friction. That
  costs a forced update path, so stale skill copies can linger.
- **What**: a thin installer per host (Cursor, OpenCode, Claude Code)
  that copies `skills/sstack/` and nothing else. No plugin API, no
  marketplace entry until a host needs one.
- **Done when**: install and update are one command per host.

## Explicitly not planned

- **A hosted runtime.** sstack runs where the agent runs (ADR-0002).
- **A test-generation product.** Happy-path coverage is the host
  repo's business (ADR-0001).
- **A security scanner.** Security is one lens among many
  (ADR-0001).
- **Mutation as the identity.** It is a strategy under proof quality,
  never the frame (ADR-0001).

## How a roadmap item ships

Every item lands the way v0 did: seeded bugs in `evals/`, a cold run
that finds them, a negative control that flips, and the result in
`evals/ACCEPTANCE.md`. A roadmap item without acceptance evidence is
not done, however good the prose is.
