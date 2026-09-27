# Security lens: what a `security` lens would own

Every claim below was read from the primary source named beside it. Where a
source does not say something, this file says so rather than filling the gap.
Research date: 2026-09-27. Linked from [`RESEARCH.md`](RESEARCH.md).

The `security` row in the lens index reads "injection, privilege escalation,
data exposure" and is unbuilt. This note exists to resolve the massive overlap
between this generic label and existing shipped lenses, and to determine whether
`security` can exist as an independent lens without cannibalizing `ownership`,
`malformed`, and `exceptional-conditions`.

## The overlap, settled

"Security" is the overarching domain of sstack, not a single failure class.
Several shipped lenses already own specific security categories:

| Security Threat Category | Shipped Owner | Primary OWASP / CWE |
|---|---|---|
| Broken Access Control / BOLA / IDOR | `ownership` | OWASP A01:2021 / A01:2025 |
| Privilege escalation / Tenant leakage | `ownership` | CWE-284, CWE-639 |
| Mass assignment / Property tampering | `ownership` | OWASP API3:2023 |
| Stack trace / Diagnostic data leak | `exceptional-conditions` | OWASP A10, CWE-209 |
| Unhandled parser exception crash | `malformed` | CWE-20, CWE-703 |
| Denial of Service / Memory blowout | `resource-exhaustion` | OWASP API4, CWE-400 |
| SQL / Command / Template Injection | `security` (Unbuilt) | OWASP A03, CWE-89, CWE-78 |
| Path Traversal / Arbitrary File Read | `security` (Unbuilt) | CWE-22 |
| Insecure Deserialization / Object Injection | `security` (Unbuilt) | OWASP A08, CWE-502 |
| Authentication / Token Forgery (JWT `alg: none`) | `security` (Unbuilt) | OWASP A07, CWE-347 |

If a `security` lens tests privilege escalation or data leakage, it duplicates
`ownership`. If it tests malformed strings crashing parsers, it duplicates
`malformed`.

To earn a place in the taxonomy, `security` must strictly own **Input Injection
(SQL, Command, Path Traversal, SSTI)** and **Integrity / Cryptographic Authentication
Flaws (JWT `alg: none`, Insecure Deserialization)**.

## What standards and specifications prove

### OWASP Top 10 (2021 & 2025): Injection and Integrity

1. **A03:2021 - Injection (CWE-89, CWE-78, CWE-77):**
   - Occurs when untrusted data is sent to an interpreter as part of a command
     or query (SQL, OS command, LDAP, XPath).
   - The attacker's hostile data tricks the interpreter into executing unintended
     commands or accessing unauthorized data.
2. **CWE-22: Improper Limitation of a Pathname to a Restricted Directory ('Path Traversal'):**
   - Using external input containing `../` or encoded traversal characters
     (`%2e%2e%2f`) to access arbitrary files on the filesystem.
3. **OWASP A08:2021 - Software and Data Integrity Failures (CWE-502):**
   - Insecure deserialization using untrusted object serialization (e.g., Python
     `pickle.loads`, Java `ObjectInputStream`, PHP `unserialize`, Ruby `Marshal.load`).
   - Allowing remote code execution by deserializing adversarial byte streams.
4. **RFC 7515 / RFC 7519: JSON Web Signature (JWS) and Tokens (JWT):**
   - RFC 7515 §4.1.1 defines the `"alg"` (Algorithm) header parameter.
   - When `"alg": "none"` is accepted by an unhardened validator, unsigned tokens
     bypass cryptographic verification (CWE-347).
   - RSA vs HMAC confusion: an RSA public key supplied to an HMAC verification
     routine allows attackers to sign valid tokens using the known public key.

## The observable oracle, checked at the source

Under negative security/injection attacks:

1. **Parameter Isolation / Safe Interpretation:**
   - SQL queries must use parameterized prepared statements (`SELECT * FROM users WHERE id = ?`).
   - OS execution must use array arguments (`subprocess.run(["cmd", arg])`) rather
     than shell string concatenation (`shell=True`).
   - Injection payloads (e.g., `' OR '1'='1`, `; rm -rf /`, `{{7*7}}`) must be
     treated as literal text data, returning empty results or literal strings,
     never altering query structure or executing commands.
2. **Path Traversal Sandboxing:**
   - File access resolving outside the root directory returns HTTP 400/403 or
     raises an explicit permission error; never returns contents of `/etc/passwd`
     or system files.
3. **Safe Serialization Formats:**
   - Application rejects unauthenticated binary serialization payloads, using
     safe formats (JSON, Protobuf) or cryptographic signatures before deserialization.
4. **Strict Cryptographic Algorithm Verification:**
   - JWT tokens with `"alg": "none"` or mismatched signature keys must be rejected
     with HTTP 401 Unauthorized immediately.

## What the lens should own

1. **SQL Injection Probing:** Supplying quote escapes, union selects, and boolean
   payloads to detect raw string interpolation.
2. **OS Command Injection:** Supplying shell metacharacters (`;`, `|`, `&&`, `` ` ``,
   `$(...)`) to endpoints that invoke external system binaries.
3. **Path Traversal Probing:** Supplying directory traversal sequences to file-reading
   or download routes.
4. **Token Signature Verification Bypass:** Supplying forged tokens with `"alg": "none"`.
5. **Insecure Deserialization:** Probing binary or pickled payload endpoints.

## Recommendation: Proceed with scoped lens

**Verdict: Recommended (Scoped to Injection & Cryptographic Integrity).**
While the label "security" is broad, the specific failure classes of Injection
(A03), Path Traversal (CWE-22), and Token Forgery (CWE-347) are not owned by
`ownership` (which owns authorization/access control) or `malformed` (which
owns grammar parsing). Shipping this lens fills the critical OWASP Injection
gap in sstack's negative testing catalog.

## Open questions

- Safety in automated runs: Negative tests for command injection must never run
  destructive shell payloads (e.g., `rm -rf`). Probes must use benign echo or
  sleep oracles (e.g., `echo "sstack_probe"`) to prove execution without risk
  to host workspaces.
