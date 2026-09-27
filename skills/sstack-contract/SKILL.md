---
name: sstack-contract
description: "Contract lens rubric. Case-generation heuristics, oracle patterns, and worked examples for API schema drift, undeclared fields, breaking type mutations, enum discrepancies, and unverified boundary contracts. Loaded inline under ### Lens rubric."
disable-model-invocation: true
---

# Contract lens

Attacks every mapped surface through the contract lens: that an
implementation must strictly adhere to its declared interface
specifications (OpenAPI, JSON Schema, Protobuf, Avro, or consumer
agreements), that schema drift between documentation and execution is
prevented, and that breaking mutations or undeclared properties are
caught at system boundaries.

## Case-generation heuristics

- Specification drift: compare documented schema (OpenAPI, JSON Schema,
  types) against runtime outputs to find missing required fields,
  retyped attributes, or mismatched status codes.
- Undeclared and extra property leakage: submit or inspect payloads
  carrying extra attributes (`additionalProperties: false`) to verify
  rejection or sanitization of internal/undocumented fields.
- Breaking schema mutations: simulate consumer interactions against
  modified provider interfaces where fields were renamed, types changed
  (e.g. integer to string), or enum variants added without versioning.
- Unenforced schema validation: check whether schemas declared in the
  codebase are actively validated at the boundary or merely decorative
  annotations.
- Boundary contract rejection: submit payloads violating structural
  schema rules (e.g. invalid string patterns, out-of-spec types) to
  verify explicit HTTP 400 or 422 rejection.

## Oracle patterns

- Strict schema conformance: returned objects strictly validate
  against declared response schemas without missing properties or type
  mismatches.
- Explicit boundary diagnostics: requests violating schema constraints
  fail at the perimeter with RFC 9110 HTTP 400 Bad Request or 422
  Unprocessable Content, naming the schema violation.
- No undeclared leakage: responses contain only declared public
  properties; internal flags and tokens are stripped before output.
- Breaking changes rejected: contract verification suites flag backwards-
  incompatible mutations prior to deployment.

Worked example — Python `BillingReportGenerator` generating monthly
financial summaries against schema `billing_summary_v1.json`: case
generator includes undocumented `internal_audit_notes` and omits
mandatory `currency` field, oracle validates output against schema and
raises `SchemaValidationError("missing required property: currency")`,
observed (bug) exports malformed JSON with leaked internal audit notes.

TypeScript `CustomerProfileEndpoint` validating incoming registration
payload against OpenAPI schema: case request body includes undeclared
`loyaltyTier` and invalid formatted date string, oracle rejects with
`422 Unprocessable Content ("additional properties not permitted: loyaltyTier")`,
observed (bug) persists unvalidated fields directly to database.

## Failure modes to watch for

- Spec-to-reality drift: API documentation claiming one contract while
  runtime code implements another.
- Mass assignment through undeclared properties (CWE-915): accepting
  unfiltered input attributes into domain objects.
- Silent breaking changes: altering serialization formats without
  updating consumer contracts or API versions.
- Unvalidated format annotations: assuming `"format": "email"` is
  validated when validator operates in annotation-only mode.

## Language notes

### Python

- Pydantic: models without `extra = "forbid"` silently accept arbitrary
  additional properties.
- `jsonschema`: draft validators require explicit check options for
  format assertion vocabularies (JSON Schema 2020-12 §7.2.1).

### JavaScript / TypeScript

- TypeScript interfaces exist only at compile time; runtime validation
  requires libraries like Zod, Valibot, or Ajv.
- Express / Fastify: route validation schemas must enforce strict
  coercion and strip unknown properties.

### Java

- Jackson: configure `DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES`
  to prevent silent acceptance of arbitrary extra fields.
- Bean Validation (JSR 380): annotations like `@NotNull` and `@Valid`
  must be explicitly triggered on controller methods with `@Validated`.

### C++

- Protobuf: unknown fields are preserved in unknown field sets by
  default; strict serialization requires explicit verification.

## When not to apply

The surface has no declared schema, no external API boundary, no
contract specification, and operates purely on private in-memory
types.
