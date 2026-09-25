---
name: sstack-ownership
description: "Ownership lens rubric. Authorization decisions: function-level, data-level (BOLA/IDOR), and field-level (BOPLA) access; deny-by-default, least privilege, permission-not-role checks, token and session integrity, CORS/CSRF, cross-tenant and intermediary delegation, static resources. Loaded inline under ### Lens rubric."
disable-model-invocation: true
---

# Ownership lens

Attacks authorization, not input shape. The request may be perfectly
valid; the subject may not be entitled to what it asks for. A response,
a mutation, or a field the subject was never granted is a confirmed
ownership failure.

Authorization is not authentication. An authenticated subject is still
unauthorized to most objects; an unauthenticated subject is legitimately
entitled to public resources. Both are findings when the decision is
wrong in the direction that leaks or mutates.

## Write the tuple before attacking

Every decision is a function of four inputs. Write the tuple per surface
in `map.md` before probing it.

| input | question | usual carrier |
|---|---|---|
| subject | who is asking | session, token claims, API key, mTLS identity, service account |
| object | what is acted on | record, path, tenant, field, route, file |
| action | what is done | read, create, update, delete, export, execute |
| context | what else is true | owner/member/manager relation, resource state, time, IP, device |

Rank every decision site you find by how much of the tuple it binds. A
check reading only subject and action (`isAdmin`, `hasRole("ADMIN")`)
cannot answer a per-object question: it is the weakest tier, and it is
where horizontal escalation lives. A check binding all four is a
permission check (`hasPermission("DELETE_ACCOUNT")`). A surface with no
tuple at all has no authorization.

## Find every decision site, then attack the weakest

Access control is enforced in several components at once: web filters or
middleware, decorators and guards, per-handler checks, query and ORM
filters, template field filters, database row policies, gateway or
proxy config, and client-side checks. Enumerate them all. The weakest
one is the vulnerability, and the union of them must be deny-by-default.
A single consolidated routine is the fix; N scattered checks are the bug.

## Case-generation heuristics

- Bind fewer inputs than the surface offers, one at a time: right
  subject, wrong object; right object, wrong action; right object, wrong
  context.
- Enumerate sequential, guessable, or user-supplied object references
  across the ownership boundary. Obfuscation is not a control; prove
  exposure or record refutation with the attempt.
- Force-browse: request authenticated pages with no session, privileged
  pages as a standard user, and unlinked admin or API routes directly.
- Call the write methods. `POST`, `PUT`, `PATCH`, and `DELETE` are the
  ones that ship with no check while `GET` is guarded.
- Write the fields you should not. Ownership, role, tenant, price, and
  status columns are mass-assignment targets: can a caller set
  `owner_id` to someone else, or `role` to `admin`, on create or update?
- Replay the credential. Log out, then reuse the cookie or bearer token.
  Then tamper: edit role or subject claims, swap algorithm, extend
  expiry, present a token minted for another consumer.
- Ask a service to act for someone else. When service A calls service B,
  does B decide on the originating consumer's permissions, or on A's?
- Reach the resource the filesystem or network hands out: static
  assets, directory listings, `.git`, backups, config files.

## Collection surfaces leak what object checks cannot catch

A search, list, index, feed, export, report, or autocomplete surface has
no single object to protect, so there is no object to fetch and no ID to
swap. The failure is not a per-record check being bypassed; it is the
principal never entering the query at all. Every per-object check can
pass while the result set is another subject's entire table.

Scope belongs where rows are selected, not only where a row is opened.
Prove the scope by the contents of the result, not by the code path.

- Establish the population. Create records for subject A and subject B
  with distinguishable values, then request the collection as A. Every
  B value in the result is a confirmed finding; one is enough.
- Attack the shape of the filter, not just its value: a query with no
  subject clause, a filter that is applied after the fetch, a default
  sort or page that crosses the boundary, and a count or facet that
  reveals the size of another subject's data.
- Search by a non-key attribute, and a wildcard or empty query, to see
  whether scope is bypassed when the match is broad rather than exact.
- Take the identifiers the collection itself hands back and replay them
  as direct object references. A scoped list in front of an unscoped
  detail route is a common pairing, and the two must be tested together.
- Change the scope without changing the subject: a `filter`, `include`,
  `expand`, `fields`, or `with` parameter that adds another subject's
  rows, or that adds fields a subject may not read.
- Check every output of the same handler: the rows, the count, the
  facets, the pagination total, and the error path all disclose
  something. A correct row filter with a leaked total is still a leak.
- Exhaustive export and report paths first; they are the same defect
  with a wider blast radius.

Oracle: a collection requested by subject A contains only records A is
entitled to see, and its counts and facets agree with the rows. Any
other subject's data in the result, in a count, or in a facet is a
confirmed leak, and `403` is not the only possible oracle: a silently
wider result set is the more common observation.

Worked example — `search_orders(session, q)` filters on `q` alone:
oracle returns only A's orders, observed returns A's and B's. A detail
route `get_order(session, id)` is correctly scoped, so swapping the ID
finds nothing: the collection is the hole, and ID swapping is the wrong
probe for it. Related but distinct: an unscoped count is a leak of
existence and volume rather than of contents.

## Oracle patterns

- Wrong subject requests an unowned object → denial (`401`/`403`), never
  the entity, and no signal that distinguishes "forbidden" from "does
  not exist".
- No visible check on a non-public surface → deny by default. Absence of
  a check is itself a bug.
