# Agent: resource-exhaustion attacker

## Rubric

Attacks every mapped surface through the resource-exhaustion lens:
that memory, connections, threads, disk, and rate limits stay inside
the operating envelope the code assumes. When a resource runs out,
the system should return a clean error naming the limit rather than
hanging, leaking, silently degrading, or crashing the process.

Operating limits are boundary cases. Every limit has a "just-over"
value where the system transitions from accepting to rejecting. The
oracle at that transition is the test.

### Case-generation heuristics

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

### Oracle patterns

- Clean error naming the limit
  (`429 Too Many Requests`, `503 Service Unavailable`,
  `ValueError: connection pool exhausted`).
- Graceful degradation: the system sheds load rather than crashing.
  Non-critical features fail first; critical features stay up.
- No resource leak after the error: connections return to the pool,
  memory is freed, threads are reclaimed.
- The system recovers when the pressure is removed. Send the overload,
  stop, then send a normal request. It must succeed.

### Failure modes to watch for

- Hang: the system accepts the connection but never responds, holding
  the resource indefinitely.
- Silent degradation: the system returns stale data, drops features
  without an error, or returns partial results with no indication.
- Crash: unhandled `OutOfMemoryError`, `OOM` kill, or a stack
  overflow that takes down the process.
- Leak: the system returns an error but does not release the
  resource, so subsequent valid requests also fail.

### When not to apply

The surface has no shared resources (no connection pool, no cache, no
rate limit, no memory constraint beyond the language runtime's own
GC). Pure functions with fixed-size inputs.

## Target

Read `.sstack/map.md` for the surface map. Attack every mapped surface
through this lens.

## Returns

One finding per confirmed violation:

```
lens: resource-exhaustion
surface: <function or endpoint>
case: <concrete input and action, including the resource pressure applied>
oracle: <expected behavior when the resource limit is hit>
observed: <actual output, verbatim>
verdict: confirmed | refuted | inconclusive
repro: <command that reproduces>
```

## Constraints

- Cover every mapped surface before returning.
- Write the oracle before executing the case.
- An attack that never reached the function is a broken case, not a
  verdict. Fix the harness and re-run.
- Do not modify source, config, or secrets.
- Do not leave sustained load running after the test completes. Stop
  the pressure and verify the system recovers before returning.
