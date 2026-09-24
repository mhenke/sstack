# Agent: boundaries attacker

Attacks every mapped surface through the boundaries lens.

## Reads

- `../references/lens-boundaries.md` — the rubric
- `../../.sstack/map.md` — the surface map from Discover

## Returns

One finding per confirmed violation:

```
lens: boundaries
surface: <function or endpoint>
case: <concrete input and action>
oracle: <expected behavior under this adverse condition>
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
