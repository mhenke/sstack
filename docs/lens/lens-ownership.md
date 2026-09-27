# Negative Testing: Ownership Lens

Research on negative testing for authorization boundaries, object ownership, privilege tiers, collection scoping, and multitenant isolation.

## Overview & Definition

Negative testing for ownership verifies that actors cannot read, mutate, or delete resources, collections, or properties they are not authorized to access.

Authorization is distinct from authentication: an authenticated subject is unauthorized to most resources, while an unauthenticated subject is legitimately entitled to public resources. Every authorization decision is evaluated across a four-part tuple: `(subject, object, action, context)`.

The lens attacks decision points that fail to bind all four elements—targeting Broken Object Level Authorization (BOLA / IDOR), Broken Object Property Level Authorization (BOPLA / mass assignment), Broken Function Level Authorization (BFLA), unscoped collection queries, privilege escalation, and cross-tenant leakage under a strict "deny-by-default" model.

## Core Concepts & Failure Modes

1. **Insecure Direct Object Reference (IDOR / BOLA) (CWE-639 / OWASP API1):**
   - User A requests User B's resource via predictable ID (`GET /orders/1002`).
   - Route handler verifies identity but omits object-level ownership checks (e.g., `SELECT * FROM orders WHERE id = :id` instead of `... AND account_id = :current_user`).
2. **Broken Object Property Level Authorization & Mass Assignment (CWE-915 / OWASP API3):**
   - Reading sensitive or private object attributes not granted to the subject's role (BOPLA read).
   - Setting restricted fields during creation or update payloads (e.g., submitting `{"role": "admin"}`, `{"is_verified": true}`, or `{"tenant_id": 99}` in profile update payloads).
3. **Broken Function Level Authorization & Verb Bypass (CWE-862 / OWASP API5):**
   - Direct execution of administrative or privileged endpoints by unprivileged callers (`POST /api/admin/reindex`, `DELETE /api/users/12`).
   - Method disparity: `GET /api/documents/10` enforced while `POST`, `PUT`, or `DELETE` on the same resource omit guards.
   - Client-side-only controls: UI hides buttons or links, but direct API or curl requests succeed unchecked.
4. **Unscoped Collections & Search Aggregations (CWE-200 / CWE-862):**
   - List, search, export, and report endpoints omitting subject scoping from the underlying query, returning entire multi-user or cross-tenant datasets.
   - Count, facet, and pagination leaks: row results are filtered, but `total_records`, facet counts, or error messages reveal the existence or volume of unauthorized records.
5. **Horizontal & Vertical Privilege Escalation (CWE-285 / CWE-863):**
   - Horizontal: Accessing or modifying resources belonging to peers within the same privilege tier.
   - Vertical: Tampering with claims, parameters, or hidden fields to gain administrative rights.
   - Static/hardcoded role checks (`hasRole("ADMIN")`) that fail to enforce granular permission boundaries or resource-level scoping.
6. **Multitenant & Intermediary Delegation Failures (CWE-441 / Confused Deputy):**
   - Tenant A initiating actions targeting Tenant B's identifiers.
   - Downstream microservice trusting intermediate caller identity rather than validating end-user delegation and permission scope.
7. **Token Integrity & Session Lifecycle Failures (CWE-384 / CWE-287):**
   - Replaying credentials after explicit logout or revocation.
   - Bypassing scope limits through JWT tampering, algorithm confusion (`alg: none`), or unvalidated scope claims.

## Real-World Examples & Test Scenarios

### Scenario 1: IDOR / BOLA on Resource Mutation
- **Contract:** User A (ID: 101, Order: 1001) and User B (ID: 102, Order: 1002).
- **Negative Action:** User A sends `DELETE /api/orders/1002` using User A's authenticated session.
- **Expected Oracle:** HTTP 403 Forbidden or HTTP 404 Not Found (to avoid leaking resource existence). Order 1002 remains completely unchanged in persistent storage.

