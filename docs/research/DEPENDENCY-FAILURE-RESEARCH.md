# Dependency-failure lens: what a `dependency-failure` lens would own

Every claim below was read from the primary source named beside it. Where a
source does not say something, this file says so rather than filling the gap.
Research date: 2026-09-27. Linked from [`RESEARCH.md`](RESEARCH.md).

The `dependency-failure` row in the lens index reads "upstream timeout, partial
response, unavailable service" and is unbuilt. This note exists to decide
whether shipping it would duplicate `exceptional-conditions` (which owns local
crashes, unhandled exceptions, and diagnostic leaks) and how an automated agent
can mock or inject faults into external dependencies safely.

## The overlap, settled
 
In shipped v0, `exceptional-conditions` (Behavior category) owns the
target's error-path behavior across all failures: verifying fail-safe
invariants, exception sanitization, resource release, and graceful
fallback when dependencies fail or time out.

The unbuilt `dependency-failure` lens (Environment category) is designed
to specialize in the external network perimeter—injecting wire-level
faults (synthetic tarpits, truncated HTTP streams, proxy drops):

| Case | Shipped owner | Notes |
|---|---|---|
| Unhandled exception / division by zero | `exceptional-conditions` | Local code path crash |
| Leaked stack trace in 500 body | `exceptional-conditions` | Diagnostic leakage (CWE-209) |
| Dropped TCP connection / socket hang | `exceptional-conditions` | Transport abort & resource cleanup |
| Fail-safe auth on policy service outage | `exceptional-conditions` | Security invariant (fail closed; CWE-636) |
| Upstream gateway timeout (504 Gateway Timeout) | `exceptional-conditions` (v0) / `dependency-failure` (future) | Upstream service latency/hang |
| Upstream invalid response (502 Bad Gateway) | `exceptional-conditions` (v0) / `dependency-failure` (future) | Upstream service crash/proxy error |
| Degraded fallback / Circuit breaker trip | `exceptional-conditions` (v0) / `dependency-failure` (future) | System resilience under partial outage |
| Connection pool exhaustion from slow upstream | `resource-exhaustion` | Resource leakage symptom |

A system resilient to dependency failure bounds all external I/O with strict
timeouts, catches socket exceptions at the client wrapper boundary, translates
upstream errors into RFC 9110 status codes (502/504), and provides degraded
fallbacks rather than triggering cascading failures across the architecture.

## What standards and specifications prove

### RFC 9110: Gateway and Proxy Error Semantics

RFC 9110 §15.6 specifies the exact semantics for dependency failures:

- **502 Bad Gateway (§15.6.3):**
  > "The 502 (Bad Gateway) status code indicates that the server, while acting
  > as a gateway or proxy, received an invalid response from an inbound server
  > it accessed while attempting to fulfill the request."
  Used when an upstream third-party returns an unparseable response, HTTP 500,
  or drops the connection prematurely.

- **503 Service Unavailable (§15.6.4):**
  > "The 503 (Service Unavailable) status code indicates that the server is
  > currently unable to handle the request due to a temporary overload or
  > scheduled maintenance, which will likely be alleviated after some delay."
  Used when circuit breakers open to shed load and protect downstream dependencies.

- **504 Gateway Timeout (§15.6.5):**
  > "The 504 (Gateway Timeout) status code indicates that the server, while
  > acting as a gateway or proxy, did not receive a timely response from an
  > upstream server it needed to access in order to complete the request."
  Used when an external HTTP call, database query, or remote RPC exceeds its
  configured timeout budget.

### Michael Nygard (*Release It!*) & Fault Tolerance Patterns

Michael Nygard's foundational work *Release It!* (2nd ed., Pragmatic Bookshelf):
1. **Timeouts:** Every network I/O call without an explicit timeout is a bug.
   Default socket timeouts in many runtimes are infinite (or 300+ seconds),
   causing thread exhaustion when an external dependency hangs.
2. **Circuit Breaker:** When consecutive upstream failures cross a threshold,
   the circuit transitions to Open, failing immediately without making network
   calls, preventing cascading resource starvation.
3. **Bulkheads:** Isolating resource pools (e.g., separate HTTP connection pools
   per external dependency) so that an outage in a non-critical analytics service
   cannot starve critical checkout paths.

## The observable oracle, checked at the source

Under negative dependency attacks:

1. **Deterministic Bounded Latency:** When an upstream dependency hangs, the
   target MUST abort the call within its configured SLA (e.g. $\le 2000$ms) and
   return HTTP 504 Gateway Timeout. It must never block the client indefinitely.
2. **Standard Gateway Error Codes:** When an upstream returns corrupted data,
   404, or 500, the target maps this to HTTP 502 Bad Gateway or 503 Service
   Unavailable, never propagating raw unhandled client exceptions
   (`requests.exceptions.ReadTimeout`, `ECONNREFUSED`, `SocketTimeoutException`).
3. **Graceful Fallback / Safe Degradation:** For optional dependencies (e.g.,
   recommendation engine, avatar service), failure returns HTTP 200 with fallback
   defaults (e.g., empty recommendation list, placeholder avatar) without
   aborting the primary transaction.

## What the lens should own

1. **Timeout Injection:** Simulating an upstream service that accepts the TCP
   handshake but never sends bytes (Blackhole / Tarpit).
2. **Malformed Upstream Responses:** Returning truncated JSON, invalid HTML, or
   unexpected schemas from mocked third-party endpoints.
3. **HTTP 5xx Upstream Faults:** Simulating upstream 500, 502, and 503 responses
   to verify error handling and retry bounds.
4. **Circuit Breaker Verification:** Verifying that repeated upstream failures
   open the circuit and fast-fail subsequent calls.

## Recommendation: Proceed with standalone lens

**Verdict: Recommended.**
Modern software is heavily coupled to third-party APIs (Stripe, Twilio, OAuth,
AWS). Upstream outages and network partitions are inevitable. The failure modes
(cascading hangs, unhandled socket exceptions, missing circuit breakers) cannot
be evaluated without simulated external faults.

## Open questions

- Fault Injection Mechanism: In unit/integration tests, injecting dependency
  failures requires intercepting HTTP clients (e.g., using `responses`, `nock`,
  `wiremock`, or environment variable endpoint overrides).
