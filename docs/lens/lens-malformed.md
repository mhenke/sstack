# Negative Testing: Malformed Lens

Research on negative testing for malformed data formats, type violations, corrupted payloads, and unexpected structures.

## Overview & Definition

Negative testing for malformed data verifies how a parser, deserializer, or endpoint behaves when receiving syntactically invalid, type-mismatched, or structurally corrupted data.

The system must reject malformed inputs early at the input boundary without crashing, raising unhandled system exceptions, or executing unauthorized control flow.

## Core Concepts & Failure Modes

1. **Syntax & Protocol Malformations (CWE-20, RFC 8259):**
   - Truncated or unbalanced payloads (e.g., unclosed JSON braces `{ "a": 1 `, XML with mismatched closing tags).
   - Illegal encodings (e.g., non-UTF-8 bytes, invalid escape sequences in string literals).
2. **Type Violations & Coercion Failures (CWE-1287, CWE-704):**
   - Strings provided where integers are expected (`"twenty"` for `age`).
   - Objects or arrays provided where scalar primitives are expected (`{"id": [1, 2]}`).
   - Booleans or numbers where date/time strings are expected.
3. **Delimiter & Injection Hazards (CWE-158, CWE-74):**
   - Payloads containing unescaped delimiters (quotes, semicolons, null bytes `\0`).
   - Structural injection trying to break parsing layers (SQL fragments, script tags, template tags).
4. **Extraneous or Conflicting Fields (CWE-915):**
   - Payloads containing conflicting duplicate keys (`{"id": 1, "id": 2}`).
   - Unrecognized extra fields when strict schema enforcement is required.

## Real-World Examples & Test Scenarios

### Scenario 1: Malformed JSON Serialization
- **Contract:** REST API expects JSON payload representing a customer record.
- **Negative Inputs:**
  - Incomplete JSON: `{"name": "Alice", "email":`
  - Wrong Content-Type mismatch: sending XML or multipart bytes with `Content-Type: application/json`.
  - Non-UTF-8 character sequences in headers or body.
- **Expected Oracle:** HTTP 400 Bad Request with a structured error body (`{"error": "Malformed JSON payload"}`). No 500 Internal Server Error or leaked stack trace.

### Scenario 2: Data Type & Format Mismatch
- **Contract:** `date_of_birth` formatted as `YYYY-MM-DD`.
- **Negative Inputs:**
  - Date format inversion: `"2024-31-12"` or `"12/31/2024"`.
  - Impossible date values: `"2024-02-30"`.
  - Numeric epoch integer instead of ISO string when string is specified.
- **Expected Oracle:** `ValidationError: date_of_birth must be a valid date formatted as YYYY-MM-DD`.

### Scenario 3: Corrupted Numeric Formats
- **Contract:** Currency field expecting decimal string or numeric representation.
- **Negative Inputs:**
  - Non-numeric alphabetic input: `"NaN"`, `"Infinity"`, `"12.34.56"`, `"$100"`.
  - Scientific notation when fixed-precision is required: `"1e6"`.
- **Expected Oracle:** Explicit format parsing error; no internal cast throwing unhandled `NumberFormatException` or `ValueError`.

### Scenario 4: Structural Shape Mismatch & Delimiter Hazards
- **Contract:** Endpoint expects an integer `account_id` and string `comment`.
- **Negative Inputs:**
  - Composite in scalar slot: `{"account_id": [101, 102]}` or `{"account_id": {"id": 101}}`.
  - Embedded NUL or unescaped delimiter: `{"comment": "user\0entry"}`.
  - Conflicting duplicate keys: `{"account_id": 101, "account_id": 999}`.
- **Expected Oracle:** HTTP 400 Bad Request naming the mismatched field and rejecting the request before DB binding. No unhandled `TypeError` or SQL truncation.

## Key Oracle Patterns

- **Clean Parsing Rejection:** Parser stops and reports syntax/type error at the boundary.
- **No Unhandled Runtime Crashes:** Never leak uncaught parser exceptions (e.g. `JSONDecodeError`, `TypeError`, `NumberFormatException`) into the outer application layer; return HTTP 400 Bad Request on web boundaries.
- **No Information Leakage (CWE-209):** Error responses must not output stack traces, internal file paths, or parser library versions.
- **Reject-or-Parse-Completely:** Parser either returns a fully validated value or raises a domain error. Never a partially parsed result.

## Primary Sources & References

- OWASP API Security Top 10: API8:2023 Security Misconfiguration & API3:2023 Broken Object Property Level Authorization
- CWE-20: Improper Input Validation
- CWE-1287: Improper Validation of Specified Type of Input
- CWE-704: Incorrect Type Conversion or Cast
- CWE-158: Improper Neutralization of Null Byte or Delimiter
- CWE-209: Generation of Error Message Containing Sensitive Information
- RFC 8259: The JavaScript Object Notation (JSON) Data Interchange Format
- RFC 9110 §15.5.1: HTTP 400 Bad Request semantics
- ISO/IEC/IEEE 29119-4: Syntax testing and negative input validation
