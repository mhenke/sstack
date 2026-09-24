# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-09-23

First release. A structured negative-testing skill pack for AI coding
agents: it discovers failure surfaces, attacks them through specialist
lenses, verifies observed behavior against an oracle declared before
the attack, minimizes confirmed failures, and turns them into
permanent regression tests.

### Added

- **Orchestrator skill** (`skills/sstack/SKILL.md`): five-stage
  lifecycle (Discover, Attack, Verify, Minimize, Regress), oracle-first
  verification, audit-not-fix safety contract, `red`/`green` regression
  vocabulary, and per-surface lens coverage requirements.
- **Three input lenses** (`references/`): `boundaries` (numeric, size,
  index, and collection edges), `malformed` (wrong types, corrupt
  structures, unvalidated parsing), and `missing` (absent fields,
  null/None/undefined, empty inputs).
- **Concept freeze** (`docs/`): `ETHOS.md` (the four rules) and
  `ARCHITECTURE.md` (canonical lifecycle, the six definitions, the full
  13-lens taxonomy, the v1 verification menu).
- **Architecture decision records** (`docs/adr/`): why negative testing
  is the domain (0001), why the pack is content-only and
  agent-agnostic (0002), and why acceptance is eval-gated (0003).
- **Seeded-bug eval repos**: `evals/seeded-py` (Python/pytest) and
  `evals/seeded-ts` (TypeScript/vitest), five deliberate bugs each, every
  bug mapped to exactly one lens and recorded in a `BUGS.md` answer
  key.
- **Cold-run acceptance harness** (`evals/run-acceptance.sh`): copies
  the skill and a BUGS.md-free, cache-free fixture into one isolated
  temp workspace so a cold agent never needs the repo it came from.
- **Acceptance record** (`evals/ACCEPTANCE.md`): seeds found, oracle
  regressions that go red on the seed and green after the canonical
  fix, every failed cold run, and the guardrail each failure forced.

### Changed

- Skill guardrails hardened through six cold acceptance runs:
  bug-pinning regressions forbidden, the audit-not-fix contract made
  unmissable, lens examples decontaminated of seeded answer keys, and
  attacks required to reach the function under test before scoring.
  (The run-by-run record lives in `evals/ACCEPTANCE.md`.)

### Fixed

- Seeded-bug expectations corrected to match real runtime behavior
  (empty-slice clamping, `maxQuantity` on empty input).
- Acceptance harness no longer ships pytest/bytecode caches that
  carried oracle strings into cold-run workspaces.

### Security

- MIT license.

[Unreleased]: https://github.com/mhenke/sstack/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/mhenke/sstack/releases/tag/v0.1.0
