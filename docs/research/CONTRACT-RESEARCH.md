# Contract lens: what a `contract` lens would own

Every claim below was read from the primary source named beside it. Where
a source does not say something, this file says so rather than filling the
gap. Research date: 2026-09-26. Linked from [`RESEARCH.md`](RESEARCH.md).

The `contract` row in the lens index reads "API contract violations between
services" and is unbuilt. This note exists to decide whether shipping it
would duplicate `boundaries`, `malformed`, and `missing`, which already own
payload validation.

## The overlap, settled

The five cases in the common "contract negative testing" summary are all
already owned:

| Case | Shipped owner |
|---|---|
| Missing required field | `missing` |
| Type mismatch (`"age": "twenty"`) | `malformed` |
| Out-of-range value (`price: -50.00`) | `boundaries` |
| Extra field (`"is_admin": true`) | `ownership` (mass assignment) or `malformed` |
| Malformed JSON | `malformed` |

A lens whose rubric is those five cases would be a fourth copy of the same
probes. So the lens has to be defined by what it owns instead.

## What a schema can and cannot prove

JSON Schema 2020-12 splits vocabularies, and the split decides whether a
declared contract is a real oracle or decoration.

The `format` keyword is annotation-only by default. From the validation
spec, §7.2.1:

> Implementations MAY still treat "format" as an assertion in addition to an
> annotation and attempt to validate the value's conformance to the specified
> semantics. The implementation MUST provide options to enable and disable
> such evaluation and MUST be disabled by default.

and on the two vocabularies, §7.1: implementing the Format-Annotation
vocabulary is REQUIRED, implementing the Format-Assertion vocabulary is
OPTIONAL. A schema full of `"format": "email"` proves nothing until a
validator opts in. sstack's own rule already covers the consequence at a
higher level: a regression that passes because the pin was wrong is not a
regression (AGENTS.md, QA Agent).

Closeness needs `unevaluatedProperties`, not `additionalProperties`. Core
spec §11.3:

> Validation with "unevaluatedProperties" applies only to the child values of
> instance names that do not appear in the "properties", "patternProperties",
> "additionalProperties", or "unevaluatedProperties" annotation results that
> apply to the instance location being validated.

`additionalProperties: false` only sees the keywords adjacent to itself, so a
schema closed with it and composed under `allOf` can still admit an extra
field. Whether a server strips or rejects unknown fields is not standardized:
OpenAPI describes the schema, and runtime behavior is the framework's choice.
The oracle has to come from the target's own decision, recorded in `map.md`.

## What a consumer-driven contract actually proves

This is the finding that separates the lens from the three that overlap it.
Avro's schema resolution states precisely what a contract permits, and it is
all about *shape over time*, not about rejecting a request:

- fields are matched by name, not position
- a writer field absent from the reader is ignored
- a reader field absent from the writer uses its default, or an error is
  signalled
- an enum symbol missing from the reader is an error
- only specific promotions are legal (`int` to `long`/`float`/`double`, and
  the string/bytes pair)

Source: Avro specification, "Schema Resolution". Compatibility is defined in
terms of what a *reader* may see, so a contract test proves a provider did
not change shape. Nothing in it requires a provider to reject anything.

The same holds for protobuf. The field number "cannot be changed once your
message type is in use because it identifies the field in the message wire
format", and numbers 19,000 to 19,999 are reserved (protobuf `proto3`
reference, "Using Field Numbers"). Breaking a contract is a silent decode
change, not a 4xx.

So: a consumer-driven contract lens would attack *drift between two
versions of a shape*, and the observed failure is a wrong value, a dropped
field, or a decode error. That is not what the other lenses do, and it is
also not what the index row promises.

## The status-code question, checked at the source

The 400-versus-422 distinction that most write-ups treat as settled is
narrower than advertised, and the version cited matters.

RFC 9110 §15.5.1 defines 400 as a perceived client error, "malformed request
syntax, invalid request message framing, or deceptive request routing". RFC
9110 §15.5.21 defines 422 as the server understanding the content type and
the syntax, but being unable to process the contained instructions, and it
notes a 415 would be inappropriate. The RFC's changes-from-7231 list
(Appendix B.3) records that 422, "previously defined in Section 11.2 of
[WEBDAV]", "has been added because of its general applicability".

So 422 is spec-defined in RFC 9110, not merely an IANA convention. But
neither RFC says a missing field must be 422 rather than 400. That choice is
the API's own, and the lens must record it rather than assert a universal
rule.

RFC 9457 makes every member optional, which is the opposite of what most
error-handling guides imply. Per §3.1, a member whose value type does not
match "MUST be ignored -- i.e., processing will continue as if the member had
not been present", and `type` defaults to `about:blank` when absent. For
`title`: "It SHOULD NOT change from occurrence to occurrence", and it is
"advisory". For `detail`: it "ought to focus on helping the client correct
the problem", and consumers "SHOULD NOT parse the 'detail' member for
information". A problem-details body with no members at all is conformant.
The observable oracle is therefore narrow: the response uses
`application/problem+json` when the target documents it, and it does not
carry internal detail. The members are not a required checklist.

JSON:API, for contrast, is the strict one. Error objects "MUST be returned
as an array keyed by errors in the top level", `data` and `errors` "MUST NOT
coexist", and when a server hits several problems it should use the most
generally applicable code, with 400 given as the example for multiple 4xx
errors. Its 4xx rules are about the *request's* shape (an unsupported
`include` path, an unknown query parameter family), not about payload
validation results.

## What the lens should own

A `contract` lens earns its place only if it attacks the boundary where a
declared interface and the implementation disagree, and three of those
failure classes are invisible to the other seven lenses:

1. **The document is the oracle.** A schema, an OpenAPI document, a
   `.proto`, or a type signature exists in the repo, and the implementation
   is checked against it rather than against prose. Drift is a finding.
2. **The contract is declared but unenforced.** A schema is present and
   never loaded, a `format` that nothing asserts, a validator in a
   non-strict default. Absence of enforcement is the defect.
3. **Two versions of the shape disagree.** A field renamed, retyped, made
   required, or renumbered between what one component writes and what
   another reads.

Class 3 is the one the index row is reaching for, and it is the only one that
is genuinely new. It is also the hardest to seed: it needs two versions of
an interface in one fixture, which none of the five current fixtures has.

## Open questions

- Pact was not consulted. The repo fetch for the v4 specification returned
  404 on the paths tried, so nothing about Pact's model is asserted here.
- Whether a `contract` lens can run as a scratch-script probe at all, or
  whether class 3 needs a build-and-decode harness, is unanswered. This is
  the same problem C++ hit: a different proof model, not more cases.
- `docs/TOOLS.md` would need a schema-validation row if this ships.

## Method note

Two background research agents reported on this question. Both described
files they had not written, and one produced findings that contradict the
specs, including a claim that 422 is not RFC-defined when RFC 9110 §15.5.21
defines it. Every claim above was re-read from the source and the agents'
output was discarded. Recorded here because the failure mode is the one
sstack exists to catch: a confident, well-formatted claim with a citation
that does not say what the claim says.
