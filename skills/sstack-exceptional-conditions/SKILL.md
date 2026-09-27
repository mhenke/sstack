---
name: sstack-exceptional-conditions
description: "Exceptional-conditions lens rubric. Fail-open paths, diagnostic leakage, cascading failures, empty catch blocks, and fail-safe oracles. Loaded inline under ### Lens rubric."
disable-model-invocation: true
---

# Exceptional-conditions lens

Attacks what the system does when something fails. `malformed`
triggers the error; this lens tests the error handler. The trigger
may be bad input, a dying dependency, a timeout, or an exhausted
resource — the verdict concerns only the failure path.

## Case-generation heuristics

- Drop a dependency or inject a timeout mid-request, then check
  whether access is denied (fail-safe) or granted (fail-open).
- Search for empty or overly generic catch blocks
  (`catch (Exception e) { }`) that swallow errors silently.
- Feed malformed input and inspect the error response for stack
  traces, database schema, API keys, hostnames, or internal paths.
- Break one component and watch its callers: does one timeout
  become one degraded response or a full-system outage?
- Retry a failing operation past its retry bound and check the
  terminal state.
- Throw or inject faults mid-operation to verify held resources
  (locks, sockets, file descriptors) are released via finally/cleanup.
- Trigger async error paths to ensure errors reject cleanly without
  unhandled promise rejections or thread termination crashes.

## Oracle patterns

- Fail-safe: an upstream failure denies access or degrades to a
  safe default, never grants access.
- Sanitized errors: the client sees a generic message plus a unique
  tracking ID. Details go to server-side logs only.
- No cascading failure: one component's timeout stays one degraded
  response.
- Empty catch blocks either rethrow a domain error or log with a
  tracking ID; silence is a bug.
- Clean resource release: locks released, handles closed, and
  partial side effects rolled back on failure paths.

Worked example — Python `checkout(order)` with a failing payment
service: oracle returns `PaymentUnavailable` with a tracking ID and
no charge, observed (bug) retries forever, then charges twice.
TypeScript `authorize(req)` with an unreachable policy service:
oracle throws `Error("authorization unavailable")`, observed (bug)
returns authorized.

## Failure modes to watch for

- Fail-open bypass: security check throws an exception, catches it,
  and mistakenly defaults to granting access or completing action.
- Silent swallowing: empty or overly broad catch blocks hiding
  critical operational failures without logging or re-raising.
- Diagnostic leakage: leaking raw stack traces, database queries,
  hostnames, or secrets to external callers.
- Resource & lock leakage: aborting execution without releasing
  mutexes, sockets, or file descriptors, causing deadlocks or leaks.
- Cascading collapse: missing timeouts or un-jittered retry loops
  turning a partial dependency slowdown into a full-system outage.
- Worker crash: unhandled promise rejections or thread termination
  taking down the application process on transient I/O errors.

## Language notes

### JavaScript / TypeScript

- Unhandled promise rejections terminate Node.js processes by
  default; ensure async functions reject cleanly and event emitters
  have error listeners.
- Verify `try...finally` or resource-disposal helpers release
  handles even when an `await` rejects.

### Python

- Bare `except:` catches `KeyboardInterrupt` and `SystemExit`;
  use `except Exception:` and re-raise domain exceptions.
- Verify context managers (`with`) or `finally` blocks handle
  `OSError`, `TimeoutError`, or connection loss.
- Wrap background tasks (`asyncio.create_task`) with done callbacks
  or error handlers so unhandled exceptions do not vanish or crash.

### Java

- Swallowing `InterruptedException` clears thread interruption;
  always re-interrupt the current thread or propagate.
- Unchecked exceptions trigger rollback in `@Transactional` by
  default, but checked exceptions do not without explicit config.
- Use `try`-with-resources to guarantee socket and stream closure.

### C++

- Exceptions escaping destructors cause immediate `std::terminate`.
- Enforce RAII guards (`std::lock_guard`, `std::unique_ptr`) to
  guarantee mutex release and file-descriptor closure during stack
  unwinding.

## Interaction with malformed

`malformed` supplies the trigger; this lens grades the handler.
Complementary, not overlapping. Where both apply, keep the
`exceptional-conditions` verdict.

## Unit tier

Mock the failing dependency, call the function, and assert the
raised exception is sanitized: no stack trace, no internal IP, no
raw message. Integration tier needs a live server for framework
routing bypasses and infrastructure cascades.

## When not to apply

The surface has no failure path: pure computation with no I/O, no
dependency, no error branch, and no catch block.
