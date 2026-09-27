# Negative Testing: Contract Lens

Research on negative testing for API contract violations, schema drift between specification and implementation, undeclared payload mutations, breaking type changes, and provider-consumer contract divergence.

## Overview & Definition

Negative testing for the contract lens evaluates the boundary where a published interface specification (OpenAPI, JSON Schema, Protobuf, Avro, or consumer-driven Pact contract) and the runtime implementation disagree.

While lenses like `malformed`, `missing`, and `boundaries` attack general payload validity, the `contract` lens attacks *divergence from declared specifications*: verifying that implementations strictly conform to versioned schema definitions, that breaking contract mutations fail loudly at build or validation time, that unannounced schema additions or omissions are caught, and that consumer expectations are protected from silent producer drift.

## Core Concepts & Failure Modes

1. **Specification vs. Implementation Drift (Spec-to-Reality Gap):**
   - The OpenAPI or JSON Schema document defines a property as required, but the endpoint accepts payloads omitting it without validation.
   - Endpoint returns HTTP status codes, headers, or response bodies not defined in the specification.
2. **Breaking Schema Mutations & Semantic Drift:**
   - Field renaming, deletion, or type narrowing (e.g. changing an integer ID to an alphanumeric UUID string) without bumping API version.
   - Enum value deprecation or removal that causes deserialization crashes in consumer services.
   - Tightening input constraints on existing endpoints without notifying consumers.
3. **Undeclared & Additional Property Leaks (Mass Assignment / Exposure):**
   - Responses leaking internal fields (e.g. `password_hash`, `internal_tenant_id`) not declared in the public response schema.
   - Endpoints silently accepting undeclared properties when the contract requires strict validation (`unevaluatedProperties: false` or `additionalProperties: false`).
4. **Consumer-Driven Contract Violations (Pact Incompatibilities):**
   - Producer altering field names or nesting structures that violate recorded consumer interaction agreements.
   - Failure of provider verification pipelines to reject breaking changes before deployment.
5. **Format & Type Annotation Laxity:**
   - Declaring `"format": "email"` or `"format": "date-time"` in schemas without enforcing assertion vocabularies (JSON Schema 2020-12 §7.2.1), admitting invalid strings into storage.

## Real-World Examples & Test Scenarios

### Scenario 1: Undocumented Field Leakage in API Response
- **Contract:** OpenAPI response schema for `GET /api/v1/orders/{id}` specifies `{ id: integer, total: number, status: string }` with `additionalProperties: false`.
- **Negative Condition:** Implementation serializes internal database entity containing `internal_flags: dict` and `payment_gateway_token: string`.
- **Expected Oracle:** Response schema validation fails in provider test suite, or boundary serializer strips undeclared internal attributes before network transmission.

### Scenario 2: Unannounced Enum Value Introduced by Provider
- **Contract:** Payment status enum documented as `["pending", "completed", "failed"]`.
- **Negative Condition:** Provider returns new status `"processing"` or `"partially_refunded"` without updating contract.
- **Expected Oracle:** Consumer parser flags unrecognized enum variant; contract verification suite fails build indicating breaking API change.

### Scenario 3: Request Payload Schema Validation Bypass
- **Contract:** Public API schema specifies that `POST /api/v1/shipments` requires `destination_zip` matching `^[0-9]{5}(-[0-9]{4})?$`.
- **Negative Condition:** Client posts `{"destination_zip": "INVALID_ZIP_CODE"}`.
- **Expected Oracle:** Endpoint validates payload against declared schema at request boundary and returns RFC 9110 HTTP 422 Unprocessable Content naming the schema violation, never passing malformed string to backend shipping client.

### Scenario 4: Breaking Field Type Narrowing
- **Contract:** Account balance field historically defined as `number` (supporting floating-point currency representation).
- **Negative Condition:** Provider updates internal model to string-based fixed-point representation (`"123.45"`), returning string in response.
- **Expected Oracle:** Contract diff tools (`oasdiff`) flag breaking type mutation; consumer contract verification rejects response format.

## Key Oracle Patterns

- **Schema Conformance:** Runtime responses strictly validate against the published schema definition without undeclared fields or mismatched types.
- **Validation at Boundary:** Requests violating declared schema rules are rejected at the edge with HTTP 400 Bad Request or HTTP 422 Unprocessable Content.
- **Explicit Breaking Change Diagnostics:** Schema diff tools and consumer pact verifications fail with explicit change reports (e.g., "Field 'sku' type changed from integer to string").
- **No Internal Exposure:** Response payloads contain only declared public schema properties.

## Primary Sources & References

- RFC 9110: HTTP Semantics §15.5.1 (400 Bad Request) & §15.5.21 (422 Unprocessable Content)
- JSON Schema 2020-12 Validation Specification (Vocabularies for Validation and Formatting)
- OpenAPI Specification v3.1.0 (Data Types, Request Bodies, Response Schemas)
- Pact Foundation Specification v4 (Consumer-Driven Contract Testing)
- `oasdiff` & Spectral (OpenAPI Linting and Breaking Change Detection Standards)
