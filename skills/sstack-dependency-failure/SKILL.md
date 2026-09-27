---
name: sstack-dependency-failure
description: "Dependency failure lens rubric. Case-generation heuristics, oracle patterns, and worked examples for upstream timeouts, network partitions, circuit breakers, 5xx propagation, and graceful degradation. Loaded inline under ### Lens rubric."
disable-model-invocation: true
---

# Dependency failure lens

Attacks every mapped surface through the dependency failure lens: that
outbound calls to downstream or upstream services, third-party APIs,
databases, or network endpoints must bound execution time with strict
timeouts, translate transport and remote errors into standard status
codes or domain exceptions, fail fast via circuit breakers under
sustained outages, and degrade gracefully on non-critical features.

## Case-generation heuristics

- Upstream timeout / tarpit: target invokes an external service that
  delays responding beyond the agreed SLA (e.g. mock server delays
  10,000ms on a 2000ms SLA).
- Hard network partition / socket disconnect: target invokes an external
  service that drops connections, refuses TCP handshakes (`ECONNREFUSED`),
  or resets connections (`ECONNRESET`).
- Upstream HTTP 5xx / gateway errors: mock returns 500 Internal Server
  Error, 502 Bad Gateway, 503 Service Unavailable, or 504 Gateway
  Timeout.
- Unchecked schema deviations: mock returns an unexpected payload or
  content-type on error (e.g. an HTML `502 Bad Gateway` error page when
  the client expects JSON).
- Circuit breaker tripping: trigger repeated consecutive upstream failures
  to verify transition to `OPEN` state, ensuring subsequent calls fail
  fast without attempting outbound network I/O.
- Graceful degradation: simulate failure of an auxiliary dependency
  (e.g. recommendations, telemetry, avatars) during a primary critical
  path (e.g. checkout, login) to verify non-fatal fallback.

## Oracle patterns

- Strict timeout enforcement: target terminates outbound calls and returns
  control within SLA ($T \le T_{timeout} + \epsilon$).
- Sanitized error translation: raw transport exceptions (e.g. socket
  timeouts, connection refused) are caught at client boundaries and
  translated to standard RFC 9110 codes (502, 504) or typed domain
  exceptions, never leaking raw stack traces.
- Rapid fail-fast under open circuits: subsequent calls during sustained
  outages return immediately (e.g. $\le 5$ms) without blocking threads.
- Safe fallbacks on non-essential features: auxiliary failures return
  HTTP 200 with default/empty payloads rather than failing the parent
  request.

Worked example — Python `ShippingRateClient` calling third-party parcel
carrier API `https://carrier.example.org/rates`: case upstream mock
delays response past 2000ms SLA, oracle aborts connection and raises
`GatewayTimeoutError("carrier rate lookup timed out")`, observed (bug)
blocks caller indefinitely until default socket timeout, exhausting
worker threads.

TypeScript `UserProfileService` fetching user info and calling external
`RecommendationService`: case recommendation service returns HTTP 503
Service Unavailable, oracle returns user profile with empty
`recommendations: []` and HTTP 200, observed (bug) throws unhandled
AxiosError 503 crashing entire profile request.

## Failure modes to watch for

- Unbounded network I/O & missing timeouts (CWE-400): clients created
  without connect/read timeouts, causing thread pool exhaustion.
- Raw exception leakage (CWE-209): unhandled transport exceptions
  bubbling up to client responses.
- Cascading failure: bombarding a failing dependency without backoff or
  circuit breakers.
- Fragile error parsing: crashing on HTML error pages returned during
  upstream outages.
- Hard coupling to non-critical systems: failure of auxiliary services
  taking down core workflows.

## Language notes

### Python

- `requests`, `httpx`, and `urllib` default to no timeout (`timeout=None`),
  blocking indefinitely; wrap calls with explicit timeout tuples and catch
  `requests.RequestException` at boundary layers.
- Async I/O: unshielded `asyncio.wait_for` tasks can leave dangling
  background coroutines if cancellation is not handled cleanly.

### JavaScript / TypeScript

- `fetch()` does not time out by default; requires `AbortSignal.timeout(ms)`
  or an `AbortController`.
- Unhandled promise rejections on network disconnect terminate Node.js
  processes; ensure outbound calls are awaited in try/catch or have `.catch()`.

### Java

- Configure both `ConnectTimeout` and `ReadTimeout` on `HttpClient` /
  `HttpURLConnection`.
- Use resilience libraries (Resilience4j) for circuit breaking, retries,
  and rate limiters; avoid unbounded retry loops that flood downstreams.

### C++

- Libcurl: explicitly set `CURLOPT_CONNECTTIMEOUT_MS` and `CURLOPT_TIMEOUT_MS`.
- RAII socket cleanup: verify socket file descriptors close cleanly on
  timeout or disconnect to prevent descriptor leaks.

## When not to apply

The surface is an isolated in-memory function, pure algorithm, or local
data transformation that makes no network, RPC, filesystem, or external
service calls.
