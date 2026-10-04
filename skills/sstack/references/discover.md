# Discover — parallel role-based exploration and deterministic caller tracing

Discover loads this reference when inventorying multi-surface,
multi-module, or layered targets. A single sequential scan over large
targets risks context exhaustion and misses caller integration seams.
This workflow structures Discover into four specialized exploration roles
and validates caller reachability using local deterministic AST inspection
(no vector store, no external daemon).

## 1. Parallel Role-Based Explorers

For targets with multiple files or layers, dispatch four exploration
subagents concurrently. Each starts blank; paste the target path,
supported languages, and `.sstack/learn/` classes:

- **Role 1 — Gateways & Auth**: Route handlers, controller actions,
  middlewares, session checks, role/permission gates (`ownership`,
  `security` lenses). Identifies where untrusted input enters and how
  identity or tenant context is verified.
- **Role 2 — Data Models & State**: Entities, schemas, storage mutations,
  caches, state accumulators (`state`, `concurrency`, `idempotency`).
  Identifies object lifetime, shared state, and partial-write risks.
- **Role 3 — Entry Points & Parsers**: Parameter parsers, decoders,
  formatters, validators, serializers (`boundaries`, `malformed`,
  `missing`, `contract`). Identifies domain constraints, range limits,
  and type-coercion traps.
- **Role 4 — External Boundaries**: Downstream clients, network calls,
  DB connectors, thread/connection pools (`dependency-failure`,
  `resource-exhaustion`, `exceptional-conditions`). Identifies timeouts,
  fail-open paths, and resource limits.

Dispatch fallback: subagents that fail or go silent twice transfer to
you — run the four roles serially.

## 2. Deterministic Caller & Edge Tracing (No Vector Store)

Vector stores hallucinate relevance and miss exact call paths. Ground
reachability and caller seams deterministically using target runtime
standard libraries (Python `ast`, Node stdlib):

### Python caller trace
```bash
python3 -c "
import ast, glob, sys
target_fn = sys.argv[1]
for path in glob.glob('**/*.py', recursive=True):
    if '.sstack' in path or 'test' in path: continue
    try:
        tree = ast.parse(open(path).read(), filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = getattr(node.func, 'id', getattr(node.func, 'attr', ''))
                if name == target_fn:
                    constants = [isinstance(a, ast.Constant) for a in node.args]
                    print(f'{path}:{node.lineno} -> {name}() const_args={all(constants) if constants else False}')
    except Exception: pass
" <function_name>
```

### Call-edge classification
1. **Dynamic caller**: Caller forwards user, HTTP, or message arguments.
   Adverse input is reachable; surface takes full negative attack.
2. **Constant-only caller**: Every argument at all call sites is a literal.
   Reachability is capped — document as constant-only and deprioritize.
3. **Shallow helper trap**: Extracted pure function called only by one
   internal sibling. Do not attack or test in isolation; map the caller's
   seam where the invariant is owed (locality principle).

## 3. Map Synthesis

Synthesize role outputs and caller traces into `.sstack/map.md`:

```markdown
| Surface | File | Language | Contract / Invariants | Impact Class | Caller Seam | Lenses |
```

- **Impact class**: privilege boundary, sensitive-data mutation,
  integrity/partial write, availability, presentation.
- **Caller seam**: name the public or gateway function through which
  dynamic input reaches this surface.
- **Lens selection**: select matching lenses with property evidence;
  record skips with quoted "When not to apply" lines.

## Safety

Read-only outside `.sstack/map.md`. AST inspection uses local standard
libraries only. No external parsers, binaries, or vector databases
(v0 scope lock).
