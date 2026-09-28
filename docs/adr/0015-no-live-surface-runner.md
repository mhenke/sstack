# ADR-0015: No live-surface testing — runner or rubric; runtime behavior is out of scope

**Status**: Accepted (supersedes the 2026-09-28 boot-and-curl rubric decision)
**Date**: 2026-09-28
**Deciders**: Mike Henke

## Context

The security and ownership lenses have a known blind spot: behavior
that only exists at runtime on a live HTTP surface — framework output
escaping, middleware ordering, header handling, CORS. Source reading
cannot decide these. A v1 `runners/` entry was proposed to close it: a
stdlib-only `run_surface.py`/`.js` script that fires HTTP probes at
the target's own server and feeds the emitter.

The roadmap organizing rule — raise proof quality or lower run cost —
and the ADR-0013/0014 precedent rejected the runner: the agent can
already run real commands itself (ADR-0004 delegation), and the
evidence contract (ADR-0006) already fingerprints any repro command's
bytes for machine replay. A wrapper script adds zero signal over the
native command. Its costs are also real: server lifecycle management
in replay (boot, readiness wait, ports, teardown) is the
"deterministic helpers are expensive to maintain" trap ADR-0002
rejected; none of the five seeded fixtures is a server, so a new
fixture class plus goldens plus cold runs would be needed to prove it;
and every cold run would gain a flakiness surface.

This ADR's first accepted form then went further: it added rubric
guidance directing the agent to boot the target's own server and
probe routes with `curl`. The decider has rejected that too, on scope
grounds: sstack is a source-first, in-process negative-testing stack.
Runtime-only behaviors — output escaping, middleware ordering, header
handling, CORS misconfiguration as decided by a live server — are
outside the product's identity, not a deferred feature. Booting user
servers from an unattended cold run also charges real costs today
(side effects on the host, an untested code path with no seed, golden,
or cold run behind it, and a replay hole `replay.py` cannot close),
against value that no recorded run has ever realized.

## Decision

We will not build or ship a live-surface runner, and `runners/`
remains absent from the tree.

Live-surface testing is out of scope entirely, as guidance as well as
infrastructure. The security and ownership lens rubrics do **not**
direct the agent to boot servers or fire HTTP probes. Runtime-only
behaviors are recorded as checked N/As in `map.md` per ADR-0007 — the
lens confirms from source that no in-process decision site exists for
the behavior, and moves on.

In-process testing of remote behavior remains in scope: a remote
dependency is tested by injecting a failing or hanging double of it
(the `failing_gateway` / `hanging_tracker` seed pattern) and asserting
the caller's handling. The network is never touched.

## Consequences

**Good**
- Zero new code, zero runtime deps, zero ADR-0002 exposure; the
  evidence contract is untouched.
- The source-first identity is unambiguous: every finding is decidable
  from source and reproducible in-process.
- Cold agents never boot user servers, open ports, or read runtime
  config; no untested behavior ships in the rubrics.
- Assumed N/As become recorded, checked N/As.

**Bad**
- Runtime-only defects (framework escaping, middleware ordering,
  live header handling) go unreported on server-shaped repos. That is
  an accepted scope boundary, not a gap to fix in v0/v1.
- Server-shaped repos get a narrower security/ownership report than
  an in-process reading of the same code might suggest.

**Risks**
- If a future proof-gate genuinely needs live execution, that is a
  product-identity change, not a tooling change: it would be proposed
  as a new ADR re-deciding this scope line, with a server-shaped
  fixture, goldens, and cold-run evidence attached.
