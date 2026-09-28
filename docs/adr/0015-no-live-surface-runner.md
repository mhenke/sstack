# ADR-0015: Do not build a live-surface runner; probe with curl through the emitter

**Status**: Accepted
**Date**: 2026-09-28
**Deciders**: Mike Henke

## Context

The security and ownership lenses have a known blind spot: behavior
that only exists at runtime on a live HTTP surface — framework output
escaping, middleware ordering, header handling, CORS. Source reading
cannot decide these, so lenses currently record "not applicable" (the
XSS / broader-injection row: a backend shop with no HTML rendering
surface). A v1 `runners/` entry was proposed to close it: a
stdlib-only `run_surface.py`/`.js` script that fires HTTP probes at
the target's own server and feeds the emitter.

The roadmap organizing rule — raise proof quality or lower run cost —
and the ADR-0013/0014 precedent apply. The proposed runner fails the
same test the PBT runner failed: the agent can already boot the
target's own server (ADR-0004 delegation) and fire probes with `curl`,
and the evidence contract (ADR-0006) already fingerprints any repro
command's bytes for machine replay. A wrapper script adds zero signal
over the native command.

Its costs are real: replay would need server lifecycle management
(boot, readiness wait, ports, teardown) — the "deterministic helpers
are expensive to maintain" trap ADR-0002 rejected; none of the five
seeded fixtures is a server, so a new fixture class plus goldens plus
cold runs would be needed to prove it; and every cold run would gain a
flakiness surface.

## Decision

We will not build or ship a live-surface runner, and `runners/`
remains absent from the tree.

Live-surface probing is rubric guidance, not infrastructure: the
security and ownership lens rubrics direct the agent to boot the
target's own server when one is discoverable, probe routes with
`curl`, and emit findings with the `curl` command as `repro`. When no
surface is discoverable, the lens records the N/A in `map.md` per
ADR-0007 — a checked N/A, not an assumed one.

## Consequences

**Good**
- Zero new code, zero runtime deps, zero ADR-0002 exposure; the
  evidence contract is untouched.
- The blind spot is closed by capability the agent already has, on
  repos that actually expose a server.
- Assumed N/As become recorded, checked N/As.

**Bad**
- Probe quality depends on agent discipline rather than a pinned
  script; two runs may probe the same surface differently.
- Replay of a live-surface finding requires the target's server to
  boot in the replay environment; `replay.py` does not manage server
  lifecycle, so such findings replay only where the command itself
  handles boot.

**Risks**
- If a v1 proof-gate (differential comparison is the candidate) needs
  execution `curl` cannot express, revisit — a narrowly-scoped script
  would be proposed as a new ADR, not a `runners/` directory.
