---
name: sstack-ordering
description: "Ordering lens rubric. Case-generation heuristics, oracle patterns, and worked examples for out-of-order execution, multi-step workflow bypasses, step-skipping, and inverted pipeline calls. Loaded inline under ### Lens rubric."
disable-model-invocation: true
---

# Ordering lens

Attacks every mapped surface through the ordering lens: that an
operation requiring prerequisite steps or phases cannot be executed
out of sequence, skipped, or inverted. While other lenses attack
payloads or single-object states, this lens attacks sequence
dependencies across multi-step workflows.

## Case-generation heuristics

- Step skipping in multi-stage workflows: in a process requiring
  steps $A \to B \to C$ (e.g. configure $\to$ validate $\to$ commit),
  call step $C$ directly, skipping $A$ and $B$, or skip intermediate step $B$.
- Inverted protocol calls: invoke dependent finalization operations
  before initialization (e.g. `process()` before `setup()`, or `close()`
  before `open()`).
- Unverified transition jumping: in workflows with verification gates
  (e.g. register $\to$ verify token $\to$ activate), call the terminal
  action with unverified or unsubmitted tokens.
- Out-of-sequence asynchronous event arrival: submit update or delete
  event payloads before creation events to verify reordering buffers or
  explicit sequencing rejection.
- Savepoint and transaction release inversion: release or roll back
  nested transaction savepoints in reverse or arbitrary sequence.

## Oracle patterns

- Unmet prerequisites produce explicit sequencing errors (e.g. HTTP
  409 Conflict, 428 Precondition Required, or domain `IllegalOrderException`),
  naming the missing prerequisite stage.
- Out-of-order calls trigger zero state mutations, zero database writes,
  and zero external side-effects.
- Pipeline stages fail fast with explicit diagnostic boundaries rather
  than proceeding with uninitialized, null, or corrupted data.
- Workflow tokens enforce monotonic sequence progression; jumping
  phases is strictly blocked.

Worked example — Python `InvoiceBuilder` requiring `set_customer(id)`
before `calculate_tax()`: case call `calculate_tax()` without prior
`set_customer()`, oracle raises `PreconditionRequiredError("customer required before tax calculation")`,
observed (bug) evaluates tax with default 0% rate and creates an unbilled invoice.

TypeScript `CheckoutSession` requiring `submitShippingAddress()` before
`confirmOrder()`: case call `confirmOrder()` directly after cart creation,
oracle rejects with `409 Conflict ("shipping address required before confirmation")`,
observed (bug) generates order record with null shipping identifier.

## Failure modes to watch for

- User-controlled execution sequence (CWE-841): allowing users to bypass
  mandatory intermediate authorization, payment, or validation steps.
- Incorrect behavior order (CWE-696): performing actions in an order that
  violates domain or protocol invariants.
- Premature finalization: executing completion logic while dependent
  asynchronous jobs or reservations remain in unverified states.
- Out-of-order message ingestion: consumer processing updates prior to
  initial creation events, leading to orphaned or corrupted records.

## Language notes

### JavaScript / TypeScript

- Promise chaining: omitting `await` or unhandled promise rejections can
  allow step 2 to execute concurrently with or before step 1 completes.
- Express/Koa middleware ordering: placing authorization or parser
  middleware after route handlers executes unauthenticated or unparsed requests.

### Python

- Context managers (`__enter__` / `__exit__`): invoking inner worker
  methods outside the manager block accesses uninitialized resources.
- Generator pipelines: calling `next()` or pumping pipelines out of order
  produces silent exhaustion or stale yields.

### Java

- Builder pattern validation: builders must validate mandatory fields
  at `build()` time or enforce stepped builder interfaces (step builders).
- Spring StateMachine / Flow: unconfigured transitions throw
  unhandled exceptions unless guarded by explicit transition listeners.

### C++

- RAII and object lifetime: accessing handles before construction
  completes or after destruction causes undefined behavior.
- Memory fences and instruction reordering: compiler or CPU reordering
  reads/writes across non-atomic boundaries.

## When not to apply

The surface is an isolated, independent scalar function with no
workflow dependencies, no prerequisite steps, and no multi-stage
lifecycle context.

## Interaction with other lenses

`ordering` owns workflow-level sequence progression and multi-step
pipeline invariants. Single-entity FSM transitions (e.g. paying for an
already cancelled order) belong to `state`. Parallel access collisions
belong to `concurrency`.
