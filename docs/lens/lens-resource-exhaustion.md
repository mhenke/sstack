# Negative Testing: Resource Exhaustion Lens

Research on negative testing for resource limits, volumetric attacks, memory leaks, rate limiting, connection pool exhaustion, and degradation under resource pressure.

## Overview & Definition

Negative testing for resource exhaustion examines how an application or service behaves under extreme load, volumetric spikes, recursive consumption, or hostile input designed to deplete memory, CPU, disk, file descriptors, thread pools, or network buffers.

The goal is to prove that the system applies defensive ceilings, early admission gates, fast load-shedding, and backpressure rather than crashing through Out-Of-Memory (OOM) kills, thread starvation, unhandled exceptions, or cascading Denial of Service (DoS). When pressure subsides, the system must self-heal immediately with zero residual resource leakage.

## Core Concepts & Failure Modes

1. **Memory & Allocation Exhaustion (CWE-770, CWE-789):**
   - Unbounded in-memory buffering (e.g., buffering multi-gigabyte uploads or large files into memory instead of streaming or chunking).
   - Unbounded queries or collections (e.g., `SELECT *` loading millions of rows into heap without pagination limits).
   - Uncapped in-memory caches, dictionaries, or queues growing indefinitely without TTL or LRU eviction policies.
   - Decompression bombs / zip bombs (CWE-409) and entity expansion (Billion Laughs) where small payloads expand into gigabytes.
2. **Rate Limiting & Request Floods (RFC 6585):**
   - Exceeding request rate per second/minute from a single IP, API token, or tenant partition.
   - Burst attacks testing token-bucket or sliding-window boundary conditions.
   - Sustained overload: testing behavior when traffic exceeds capacity for extended durations.
3. **Thread, Worker & Concurrency Starvation (CWE-400, CWE-834):**
   - Thread pool exhaustion: unbounded worker spawning or requests filling fixed thread pools without rejection policies.
   - Unbounded task queues: task queues accepting infinite jobs and swelling heap until `OutOfMemoryError` occurs.
   - Event-loop starvation: synchronous CPU-heavy work or runaway microtasks blocking the single-threaded event loop (Node.js, Python asyncio).
4. **Connection Pool & Handle Leaks (CWE-775, CWE-404):**
   - Exhausting available database or downstream HTTP connections by failing to return connections under error or timeout paths.
   - Exhausting OS file descriptors (`EMFILE` / `ENFILE`) by failing to close open files, sockets in lingering states (`TIME_WAIT`), or child processes.
5. **CPU Exhaustion & Algorithmic Complexity Attacks (CWE-1333, CWE-407):**
   - Regular expression denial of service (ReDoS) via catastrophic backtracking on crafted inputs.
   - HashDoS: malicious payloads exploiting hash collision vulnerabilities to degrade hash map lookups from $O(1)$ to $O(N^2)$.
   - Deeply nested structures causing stack overflow (deep JSON/XML nesting, recursive queries, AST traversal).

## Real-World Examples & Test Scenarios

### Scenario 1: Rate Limit Threshold & Throttling
- **Contract:** Maximum 100 requests per minute per API client.
- **Negative Action:** Client issues 150 requests in 5 seconds.
- **Expected Oracle:** First 100 requests succeed; requests 101-150 receive HTTP 429 Too Many Requests with `Retry-After: 55` header. Other clients and tenant partitions continue to be served without latency degradation.

### Scenario 2: Payload Size Ceiling (Payload Too Large)
- **Contract:** Gateway/endpoint accepts max 5MB request body.
- **Negative Action:** Client sends a 50MB request or streams indefinitely without terminating.
- **Expected Oracle:** Connection rejected immediately with HTTP 413 Content Too Large at the gateway/middleware before allocating worker buffer memory; connection closed cleanly without downstream worker crash.

### Scenario 3: Recursive Depth & Stack Limitation
- **Contract:** Parser traverses nested syntax or JSON tree with a maximum recursion depth limit of 100 levels.
- **Negative Action:** Input payload has 5,000 levels of nested arrays `[[[[...]]]]`.
- **Expected Oracle:** Parser rejects with structured domain error (`DepthLimitExceededException` or HTTP 400 Bad Request) rather than crashing the runtime with unhandled `RecursionError` or process-level stack overflow.

### Scenario 4: Connection Pool Exhaustion & Fast Rejection
- **Contract:** Database connection pool capped at 10 connections with a 2.0s acquisition timeout.
- **Negative Action:** 15 concurrent requests arrive; first 10 hold connections for 3.0s.
- **Expected Oracle:** Requests 11–15 wait up to 2.0s, then fail fast with HTTP 503 Service Unavailable (`ConnectionPoolExhaustedException`) instead of hanging indefinitely. When the first 10 finish, subsequent requests immediately acquire connections successfully (no leaked handles).

### Scenario 5: Unbounded Query & Memory Allocation Ceiling
- **Contract:** Endpoint `/records/export` exports user transaction records; maximum result window capped at 50,000 rows.
- **Negative Action:** Client requests export for 2,000,000 records without date filtering or pagination.
- **Expected Oracle:** Endpoint rejects with HTTP 400 Bad Request ("Result set exceeds export limit: please narrow date range") or enforces cursor streaming; memory footprint stays bounded; runtime process avoids OS OOM kill (`SIGKILL`).

## Key Oracle Patterns

- **Early Gate Enforcement (HTTP 413 / 429):** Volumetric and payload violations are intercepted at edge or middleware before consuming core application memory or compute.
- **Strict Bounded Execution Time & Space:** Loops, recursions, buffer allocations, and query sizes are constrained with explicit maximum counts and depth limits.
- **Fast Load-Shedding Over Indefinite Queueing:** When worker pools or queues saturate, incoming excess requests fail fast (HTTP 503 / `RejectedExecutionException`) rather than queueing unboundedly into OOM or hanging callers.
- **Post-Pressure Self-Healing (Zero Residual Leak):** Once overload traffic ceases, connections return to the pool, buffers are garbage collected, and normal traffic immediately succeeds without process restart.
- **Bulkheading & Isolation:** Exhaustion within one pool, tenant, or external dependency is isolated and cannot starve unrelated endpoints or tenants.

## Primary Sources & References

- OWASP API Security Top 10: API4:2023 – Unrestricted Resource Consumption
- CWE-400: Uncontrolled Resource Consumption
- CWE-770: Allocation of Resources Without Limits or Throttling
- CWE-789: Memory Allocation with Excessive Size Value
- CWE-1333: Inefficient Regular Expression Complexity (ReDoS)
- CWE-409: Improper Handling of Highly Compressed Data (Data Amplification)
- RFC 6585: Additional HTTP Status Codes (429 Too Many Requests)
- RFC 9110: HTTP Semantics (413 Content Too Large, 503 Service Unavailable, Retry-After header)
- Michael Nygard, *Release It! Design and Deploy Production-Ready Software* (Bulkhead, Resource Pools, Capacity)
