# Negative Testing: Security Lens

Research on negative testing for injection vulnerabilities (SQLi, OS Command Injection, SSTI), path traversal, cryptographic token tampering (JWT alg: none), and insecure deserialization invariants.

## Overview & Definition

Negative testing for the security lens evaluates how software behaves when presented with hostile payloads designed to exploit interpreter boundaries, escape filesystem sandboxes, forge cryptographic authentication tokens, or execute arbitrary code via insecure object deserialization.

While `ownership` attacks authorization logic (BOLA/IDOR/BOPLA) and `malformed` attacks syntax parsers, the security lens attacks data-to-code boundary confusion. A resilient system must parameterize all queries and subcommands, strictly canonicalize and constrain filesystem paths, verify cryptographic signatures using explicit allowed-algorithm sets, and reject untrusted binary serialization streams.

## Core Concepts & Failure Modes

1. **SQL Injection (OWASP A03 / CWE-89):**
   - Interpolating unescaped external strings directly into SQL queries (`f"SELECT * FROM users WHERE name = '{name}'"`).
   - Attackers injecting syntax (`' OR '1'='1' --`) to bypass authentication or extract entire database tables.
2. **OS Command Injection (CWE-78):**
   - Passing user-controlled arguments to a system shell (`subprocess.run(f"ping {ip}", shell=True)` or `system("convert " + file)`).
   - Attackers injecting shell metacharacters (`;`, `|`, `&&`, `$()`) to execute arbitrary host commands with application privileges.
3. **Path Traversal & Arbitrary File Access (CWE-22):**
   - Using external input to locate files without path canonicalization (`open(f"/var/data/{user_path}")`).
   - Attackers supplying `../../../../etc/passwd` or encoded variants (`%2e%2e%2f`) to read sensitive host files or overwrite executable binaries.
4. **Cryptographic Token Forgery (CWE-347 / RFC 7515):**
   - Accepting JSON Web Tokens (JWT) with `"alg": "none"` without verifying cryptographic signatures.
   - Algorithm confusion: Verifying an RSA token using HMAC-SHA256 with the server's public key as the secret.
5. **Insecure Deserialization (OWASP A08 / CWE-502):**
   - Deserializing untrusted byte streams using native object serializers (Python `pickle`, Java `ObjectInputStream`, PHP `unserialize`).
   - Attackers crafting malicious serialized payloads that execute arbitrary code upon instantiation (`__reduce__` in Python).
6. **Server-Side Template Injection (SSTI / CWE-1336):**
   - Rendering user input directly as template code (Jinja2, Twig, ERB) rather than passing it as a template context variable.

## Real-World Examples & Test Scenarios

### Scenario 1: SQL Injection via Query Parameter
- **Contract:** Endpoint `GET /api/v1/search?q=<query>` searches public articles.
- **Negative Inputs:**
  - Query parameter: `q=' UNION SELECT id, username, password_hash, '1' FROM users --`.
- **Expected Oracle:** The application executes a parameterized query where the entire string is treated as a literal search term. Returns HTTP 200 with 0 search matches (or searches for the literal string), never returning database error strings or user credentials.

### Scenario 2: OS Command Injection in Utility Script
- **Contract:** Diagnostic endpoint `POST /tools/ping` takes `{"host": "example.com"}` and checks reachability.
- **Negative Inputs:**
  - Body: `{"host": "127.0.0.1; echo 'SSTACK_EXPLOIT_VERIFIED'"}`.
- **Expected Oracle:** Host validator rejects the input with HTTP 400 Bad Request (`{"error": "invalid_hostname"}`), or executes using non-shell array args (`["ping", "-c", "1", "127.0.0.1; echo..."]`) which fails safely as an unknown host. The payload string is never executed by `/bin/sh`.

### Scenario 3: Path Traversal in Document Download
- **Contract:** Endpoint `GET /download?file=<filename>` serves files from `/var/www/uploads/`.
- **Negative Inputs:**
  - `GET /download?file=../../../../etc/passwd`.
  - `GET /download?file=%2e%2e%2f%2e%2e%2fetc%2fpasswd`.
- **Expected Oracle:** Path is canonicalized and verified to reside strictly within `/var/www/uploads/`. Requests resolving outside return HTTP 403 Forbidden or 400 Bad Request. System files are never returned.

### Scenario 4: JWT Signature Bypass with "alg": "none"
- **Contract:** Endpoint `GET /api/v1/admin` requires valid administrator JWT.
- **Negative Inputs:**
  - Client sends unsigned JWT with header `{"alg": "none", "typ": "JWT"}` and payload `{"user": "admin", "is_admin": true}`.
- **Expected Oracle:** HTTP 401 Unauthorized (`{"error": "invalid_token_algorithm"}`). System strictly rejects tokens specifying the "none" algorithm or missing a valid signature.

### Scenario 5: Insecure Deserialization of Session State
- **Contract:** Session cookie or payload stores client state.
- **Negative Inputs:**
  - Request sends serialized Python `pickle` payload designed to instantiate a reverse shell or write a probe file.
- **Expected Oracle:** Application rejects binary serialization, parsing strictly with JSON parser, or validates HMAC signature prior to deserialization. Returns HTTP 400/401; no arbitrary code executes.

## Key Oracle Patterns

- **Literal Parameter Interpretation:** Interpreter boundaries (SQL, Shell, Templates) treat hostile inputs strictly as literal string values, never altering code or query structure.
- **Strict Path Canonicalization:** Path operations verify that `os.path.realpath(target).startswith(base_dir)` before opening files.
- **Explicit Allowed-Algorithm Whitelists:** Cryptographic validators whitelist accepted algorithms (`["RS256"]`), rejecting `"none"`, `"HS256"` (when expecting RSA), or empty algorithm fields.
- **Zero Unhandled Interpreter Exceptions:** Database syntax errors (`sqlite3.OperationalError`, `psycopg2.errors.SyntaxError`) and shell errors are caught and masked at the boundary.

## Primary Sources & References

- OWASP Top 10 (2021 & 2025): A03: Injection, A02: Cryptographic Failures, A07: Identification and Authentication Failures, A08: Software and Data Integrity Failures
- CWE-89: Improper Neutralization of Special Elements used in an SQL Command ('SQL Injection')
- CWE-78: Improper Neutralization of Special Elements used in an OS Command ('OS Command Injection')
- CWE-22: Improper Limitation of a Pathname to a Restricted Directory ('Path Traversal')
- CWE-502: Deserialization of Untrusted Data
- CWE-347: Improper Verification of Cryptographic Signature
- RFC 7515: JSON Web Signature (JWS) §4.1.1 (Algorithm "none" security considerations)
- RFC 7519: JSON Web Token (JWT)
