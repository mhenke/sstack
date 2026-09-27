# Negative Testing: Missing Lens

Research on negative testing for missing fields, omitted parameters, null/undefined values, falsy coercion traps, defaulted states, and configuration invariants.

## Overview & Definition

Negative testing for missing inputs examines what happens when mandatory attributes, required HTTP headers, function arguments, configuration variables, or object properties are omitted or provided as null/undefined.

A resilient system must detect absent requirements and provide explicit, actionable errors at the boundary rather than failing deep inside call stacks with raw `NullPointerException`, `KeyError`, `AttributeError`, `TypeError`, or silently proceeding with corrupted partial state.

## Core Concepts & Failure Modes

1. **Omitted Required Keys / Arguments (CWE-476, CWE-252):**
   - Omitting mandatory JSON object keys in API payloads.
   - Missing required query parameters (e.g., `?token=`, `?page=`).
   - Missing CLI flags or positional function arguments.
2. **Explicit Null vs. Absence Distinction (RFC 7396 / RFC 8259):**
   - In POST/PUT, omitted mandatory fields fail validation; explicit `null` fails type checking.
   - In PATCH / JSON Merge Patch (RFC 7396), omitted fields mean "preserve existing value", while explicit `null` means "clear/delete attribute". Conflating the two either drops data or blocks field clearing.
   - Supplying `null` / `None` / `undefined` for fields that require a typed scalar.
3. **Falsy Coercion & Defaulting Hazards:**
   - Conflating absence with `false`, `0`, or `""` due to loose falsy evaluation (`if not val:`, `val || default`).
   - Python `dict.get(k, default)` behavior: if `k` exists with explicit `None`, `get` returns `None`, bypassing the fallback default and causing deferred `TypeError` (`1 - None`, `None.upper()`) downstream.
   - JavaScript `undefined` (absent) vs `null` (explicit absence): optional chaining (`?.`) suppressing errors when explicit handling is required.
4. **Missing Authentication & Protocol Context:**
   - Requests missing `Authorization`, `X-Tenant-ID`, or `Idempotency-Key` headers.
   - Missing `Content-Type` header causing unhandled 500s or silent empty-body parsing.
   - Incomplete multipart boundaries or missing `Content-Length`.
5. **Partial Object Processing & Unsafe Attribute Traversal:**
   - Attempting nested property access on undefined objects (`user.profile.address.zip`).
   - Partial domain models constructed with missing child associations, breaking invariant checks.
6. **Missing Environment & Boot-Time Configuration (CWE-457):**
   - Services booting with missing mandatory environment variables (`DATABASE_URL`, `JWT_SECRET`, `ENCRYPTION_KEY`).
   - Insecure fail-open fallbacks (e.g., falling back to hardcoded empty secret `""` or `default_key`) rather than failing fast at boot.

## Real-World Examples & Test Scenarios

### Scenario 1: Missing Required Parameter in REST Endpoint
- **Contract:** `POST /api/v1/users` requires `email` and `username`.
- **Negative Inputs:**
  - Request body: `{"username": "jdoe"}` (missing `email`).
  - Request body: `{}` (empty payload).
  - Request body: `{"username": "jdoe", "email": null}` (null value).
- **Expected Oracle:** HTTP 400 Bad Request with field-level diagnostic (`{"errors": [{"field": "email", "message": "Email is required"}]}`). No partial record persisted.

### Scenario 2: Traversal of Incomplete Nested Data
- **Contract:** A tax calculation function traverses `invoice["customer"]["tax_identifier"]`.
- **Negative Inputs:**
  - `invoice = {"items": []}` (omitted `"customer"` key).
  - `invoice = {"customer": None}`.
- **Expected Oracle:** Raises domain-specific error (`ValueError: invoice must contain a valid customer object`) at the boundary instead of raw `KeyError: 'customer'` or `TypeError: 'NoneType' object is not subscriptable`.

### Scenario 3: Missing Security Headers & Tokens
- **Contract:** Multi-tenant endpoint requires `X-Tenant-ID` header to route data to the tenant partition.
- **Negative Input:** Request sent with no `X-Tenant-ID` header.
- **Expected Oracle:** HTTP 400 Bad Request or 401 Unauthorized explicitly naming the missing header. Execution terminates before database connection initialization; never defaults to tenant 0 or master partition.

### Scenario 4: Partial Update (PATCH) Semantic Integrity
- **Contract:** `PATCH /api/v1/profiles` updates user attributes. Omitted fields remain untouched; `null` clears the field.
- **Negative Inputs:**
  - Request body: `{}` (all optional fields omitted).
  - Request body: `{"bio": null}` (explicit null).
- **Expected Oracle:** For `{}`, existing profile attributes remain unchanged (no overwriting with `null`). For `{"bio": null}`, `bio` is cleared/set to null without triggering "missing required field" errors.

### Scenario 5: Missing Startup Secrets / Environment Variables
- **Contract:** Application boots requiring `JWT_SIGNING_KEY` environment variable.
- **Negative Input:** Service started with `JWT_SIGNING_KEY` unset or empty `""`.
- **Expected Oracle:** Application aborts startup immediately with fatal log (`ConfigurationError: JWT_SIGNING_KEY environment variable is required`), exiting with non-zero status. Never defaults to dummy secret or waits to fail on first client request.

## Key Oracle Patterns

- **Explicit Presence Validation:** Missing field errors explicitly name the absent identifier at the boundary before execution proceeds.
- **Fail-Fast Defense:** Missing prerequisites stop execution before downstream services, database mutations, or arithmetic operations execute.
- **Strict Distinction Between Empty, Null, and Absent:** Logic isolates deliberate empty values (`""`, `0`, `false`), explicit deletions (`null`), and missing keys.
- **No Deferred Type Failures:** Missing or null inputs never leak past the boundary to surface as unhandled `TypeError`, `AttributeError`, or `NullPointerException`.
- **Startup Invariant Enforcement:** Critical infrastructure configuration fails boot cleanly rather than failing open with insecure defaults.

## Primary Sources & References

- OWASP REST Security Cheat Sheet (Mandatory Parameters & Input Validation)
- OWASP API Security Top 10: API3:2023 (Broken Object Property Level Authorization)
- CWE-476: NULL Pointer Dereference
- CWE-457: Use of Uninitialized Variable
- CWE-252: Unchecked Return Value
- RFC 7396: JSON Merge Patch (Omitted vs. Null semantics)
- RFC 8259: The JavaScript Object Notation (JSON) Data Interchange Format
- PEP 484 / Python Type Hints (Optional vs Required typing invariants)
- JSON Schema Specification (Draft 2020-12: `required` keyword validation)
