# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Developers using AI coding agents (Claude Code, Cursor, Codex, OpenCode,
Windsurf, and the rest), arriving at the site from the repo, the README,
or word of mouth. Two adjacent audiences with separate jobs:

- **Evaluators** deciding whether the pack is trustworthy: they read the
  lens list, the lifecycle, and the acceptance numbers.
- **Installers** ready to act: they copy the `npx skills add` command
  and paste the attacker-agent install prompt.

Secondary: contributors reading `docs/` and `evals/` who arrive from
the site's footer/doc links.

## Product Purpose

sstack is structured negative testing for AI coding agents: a
skill-pack that maps a target's surfaces, attacks each one through
failure-class lenses (boundaries, malformed, missing, ownership,
exceptional-conditions, resource-exhaustion, state), verifies observed
behavior against an oracle declared before the attack, and turns every
confirmed failure into a regression test plus the minimal fix.

The website's job (confirmed): **pitch + docs gateway** — convince the
evaluator the pack is real, hand the installer the copy-paste install,
and route readers into `docs/` and `evals/` on GitHub.

Success = a visitor either runs the npx install or follows a doc link
with an accurate picture of what the pack does and what its evidence
supports.

## Positioning

The oracle discipline is the claim a neighbor cannot copy: expected
behavior is written down *before* the attack, one oracle per observable
outcome, and a finding only counts when real command output backs it.
Competing "agent testing" tools assert robustness; sstack exercises
the failure condition, quotes the real output, and ships red→green
regressions. Also unfakeable-cheap: `gstack, pstack, sstack` — same
suffix family, same install shape.

## Operating Context

- Install: `npx skills@latest add mhenke/sstack` (skills only);
  attacker agents install separately via a paste-in prompt (README).
- Runs as `/sstack <scope>` in Claude Code; same words as a prompt in
  hosts without slash commands.
- Zero runtime dependencies beyond the Python stdlib; one shipped
  emitter script (`emit_findings.py`). Nothing to configure.
- Output lands in the *user's* repo under `.sstack/` (map, plan,
  findings, scratch, learn) plus regression tests and fixes in their
  suite and source. Config/secrets stay read-only.
- Host-specific: works in any agent that can read a skill file; eval
  harness never launches a host-specific agent.

## Capabilities and Constraints

- Seven shipped lenses; eight more (ordering, concurrency, idempotency,
  dependency-failure, contract, mutation, agent, security) specified
  and unbuilt, activatable by user-dropped `sstack-`-prefixed files.
- Customization contract: the `sstack-` prefix in the user's own tree;
  shipped `skills/` and `agents/` are replaced wholesale on update.
- **Site constraint (confirmed): single static `index.html`, forever.**
  No build step, no JS, no framework, no extra pages. Deployed from
  `site/` via GitHub Actions to GitHub Pages at
  https://mhenke.github.io/sstack/.
- Visual system: sentry package from nexu-io/open-design (DESIGN.md +
  tokens.css live in `site/`); dark purple-black canvas, Rubik, Monaco
  mono, one lime pop per section.
- **Evidence rule (confirmed): the site mirrors the README's acceptance
  table.** Numbers are updated together with the README at each site
  change; `evals/ACCEPTANCE.md` stays the authority of record.
- Cold-run containment: a cold agent gets no answer key; the harness
  strips `BUGS.md` and the sstack repo from its workspace.

## Brand Commitments

- Name: sstack ("sad stack"). Family: gstack, pstack, sstack.
- Voice (binding, from repo docs): dry, terse, evidence-first.
  "Don't ask whether the software is robust." The not-happy list, the
  oracle-first rule, the four rules — real copy, never invented claims.
- The README's blockquote copy and the four-rules prose are the site's
  canonical text; wording changes require the same rigor as any
  skill-behavior change (every recorded number came from exact text).

## Evidence on Hand

- Acceptance evidence: `evals/ACCEPTANCE.md` + the README table
  (seeded-py/ts/js/java/cpp cold passes and replay counts).
- Live site: https://mhenke.github.io/sstack/ (deployed from `site/`).
- The `.sstack/` directory layout, lens index, stage list, and install
  commands — all quoted from real repo files.
- Absences the site must not fabricate: no testimonials, no customer
  logos, no star counts, no downloads numbers, no benchmarks beyond
  the fixture table.

## Product Principles

1. Evidence over assertion — never a claim without a real command's
   output behind it; the site inherits this or it is off-brand.
2. The oracle before the attack — on the site too: numbers only ever
   quote the acceptance record, never extrapolate.
3. Nothing to configure — install, point at a scope, run; the site
   shows the same zero-config story.
4. Failures are the product — the not-happy list is the pitch, not a
   confession.
5. One page, one job — pitch + gateway; anything else links out.

## Accessibility & Inclusion

Target WCAG AA on the site itself (4.5:1 body contrast, visible focus,
24px+ touch targets). The irony of a negative-testing pack shipping
sub-AA contrast is unacceptable; site quality issues are treated as
findings.
