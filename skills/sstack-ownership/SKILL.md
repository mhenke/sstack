---
name: sstack-ownership
description: "Ownership lens rubric. Authorization decisions: function-level, data-level (BOLA/IDOR), and field-level (BOPLA) access; deny-by-default, least privilege, permission-not-role checks, token/session integrity, header/IP bypasses, CORS/CSRF, cross-tenant and intermediary delegation, static resources. Loaded inline under ### Lens rubric."
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
  across the ownership boundary. Seed ≥2 subjects with distinguishable
  objects before probing BOLA/IDOR so 404s reflect authorization denials
  rather than nonexistent records. Obfuscation is not a control.
- Force-browse: request authenticated pages with no session, privileged
  pages as a standard user, and unlinked admin or API routes the UI
  never links — probe each in the route table and handler guards.
- Call the write methods and alternate verbs. `POST`, `PUT`, `PATCH`, and
  `DELETE` frequently ship without checks while `GET` is guarded.
- Header routing and IP spoofing: send `X-Original-URL: <target>` and
  `X-Rewrite-URL: <target>` to bypass reverse-proxy route filters; spoof
  `X-Forwarded-For: 127.0.0.1`, `X-Remote-IP`, or `X-Client-IP` against
  network-gated or admin paths.
- Partial-URL and traversal bypass: test route prefix checks
  (`startswith`, `indexOf`, unanchored regex) with URL-encoding (`%2f`),
  path traversal (`/..;/admin`), or matrix/semicolon params.
- Write the fields you should not. Ownership, role, tenant, price, and
  status columns are mass-assignment targets: can a caller set
  `owner_id` to someone else, or `role` to `admin`, on create or update?
- Replay the credential. Log out, then reuse the cookie or bearer token.
  Then tamper: edit role or subject claims, drop required OAuth/API
  scopes, swap algorithm, extend expiry, present a token minted for
  another consumer.
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
- Scoped rows carrying unscoped embeds: a check, invoice, or document
  row may embed related objects (issuer, comments, attachments,
  joined relations) fetched without the subject predicate. Every
  embedded object must obey the row's scope; assert no other subject's
  data inside an in-scope row.
- Suggestion and autocomplete surfaces are collections too: a match
  list built from an unscoped population returns other subjects'
  values. Same oracle as the main collection.
- Aggregates computed over the unscoped population — totals,
  breakdowns, averages — leak another subject's volume or values even
  when every row is correctly scoped. Assert each aggregate agrees
  with the scoped rows.
- Snippets and highlights: a search that excludes another subject's
  rows but returns excerpt text drawn from their content has leaked
  it. Excerpt fields obey the same oracle as rows.
- Exhaustive export and report paths first; they are the same defect
  with a wider blast radius.

Oracle: a collection requested by subject A contains only records A is
entitled to see, and its counts and facets agree with the rows. Any
other subject's data in the result, in a count, or in a facet is a
confirmed leak, and `403` is not the only possible oracle: a silently
wider result set is the more common observation.

Worked example — `find_invoices(account_id, query)` filters on the
query text alone and ignores which account asked: the oracle returns
only that account's invoices, observed (bug) returns every
matching invoice across all accounts. A sibling `get_invoice(session,
invoice_id)` is correctly scoped, so swapping the ID finds nothing:
the collection is the hole, and ID swapping is the wrong probe for it.
Related but distinct: an unscoped count is a leak of existence and
volume rather than of contents.

## Oracle patterns

- Wrong subject requests an unowned object → denial (`403` or `404` per
  RFC 9110 §15.5.4 to hide existence; `401` if unauthenticated or
  redirect-to-login), never the entity, and no signal that distinguishes
  "forbidden" from "does not exist". Any `2xx` returning a foreign
  entity or successful mutation is the finding.
- Dual-user baseline-diff: Subject A accesses Object A → baseline `200`;
  Subject B replays the exact same request → response must differ from
  the baseline `200` (`403`/`404`). Identical response body or data
  indicates a bypass.
- No visible check on a non-public surface → deny by default. Absence of
  a check is itself a bug.
- A check that throws, or a policy chain that reaches its last branch,
  denies. An exception inside the check is a denial, never a fall-through
  to allow.
- Response fields and accepted write fields match the documented grant.
  A field the subject may not read, or set, is BOPLA.
- Cross-tenant and cross-entity enumeration returns denials, not records.
  Even a single foreign record or identifier in the payload is a finding.
- Collection surfaces obey the oracle stated above; see that section
  before probing a list, search, export, or report.
- Denials are logged with subject, object, action, and reason, and a
  repeated-denial burst is visible.
- Public resources are reachable unauthenticated on purpose, and that
  intent is written down; everything else is not.

