---
name: sstack-security
description: "Security lens rubric. Case-generation heuristics, oracle patterns, and worked examples for SQL injection, OS command execution, path traversal, JWT token tampering, and insecure deserialization. Loaded inline under ### Lens rubric."
disable-model-invocation: true
---

# Security lens

Attacks every mapped surface through the security lens: that an
application must protect interpreter and execution boundaries from
data-as-code confusion, sanitize inputs to external shells and SQL
engines, enforce filesystem containment boundaries, and reject forged
or unverified cryptographic authentication tokens.

## Case-generation heuristics

- SQL injection (OWASP A03 / CWE-89): supply string inputs containing SQL
  syntax metacharacters (`' OR '1'='1' --`, `'; DROP TABLE...`, `UNION SELECT`)
  to endpoints and functions constructing database queries.
- OS command injection (CWE-78): supply arguments containing shell metacharacters
  (`;`, `|`, `&&`, `$()`, `` ` ``, `\n`) to functions invoking subprocesses or
  operating system commands.
- Path traversal & sandbox escaping (CWE-22): supply paths containing directory
  traversal sequences (`../`, `..\`, `%2e%2e%2f`, absolute root paths `/etc/passwd`)
  to functions resolving, reading, or writing filesystem paths.
- Cryptographic token tampering (CWE-347 / RFC 7515): supply JWTs with
  `"alg": "none"`, stripped signatures, or cross-algorithm RSA-to-HMAC
  substitutions to authentication boundaries.
- Insecure deserialization (OWASP A08 / CWE-502): supply untrusted serialized
  byte streams (Python `pickle`, Java `ObjectInputStream`) to functions parsing
  object representations.
- Server-side template injection (SSTI / CWE-1336): supply template expression
  payloads (`{{7*7}}`, `${7*7}`) into user-facing text fields.

## Oracle patterns

- Parameterized interpreter execution: queries and commands execute with
  untrusted inputs strictly bound as literal parameters, never evaluating
  injected syntax as executable instructions.
- Strict path containment: resolved filesystem paths must be canonicalized
  and verified to reside strictly within the designated parent directory
  boundary; attempts to escape trigger immediate `PermissionError` or HTTP 403.
- Signature verification enforcement: authentication tokens lacking valid
  cryptographic signatures or specifying `"alg": "none"` are rejected with
  HTTP 401 Unauthorized.
- Safe serialization: untrusted inputs are deserialized using safe, data-only
  parsers (e.g. JSON), never executing native object instantiation hooks.

Worked example — Python `BackupRunner` building a shell command for a
tar archive from a caller-supplied `label`: case `label = "daily; rm -rf /"`,
oracle passes the argument as a list element to `subprocess.run` with
`shell=False`, so the semicolon is data and the archive label contains it
verbatim, observed (bug) interpolates it into an f-string passed to
`shell=True`, and the second command runs.

TypeScript `DocumentSearchService` executing database query: case query
term contains `' UNION SELECT id, token, '1' FROM api_keys --`, oracle
uses parameterized query binding parameter `$1`, returning zero matching
documents, observed (bug) executes raw interpolated SQL and returns leaked
API keys in search results.

## Failure modes to watch for

- SQL injection (CWE-89): string formatting or interpolation in database calls.
- OS command injection (CWE-78): `shell=True` in subprocess calls or shell
  string concatenation.
- Path traversal (CWE-22): `os.path.join` without `os.path.commonpath` or
  boundary validation (note: `os.path.join('/base', '/etc/passwd')` ignores `/base`).
- Cryptographic signature bypass (CWE-347): unverified JWT header algorithms.
- Unsafe object deserialization (CWE-502): `pickle.loads` on external data.

## Language notes

### Python

- Path containment: always use `os.path.commonpath([base_dir, resolved_path]) == base_dir`
  to verify containment; `os.path.join` treats leading slashes in arguments as root.
- Subprocesses: pass arguments as list of strings (`["ls", "-l", path]`) with
  `shell=False` (default); never use `f"cmd {user_arg}"` with `shell=True`.
- SQLite / DB-API: use parameter markers `?` or `%s` with query parameter tuples.

### JavaScript / TypeScript

- Path containment: use `path.resolve` and check `resolved.startsWith(baseDir + path.sep)`.
- Command execution: use `child_process.execFile` or `child_process.spawn` with argument
  arrays instead of `child_process.exec`.
- SQL: use parameterized tagged template literals or query builder bindings.

### Java

- Path validation: use `Path.normalize()` and `Path.startsWith(baseDir)`.
- SQL: use `PreparedStatement` with bind variables, never string concatenation.

### C++

- Paths: use `std::filesystem::canonical` and check `lexically_relative`.
- Process execution: use `execv` / `execve` with argument vectors, avoiding `system()`.

## When not to apply

The surface performs pure in-memory computations on numeric or enum inputs,
makes no database queries, touches no filesystem paths, spawns no subprocesses,
and processes no authentication tokens or serialized streams.
