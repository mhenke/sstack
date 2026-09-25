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

## Oracle patterns

- Fail-safe: an upstream failure denies access or degrades to a
  safe default, never grants access.
- Sanitized errors: the client sees a generic message plus a unique
  tracking ID. Details go to server-side logs only.
- No cascading failure: one component's timeout stays one degraded
  response.
- Empty catch blocks either rethrow a domain error or log with a
  tracking ID; silence is a bug.

Worked example — Python `checkout(order)` with a failing payment
service: oracle returns `PaymentUnavailable` with a tracking ID and
no charge, observed (bug) retries forever, then charges twice.
TypeScript `authorize(req)` with an unreachable policy service:
oracle throws `Error("authorization unavailable")`, observed (bug)
returns authorized.

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
