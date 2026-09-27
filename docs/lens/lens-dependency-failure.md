# Negative Testing: Dependency Failure Lens

Research on negative testing for upstream network partitions, third-party API outages, gateway timeouts, slow-read tarpits, circuit breakers, and graceful degradation invariants.

## Overview & Definition

Negative testing for dependency failure evaluates how applications behave when downstream or upstream external systems (third-party payment gateways, auth providers, microservices, databases, or cloud storage) slow down, return errors, drop packets, or become unavailable.

In distributed architectures, external failure is a certainty. A resilient service must bound every outbound network call with strict timeouts, prevent cascading thread pool exhaustion through bulkheads and circuit breakers, translate remote errors into well-defined RFC 9110 status codes (502 Bad Gateway, 504 Gateway Timeout), and fall back to degraded modes rather than failing completely.

## Core Concepts & Failure Modes

1. **Unbounded Network I/O & Missing Timeouts (CWE-400):**
   - HTTP/RPC client calls instantiated without connect or read timeouts.
   - Upstream services hanging (tarpit) cause threads to block indefinitely, exhausting application worker pools.
2. **Upstream 5xx Propagation & Raw Exception Leakage (CWE-209):**
   - Propagating unhandled internal socket exceptions (`requests.exceptions.ConnectTimeout`, `java.net.SocketTimeoutException`, `ECONNREFUSED`) to client responses.
   - Returning internal 500 errors instead of properly classified RFC 9110 502 (Bad Gateway) or 504 (Gateway Timeout).
3. **Cascading Failure & Missing Circuit Breakers:**
   - Continuing to bombard a failing upstream dependency with full traffic, exacerbating its outage and wasting local resources.
   - Failure to implement circuit breaker patterns (failing fast when error rates exceed thresholds).
4. **Unchecked Upstream Schema Changes & Truncated Payloads:**
   - Third-party API returning HTML error pages (`<html>502 Bad Gateway</html>`) when JSON is expected, causing unhandled JSON parse crashes deep in application logic.
5. **Absence of Graceful Degradation / Bulkheads:**
   - Failure of an auxiliary, non-critical service (e.g., product recommendations, user avatars, audit logging) causing complete failure of primary critical paths (e.g., checkout, login).

## Real-World Examples & Test Scenarios

### Scenario 1: Upstream Gateway Timeout on Payment Processor
- **Contract:** Checkout calls external payment gateway `https://payments.example.com/charge` with a 3000ms SLA.
- **Negative Inputs:**
  - Upstream payment mock accepts TCP connection but delays response by 10,000ms (tarpit simulation).
- **Expected Oracle:** The target client aborts the connection at 3000ms and returns HTTP 504 Gateway Timeout (`{"error": "payment_gateway_timeout"}`) within 3100ms. No worker threads remain blocked.

### Scenario 2: Upstream Outage with Graceful Degradation
- **Contract:** User profile endpoint `GET /api/v1/profile` aggregates user details from primary database and recommended articles from an external ML recommendation engine.
- **Negative Inputs:**
  - Recommendation engine returns HTTP 503 Service Unavailable or connection refused.
- **Expected Oracle:** User profile endpoint returns HTTP 200 with complete user details and an empty recommendations list `{"recommendations": []}`. Primary user experience remains intact.

### Scenario 3: Circuit Breaker Trip Under Sustained Upstream Outage
- **Contract:** External SMS notification provider fails 10 consecutive requests.
- **Negative Inputs:**
  - Mock SMS provider returns HTTP 500 on 10 consecutive calls. On the 11th call, incoming notification request arrives.
- **Expected Oracle:** The 11th call fails immediately in $\le 5$ms with HTTP 503 Service Unavailable without attempting network I/O to the SMS provider. The circuit is verified as `OPEN`.

### Scenario 4: Upstream Malformed Error Body (HTML on JSON Contract)
- **Contract:** Target consumes weather API `GET https://weather.example.com/data` expecting JSON.
- **Negative Inputs:**
  - Upstream Cloudflare edge proxy returns HTTP 502 with body `<html><head><title>502 Bad Gateway</title></head>...`.
- **Expected Oracle:** Target catches parse exception at boundary, logs upstream communication error, and returns clean HTTP 502 Bad Gateway to the user, never crashing with unhandled `json.decoder.JSONDecodeError`.

### Scenario 5: DNS Resolution Failure Handling
- **Contract:** Target contacts external webhook receiver.
- **Negative Inputs:**
  - Hostname resolves to `NXDOMAIN` (DNS resolution failure).
- **Expected Oracle:** Target marks webhook delivery as failed/pending retry, logging domain error without crashing the parent event listener process.

## Key Oracle Patterns

- **Strict Timeout Adherence:** Target response time is strictly bounded by configured client timeouts ($T_{target} \le T_{timeout} + \epsilon$).
- **RFC Gateway Error Classification:** Upstream timeouts map to HTTP 504; upstream malformed responses map to HTTP 502; open circuit breakers map to HTTP 503.
- **Safe Degradation on Optional Features:** Non-essential dependency failures return HTTP 200 with fallback defaults or cached values.
- **No Leaked Transport Stack Traces:** Network and socket exceptions are caught and sanitized at the client wrapper layer.

## Primary Sources & References

- RFC 9110: HTTP Semantics §15.6.3 (502 Bad Gateway), §15.6.4 (503 Service Unavailable), §15.6.5 (504 Gateway Timeout)
- Michael Nygard, *Release It!: Design and Deploy Production-Ready Software* (Circuit Breaker, Bulkheads, Timeouts)
- Martin Fowler, "CircuitBreaker" (martinfowler.com/bliki/CircuitBreaker.html)
- AWS Well-Architected Framework: Reliability Pillar (Failure Management & Degradation)
- Netflix Hystrix & Resilience4j Architectural Design Guides
