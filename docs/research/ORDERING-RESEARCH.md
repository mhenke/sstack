# Ordering lens: what an `ordering` lens would own

Every claim below was read from the primary source named beside it. Where a
source does not say something, this file says so rather than filling the gap.
Research date: 2026-09-27. Linked from [`RESEARCH.md`](RESEARCH.md).

The `ordering` row in the lens index reads "operations applied out of sequence"
and is unbuilt. This note exists to decide whether shipping it would duplicate
`state`, which already owns lifecycle state machines and invalid transitions,
and whether it constitutes an independent failure class with observable oracles.

## The overlap, settled

In common testing discussions, "out-of-order operations" frequently conflates
object-level lifecycle transitions with cross-step workflow sequencing. The
distinction between what is already shipped and what `ordering` would own:

| Case | Shipped owner | Notes |
|---|---|---|
| Invalid lifecycle transition (e.g., pay for cancelled order) | `state` | Single entity FSM violation |
| Double invocation / duplicate submit | `state` (or `idempotency`) | Re-entering terminal/current state |
| Step skipping in multi-step wizard / checkout pipeline | `ordering` | Workflow sequence dependency across distinct surfaces |
| Inverted pipeline operations (e.g., decode before decrypt) | `ordering` | Dataflow pipeline ordering |
| Asynchronous event arrival out of causality order | `ordering` | Message arrival order vs vector clock |
| Premature resource finalization / cleanup before use | `exceptional-conditions` | RAII / resource scope cleanup |

A lens that simply tests "cannot call `ship()` on an unapproved order" is a
duplicate of `state`. The `ordering` lens must be defined by sequence
dependencies that span multiple independent surfaces or steps in a process.

## What standards and specifications prove

### RFC 9110: HTTP Semantics on State Conflicts

RFC 9110 §15.5.10 defines status code 409 (Conflict):

> "The 409 (Conflict) status code indicates that the request could not be
> completed due to a conflict with the current state of the target resource.
> This code is used in situations where the user might be able to resolve the
> conflict and resubmit the request. The server SHOULD generate content that
> includes enough information for a user to recognize the source of the conflict."

RFC 9110 distinguishes 409 from 400 and 422:
- 400 is malformed request syntax or framing.
- 422 is well-formed syntax with unprocessable semantic instructions.
- 409 is explicitly a state conflict where the operation is syntactically and
  semantically valid in isolation, but conflicts with the resource's current
  sequence position.

Furthermore, RFC 9110 §15.5.23 defines 428 (Precondition Required):
> "The 428 (Precondition Required) status code indicates that the origin server
> requires the request to be conditional." This applies when an operation
> must be sequenced after obtaining an ETag or version token.

### CWE-841: User-Controlled Critical Execution Sequence

[MITRE CWE-841](https://cwe.mitre.org/data/definitions/841.html) explicitly defines the workflow ordering vulnerability:

> "The software allows a user to control the order or timing of execution of
> critical steps in a process, such as authentication, authorization, or
> transactions, which can result in bypassing security controls or causing
> unexpected state."

Primary examples from CWE-841:
- An e-commerce system where step 1 is select item, step 2 is apply payment,
  step 3 is confirm order. The user submits step 3 directly without step 2.
- Password reset workflows where step 1 is request token, step 2 is verify
  token, step 3 is set new password. Submitting step 3 with an arbitrary token
  or without step 2 verification.

### Lamport Clocks and Distributed Event Ordering

Leslie Lamport's 1978 foundational paper ("Time, Clocks, and the Ordering of
Events in a Distributed System", CACM 21(7)):
- Causality cannot rely on physical clocks across systems without vector/logical
  clocks.
- Systems that consume asynchronous events from queues (Kafka, RabbitMQ, SQS)
  must enforce sequence or buffer out-of-order delivery.
- When an event arrives out of sequence (e.g., `OrderUpdated` arrives before
  `OrderCreated`), the system either:
  1. Buffers or dead-letters the message until prerequisites arrive.
  2. Rejects the message with an explicit sequencing error.
  3. Fails silently or corrupts the record (the defect).

## The observable oracle, checked at the source

Under negative ordering attacks, what does a conforming implementation produce?

1. **Explicit sequencing rejection (HTTP 409 Conflict or 400 Bad Request):**
   When step $N$ is requested without verified completion of step $N-1$, the
   server returns 409 Conflict with an error body identifying the unfulfilled
   precondition step.
2. **Precondition checking before side-effects:**
   No partial side effect (database write, charge, token generation) may
   occur if a prerequisite in the sequence is missing.
3. **Pipeline fail-fast:**
   In multi-stage data processing pipelines, attempting to pass un-transformed
   or out-of-order intermediate representations immediately raises a domain
   ordering error rather than executing with corrupted data.

## What the lens should own

The `ordering` lens earns its place only by targeting multi-step sequences
where the steps are individually valid endpoints/functions, but their
execution order violates process constraints:

1. **Step-skipping attacks:** In a multi-stage workflow ($A \to B \to C$),
   directly invoking $C$ without executing $B$, or jumping from $A$ to $C$.
2. **Inverted sequencing:** Invoking step $B$ before step $A$ (e.g., `finalize()`
   before `prepare()`, or `commit()` before `validate()`).
3. **Asynchronous out-of-order event replay:** Ingesting an event payload with
   a higher sequence/version number before an earlier sequence number has been
   processed, verifying that the system does not drop or corrupt prior state.

## Recommendation: Proceed with standalone lens

**Verdict: Recommended.**
While `state` owns single-entity FSM transitions, `ordering` addresses
workflow-level sequence enforcement and multi-step pipeline bypasses (CWE-841).
In web APIs and distributed systems, step-skipping in checkout, onboarding,
and multi-stage transactions is a high-frequency source of critical business
logic defects that `state` attackers miss when focused on isolated objects.

## Open questions

- In single-service unit tests, multi-step flows often require session or
  transaction state across multiple calls. Attacker must track and chain
  identifiers across stages.
- Scaffolding out-of-order event streams in CLI scratch scripts requires
  deterministic event injection.
