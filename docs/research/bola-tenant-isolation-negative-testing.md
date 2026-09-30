# Negative testing for BOLA / cross-tenant data leak (BOLA tenant isolation)



## Background: BOLA/LEIDOR negative test shapes in OWASP and the no-socket test rule

**BOLA**: OWASP API1 2023 (0xa1), CWE-639, "Authorization Bypass Through User-Controlled Key". Alternate terms: IDOR, Horizontal Authorization, "LEIDOR" when cross-tenant.

**Method scope rule (ADR-0015)**: A behavior is in scope iff the agent can confirm it by importing code and calling a function, with no listening socket; out-of-scope = requires a socket → recorded as a checked N/A.

### OWASP API Security Top 10 — API1:2023 BOLA risk page

OWASP API1:2023 provides the primary BOLA prevention rule: implement
authorization mechanisms that rely on user policies and check "the
user who is logged in has access to perform the requested action on
the record in **every function** that uses an input from the client to
access a record in the database"
([API1:2023](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/)).

- **Batch/List endpoint authorization applied to ALL elements** —
  *synthesis, not a direct quote*: no OWASP page explicitly says
  "validate every element of an array" (an OWASP "API Security Cheat
  Sheet" page by that name does not exist — the URL is 404). The
  requirement follows directly from API1:2023's every-function rule:
  each element of a client-supplied ID array is an input that accesses
  a record, so the ownership check must hold per element, not once per
  batch. The in-repo ownership lens already covers the sibling
  collection-scoping side ("unscoped collection leakage").
- **Rate limiting**: API1:2023's prevention notes do not prescribe it
  for BOLA; rate limiting maps to API4:2023 (Unrestricted Resource
  Consumption), a different risk page — do not cite it as BOLA guidance.

### OWASP Authorization Cheat Sheet (successor to Access Control)

Prescribes the canonical check sequence and key test oracles for BOLA/LEIDOR:

- Deny-by-default, validate permissions on every request.
- ABAC/ReBAC models: authorization decisions must consider subject, object, action, and contextual inputs (owner, tenant, role).
- **403 vs 404**: An origin server may respond with 404 to hide existence of a forbidden target resource. For negative testing, both 403 Forbidden and 404 Not Found qualify as passing denials, while 200 OK is the failure indicator.
- **Collection surfaces leak what object checks cannot catch**: A list/search endpoint must not return rows from another subject/tenant even if each row individually would be blocked by object-level checks.

### RFC 9111 §5.2.2.7 & RFC 9110 §15.5.5

- `no-store`/`private` cache-control semantics for tokens/subjects; replay after logout must be detectable.
- 404-or-403 distinction for existence hiding preserved in RFC 9110 §15.5.5.

### WSTG IDOR (ATHZ-04)

**Exact test method** ([WSTG-ATHZ-04, latest](https://wstg.owasp.org/latest/4-Web_Application_Security_Testing/05-Authorization/04-Insecure_Direct_Object_References/)): "map out all locations in the application where user input is used to reference objects directly … the tester should modify the value of the parameter used to reference objects and assess whether it is possible to retrieve objects belonging to other users or otherwise bypass authorization."

Oracle throughout: the other user's object must not be readable/writable. Needs ≥2 users with distinguishable objects.

### Cross-reference to existing A01 negative testing file

The prior `negative-testing-a01-broken-access-control.md` already covers BOLA in its "Horizontal (IDOR), 'Multi-User Replay'" row (lines 193-196) and tenant isolation (lines 201-204). We reuse those oracles and expand to the two new candidate rubric additions: (1) batch/list scope, (2) session/subject mismatch. We keep the same citation style and include all four families defined here.

## Four BOLA tenant-isolation negative test families

### 1. Cross-tenant ID manipulation (BOLA/LEIDOR)

**What it proves**: Object-level authorization is bypassed when a user-controlled key references another tenant’s object.

**No-socket classification**: In-scope code-observable (ADR-0015 lines 50-68). Object-fetching can be exercised by importing the resolver and calling it with swapped identifiers; no live HTTP required.

**Oracle shape**: Dual-user baseline-diff. Baseline A accesses Object-A → `200`. Baseline B (same role, different tenant) replays the same request with B’s object → response must differ (403/404), never `200`. For list endpoints, request a collection for subject A where A and B objects exist; any B object in the result is a confirmed leak.

**Generic Python worked example**:
```python
# Baseline: account belongs to caller
def get_account(session, account_id):
    return db.query("SELECT * FROM accounts WHERE id = ? AND owner = ?",
                    account_id, session["user_id"])

# Negative test: swap account_id across tenants (same user ID differs across tenants)
session_a = {"user_id": "user-1", "tenant": "tenant-a"}
session_b = {"user_id": "user-1", "tenant": "tenant-b"}

# Baseline call
resp_a = get_account(session_a, "acct-a-123")
assert resp_a.status_code == 200

# Cross-tenant swap using same user ID (different tenant isolation)
resp_a_over = get_account(session_a, "acct-b-456")
assert resp_a_over.status_code in (403, 404), "Cross-tenant IDOR leak"

# If the function instead filtered only by account_id without tenant check:
# resp_a_over would return 200 (finding)
```

**Generic TypeScript worked example**:
```typescript
// Baseline: account belongs to caller
async function getAccount(session: Session, accountId: string): Promise<Account | null> {
  const row = await db.accounts.findFirst({
    where: { id: accountId, ownerId: session.userId, tenantId: session.tenantId }
  });
  return row ?? null;
}

// Negative test: swap accountId across tenants (same user ID differs across tenants)
const sessionA = { userId: "user-1", tenantId: "tenant-a" };
const sessionB = { userId: "user-1", tenantId: "tenant-b" };

const baselineA = await getAccount(sessionA, "acct-a-123");
expect(baselineA).not.toBeNull();

const crossTenant = await getAccount(sessionA, "acct-b-456");
expect(crossTenant).toBeNull(); // Should be forbidden/not found

// If the function filters only by accountId (missing tenant):
// crossTenant would return an Account (finding)
```

**When not to apply**: When the surface has no principal, tenant, or account boundary and all callers are trusted system-internal code with no user context (see ownership lens "When not to apply").

### 2. Session/token-vs-argument mismatch (session replay-after-logout)

**What it proves**: The authorization decision relies on request-supplied subject/tenand arguments that can be mismatched with the authenticated session.

**No-socket classification**: In-scope if the check reads both token claims and function arguments and compares them in-process; out-of-scope if the comparison only happens in a live framework/middleware stack that cannot be exercised in-process (e.g., middleware ordering, live header rewriting). ADR-0015 lines 60-68 distinguish between source-decidable (in-scope) and runtime-only (out-of-scope).

**Oracle shape**: Session replay with tampered arguments. Log out (invalidate session), replay the same bearer token (if the system fails to invalidate) while swapping the tenant/subject arguments in the request; a successful response indicates a mismatch.

**Generic Python worked example**:
```python
# Hypothetical API that expects (tenant, account) in the path and session["user_id"]
def get_tenant_account(session, tenant_param, account_param):
    # Correct enforcement: session.user_id must match owner for tenant_param/account_param
    row = db.execute("""
        SELECT * FROM tenant_accounts ta
        JOIN accounts a ON a.id = ta.account_id
        WHERE ta.tenant_id = ? AND ta.account_id = ? AND a.owner = ?
    """, tenant_param, account_param, session["user_id"])
    return row

# Normal baseline: session from tenant-a owns account-a
session = {"user_id": "user-1", "tenant": "tenant-a"}
resp = get_tenant_account(session, "tenant-a", "account-a-123")
assert resp.status_code == 200

# Negative test 1: replay the same session but swap tenant argument (session.user_id != owner)
resp_swap_tenant = get_tenant_account(session, "tenant-b", "account-b-456")
assert resp_swap_tenant.status_code in (403, 404)

# Negative test 2: logout invalidates token; replay same bearer token (if system bugs)
# Simulated by calling function with session["valid"] = False
resp_replay = get_tenant_account({"user_id": "user-1", "valid": False}, "tenant-a", "account-a-123")
# In a correct implementation, `valid` check should prevent access.
```

**Generic TypeScript worked example**:
```typescript
// Hypothetical API that expects tenant/account in route and session.userId
async function getTenantAccount(session: Session, tenantParam: string, accountParam: string): Promise<Account | null> {
  const row = await db.$queryRaw<{ id: string }>`
    SELECT a.* FROM tenant_accounts ta
    JOIN accounts a ON a.id = ta.account_id
    WHERE ta.tenant_id = ${tenantParam}
      AND ta.account_id = ${accountParam}
      AND a.owner_id = ${session.userId}`;
  return row?.length ? row[0] : null;
}

// Baseline
const sessionA = { userId: "user-1", tenantId: "tenant-a" };
const baseline = await getTenantAccount(sessionA, "tenant-a", "account-a-123");
expect(baseline).not.toBeNull();

// Negative test: same user, different tenant argument
const crossTenant = await getTenantAccount(sessionA, "tenant-b", "account-b-456");
expect(crossTenant).toBeNull();

// Negative test: replay token after logout (session invalid)
const replay = await getTenantAccount({ userId: "user-1", valid: false }, "tenant-a", "account-a-123");
// Correct system would reject due to invalid session.
```

**When not to apply**: When the decision is made solely by a static role (e.g., role-based grant) and not by comparing dynamic subject vs object arguments.

### 3. Batch/array parameter pollution (list scope)

**What it proves**: Authorization on batch/list endpoints is applied only to the first element, leaving the rest of the returned set scope-violating.

**No-socket classification**: In-scope if the collection query can be exercised in-process by seeding fixtures and inspecting the result set; out-of-scope only if the query is behind a live server that cannot be exercised (rare). ADR-0015 lines 60-68 allow in-process testing of collection surfaces.

**Oracle shape**: Collection scope. Seed two subjects A and B with distinguishable records. Request a list/search as A; the result must contain only A’s rows. Any B row in the response (or in the count/facet total) is a confirmed leak.

**Generic Python worked example**:
```python
# Hypothetical batch get_invoices that filters only by query text, not by owner/tenant
def get_invoices(session, query=None):
    # Vulnerable: only query text, no tenant or owner filter
    where = []
    params = []
    if query:
        where.append("invoice_text LIKE ?")
        params.append(f"%{query}%")
    sql = f"SELECT * FROM invoices WHERE {' AND '.join(where)}"
    return db.execute(sql, *params)

# Setup: create records for A and B with distinguishable text
# Assume we can seed via test fixtures (in-scope)

# Baseline: query returns only A's records (if correct)
# Negative test: query text matches both A and B records; B rows leak
res = get_invoices({"user_id": "a", "tenant": "t-a"}, "important")
# If res contains any record with owner != a or tenant != t-a → finding
# A correct implementation would add owner/tenant filters to the WHERE clause.
```

**Generic TypeScript worked example**:
```typescript
// Hypothetical batch getInvoices that filters only by query text
async function getInvoices(session: Session, query?: string): Promise<Invoice[]> {
  let sql = `SELECT * FROM invoices`;
  const params: any[] = [];
  if (query) {
    sql += ` WHERE invoice_text LIKE ?`;
    params.push(`%${query}%`);
  }
  return db.query(sql, params);
}

// Setup: seed records for A and B via test fixtures (in-scope)

// Baseline: query returns only A's records
// Negative test: query matches both A and B rows
const results = await getInvoices({ userId: "a", tenantId: "t-a" }, "important");
// Finding: any row where ownerId !== "a" or tenantId !== "t-a" present
```

**When not to apply**: When the surface is a pure computation over data already scoped by its caller (e.g., a function that only processes owned data and has no user input).

### 4. Cache/header manipulation (cross-tenant cache confusion)

**What it proves**: Authorization decisions may be polluted by cached responses or manipulated request headers that bypass tenant/subject checks.

**No-socket classification**: In-scope if the cache keying can be exercised in-process (e.g., a memory cache that key prefixes only by path, not by tenant). Header manipulation that relies on live middleware routing or response header rewriting (e.g., `Access-Control-Allow-Origin`) is out-of-scope per ADR-0015 lines 65-68.

**Oracle shape**: Cache key includes tenant/subject. For in-scope caches, two requests with different subjects for the same logical object must produce distinct cached results (or eviction). If the same cached result is returned, it's a leak.

**Generic Python worked example** (simplified in-memory cache):
```python
from functools import lru_cache

# Vulnerable cache: key only by object id, not by tenant
@lru_cache(maxsize=128)
def get_cached_invoice(invoice_id):
    return db.get("SELECT * FROM invoices WHERE id = ?", invoice_id)

# Setup: invoice-123 belongs to tenant-a, invoice-456 to tenant-b

# Positive: cache per invoice id across subjects (bad)
caller_a = {"tenant": "tenant-a"}
caller_b = {"tenant": "tenant-b"}

# Both callers request same invoice id (but different tenant isolation expected)
# If the cache is shared without tenant scoping, both get the same row → finding
# A correct implementation would include tenant in the cache key.
```

**Generic TypeScript worked example** (simplified Map cache):
```typescript
const invoiceCache = new Map<string, Invoice>();

async function getInvoice(session: Session, invoiceId: string): Promise<Invoice | null> {
  const key = `inv:${invoiceId}`; // Vulnerable: no tenant in key
  if (invoiceCache.has(key)) {
    return invoiceCache.get(key)!;
  }
  const row = await db.invoices.findUnique({ where: { id: invoiceId } });
  invoiceCache.set(key, row);
  return row;
}

// Setup: invoice-123 belongs to tenant-a, invoice-456 to tenant-b

// Negative test: caller A and caller B requesting same invoice id (if they are isolated per tenant)
// If cache returns the same row regardless of session.tenantId → finding
```

**When not to apply**: When the cache key already incorporates subject/tenant/context, or when header manipulation involves live middleware routing (out-of-scope).

## Six-method synthesis (which families are code-decidable, which are not)

| Family | Code-decidable? | Reason (ADR-0015 citation) |
|--------|-----------------|----------------------------|
| Cross-tenant ID manipulation | Yes | Object-fetching can be exercised by importing code and calling a function (lines 50-53). |
| Session/token-vs-argument mismatch | Yes (if comparison is in code) / No (if only in live middleware) | In-scope if the check reads both token and function arguments in the same routine; out-of-scope if it lives in a live framework/middleware ordering or live header handling (lines 60-68). |
| Batch/array parameter pollution | Yes | Collection queries can be exercised in-process by seeding fixtures and inspecting result sets (lines 70-73). |
| Cache/header manipulation | Yes (if cache key is in code) / No (if live header rewriting) | In-scope if cache key includes tenant/subject in the same function; out-of-scope for live header handling (lines 65-68). |

## Gap mapping to existing ownership lens (skills/sstack-ownership/SKILL.md)

Reviewing the existing ownership lens failure classes and probes:

- **Unscoped collection leakage** (class 84, probe 94-97) matches Family 3 (list scope). The lens already requires collection surfaces to obey the oracle: result must contain only records the caller is entitled to see. This covers the batch/array pollution gap.
- **Cross-tenant write** (class 195, probe cross-tenant) matches Family 1 (cross-tenant ID manipulation). The lens already requires cross-tenant enumeration to return denials, not records.
- **Token tampering / stale grant / logout not invalidating** (classes 190-193) partially cover Family 2 (session/token-vs-argument mismatch) but focus on token validation, not on argument vs session mismatch. The existing lens does not explicitly require checking that request-supplied subject/tenand arguments match the authenticated session. This is the **second candidate addition**.
- **Header routing bypass** (class 186) matches Family 4 (header manipulation) when in-scope (header routing bypass is in-scope; live header rewriting is out-of-scope). The lens already tests `X-Original-URL` and `X-Rewrite-URL`.

**Missing additions**: 
1. **Batch/List endpoint authorization applied to ALL elements** – covered by "Unscoped collection leakage" but the lens's probe focuses on wildcard/empty queries and include/expand parameters. It does not explicitly require that each element in a returned batch respects object-level authorization. (No OWASP page states this explicitly; it follows from API1:2023's every-function rule — see the synthesis note above.)
2. **Session-derived subject vs request-supplied tenant/subject argument mismatch** – not covered. The lens has token tampering and stale grant but not the case where the authenticated subject (session) is compared against request-supplied tenant/subject arguments (e.g., path or query parameters). The two candidate additions map directly to these.

## Primary sources list

All sources accessed 2026-09-30 (unless otherwise noted):

1. OWASP API Security Top 10, API1:2023 Broken Object Level Authorization (risk page, not a cheat sheet): https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/
2. OWASP Authorization Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
3. WSTG IDOR testing (WSTG-ATHZ-04, latest): https://wstg.owasp.org/latest/4-Web_Application_Security_Testing/05-Authorization/04-Insecure_Direct_Object_References/
4. MITRE CWE-639 (Authorization Bypass Through User-Controlled Key): https://cwe.mitre.org/data/definitions/639.html
5. RFC 9111 §5.2.2.7 (cache-control semantics): https://www.rfc-editor.org/rfc/rfc9111.html — RFC 9110 §15.5.5 (404 vs 403 existence hiding): https://www.rfc-editor.org/rfc/rfc9110.html#section-15.5.5
6. Existing negative-testing-a01-broken-access-control.md (repository)
7. Ownership lens SKILL.md (repository)
8. ADR-0015 no-socket table (repository)

Rejected during verification (listed so nobody re-discovers them): an
"OWASP API Security Cheat Sheet" at cheatsheetseries.owasp.org does not
exist (404); a GitHub raw path for the WSTG chapter also 404s — the
canonical WSTG URL above is the live source; the OWASP IDOR Prevention
Cheat Sheet exists (200) but contains no batch/array guidance.

