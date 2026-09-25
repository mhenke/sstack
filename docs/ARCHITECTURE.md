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
| Test | permanent negative test in the host repo's suite (red on confirmed, green on hardened) | yes |
| Fix | minimal source change that satisfies the oracle, turning red to green | yes |
| Learn | `.sstack/learn/` failure classes feeding future planning | deferred |

## Six definitions

These prevent drift back into "a big bag of negative-testing
skills". If a new file does not fit one of these nouns, it does not
belong in the pack.

- **Skill** — the methodology for a stage. One entry skill owns
  routing and rules (`skills/sstack/SKILL.md`).
- **Lens** — an attack strategy over a failure class. Content
  (`agents/sstack-<lens>-attacker.md` loading the peer
  `skills/sstack-<lens>/SKILL.md`), not machinery. Selected per
  target by the Attack stage.
- **Agent** — a Thermos dispatch handle. One file per shipped lens
  (`agents/sstack-<lens>-attacker.md`); the orchestrator dispatches
  it by name at the Attack stage.
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
| Access | ownership | next (highest priority) |
| Behavior | exceptional-conditions | next |
| Behavior | state | future |
| Behavior | ordering | future |
| Behavior | concurrency | future |
| Behavior | idempotency | future |
| Environment | dependency-failure | future |
| Environment | resource-exhaustion | ✅ (peer skill + agent; future: rubric depth) |
| Contracts | contract | future |
| Evidence | mutation | future |
| AI / Agent | agent | future |
| Security | security | future |

### Vocabulary

The QA field splits "negative testing" more narrowly than sstack does,
and the split is load-bearing for oracle design:

- **Edge case** — a location on a parameter's range. `0`, `-1`, `max`,
  an empty string. Often still a *valid* input.
- **Negative case** — a class of input the system should reject or
  degrade on. Wrong type, malformed structure, absent field.

`boundaries` is the edge-case lens. `malformed` and `missing` are
negative-case lenses. Negative testing is the domain and covers both.

Sources disagree on where boundary values sit relative to negative
testing. Tricentis includes boundary values under negative testing;
TestinGil separates them. sstack follows the TestinGil split because
the oracle differs: a boundary input may be valid (return a short
page) while a negative input must be rejected or degraded. If the
oracle for a boundary input is "raise an error," it has crossed into
negative-case territory regardless of where it sits on the number
line.

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

`skills/sstack/SKILL.md` (orchestrator) + 4 peer lens skills
(`skills/sstack-<lens>/SKILL.md`) + 4 attacker agents
(`agents/sstack-<lens>-attacker.md`) + this docs pair + five seeded
eval fixtures. Discover consumes `create-verification-skill` and
`maintain-verification-skill` when the target provides them, with a
docs/types/call-sites fallback. Everything else (runners, evidence
schema, learn loop, 11 remaining lenses, host packaging) is additive
later via new peer skill and agent files — no restructuring.

## Prior art

- **gstack** — process model: discrete, artifact-producing,
  resumable stages. Infra (binaries, daemon) deliberately not
  copied.
- **pstack** — one launcher skill + on-demand content files.
- **impeccable** — `references/` per subcommand; `scripts/`
  evidence layer addable later. (sstack rejects impeccable's
  audit-not-fix stance per ADR-0005.)
