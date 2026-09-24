# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- ADR-0004: lenses delegate to the target's existing tools
- ADR-0005: sstack finds, tests, and fixes (supersedes the
  audit-not-fix portion of ADR-0002)
- Per-lens attacker agents (`agents/sstack-<lens>-attacker.md`):
  boundaries, malformed, missing, resource-exhaustion — each loading
  its peer lens skill, with returns format and constraints
- Thermos pattern: per-lens fan-out at Attack stage, one agent per
  lens, parallel when the host supports subagent dispatch
- Property-based testing delegation: Attack stage checks for
  Hypothesis, fast-check, jqwik, RapidCheck and writes a property
  before hand-designing cases
- Mutation testing references: PIT (Java), Stryker (JS/TS), mutmut
  (Python)
- Run-end checks: source unchanged, every finding has a regression,
  regression states honest, no confirmed finding with only a green
  regression
- Steel-man Verify step: strongest case that the observed behavior is
  correct, before recording confirmed
- Edge-case vs negative-case vocabulary split in ARCHITECTURE.md and
  the boundaries lens
- Ownership lens (OWASP A01): authorization-scope violations, BOLA,
  IDOR. Unit tier works with mocks; integration tier needs sessions
- Exceptional-conditions lens (OWASP A10): fail-open paths,
  diagnostic leakage, cascading failures. Unit tier works with mocks;
  integration tier needs injectable failures
- Containment: `evals/verify-isolation.sh` gained lock, unlock, and
  check subcommands, then was removed per the no-sh-files rule.
  Containment is caller responsibility going forward
- Tool inventory by language (`docs/TOOLS.md`)
- Research index (`docs/RESEARCH.md`)
- Research record (`docs/LEARNED.md`)
- Language breadth on the roadmap: Python, JavaScript, TypeScript,
  Java, C++
- Roadmap: Thermos per-lens fan-out architecture, C++ second
  verification mode question, Readme honesty line

### Changed

- Lifecycle expanded: Regress split into Test (write regression, goes
  red) and Fix (apply minimal change, goes green)
- Verify requires steel-manning observed behavior before recording
  confirmed
- Discover reads a verification skill or feature map as a head start
- AGENTS.md restructured for the always-loaded budget
- ROADMAP.md humanized and expanded
- README language support stated honestly

### Fixed

- Attack coverage paragraph restored after silent deletion
- Acceptance harness and skill corrected after guardrail iterations

### Security

- Acceptance containment hardened: worktree locked read-only during
  cold runs

### Removed

- `docs/superpowers/` (process artifacts, gitignored)
- `references/lens-*.md` (superseded by peer skills and agents)

## [0.1.0] - 2026-09-23

First release. A structured negative-testing skill pack for AI coding
agents.

### Added

- Orchestrator skill (`skills/sstack/SKILL.md`): five-stage lifecycle
  (Discover, Attack, Verify, Minimize, Regress), oracle-first
  verification, red/green regression vocabulary, per-surface lens
  coverage
- Three input lenses (`references/`): boundaries, malformed, missing
- Concept freeze (`docs/`): ETHOS.md, ARCHITECTURE.md
- Seeded-bug eval repos: `evals/seeded-py` and `evals/seeded-ts`
- Cold-run acceptance harness (`evals/run-acceptance.sh`)
- Acceptance record (`evals/ACCEPTANCE.md`)
- MIT license

[unreleased]: https://github.com/mhenke/sstack/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/mhenke/sstack/releases/tag/v0.1.0
