# sstack site package usage

Design package for the sstack marketing site (`site/index.html`). Base:
the OpenDesign "[sentry](https://github.com/nexu-io/open-design/tree/main/design-systems/sentry)" package (`design-systems/sentry`). Adapted, not
copied — see `DESIGN.md` §Deltas.

## Read order

1. This file — the package contract.
2. `DESIGN.md` — visual intent, deltas from the sentry base, voice.
3. `tokens.css` — paste its `:root` block verbatim into the first
   `<style>` of any artifact (already done in `index.html`).
4. `components.manifest.json` — compact inventory; `components.html`
   has the exact markup.
5. `preview/` — quick visual sanity check of colors, type, spacing.

## Highlights

- Dark purple-black canvas (`#1f1633`, `#150f23`) — never pure black.
- One loud accent: magenta-pink `#fa7faa` for links, focus rings, the
  hero accent word, and CTA fills (dark text on it).
- Rubik everywhere; Monaco/Menlo mono for code and evidence.
- Flat depth: border + surface tint, no decorative shadows.

## Do

- Reference `var(--*)` only; raw hex lives only inside the `:root`
  block of `tokens.css`.
- Keep `--accent` as the single interactive anchor (links, focus, one
  accent word per heading at most).
- Keep copy dry and evidence-first: quote the README, don't invent
  claims.

## Avoid

- No testimonials, logos, star counts, or invented benchmarks.
- No raw hex outside the token block.
- No drop shadows for depth; use `--border` + `--surface`.
- No tracked-out uppercase eyebrows beyond the one hero eyebrow
  pattern; no more than one accent-colored word per heading.
