# sstack architecture

> sstack is a structured negative-testing skill pack for AI coding
> agents: it discovers failure surfaces, attacks them through
> specialist lenses, verifies observed behavior against a declared
> oracle, minimizes confirmed failures, and converts them into
> permanent regression tests.

## Lifecycle

Canonical, in order. Each stage is discrete, artifact-producing, and
resumable from its artifact (gstack's process lesson).

| Stage | Produces | Status |
|---|---|---|
| Discover | `.sstack/map.md` — surfaces + assumed contracts | shipped |
| Model | expected behavior per surface (folded into `map.md`) | folded |
| Attack | executed cases + verbatim observed output | shipped |
| Observe | captured actual behavior (folded into Attack) | folded |
| Verify | verdict per case: confirmed / refuted / inconclusive | shipped |
| Minimize | minimal repro per confirmed finding | shipped |
| Test | permanent negative test in the host repo's suite (red on confirmed, green on hardened) | shipped |
| Fix | minimal source change that satisfies the oracle, turning red to green | shipped |
| Learn | `.sstack/learn/` failure classes feeding future planning | shipped, proven cold 2026-09-24 |

## Six definitions

These prevent drift back into "a big bag of negative-testing
skills". If a new file does not fit one of these nouns, it does not
belong in the pack.

- **Skill** — the methodology for a stage. One entry skill owns
  routing and rules (`skills/sstack/SKILL.md`).
- **Lens** — an attack strategy over a failure class. Seven peer skills
  (`skills/sstack-<lens>/SKILL.md`) loaded inline under
  `### Lens rubric`, never by name. Selected per target by the Attack
  stage. A target repo can add more without changing the pack: see
  **Custom lens**.
- **Agent** — a `runSubagent` dispatch handle. One file per shipped
  lens (`agents/sstack-<lens>-attacker.md`); the orchestrator pastes
  workspace, surface map, rubric, and the Report format block into
  the subagent's message. A subagent starts blank: the paste is the
  carrier; the attacker file keeps field names as fallback.
- **Runner** — deterministic execution of generated cases. Deferred:
  v0 has the agent run real commands itself and quote real output.
- **Oracle** — the expected-behavior declaration written *before*
  the attack. Errors, degradation, retry bounds, invariants,
  rejections — not only crashes.
- **Evidence** — observed output vs. oracle, recorded as markdown
  plus machine JSON in `.sstack/findings/`. `evals/replay.py`
  re-verifies the fingerprint with the agent out of the loop.


- **Custom lens** — a repo-authored attack strategy in
  `.sstack/lenses/<name>.md`, selected by `.sstack/config.md`. The
  seven shipped lenses are a floor, not a ceiling: a custom lens
  appends its rubric to an existing attacker agent's dispatch rather
  than adding a new agent, and runs under the same Report format,
  emitter, and run-end checks. Config and lenses are the only
  `.sstack/` entries kept out of the ignore list, so a team can
  commit them.
## Taxonomy

Negative testing is the domain; lenses explore it. Security is a
lens, never the identity.

| Category | Lens | v0 |
|---|---|---|
| Input | boundaries | ✅ |
| Input | malformed | ✅ |
| Input | missing | ✅ |
| Access | ownership | ✅ (peer skill + agent) |
| Behavior | exceptional-conditions | ✅ (peer skill + agent) |
| Behavior | state | ✅ (peer skill + agent) |
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

`skills/sstack/SKILL.md` (orchestrator) + 7 peer lens skills
(`skills/sstack-<lens>/SKILL.md`) + 7 attacker agents
(`agents/sstack-<lens>-attacker.md`) + five seeded eval fixtures.
Discover consumes `create-verification-skill` and
`maintain-verification-skill`; Attack consumes
`principle-attack-the-premise`; Test consumes
`principle-test-behavior-not-implementation`; Fix consumes
`principle-fix-root-causes` when available, with docs/types/call-sites
fallback. Every optional dependency carries an inline fallback
(ADR-0007). Extension is additive and goes two ways: a pack
extension is one lens skill, one agent file, one index row, and a
target-repo extension is one file in `.sstack/lenses/`, selected by
`.sstack/config.md` and appended to an existing attacker's dispatch,
with no pack change at all. The evidence schema and replay verifier
shipped as one example of the first shape.


## Prior art

- **gstack** — process model: discrete, artifact-producing,
  resumable stages. Infra (binaries, daemon) deliberately not
  copied.
- **pstack** — one launcher skill + on-demand content files.
- **impeccable** — `references/` per subcommand; `scripts/`
  evidence layer addable later. (sstack rejects impeccable's
  audit-not-fix stance per ADR-0005.)
