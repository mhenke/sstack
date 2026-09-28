---
name: sstack-resource-exhaustion
description: "Resource-exhaustion lens rubric. Case-generation heuristics, oracle patterns, failure modes, and worked examples for connection pool exhaustion, rate limits, memory ceilings, payload limits, and disk pressure. Loaded inline under ### Lens rubric."
disable-model-invocation: true
---

# Resource-exhaustion lens

Attacks every mapped surface through the resource-exhaustion lens:
that memory, connections, threads, disk, and rate limits stay inside
the operating envelope the code assumes. When a resource runs out,
the system should return a clean error naming the limit rather than
hanging, leaking, silently degrading, or crashing the process.

Operating limits are boundary cases. Every limit has a "just-over"
value where the system transitions from accepting to rejecting. The
oracle at that transition is the test.

## Case-generation heuristics

- Paired limit probes: probe at the declared capacity $N$ (must succeed)
  and $N+1$ (must shed load or reject cleanly). Both vectors are
  required to verify the boundary is enforced without false rejections.
- Memory: inputs sized just under and just over any buffer, cache,
  or collection limit the code documents or implies.
- Connections: open more concurrent connections than the pool size.
  Hold them past the timeout window.
- Rate limits: send requests just-under and just-over any documented
  rate limit. Then sustained: send at 2x the limit for the timeout
  window.
- Unbounded queries & collections: request unbounded lists or large
  exports (omitted `limit`, massive page size) to test memory ceilings
  and streaming boundaries.
- Disk: write outputs large enough to fill the available temp space
  or exceed any file-size limit.
- Threads & workers: spawn more concurrent tasks than worker/thread
  pool capacity; push past queue limits to test rejection policies.
- Algorithmic & recursive depth: feed deeply nested structures
  (1,000+ levels of JSON/arrays) or ReDoS patterns to test call stack
  and execution limits.
- Payload size: at and just above any documented max request body,
  header, or URL length limit.
- Post-pressure recovery: send an overload burst, stop, then send a
  normal request to test self-healing and handle leakage.

## Oracle patterns

- Clean error naming the limit (`429 Too Many Requests`,
  `503 Service Unavailable`, `413 Content Too Large`,
  `ValueError: connection pool exhausted`).
- Early admission gates: payload size (`413`) and rate (`429` with
  `Retry-After`) checked before body buffer allocation or processing.
- Fast load shedding over unbounded queueing: saturated pools or task
  queues reject fast (`503` or `RejectedExecutionException`) rather than
  buffering unboundedly into OOM or hanging callers.
- Graceful degradation & bulkheads: the system sheds load rather than
  crashing. Saturated pools or tenants do not starve unrelated routes.
- No resource leak after the error: connections return to the pool,
  memory is freed, threads and file descriptors are reclaimed.
- Self-healing recovery: the system recovers immediately once pressure
  is removed. Overload, stop, normal request succeeds with standard
  latency.
- Threshold sensitivity: verify admission at $N$ and rejection at $N+1$;
  an early gate that rejects at $N$ has turned a valid peak into an outage.

Worked example — Python `export_records(query)` with 2,000,000 matching
rows and a 10,000 row safety limit: oracle raises
`ResultLimitExceeded("query exceeds maximum export limit of 10000 rows")`,
observed (bug) attempts to load all 2,000,000 rows into memory and
crashes with `MemoryError`.

TypeScript `acquireWorkerConnection(pool)` with 10 max connections and a
2.0s timeout: 11th concurrent caller: oracle throws
`Error("connection pool exhausted")` at 2.0s, observed (bug) hangs
indefinitely awaiting an unavailable connection.

## Failure modes to watch for

- Hang: the system accepts the connection or task but never responds,
  holding the resource indefinitely.
- Silent degradation: the system returns stale data, drops features
  without an error, or returns partial results with no indication.
- Crash: unhandled `OutOfMemoryError`, OOM kill, or a stack overflow
  that takes down the process.
- Leak: the system returns an error but does not release the
  resource, so subsequent valid requests also fail.
- Unbounded queue buildup: queues accepting tasks without capacity
  limits, swelling memory until the process terminates.
- Event-loop starvation: synchronous blocking operations freezing
  the single-threaded event loop.

## Language notes

### JavaScript / TypeScript

- `Math.max(...largeArray)` can throw `RangeError: Maximum call
  stack size exceeded`; use a reduce loop for large collections.
- A rejected promise without a handler can terminate the process;
  exhaustion paths must settle every request.
- `Buffer.alloc` throws on an oversized allocation; `Buffer.concat`
  may grow until the process is killed.
- Heavy synchronous operations or recursive microtask loops block the
  event loop; yield periodically or offload to worker threads.

### Java

- An exhausted `ExecutorService` rejects with `RejectedExecutionException`,
  not a hang. A bounded queue with no rejection policy throws
  `OutOfMemoryError` under sustained load.
- Streams and `try`-with-resources can retain resources until
  consumption finishes; verify closure on an error path.

### C++

- Allocation failure is commonly signaled by `std::bad_alloc`, but
  unchecked `new` may terminate the process. Prefer the
  nothrow-aware or smart-pointer path.
- File descriptors are finite OS resources; exceeding `RLIMIT_NOFILE`
  yields `EMFILE`, and leaked descriptors keep the pressure high.

### Python

- `ThreadPoolExecutor` raises `RuntimeError: cannot schedule new
  futures after shutdown` and queues unbounded by default; bound the
  queue before testing exhaustion.
- Large `bytes` or `list` allocations raise `MemoryError` in-process,
  while some native allocations are killed by the OS instead.
- Asyncio queues (`asyncio.Queue`) default to unbounded (`maxsize=0`);
  always enforce explicit `maxsize` to prevent heap exhaustion.

## When not to apply

The surface has no shared resources (no connection pool, no cache,
no rate limit, no memory constraint beyond the language runtime's own
GC). Pure functions with fixed-size inputs.
