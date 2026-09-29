# Architecture Decision Records

This directory holds the decision history for sstack: the *why* behind
the product. For *what* the code does, read [`../ARCHITECTURE.md`](../ARCHITECTURE.md),
[`../ETHOS.md`](../ETHOS.md), and the skill itself.

## Index

| ADR | Title | Status | Date |
|---|---|---|---|
| [0001](0001-negative-testing-is-the-domain.md) | Negative testing is the product domain | Accepted | 2026-09-27 |
| [0002](0002-content-only-agent-agnostic-skill.md) | Content-only, agent-agnostic skill pack | Accepted | 2026-09-27 |
| [0003](0003-eval-gated-acceptance.md) | Eval-gated acceptance with seeded repos | Accepted | 2026-09-27 |
| [0004](0004-delegate-to-target-existing-tools.md) | Lenses delegate to the target's existing tools | Accepted | 2026-09-27 |
| [0005](0005-sstack-finds-tests-and-fixes.md) | sstack finds, tests, and fixes | Accepted | 2026-09-27 |
| [0006](0006-evidence-re-verifiable-by-machine.md) | Finding evidence is machine-re-verifiable | Accepted | 2026-09-27 |
| [0007](0007-optional-deps-degrade-inline.md) | Optional dependencies degrade inline | Accepted | 2026-09-27 |
| [0008](0008-user-extends-by-naming-a-file.md) | The user extends sstack by naming a file, not by editing ours | Accepted | 2026-09-27 |
| [0009](0009-uniform-six-part-lens-anatomy.md) | Uniform six-part lens anatomy | Accepted | 2026-09-27 |
| [0010](0010-cross-language-fixture-parity.md) | Cross-language fixture parity | Accepted | 2026-09-27 |
| [0011](0011-lens-grid-uniform-accept-two-card-tail.md) | Keep the lens grid uniform and accept the two-card tail | Accepted | 2026-09-27 |
| [0012](0012-self-host-rubik-variable-fonts.md) | Self-host the Rubik variable fonts | Accepted | 2026-09-27 |
| [0013](0013-no-dedicated-pbt-runner.md) | Do not build a dedicated PBT runner; record seeds in evidence | Accepted | 2026-09-27 |
| [0014](0014-do-not-build-mutation-runner.md) | Do not build a mutation runner | Accepted | 2026-09-27 |
| [0015](0015-no-live-surface-runner.md) | No live-surface testing — runner or rubric; runtime behavior is out of scope | Accepted | 2026-09-28 |
| [0016](0016-on-demand-references-tier.md) | Subcommand bodies live in an on-demand references tier | Accepted | 2026-09-28 |
| [0017](0017-grader-gates-on-evidence-integrity.md) | The grader verifies evidence fingerprints itself; a PASS cannot rest on evidence replay could not verify | Accepted | 2026-09-28 |
| [0018](0018-harden-is-a-routing-subcommand.md) | Harden is a routing subcommand that fills gaps, not a stage or lens | Accepted | 2026-09-29 |
| [0019](0019-scan-baseline-for-change-triage.md) | map.md records a scan baseline; the next run triages by git diff | Accepted | 2026-09-29 |
| [0020](0020-targets-are-resolved-never-chosen.md) | The target is resolved, never chosen — whole-target maps span runs | Accepted | 2026-09-29 |
| [0021](0021-evidence-is-recorded-portable-not-verbatim.md) | Evidence is recorded portable, not byte-verbatim | Accepted | 2026-09-29 |

## Status

- **Proposed** — under discussion
- **Accepted** — decided and in force
- **Deprecated** — no longer relevant
- **Superseded** — replaced by a later ADR
- **Rejected** — considered and not adopted (kept for the record)

## Writing a new ADR

Copy [`template.md`](template.md) to `NNNN-title-with-dashes.md`,
fill it in, and add a row to the index above. Do not edit an accepted
ADR in place: write a new one and mark the old **Superseded**.