### Scenario 2: Unscoped Collection Query & Count Leak
- **Contract:** Multi-tenant invoice search endpoint `GET /api/invoices?q=March`.
- **Negative Action:** Tenant A executes search with valid query term matching documents across multiple tenants.
- **Expected Oracle:** Results array contains exclusively invoices belonging to Tenant A. Summary fields (`total_count`, page metadata) match only Tenant A's result count, leaking zero information about Tenant B.

### Scenario 3: BOPLA / Mass Assignment on Profile Update
- **Contract:** User self-service profile update accepts `name` and `email`.
- **Negative Action:** Standard user submits `PATCH /api/users/me` with payload `{"name": "Alice", "role": "admin", "verified": true}`.
- **Expected Oracle:** Service rejects request (`HTTP 400` / `HTTP 422`) or cleanly ignores unauthorized properties. User's stored role remains `standard` and `verified` remains `false`.

### Scenario 4: Function-Level Verb Bypass / UI-Only Control
- **Contract:** Administrative user management endpoints restricted to `role: admin`.
- **Negative Action:** Standard user issues direct `POST /api/users/102/suspend` bypassing the hidden UI element.
- **Expected Oracle:** HTTP 403 Forbidden. Target user status is unmodified; event logged as security warning.

### Scenario 5: Cross-Tenant Batch Operation
- **Contract:** Bulk item processing accepts list of item IDs.
- **Negative Action:** Tenant A submits batch update for `[201, 202, 305]` where item `305` belongs to Tenant B.
- **Expected Oracle:** Atomic rejection of entire batch or granular denial on item `305`. Item `305` suffers zero side effects or state mutation.

## Key Oracle Patterns

- **Deny-by-Default Invariant:** Absence of explicit allow rule denies access immediately. Throwing authorization checks fail closed (never allow).
- **Baseline-Diff Oracle (WSTG-ATHZ-02):** Compare requests from distinct subjects against identical resources. Authorized subject receives `200 OK`; unauthorized subject receives `403 Forbidden` or `404 Not Found`.
- **Existence Neutrality & Anti-Enumeration (RFC 9110):** Unauthorized requests return `404 Not Found` or identical generic error responses to prevent enumerating IDs across account boundaries.
- **Collection Scope Invariant:** Result sets, aggregates, facet counts, and pagination headers must never exceed the requesting principal's verified boundary.
- **Property Sanitization:** Disallowed read fields are stripped from responses; unpermitted write fields are rejected or dropped before ORM/database persistence.
- **Zero Side Effects:** Failed authorization attempts execute zero state mutations, zero partial writes, and trigger security audit telemetry with correlation IDs.
- **Credential Invalidation:** Logged-out or revoked session tokens fail with `401 Unauthorized` on immediate subsequent requests.

## Primary Sources & References

- OWASP Top 10:2025 & 2021 – A01: Broken Access Control
- OWASP API Security Top 10:2023 – API1: Broken Object Level Authorization (BOLA)
- OWASP API Security Top 10:2023 – API3: Broken Object Property Level Authorization (BOPLA)
- OWASP API Security Top 10:2023 – API5: Broken Function Level Authorization (BFLA)
- OWASP Web Security Testing Guide (WSTG v4.2): WSTG-ATHZ-02 (Bypassing Authorization Schema), WSTG-ATHZ-03 (Privilege Escalation), WSTG-ATHZ-04 (IDOR)
- RFC 9110 HTTP Semantics (Sections 15.5.2 `401 Unauthorized`, 15.5.4 `403 Forbidden`, 15.5.5 `404 Not Found`)
- MITRE CWE-284 (Improper Access Control), CWE-285 (Improper Authorization), CWE-639 (BOLA/IDOR), CWE-862 (Missing Authorization), CWE-863 (Incorrect Authorization), CWE-915 (Mass Assignment), CWE-441 (Confused Deputy), CWE-918 (SSRF)
- NIST SP 800-162 (Guide to Attribute Based Access Control)
