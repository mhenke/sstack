# Research index

The dated community scans behind decisions in this repo, and the ones
still open. Full raw transcripts live in the local research library.
This file is the index into them and the record of what each one
changed.

## Applied to shipped decisions

### Negative testing across five languages (2026-09-27)

Tool inventory from this scan: [`TOOLS.md`](../TOOLS.md).

Source: `negative-testing-edge-case-unit-testing-across-languages-raw-v3.md`
in the library. Distilled into
[FINDINGS-2026-09-27.md](FINDINGS-2026-09-27.md). Fed [ADR-0004](../adr/0004-delegate-to-target-existing-tools.md)
(lenses delegate to the target's own property-based and mutation
tooling), the edge-case/negative-case Vocabulary block in
[ARCHITECTURE.md](../ARCHITECTURE.md), and the property-based and
mutation items on the roadmap.


### Contract testing and machine-checkable oracles (2026-09-26)

Distilled into
[CONTRACT-RESEARCH.md](CONTRACT-RESEARCH.md). Feeds a decision on
whether the unbuilt `contract` index row ships, and if so what it owns:
JSON Schema 2020-12 vocabularies (an unenforced schema is a false
negative), Avro and protobuf compatibility rules (contract drift is a
decode change, not a 4xx), and the RFC 9110 and RFC 9457 text for what a
rejected request can be asserted to return. Read from the specs directly
after two research agents reported findings that contradicted them; the
method note at the end of the file records that.

### Negative testing for A01:2025 Broken Access Control (2026-09-26)

Findings: [`negative-testing-a01-broken-access-control.md`](negative-testing-a01-broken-access-control.md).
Primary-source pass (OWASP Top 10 2025/2021, WSTG ATHZ/APIT, cheat
sheets, RFC 9110, CWE, ZAP) on how access control is tested by requests
that should be denied: baseline-diff oracle (WSTG-ATHZ-02), RFC 9110
existence neutrality (404/403), IDOR/BOLA, BOPLA, header/IP route
bypasses, and unscoped collection leaks. Applied to
[`lens-ownership.md`](../lens/lens-ownership.md),
[`skills/sstack-ownership/SKILL.md`](../../skills/sstack-ownership/SKILL.md),
and [`agents/sstack-ownership-attacker.md`](../../agents/sstack-ownership-attacker.md).

### Negative testing for Resource Exhaustion (2026-09-26)

Primary-source pass (OWASP API4:2023, CWE-400/770/789/1333/409, RFC
6585/9110, Michael Nygard) on negative testing for resource exhaustion:
early admission gates (413/429), fast load shedding (503), unbounded
query memory ceilings, connection/thread pool exhaustion, and
post-pressure self-healing. Applied to
[`lens-resource-exhaustion.md`](../lens/lens-resource-exhaustion.md),
[`docs/LENS.md`](../LENS.md),
[`skills/sstack-resource-exhaustion/SKILL.md`](../../skills/sstack-resource-exhaustion/SKILL.md),
and [`agents/sstack-resource-exhaustion-attacker.md`](../../agents/sstack-resource-exhaustion-attacker.md).

### Evaluation of remaining taxonomy lenses (2026-09-27)

Primary-source pass evaluating unbuilt taxonomy rows:
- **Ordering:** [`ORDERING-RESEARCH.md`](ORDERING-RESEARCH.md), applied to [`lens-ordering.md`](../lens/lens-ordering.md). RFC 9110 409 Conflict, CWE-841 workflow sequencing. Recommended.
- **Concurrency:** [`CONCURRENCY-RESEARCH.md`](CONCURRENCY-RESEARCH.md), applied to [`lens-concurrency.md`](../lens/lens-concurrency.md). RFC 7232 412 Precondition Failed, CWE-362/367 TOCTOU, SQL isolation levels. Recommended.
- **Idempotency:** [`IDEMPOTENCY-RESEARCH.md`](IDEMPOTENCY-RESEARCH.md), applied to [`lens-idempotency.md`](../lens/lens-idempotency.md). RFC 9110 §9.2.2, IETF `Idempotency-Key` draft, duplicate replay invariant. Recommended.
- **Dependency-Failure:** [`DEPENDENCY-FAILURE-RESEARCH.md`](DEPENDENCY-FAILURE-RESEARCH.md), applied to [`lens-dependency-failure.md`](../lens/lens-dependency-failure.md). RFC 9110 502/503/504 gateway semantics, Michael Nygard circuit breakers. Recommended.
- **Mutation:** [`MUTATION-RESEARCH.md`](MUTATION-RESEARCH.md). DeMillo et al. (1978). Category analysis: Evidence verification runner, not an attacker lens. Not recommended as a lens.
- **Agent:** [`AGENT-RESEARCH.md`](AGENT-RESEARCH.md), applied to [`lens-agent.md`](../lens/lens-agent.md). OWASP LLM Top 10 (2025), Anthropic MCP tool schemas, context eviction invariants. Recommended.
- **Security:** [`SECURITY-RESEARCH.md`](SECURITY-RESEARCH.md), applied to [`lens-security.md`](../lens/lens-security.md). OWASP A03 Injection (SQLi, Command Injection, Path Traversal, SSTI) and A08 Integrity. Access control carved out to `ownership`. Recommended.

## Relevant to open roadmap work

### Agent harness evaluations (2026-07-13 to 2026-08-12)

Source: `ai-harness-evaluations-best-practices-oh-my-opencode-slim-omos-raw-v3.md`.
Relevant because sstack's whole thesis is eval-gated acceptance
(ADR-0003). The scan covers custom native evaluation harnesses for AI
systems, including the point that production AI degrades silently
without one. The evidence-schema problem it describes shipped as
ADR-0006; the scan remains the reference for any future harness
work.

### Evals for agents (2026-07-21 to 2026-08-20)

Source: `evals-for-agents-raw-v3.md`. Same subject from a later
window, and it overlaps the acceptance-harness work already shipped.
Relevant to any v1 decision about how seeded-repo evals should be
structured or scored.

### Loop engineering (2026-05-28 to 2026-06-27)

Source: `loop-engineering-raw-v3.md`. Relevant to the learn-loop
roadmap item. Covers driving long autonomous agent runs to completion;
the learn loop is a smaller version of the same problem, keeping a run
prioritized by what a prior run learned.

## Background, no action yet

### Rolling out AI into the software lifecycle (2026-06-14 to 2026-07-14)

Source: `rolling-out-ai-into-the-software-development-lifecycle-raw.md`.
General SDLC framing. No specific roadmap item depends on it; kept for
context if the project scope widens beyond testing.

## Adding to this index

When a scan changes a decision, distill it the way `FINDINGS-2026-09-27.md`
and link it from here. Do not paste raw transcripts into this repo.
The library is the archive; this file is the map.
