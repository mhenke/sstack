# Negative testing for A01:2025 Broken Access Control

Saved to `docs/research/negative-testing-a01-broken-access-control.md`. Should be
indexed in [`RESEARCH.md`](RESEARCH.md) (not edited here).

Primary sources only: [OWASP Top 10](https://owasp.org/Top10/) 2025/2021, [OWASP WSTG](https://owasp.org/www-project-web-security-testing-guide/) (latest),
[OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/), [MITRE CWE](https://cwe.mitre.org/), [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110), [ZAP](https://www.zaproxy.org/) first-party docs.
All accessed 2026-09-26; each citation carries that date.

## A01:2025 in one pass

- A01:2025 stays #1; "100% of the applications tested were found to have
  some form of broken access control". 40 mapped CWEs, 1,839,701
  occurrences, 32,654 CVEs. ([A01:2025](https://top10.owasp.org/2025/A01_2025-Broken_Access_Control/index.html),
  accessed 2026-09-26)
- The failure modes it enumerates are already negative-test shapes:
  deny-by-default violations, bypassing checks by URL/state/HTML
  tampering or tool-modified API requests, IDOR, missing API controls on
  POST/PUT/DELETE, elevation of privilege, JWT/cookie/hidden-field
  metadata manipulation, CORS misconfiguration, force browsing
  ("guessing URLs") to authenticated or privileged pages as the wrong
  principal. ([A01:2025](https://top10.owasp.org/2025/A01_2025-Broken_Access_Control/index.html),
  accessed 2026-09-26)
- Detection guidance on the page is thin and indirect: deny by default;
  log access control failures and alert on repeats; rate-limit API and
  controller access; "Developers and QA staff should include functional
  access control in their unit and integration tests." No HTTP status
  codes prescribed — A01 is a risk list, not a test oracle. The oracles
  live in WSTG, the cheat sheets, and RFC 9110. ([A01:2025](https://top10.owasp.org/2025/A01_2025-Broken_Access_Control/index.html),
  accessed 2026-09-26)
- Scenario #3 is new in 2025: access control living only in the
  front-end — the page is unreachable via browser JS but
  `curl https://example.com/app/admin_getappInfo` still returns it. The
  negative test is "issue the request outside the UI". ([A01:2025](https://top10.owasp.org/2025/A01_2025-Broken_Access_Control/index.html),
  accessed 2026-09-26)
- Scenario #1 (mutate `acct=` account number) and #2 (force-browse
  `admin_getappInfo` as unauthenticated / non-admin; "If an
  unauthenticated user can access either page, it's a flaw") are
  unchanged from 2021. ([A01:2025](https://top10.owasp.org/2025/A01_2025-Broken_Access_Control/index.html),
  accessed 2026-09-26; [A01:2021](https://top10.owasp.org/2021/A01_2021-Broken_Access_Control/index.html),
  accessed 2026-09-26)

## A01:2025 vs A01:2021

Diff of the two official pages (both links above, accessed 2026-09-26):

- CWE mapping: 34 → 40.
  - Added: CWE-36, 61, 65, 281, 282, 283, 379, 424, 615, 732, 749, and
    918 (SSRF folded into A01).
  - Removed: CWE-35, 264, 275, 651, 706, 913.
  - Kept across both: CWE-862, 863, 639, 425, 284, 285, 864 … (full
    lists on the two mapping pages).
- Notable-CWE callout: 2021 cited CWE-200, 201, 352; 2025 adds CWE-918
  SSRF alongside 200/201/352.
- Description: bullet list essentially unchanged; force browsing gains
  the parenthetical "(guessing URLs)"; elevation-of-privilege reworded
  to "gaining privileges beyond those expected of the logged in user".
- Prevention: new bullet "Use well-established toolkits or patterns that
  provide simple, declarative access controls"; JWT guidance now says
  consider refresh tokens plus OAuth revocation.
- Scenario #3 (front-end-only access control, curl bypass) added.
- References: ASVS link moves from "V4 Access Control" to "V8
  Authorization"; WSTG and Authorization Cheat Sheet links unchanged.
- Stats: 100% of apps affected (2025) vs "94% of applications were
  tested for some form of broken access control" (2021); occurrences
  318,487 → 1,839,701.

Both pages' WSTG reference points at
[05-Authorization_Testing](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/05-Authorization_Testing/README)
(accessed 2026-09-26), whose current live content is the wstg.owasp.org
"latest" build cited below.

## What the WSTG prescribes (the negative tests)

Section 4.5 "Authorization" holds four testable pages: 4.5.1 Directory
Traversal File Include, 4.5.2 Bypassing Authorization Schema
(WSTG-ATHZ-02), 4.5.3 Privilege Escalation (WSTG-ATHZ-03), 4.5.4 IDOR
(WSTG-ATHZ-04); plus 4.5.5 OAuth Weaknesses. API counterparts: WSTG-APIT-02
Broken Object Level Authorization, WSTG-APIT-04 Broken Function Level
Authorization. ([WSTG contents](https://wstg.owasp.org/latest/),
accessed 2026-09-26)

### WSTG-ATHZ-02 Bypassing Authorization Schema

Test objective: "Assess if unauthenticated, horizontal, or vertical
access is possible."
([ATHZ-02](https://wstg.owasp.org/latest/4-Web_Application_Security_Testing/05-Authorization/02-Bypassing_Authorization_Schema),
accessed 2026-09-26)

- Unauthenticated / forced browsing: request a protected page directly
  (address bar, or ffuf/gobuster/ZAP/Burp Intruder). Oracle: anonymous
  request must not return the protected resource.
- Horizontal procedure: two users, identical privileges, two live
  sessions; "For every request, change the relevant parameters and the
  session identifier from token one to token two". "An application will
  be considered vulnerable if the responses are the same, contain same
  private data or indicate successful operation on other users'
  resource or data." Baseline-diff oracle: victim gets `200`, other-user
  identity must differ; anonymous must get `401` (the page's worked
  `gori` run flags BYPASS when other-user matches the baseline 200 and
  prints `anonymous … 401` as correct).
  ([ATHZ-02](https://wstg.owasp.org/latest/4-Web_Application_Security_Testing/05-Authorization/02-Bypassing_Authorization_Schema),
  accessed 2026-09-26)
- Vertical: POST `/admin/addUser` as a non-admin — "What happens if a
  non-administrative user tries to execute that request? Will the user
  be created?" Same page, accessed 2026-09-26.
- Header bypass probes: send `X-Original-URL: /donotexist1` /
  `X-Rewrite-URL: /donotexist2`; "If the response … contains markers
  that the resource was not found … 404, or a 'resource not found'
  message", the header is honored and can be used to smuggle the real
  target URL past a URL-based front-end check. Also spoof
  `X-Forwarded-For`, `X-Remote-IP`, `X-Client-IP`, etc. with
  `127.0.0.1`/RFC1918 values. Same page, accessed 2026-09-26.

### WSTG-ATHZ-03 Privilege Escalation

Objectives: "Identify injection points related to privilege
manipulation. Fuzz or otherwise attempt to bypass security measures."
([ATHZ-03](https://wstg.owasp.org/latest/4-Web_Application_Security_Testing/05-Authorization/03-Privilege_Escalation),
accessed 2026-09-26)

- Mutate privilege-bearing parameters: `groupID`/`orderID` in
  `POST /user/viewOrder.jsp`; hidden HTML field
  `profile=SysAdmin` → set to another value; condition values
  (`PVValid` `-1`→`0`); `X-Forwarded-For` for IP-gated paths. Same
  page, accessed 2026-09-26.
- Vertical procedure: two sessions, different roles; per request swap
  the session identifier and evaluate responses. "An application will
  be considered vulnerable if the weaker privileged session contains
  the same data, or indicate successful operations on higher privileged
  functions." Worked oracle: admin `POST /account/deleteEvent` returns
  `200 {"message": "Event was deleted"}`; replaying it with
  `CUSTOMER_USER_SESSION` and the same response ⇒ vulnerable. Also:
  "developers perform authorization validation at the GUI level only"
  — any non-admin role reaching the admin menu is a finding. Same
  page, accessed 2026-09-26.
- White-box note: partial-URL checks (`startswith`, `contains`,
  `indexOf`) can be worked around with URL encoding. Same page,
  accessed 2026-09-26.

### WSTG-ATHZ-04 IDOR

"Map all locations where user input is used to reference objects
directly … modify the value of the parameter … and assess whether it is
possible to retrieve objects belonging to other users." Needs ≥2 users
holding different objects (and, if relevant, different privileges) so
you don't guess IDs. Four canonical mutation shapes: `?invoice=12345`
(DB record), `changepassword?user=someuser` (operation target),
`showImage?img=` (file), `accessPage?menuitem=12` (function via menu
id). Some references span multiple parameters. Oracle throughout: the
other user's object must not be readable/writable. ([ATHZ-04](https://wstg.owasp.org/latest/4-Web_Application_Security_Testing/05-Authorization/04-Insecure_Direct_Object_References),
accessed 2026-09-26)

### WSTG-APIT-04 Broken Function Level Authorization (missing function-level checks)

- Log in as a low-privilege user, hit admin endpoints
  (`POST /api/admin/deleteUser`, `GET /api/admin/getAllUsers`,
  `POST /api/admin/promoteUser`, `DELETE /api/admin/deleteUser/12345`),
  and repeat each resource with alternate HTTP methods (undocumented
  `PUT`/`DELETE`/`PATCH`) recording "any difference in response
  behavior or authorization outcome". GraphQL: `mutation {
  deleteUser(id: "12345") … }` as a low-priv user.
- Indicators: "Properly secured APIs in general would return `403
  Forbidden` or `401 Unauthorized` when invoked restricted functions
  instead of a `200 OK` response"; inconsistent enforcement across
  endpoints is itself a signal. ([WSTG-APIT-04](https://wstg.owasp.org/latest/4-Web_Application_Security_Testing/12-API_Testing/04-API_Broken_Function_Level_Authorization),
  accessed 2026-09-26)

## OWASP cheat-sheet test rows and oracles

The Access Control Cheat Sheet is deprecated; the Authorization Cheat
Sheet is its successor. ([Access Control Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Access_Control_Cheat_Sheet.html),
accessed 2026-09-26)

**Authorization Cheat Sheet** — relevant prescriptions: deny by default;
validate permissions on every request; enforce checks on static
resources; checks must be server-side, not client-side; fail safely on
denied checks; "Create Unit and Integration Test Cases for Authorization
Logic" (is access denied by default? do failures terminate safely? are
ABAC policies enforced?). On IDOR: mutating `acct_id` must fail because
of an access-control check, not merely because the record is missing —
a real oracle distinction. Its lookup-ID example:
`https://mybank.com/accountTransactions?acct_id=901` → change to
another id and expect denial. ([Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html),
accessed 2026-09-26)

**Authorization Regression Testing Cheat Sheet** — the most explicit
negative-test table OWASP publishes:

- Matrix row shape (machine-readable fixture):
  `resource / method / allowed_roles / denied_roles /
  expected_denial_code: 403`.
- Horizontal (IDOR), "Multi-User Replay": A creates resource X; B
  (same role) reads/updates/deletes X. "The system must return a `403
  Forbidden` or `404 Not Found` (to avoid information leakage about
  resource existence), never a `200 OK`."
- Vertical, "Role Demotion Check": iterate every non-admin role
  (including unauthenticated) against admin endpoints; endpoints must
  explicitly reject — "Relying on UI hiding is insufficient; the API
  layer must enforce the check."
- Tenant isolation, "Cross-Tenant Boundary Test": seed Tenant Alpha,
  query broadly as Tenant Beta; "Assert that the response payload
  contains absolutely no records belonging to Tenant Alpha. Even a
  single leaked record identifier constitutes a critical failure."
- Contract-driven: if OpenAPI says an operation needs scope
  `read:invoices`, "tokens lacking this scope receive a `401
  Unauthorized` or `403 Forbidden` response"; Schemathesis/Dredd
  auto-generate the negative cases (no token, expired token, missing
  scope).
- CI note: flag unusual volumes of 401/403 during integration testing —
  they can mean functional changes collided with security controls.
  ([Authorization Regression Testing Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Regression_Testing_Cheat_Sheet.html),
  accessed 2026-09-26)

**Authorization Testing Automation Cheat Sheet** — XML authorization
matrix where each service declares
`http-response-code-for-access-allowed="200"` and
`http-response-code-for-access-denied="403"` per role
(ANONYMOUS/BASIC/ADMIN); one JUnit test per "Point Of View" calls every
service and fails on three states: allowed-code returned to a denied
role, denied-code returned to an allowed role, or any unexpected code.
Failure text: "The service 'DeleteMessage' when called with POV
'ANONYMOUS' return a response code 200 that is not the expected one
(403 expected)." ([Authorization Testing Automation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Testing_Automation_Cheat_Sheet.html),
accessed 2026-09-26)

## HTTP status oracles (RFC 9110)

- `401 Unauthorized`: request "has not been applied because it lacks
  valid authentication credentials for the target resource"; with
  credentials provided, 401 "indicates that authorization has been
  refused for those credentials". (RFC 9110 §15.5.2,
  [link](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.5.2),
  accessed 2026-09-26)
- `403 Forbidden`: "the server understood the request but refuses to
  fulfill it"; if credentials were provided they are "insufficient to
  grant access"; and "An origin server that wishes to 'hide' the
  current existence of a forbidden target resource MAY instead respond
  with a status code of 404". This is why 403-or-404 both qualify as a
  passing denial while 200 does not. (RFC 9110 §15.5.4,
  [link](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.5.4),
  accessed 2026-09-26)
- "A server that receives valid credentials that are not adequate to
  gain access ought to respond with the 403 (Forbidden) status code."
  (RFC 9110 §11.4,
  [link](https://www.rfc-editor.org/rfc/rfc9110.html#section-11.4),
  accessed 2026-09-26)
- RFC 9110 defines no application-authorization policy of its own; it
  only owns these response semantics. (RFC 9110 §11 "HTTP
  Authentication", [link](https://www.rfc-editor.org/rfc/rfc9110.html#section-11),
  accessed 2026-09-26)

## Mapped CWEs that are the negative-test targets

Titles for all 40 are on the A01:2025 mapping list (link above,
accessed 2026-09-26). The load-bearing ones, quoted from MITRE
(all accessed 2026-09-26):

- [CWE-862 Missing Authorization](https://cwe.mitre.org/data/definitions/862.html):
  "The product does not perform an authorization check when an actor
  attempts to access a resource or perform an action." Its notes define
  authorization as "determining whether that user can access a given
  resource, based on the user's privileges". Detection notes: automated
  dynamic analysis "may find many or all possible interfaces that do
  not require authorization, but manual analysis is required to
  determine if the lack of authorization violates business logic."
- [CWE-639 Authorization Bypass Through User-Controlled Key](https://cwe.mitre.org/data/definitions/639.html):
  "does not prevent one user from gaining access to another user's data
  or record by modifying the key value identifying the data."
  Alternate terms listed: IDOR, BOLA, Horizontal Authorization. Common
  consequences name horizontal escalation always, vertical escalation
  "if the user-controlled key is actually a flag that indicates
  administrator status".
- [CWE-425 Direct Request ('Forced Browsing')](https://cwe.mitre.org/data/definitions/425.html):
  "The web application does not adequately enforce appropriate
  authorization on all restricted URLs, scripts, or files." Mitigation:
  "Apply appropriate access control authorizations for each access to
  all restricted URLs, scripts or files."
- CWE-863 Incorrect Authorization is the sibling class (CWE-639's
  parent); both are in A01's 2021 and 2025 maps. (A01:2025 mapping
  list, link above, accessed 2026-09-26)

## First-party tool docs

- ZAP "Access Control Testing" add-on: define Access Rules per user per
  site node — Allowed / Denied / Unknown — then "an 'attack' is
  performed by ZAP by trying to access every URL of the web-app from
  the perspective of every user"; results mark "the cases where the
  access rules where not followed." Alerts: 10101 Improper
  Authentication, 10102 Improper Authorization. The oracle is
  rule-vs-observed access, not a fixed status code. ([ZAP Access
  Control Testing](https://www.zaproxy.org/docs/desktop/addons/access-control-testing/),
  accessed 2026-09-26)
- The WSTG tool lists for ATHZ-02 name ZAP's Access Control Testing
  add-on, Burp Intruder, AuthMatrix, Autorize, and `gori` as the
  automation for replay-across-identities. ([ATHZ-02](https://wstg.owasp.org/latest/4-Web_Application_Security_Testing/05-Authorization/02-Bypassing_Authorization_Schema),
  accessed 2026-09-26)

## Synthesis for an access-control lens (sstack interpretation)

Not a source claim — how the above lands in this repo's format:

1. Negative-test canonical set, all primary-sourced: forced browsing
   (anonymous → deny), horizontal replay (peer identity → 403/404
   never 200), vertical role demotion (low-priv → deny admin
   function), IDOR id mutation (foreign key → deny, and deny must be
   authz-based not 404-by-accident), function-level/method tampering
   (undocumented verb or admin route → 401/403 not 200), tenant
   isolation (zero foreign records), header/parameter privilege
   smuggling (X-Original-URL, X-Forwarded-For, `role=`/`profile=`).
2. Oracle wording: expect 401 (no/bad credentials), 403 or 404
   (authenticated-but-denied; 404 allowed per RFC 9110 §15.5.4 to hide
   existence), redirect-to-login for browser flows; any 2xx on a
   denied-row is the finding. A "same response as baseline" diff
   (WSTG-ATHZ-02) is the cheapest generic oracle.
3. A01:2025 adds nothing to test mechanics — its delta vs 2021 is
   mapping breadth (SSRF, permission/ownership CWEs) plus the
   front-end-only-access-control scenario, which is itself a negative
   test (curl the admin URL).