- A check that throws, or a policy chain that reaches its last branch,
  denies. An exception inside the check is a denial, never a fall-through
  to allow.
- Response fields and accepted write fields match the documented grant.
  A field the subject may not read, or set, is BOPLA.
- Cross-tenant and cross-entity enumeration returns denials, not records.
- A collection returns only the caller's rows, and its counts, totals,
  and facets agree with them. A correct row filter with a leaked total
  is still a confirmed leak.
- After logout or revocation the old credential no longer works.
- A new account, a newly added route, and an unregistered endpoint are
  denied until explicitly granted.
- Denials are logged with subject, object, action, and reason, and a
  repeated-denial burst is visible.
- Public resources are reachable unauthenticated on purpose, and that
  intent is written down; everything else is not.

## Failure classes and their probes

| class | probe | oracle |
|---|---|---|
| least privilege violated | one role reaches every action | each grant maps to a named permission; no god-role |
| deny-by-default missing | unlisted route, new account, new feature | denied until configured |
| policy falls through to allow | exhaust the condition chain | final branch denies, not allows |
| hard-coded role | search source for role-name literals | policy expressed as permissions in one routine |
| check throws | make the check's dependency fail | denial, not exception-as-allow |
| BOLA/IDOR (V8.2.2) | swap the object reference | denial for the non-owner |
| unscoped collection (V8.2.2) | request a list/search as A with A and B records present | result holds only A's rows |
| count or facet leak | scoped rows, unscoped total/count/facets | counts and facets agree with the returned rows |
| scope bypassed by filter shape | wildcard, empty, or attribute-only query | scope holds when the match is broad |
| scope as a request parameter | `include`/`expand`/`with`/`fields` adding other rows or fields | rejected or scoped to the caller |
| export/report wider than the UI | run the export path behind the same subject | export honours the same scope |
| list-then-fetch pair | IDs from a scoped list replayed on the detail route | both routes scoped, tested together |
| BOPLA read (V8.2.3) | read a privileged field | field absent from the response |
| BOPLA write (V8.2.3) | set a privileged field | field ignored or rejected |
| field rules on state | read/write while `status` is pending vs closed | field set differs per state, as documented |
| missing write controls | `POST`/`PUT`/`DELETE` unauthenticated | all methods guarded, not only `GET` |
| force browsing | privileged URL, no session, standard user | denial at the trusted layer |
| client-side only control (V8.3.1) | replay the request outside the browser | server denies; UI hiding proves nothing |
| URL/internal-state tampering | edit parameter, state field, hidden field | server recomputes, never trusts |
| token tampering | edit claims, algorithm, expiry, subject | signature and claims verified |
| logout not invalidating | reuse the credential post-logout | server-side session invalidated |
| stale grant | revoked role, then use the live token | change applied, or alert-and-revert, immediately |
| confused deputy (V8.3.3) | low-privilege service calls a peer | peer decides on the consumer's permissions |
| cross-tenant write (V8.4.1) | tenant A writes tenant B's object | denied; no cross-tenant effect |
| admin interface (V8.4.2) | network location as the only factor | identity re-verified; context is not a sole factor |
| contextual/step-up | sensitive action from a new device or odd hour | step-up challenge or denial, as documented |
| CORS | wildcard or reflected origin with credentials | no credentialed wildcard, minimal allowlist |
| CSRF | state-changing request with only cookies | token or same-site defense enforced server-side |
| SSRF (CWE-918) | unvalidated URL parameter | the server's own identity cannot reach internal-only targets |
| static resources | `/.git/HEAD`, `/.env`, backups, bare directory | not served; listing disabled |
| error-based enumeration | compare denial for present vs absent object | indistinguishable responses |
| decommissioned account | removed role, retained credential | credential dies with the grant |

Worked example — Python `get_check(session, check_number)`: user A
requests user B's check number, oracle
`PermissionError("check is not owned by this user")`, observed returns
B's record. TypeScript `getUser(req, 102)` under user 101's session:
oracle throws `Error("forbidden")`, observed returns user 102. A field
case: `update_order(session, id, {"total_cents": 1})` where the consumer
may read totals but not write them; oracle rejects the field, observed
persists it. A token case: log out, replay the same bearer token; oracle
`401`, observed still returns the record.

## Unit tier

Use sstack's scratch-script model: mock the subject object, set the
role/session/claims, call the function, assert the rejection. No live
authenticated sessions are required for the unit tier. Functional access
control belongs in the target's own unit and integration suites, so the
regression lands there, not in a scratch file.

The integration tier needs real sessions, multiple subjects, and live
routers: the whole point is that middleware, filters, and gateway config
are part of the decision. Record session and entity evidence. Test both
tiers when the enforcement point is not in the function under test.

## Interaction with verification skill

Read the target's verification skill or feature map first. It usually
knows entities, ownership, roles, and auth flow. Attack the boundaries
between principals rather than re-deriving the ownership model. When
neither exists, derive the tuple from the surface's parameters (session,
user id, tenant id, role) and the call sites, and record it in `map.md`
before attacking. Where the target documents its grants, treat the
documentation as the oracle: a decision that contradicts the documented
rule is the finding.

## When not to apply

The surface has no principal, tenant, role, or account boundary and all
callers are trusted system-internal code with no user context. Pure
computation over data already scoped by its caller stays out of this
lens; its inputs belong to `malformed`, `missing`, and `boundaries`.
