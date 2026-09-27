# sstack lenses

A lens is a failure class the pack attacks. The oracle — expected
behavior under the adverse condition — is written before the attack
runs. The fourteen shipped lenses, in lens-index order:

## boundaries

Edge cases: numbers, sizes, indexes, slices, collections, pagination,
loops. Out-of-range inputs must fail with explicit diagnostics, never
silent truncation or crashes. Detail: [lens-boundaries.md](lens/lens-boundaries.md).

## malformed

Strings parsed from outside: JSON, encodings, dynamic types,
structural mismatches, delimiter hazards. Malformed payloads are
rejected at the boundary — no unhandled parser exceptions, no leaked
stack traces. Detail: [lens-malformed.md](lens/lens-malformed.md).

## missing

Optional fields, records from external data, null/None/undefined,
falsy traps, and PATCH omission. Absent requirements produce explicit,
actionable errors — not raw `KeyError`/`NullPointerException`/`TypeError`
or silent partial data. Detail: [lens-missing.md](lens/lens-missing.md).

## ownership

A subject, an object, an action, and the context that joins them.
BOLA/IDOR, BOPLA, privilege escalation, collection leaks, cross-tenant
leakage; deny by default, object-level verification on every operation.
Detail: [lens-ownership.md](lens/lens-ownership.md).

## exceptional-conditions

Fail-open security bypasses, diagnostic leakage, dropped connections,
downstream timeouts, deadlocks. Software fails safe, preserves data
consistency, releases held resources, and sanitizes diagnostics. Detail:
[lens-exceptional-conditions.md](lens/lens-exceptional-conditions.md).

## resource-exhaustion

Connection pools, thread pools, rate limits, memory ceilings, payload limits, unbounded queries.
The system applies early gates, fast load shedding, and defensive ceilings rather than
crashing through OOM, starvation, or DoS, and self-heals with zero leaked resources. Detail:
[lens-resource-exhaustion.md](lens/lens-resource-exhaustion.md).

## state

Objects with lifetime: cached/derived reads, mutable input written
through, partial update after failure, internal references escaped.
Illegal transitions rejected, concurrency serialized, no double-spend.
Detail: [lens-state.md](lens/lens-state.md).

## ordering

Multi-step workflows, pipeline execution sequences, and prerequisite
gates. Step-skipping, inverted calls, and unfulfilled preconditions
must fail with explicit diagnostics (e.g. 409 Conflict, 428 Precondition
Required), never partial mutations or silent defaults. Detail:
[lens-ordering.md](lens/lens-ordering.md).

## concurrency

Race conditions, parallel access, double-spend, lost updates. Operations
must serialize concurrent mutations, prevent double-spending or over-allocation,
and reject stale conditional updates with explicit diagnostics (e.g. 412
Precondition Failed, 409 Conflict). Detail: [lens-concurrency.md](lens/lens-concurrency.md).

## idempotency

Retried mutations, duplicate submissions, Idempotency-Key divergence.
Replaying an operation produces the same server-side state as a single
invocation; key reuse with altered payloads must be rejected with explicit
diagnostics (e.g. 422, 409). Detail: [lens-idempotency.md](lens/lens-idempotency.md).

## dependency-failure

Upstream and third-party systems that time out, return 5xx, drop packets, or
vanish. Every outbound call is bounded by explicit timeouts; remote errors
translate to gateway semantics (e.g. 502, 504) rather than raw exceptions or
unbounded retries; bulkheads and circuit breakers stop one failing dependency
cascading into total outage. Detail:
[lens-dependency-failure.md](lens/lens-dependency-failure.md).

## contract

API contract violations, schema drift, undeclared fields, and breaking
type mutations. Runtime outputs strictly conform to declared interface
specifications; extra or undeclared properties are rejected or stripped;
breaking changes are caught at build and validation boundaries. Detail:
[lens-contract.md](lens/lens-contract.md).

## agent

AI agent orchestrators, Model Context Protocol (MCP) dispatchers, and tool-calling
runtimes. Model-generated tool arguments are strictly validated against schemas
before execution; external tool execution failures format as structured error results
without crashing the loop; untrusted tool outputs are isolated from prompt injection;
and system prompt constraints are preserved across context window compaction. Detail:
[lens-agent.md](lens/lens-agent.md).

## security

Interpreter and execution boundary confusion: SQL injection, OS command
injection, path traversal, cryptographic token tampering (JWT alg: none),
and insecure deserialization. Inputs to interpreters are strictly parameterized;
filesystem access is confined to designated sandboxes; authentication tokens
require valid cryptographic signatures. Detail:
[lens-security.md](lens/lens-security.md).

---

Shipped rubrics live in `skills/sstack-<name>/SKILL.md`; attacker
agents in `agents/sstack-<name>-attacker.md`. Users add lenses by
dropping a `sstack-`-prefixed file into their own tree — see
[CUSTOMIZING.md](CUSTOMIZING.md).
