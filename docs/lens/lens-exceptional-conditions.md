# Negative Testing: Exceptional Conditions Lens

Research on negative testing for error-path behavior, exception handling, diagnostic sanitization, fail-safe invariants, and resource cleanup under adverse conditions.

## Overview & Definition

`exceptional-conditions` is a **Behavior** lens: it attacks what software does when an execution path fails. While the trigger may originate from bad input, OS faults (full disks, broken pipes), or failing external dependencies, this lens tests the **error handler and recovery contracts**.

Software must maintain data consistency, fail safe (never fail open), sanitize client diagnostics while retaining server telemetry, release held locks and resources, and avoid unhandled process crashes or cascading outages.

## Core Concepts & Failure Modes

1. **I/O & File System Faults:**
   - Disk full (`ENOSPC`) during writes, temporary file generation, or logging.
   - Permission denied (`EACCES`) when reading configuration or writing output.
   - File disappearing or being replaced mid-read (`ENOENT`); partial writes leaving corrupted artifacts on disk.
2. **Network & Connection Failures:**
   - Sudden connection reset (`ECONNRESET`) or broken pipe (`EPIPE`) during payload streaming.
   - Host unreachable, DNS resolution failure, or connection refused (`ECONNREFUSED`).
   - Truncated payloads or premature socket closure mid-stream.
3. **Timeouts & Cascading Degradation:**
   - Downstream service or database hanging indefinitely without response; missing timeouts.
   - Retry storms: unbounded retries or retries without exponential backoff and jitter, amplifying downstream brownouts into full collapses.
   - Lack of bulkheads or circuit breakers: one slow dependency exhausts worker threads and starves unrelated endpoints.
4. **Fail-Open vs Fail-Safe Security Invariants (CWE-636):**
   - Authorization or policy service unreachable: failing open (granting access) instead of failing closed/safe (denying access).
   - Authentication cache failure falling through to default permissive state.
5. **Diagnostic Leakage & Information Exposure (CWE-209 / OWASP A05):**
   - Unhandled exceptions returning raw stack traces, database schema, SQL queries, internal IPs, hostnames, or API keys in client error responses.
   - Overly broad or empty catch blocks (`catch (Exception e) {}`) swallowing errors silently without logging or domain translation.
6. **Async & Resource Lifecycle Leaks (CWE-775):**
   - Sockets, file descriptors, locks, or database connections unreleased when an exception aborts mid-function before cleanup.
   - Unhandled promise rejections or thread termination crashing worker processes on transient downstream errors.

## Real-World Examples & Test Scenarios

### Scenario 1: Downstream Timeout & Circuit Breaking
- **Contract:** Service queries external payment gateway with a 3.0s timeout limit.
- **Negative Action:** Gateway delays response for 10.0s (injected delay or hung socket).
- **Expected Oracle:** Calling service terminates connection precisely at 3.0s, logs timeout event with correlation ID, and returns HTTP 504 Gateway Timeout or graceful fallback. Calling thread is freed; worker pool does not starve.

### Scenario 2: Fail-Safe Authorization Under Outage
- **Contract:** Endpoint verifies user permissions against external policy PDP service before executing action.
- **Negative Action:** PDP service is down or returns HTTP 503 / connection refused.
- **Expected Oracle:** Endpoint denies access immediately (`403 Forbidden` or `503 Service Unavailable`), records error to internal audit log, and never falls open to authorized execution.

### Scenario 3: Disk Full During File Processing / Export
- **Contract:** Application generates and writes a large CSV/PDF report to local disk.
- **Negative Action:** File write triggers `IOError: [Errno 28] No space left on device`.
- **Expected Oracle:** Function catches write failure, removes partial/corrupt artifact from disk, and raises descriptive `StorageExhaustedException`. Database record is not marked "Completed", and file descriptors are closed.

### Scenario 4: Diagnostic Leakage on Database Failure
- **Contract:** User queries account transactions; backend connects to SQL database.
- **Negative Action:** Database query throws connection error or syntax/constraint exception.
- **Expected Oracle:** Client receives generic message ("Unable to retrieve transactions") and unique error tracking ID (`HTTP 500`). Raw stack trace, SQL query, and database connection strings exist only in secure server logs.

## Key Oracle Patterns

- **Fail-Safe Invariant:** Security and integrity checks fail closed; partial or missing dependency answers always default to deny or safe fallback.
- **Sanitized Client Diagnostics:** The client receives a generic error description and a correlation/tracking ID; internal details (stack traces, paths, schemas) stay server-side.
- **Clean Resource Deallocation (RAII / finally):** Sockets, file descriptors, mutex locks, and database connections are reliably released even when execution aborts midway.
- **Atomic Abort & Rollback:** Partial writes or multi-step operations cleanly undo incomplete side effects; no orphaned disk artifacts or half-mutated records.
- **Deterministic Timeout & Bounded Retries:** Operations enforce bounded execution timers; retry loops have strict caps with backoff and jitter.
- **Process & Worker Stability:** Transient I/O or downstream faults never cause unhandled promise rejections or process-level crashes.

## Primary Sources & References

- Michael Nygard, *Release It! Design and Deploy Production-Ready Software* (Circuit Breaker, Bulkhead, Timeouts)
- OWASP Top 10: A05:2021 – Security Misconfiguration (Error Handling & Verbose Messages)
- CWE-209: Generation of Error Message Containing Sensitive Information
- CWE-636: Not Failing Securely ('Failing Open')
- CWE-703: Improper Check or Handling of Exceptional Conditions
- CWE-775: Missing Release of Resource after Effective Lifetime
- POSIX.1-2017 Error Numbers (Errno handling: `ETIMEDOUT`, `ECONNRESET`, `ENOSPC`, `EACCES`)
