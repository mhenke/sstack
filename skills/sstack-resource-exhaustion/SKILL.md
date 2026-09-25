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

- Memory: inputs sized just under and just over any buffer, cache,
  or collection limit the code documents or implies.
- Connections: open more concurrent connections than the pool size.
  Hold them past the timeout window.
- Rate limits: send requests just-under and just-over any documented
  rate limit. Then sustained: send at 2x the limit for the timeout
  window.
- Disk: write outputs large enough to fill the available temp space
  or exceed any file-size limit.
- Threads: spawn more concurrent workers than the thread pool size.
- Payload size: at and just above any documented max request body,
  header, or URL length limit.

## Oracle patterns

- Clean error naming the limit (`429 Too Many Requests`,
  `503 Service Unavailable`,
  `ValueError: connection pool exhausted`).
- Graceful degradation: the system sheds load rather than crashing.
  Non-critical features fail first; critical features stay up.
- No resource leak after the error: connections return to the pool,
  memory is freed, threads are reclaimed.
- The system recovers when the pressure is removed. Send the
  overload, stop, then send a normal request. It must succeed.

Worked example — 100 concurrent checkout requests against a pool of
10: oracle excess requests get `503 Service Unavailable` naming the
pool, observed (bug) requests hang and valid traffic stalls behind
stuck connections. Request body 1 byte over a 1 MB limit: oracle
`413 Payload Too Large` naming the limit, observed (bug) body parsed
and downstream OOM on the untruncated buffer.

## Failure modes to watch for

- Hang: the system accepts the connection but never responds,
  holding the resource indefinitely.
- Silent degradation: the system returns stale data, drops features
  without an error, or returns partial results with no indication.
- Crash: unhandled `OutOfMemoryError`, OOM kill, or a stack overflow
  that takes down the process.
- Leak: the system returns an error but does not release the
  resource, so subsequent valid requests also fail.

## Language notes

### JavaScript / TypeScript

- `Math.max(...largeArray)` can throw `RangeError: Maximum call
  stack size exceeded`; use a reduce loop for large collections.
- A rejected promise without a handler can terminate the process;
  exhaustion paths must settle every request.
- `Buffer.alloc` throws on an oversized allocation; `Buffer.concat`
  may grow until the process is killed.

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

## When not to apply

The surface has no shared resources (no connection pool, no cache,
no rate limit, no memory constraint beyond the language runtime's own
GC). Pure functions with fixed-size inputs.
