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
