---
name: sstack-ownership
description: "Ownership lens rubric. Authorization-scope violations, BOLA/IDOR, deny-by-default oracles, and unit-tier session-mocking guidance. Loaded inline under ### Lens rubric."
disable-model-invocation: true
---

# Ownership lens

Attacks authorization scope, not input shape. The request may be
valid; the session may be wrong. A response must belong to the caller.
Any entity returned to the wrong principal is a confirmed ownership
failure.

## Case-generation heuristics

- Swap entity IDs between two principals: request entity 102 using
  user A's credentials after observing entity 101.
- Search by a non-key attribute such as check number and inspect
  whether another principal's records appear.
- Enumerate sequential IDs across the ownership boundary. Prove
  actual exposure; do not assume GUIDs or obfuscation prevent access.
- Remove the role or session from an otherwise valid request to test
  deny-by-default behavior.
- Build a permission matrix: role × entity × operation. Attempt every
  reachable cell rather than testing only the documented happy path.
- Trace whether authorization is centralized in middleware, a guard,
  or a decorator, rather than hidden client-side.

## Oracle patterns

- Wrong principal requests another principal's entity →
  `401 Unauthorized` or `403 Forbidden`, never the entity.
- No visible authorization check on an entity surface → deny by
  default. Absence of a check is itself a bug.
- Enumeration of sequential IDs across tenants returns denials rather
  than records.
- Error responses do not reveal whether the target entity exists.
- Centralized authorization is visible in the request path rather than
  implied by UI behavior.

Worked example — Python `get_check(session, check_number)`:
case authenticated user A requests user B's check number, oracle
`PermissionError("check is not owned by this user")`, observed (bug)
returns B's record. TypeScript `getUser(req, 102)` called with user
101's session: oracle throws `Error("forbidden")`, observed (bug)
returns user 102.

## Unit tier

Use sstack's scratch-script model: mock the user object, set the
role/session, call the function, and assert the rejection. No live
authenticated sessions are required for the unit tier. Integration
testing with real sessions, multiple users, and live routers is a
separate tier and needs session/entity evidence recording.

## Interaction with verification skill

Read the target's verification skill or feature map first. It usually
knows entities, ownership, roles, and auth flow. Attack the boundaries
between principals rather than re-deriving the ownership model. When
neither exists, derive the ownership model from the surface's
parameters (session, user id, tenant id, role) and the call sites;
record it in `map.md` before attacking.

## When not to apply

The surface has no principal, tenant, role, or account boundary; all
callers are fully trusted system-internal code with no user context.