Worked example — Python `get_check(session, check_number)`: user A
requests user B's check number, oracle
`PermissionError("check is not owned by this user")`, observed (bug) returns
B's record. TypeScript `getUser(req, 102)` under user 101's session:
oracle throws `Error("forbidden")`, observed (bug) returns user 102. A field
case: `update_order(session, id, {"total_cents": 1})` where the consumer
may read totals but not write them; oracle rejects the field, observed (bug)
persists it. A token case: log out, replay the same bearer token; oracle
`401`, observed (bug) still returns the record.

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
| scoped row, unscoped embed | read a row that embeds related objects | every embedded object obeys the row's scope |
| aggregate over unscoped population | run a total/breakdown surface as subject A | aggregates agree with A's scoped rows |
| snippet or highlight leak | search returns excerpt text | excerpts contain only A-scoped content |
| suggestion list unscoped | autocomplete as subject A | every match is A-scoped |
| export/report wider than the UI | run the export path behind the same subject | export honours the same scope |
| list-then-fetch pair | IDs from a scoped list replayed on the detail route | both routes scoped, tested together |
| BOPLA read (V8.2.3) | read a privileged field | field absent from the response |
| BOPLA write (V8.2.3) | set a privileged field | field ignored or rejected |
| field rules on state | read/write while `status` is pending vs closed | field set differs per state, as documented |
| missing write controls | `POST`/`PUT`/`DELETE` unauthenticated | all methods guarded, not only `GET` |
| force browsing | privileged URL, no session, standard user | denial at the trusted layer |
| client-side only control (V8.3.1) | replay the request outside the browser | server denies; UI hiding proves nothing |
| header routing bypass | `X-Original-URL: /admin` or `X-Rewrite-URL` | denied; internal route not smuggled |
| IP spoofing bypass | `X-Forwarded-For: 127.0.0.1`, `X-Remote-IP` | denied; client headers untrusted |
| partial-URL filter bypass | URL encoding, `/..;/admin`, unanchored match | path normalized before route check |
| URL/internal-state tampering | edit parameter, state field, hidden field | server recomputes, never trusts |
| token tampering | edit claims, algorithm, expiry, subject | signature and claims verified |
| missing OAuth/API scope | token omitting required scope (e.g. `read:orders`) | `401`/`403` denial |
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

## Tiers

Unit tier: mock the subject object, set the role/session/claims, call
the function, assert the rejection — sstack's scratch-script model.
Functional access control belongs in the target's own unit and
integration suites, so the regression lands there, not in a scratch
file.

Integration tier: the enforcement point lives in middleware, filters,
or gateway config rather than the function under test. Read those
artifacts from source and test the decision functions in-process,
seeding real subjects and distinguishable objects as fixtures.
Behaviors decidable only at runtime — framework output escaping,
middleware ordering, live header handling — are checked N/As in
`map.md`: cite the artifact, note that source cannot decide it.

## Interaction with verification skill

Read the target's verification skill or feature map first. It usually
knows entities, ownership, roles, and auth flow. Attack the boundaries
between principals rather than re-deriving the ownership model. When
neither exists, derive the tuple from the surface's parameters (session,
user id, tenant id, role) and the call sites, and record it in `map.md`
before attacking. Where the target documents its grants, treat the
documentation as the oracle: a decision that contradicts the documented
rule is the finding.

## Failure modes to watch for

- Broken Object Level Authorization / IDOR (OWASP API1, CWE-639): accessing or mutating
  unowned objects by swapping identifiers without authorization checks.
- Broken Object Property Level Authorization / BOPLA (OWASP API3, CWE-915): reading
  or writing unauthorized fields via missing schema projection or mass assignment.
- Unscoped collection leakage: queries filtering on search criteria while omitting
  tenant or subject boundary constraints.
- Fail-open authorization policies (CWE-285): policy fall-through, unhandled exceptions,
  or missing deny-by-default rules permitting access.
- Intermediary route bypass: spoofing routing headers (`X-Original-URL`, `X-Forwarded-For`)
  to bypass reverse-proxy security controls.

## Language notes

### Python

- ORM queries: always filter queries by active session identifiers (`filter_by(user_id=session["user_id"])`),
  never fetching solely by raw entity id before authorization checks.
- Mass assignment: avoid initializing or updating domain models directly from raw request
  dictionaries (`Model(**request.json)`).

### JavaScript / TypeScript

- Object spread: avoid spreading unvalidated request payloads into ORM write operations
  (`prisma.user.update({ where: { id }, data: { ...req.body } })`).
- Collection queries: apply tenant-scoping middleware or repository-level where clauses.

### Java

- Method security: use `@PreAuthorize` with object ownership evaluations (`#order.userId == authentication.name`)
  rather than role-only gates (`@RolesAllowed("USER")`).
- Multi-tenancy: configure Hibernate/JPA tenant filters (`@FilterDef`, `@Filter`) on data access layers.

### C++

- Dispatch verification: validate security tokens and subject permissions before invoking
  service handlers; never trust unverified client headers.

## When not to apply

The surface has no principal, tenant, role, or account boundary and all
callers are trusted system-internal code with no user context. Pure
computation over data already scoped by its caller stays out of this
lens; its inputs belong to `malformed`, `missing`, and `boundaries`.
