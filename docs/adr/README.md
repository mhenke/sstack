# Architecture Decision Records

This directory holds the decision history for sstack: the *why* behind
the product. For *what* the code does, read [`../ARCHITECTURE.md`](../ARCHITECTURE.md),
[`../ETHOS.md`](../ETHOS.md), and the skill itself.

## Index

| ADR | Title | Status | Date |
|---|---|---|---|
| [0001](0001-negative-testing-is-the-domain.md) | Negative testing is the product domain | Accepted | 2026-09-23 |
| [0002](0002-content-only-agent-agnostic-skill.md) | Content-only, agent-agnostic skill pack | Accepted | 2026-09-23 |
| [0003](0003-eval-gated-acceptance.md) | Eval-gated acceptance with seeded repos | Accepted | 2026-09-23 |
| [0004](0004-delegate-to-target-existing-tools.md) | Lenses delegate to the target's existing tools | Accepted | 2026-09-23 |
| [0005](0005-sstack-finds-tests-and-fixes.md) | sstack finds, tests, and fixes | Accepted | 2026-09-23 |
| [0006](0006-evidence-re-verifiable-by-machine.md) | Finding evidence is machine-re-verifiable | Accepted | 2026-09-24 |
| [0007](0007-optional-deps-degrade-inline.md) | Optional dependencies degrade inline | Accepted | 2026-09-24 |

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
