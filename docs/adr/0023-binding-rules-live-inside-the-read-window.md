# ADR-0023: Binding rules live inside the cold backend's read window

**Status**: Accepted
**Date**: 2026-09-30
**Deciders**: Mike Henke

## Context

An unbounded `read` of the entry skill truncates around 16KB —
roughly line 230 of a 540-line file. Four wording regimes failed the
emit step before anyone measured this: heredoc example, `--finding`
availability, Verify-stage imperative, and a co-located command. Each
round edited the skill text correctly and each round produced the same
zero emitter invocations. Transcript instrumentation found why: a cold
backend reads the first ~230 lines and never sees the rest, so every
instruction past that line is not wrong, it is invisible.

The same gap hid the dispatch fallback (the rule that transfers a
failed subagent dispatch back to the orchestrator). ColdWindowContract
fanned out per lens, its dispatch failed silently, and the agent read
the attacker files — half-taking the fallback — then relapsed into
waiting on a child that never existed. The rule existed at line 320.

## Decision

Every rule a cold backend must obey lives in the read window: the
emit contract, the dispatch fallback, the routing execution model.
Content past the window is reference a strong model reads on demand
and a weak one never sees, which is a legitimate tier for stage detail
and lens material. The entry skill may keep growing past the window;
what it may not do is bind through it.

The window is pinned by a rerunnable check
(`test_no_text_instructs_hand_writing_evidence` in
`evals/test_emitter.py`): it asserts the emit contract and the
dispatch fallback are present in the first 200 lines and that the
Verify stage stays outside.

## Consequences

**Good**: a rule that lives in the window provably reaches every
backend the host dispatches to, which is what "works regardless of
mode" requires; the four failed wording rounds are replaced by one
measured placement rule; the test makes a silent regression
impossible.

**Bad**: the window is a fixed 200 lines while the contract is
rewriteable, so adding a rule means finding room or moving something
out; the entry skill's first 200 lines carry a different budget than
the rest of the file, and that boundary is invisible in the Markdown;
a backend with a larger or windowless read tool will not notice the
rule at all, so the constraint is enforced against the weakest reader
we have evidence for, not a universal one.

**Risks**: a host whose truncation lands earlier than 230 lines
reintroduces the whole failure class invisibly — the test's 200-line
pin is a floor, not a guarantee, and a stricter backend needs it
tightened. Revisit if a cold run on a new backend again skips a rule
the test proves is in-window.