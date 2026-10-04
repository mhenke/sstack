# sstack — site design rules

Visual rules for the sstack marketing site. Base package: OpenDesign
"[sentry](https://github.com/nexu-io/open-design/tree/main/design-systems/sentry)" (`design-systems/sentry`). This file records what sstack keeps,
what it changes, and the targets the pages must hold.

## Palette (source of truth: `tokens.css`)

| Role | Hex | Use |
|---|---|---|
| `--bg` | `#1f1633` | Page canvas. Never pure black. |
| `--surface` | `#150f23` | Panels, code wells, footer, recessed sections |
| `--fg` / `--fg-2` | `#f6f2fb` / `#e5e7eb` | Primary / secondary text |
| `--muted` | `#9d96b3` | Meta, sub-copy (6.1:1 on bg) |
| `--border` | `#362d59` | Quiet decorative hairlines |
| `--border-strong` | `#6f63b8` | Interactive control chrome (2.9:1 on bg) |
| `--accent` | `#fa7faa` | Magenta-pink: links, focus ring, accent word, CTA fill |
| `--accent-on` | `#150f23` | Dark text ON accent fills |
| `--success` / `--danger` | `#4ade80` / `#f87171` | Red→green evidence states |
| `--code` | `#dcdcaa` | Syntax tint for mono strings |

Contrast verified arithmetically ([WCAG 2.2](https://www.w3.org/TR/WCAG22/)):
- `#fa7faa` on `#1f1633`: 7.1:1 — AA/AAA pass at all sizes.
- `#150f23` on `#fa7faa` (CTA): 7.7:1.
- `#9d96b3` on `#1f1633`: 6.1:1 (AA body).
- `#f6f2fb` on `#150f23`: 16.9:1; on `#1f1633`: 15.6:1.
- Decorative hairline `#362d59` vs bg is 1.4:1 — accepted as purely
  decorative; anything carrying interactive state uses
  `--border-strong` or `--focus-ring`.

## Type

- Display + body: **[Rubik](https://fonts.google.com/specimen/Rubik)** (400–800, Google Fonts). Dammit Sans from
  the base package is unavailable; Rubik bold is the display face, as
  in the base package's own degraded landing template.
- Mono: **Monaco, Menlo, Ubuntu Mono, ui-monospace**.
- Scale: 88/60/30/24/20/16/14/12. Hero uses fluid
  `clamp(2.75rem, 6vw + 1rem, 5.5rem)`; headings `line-height 1.2`,
  body `1.5`.
- One accent word per heading, max, always roman (no italics in display
  type). No tracked-out uppercase eyebrows beyond the single hero
  eyebrow.

## Space, radius, rhythm

- 8px base unit. Section rhythm 80/64/48 (desktop/tablet/phone).
- Container max 1152px; gutters 64/32/24.
- Radius ladder 6/8/12/pill. Buttons and cards 8px.

## Depth

Flat first: depth = `--border` + `--surface` tint. No drop shadows for
structure; `--elev-raised` reserved for nothing on the homepage.

## Voice

Dry, terse, evidence-first. No testimonials, logos, star counts,
invented benchmarks. The not-happy list (the empty string, the `null`,
the duplicate webhook, the dependency that dies at 2am, the second
concurrent request) is the pitch. Acceptance numbers are quoted
exactly from `README.md`.

## Accessibility targets (WCAG 2.2 AA)

- 4.5:1 body text, 3:1 large text — verified above.
- Visible focus: `--focus-ring` = 2px solid `--accent` on every
  `:focus-visible`.
- Touch targets ≥ 24px (buttons are 44px min-height).
- Semantic landmarks: header/nav/main/sections/footer, skip link,
  `lang="en"`.
- `prefers-reduced-motion`: the single page-load reveal is disabled.

## Deltas from the sentry base package

1. **Accent**: Sentry Purple `#6a5fc1` → magenta-pink `#fa7faa`
   (the base palette's own pink). Matches the target look (Sentry's
   marketing homepage) and passes AA on this canvas, which a lighter
   purple would not. Sentry's lime `#c2ef4e` is dropped entirely.
2. **`--accent-on`** flips to dark `#150f23`: white on magenta is only
   ~3.7:1, failing AA at button size; dark text reaches 7.7:1.
3. **Display font**: Dammit Sans removed; Rubik leads both stacks.
4. **New tokens**: `--border-strong` (#6f63b8) for interactive chrome;
   `--code` (#dcdcaa, the base's documented Code Yellow) for syntax
   tint.
5. **Semantics brightened for the dark canvas**: success `#16a34a` →
   `#4ade80`, danger `#dc2626` → `#f87171` (base values fail contrast
   on `--surface`).
6. **Elevation flattened**: the base's ambient purple glow and frosted
   glass are not used; depth is border + tint per the target look.
7. **Motion restrained**: one page-load reveal only, killed under
   `prefers-reduced-motion`. The base package's drama-in-shadow style
   is not carried over.
8. **External-link indicator**: every absolute http(s) link
   (`a[href^="http"]`) carries a ↗ pseudo-glyph in every context — nav,
   buttons, cards, table, footer. Anchors and relative links never do.
   The glyph is plain inline text, not an atomic inline-block, so it
   cannot wrap onto its own line away from the label; nav links and
   buttons add `white-space: nowrap` as belt-and-braces. Empty alt text
   (`content: "↗" / ""`) keeps it silent for assistive tech. Glyph
   inherits the link color — no new tokens.
9. **Buttons tracked out**: all button labels are ALL-CAPS `--text-xs`
   with 0.08em letter-spacing (the sentry reference look). Radius,
    44px min-height, and the verified AA pairs (dark-on-`--fg` 16.9:1,
    dark-on-magenta 7.7:1) are unchanged; 12px caps still pass AA
    against both fills.
10. **Evidence table goes stacked on phones**: below 640px the evidence
    table renders as cards — fixture as the card title (a real
    `th scope="row"`), Seeds and Cold evidence as `data-label` rows.
    Same table markup and caption; `thead` is visually clipped, still
    announced. ≥640px unchanged. The ACCEPTANCE.md link moved out of
    the caption into a `.table-note` paragraph with `--space-8` above
    it — it was sitting tight against the section sub-copy.
11. **Hero starfield**: one static decorative illustration — tiled
    radial-gradient pinpricks in `--border-strong` with a rare
    `--accent`, masked to fade at the hero's lower edge. Pure CSS,
    `aria-hidden`, no motion (reduced-motion safe by construction), no
    new tokens, no raw hex outside `:root`.
12. **Header — one focal CTA**: wordmark, nav (Rules, Lifecycle,
    Lenses, Evidence, Docs↗, GitHub↗ — the four-rules section joined
    the TOC first, per the nav-mirrors-page-order rule), and a single
    white **Get started** button. No ghost GitHub button anywhere — the nav carries that
    link at every width. Under 760px the nav drops to its own
    full-width row and the wordmark shares the first row with the
    Get started CTA. All three #install CTAs (header, hero, final)
    read "Get started".
16. **Mobile header — Sentry pattern**: at ≤759px the bar is one 56px
    row: wordmark left, white Get started + hamburger right. All five
    nav links (incl. the only GitHub entry) move into a
    `<details>`/`<summary>` disclosure menu — keyboard-operable with
    no JS to open; a small script closes it on link activation and
    Escape (focus returns to the summary). Burger is pure CSS (one
    bar + two box-shadows), `aria-hidden`; the summary carries the
    accessible name "Menu". The bar drops its bottom border at mobile
    and blends into the hero. External-link ↗ works in menu items
    unchanged. Desktop sticky header is untouched.
13. **Oracle callout**: the canonical oracle definition (verbatim from
    README/CONTEXT.md — wording is frozen, edit it in the repo first)
    sits under the four-rules intro as an `<aside>` panel. Flat per
    the depth language: 1px `--accent` border, `--surface` fill, the
    strong lead word in `--accent`. Text is `--fg-2` on `--surface`
    (~13:1, AA). No left accent bar, no shadow.
14. **Install as two equal tracks**: the install section is a 1/2
    numbered card pair — "Install the skills" (npx command) and
    "Install the attackers" (the verbatim README paste-in prompt) —
    same card treatment, same code block + copy button, 2-col ≥820px,
    stacked below. Prompt text is frozen README copy. Python is
    demoted to a muted `--text-xs` footnote: the emitter is optional
    tooling, not the pitch.
15. **Install band**: the install section is the page's only
    full-bleed `--surface` band, fenced by hairline `--border`
    dividers top and bottom — the footer/strip pattern promoted to
    the conversion moment. Flat: no shadow, no radius at page width.
17. **`--fg` tinted off pure white**: `#ffffff` → `#f6f2fb` (a faint
    violet-white on-palette tint). Contrast: `--surface` on `--fg`
    16.9:1, `--fg` on `--bg` 15.6:1 — AA/AAA hold everywhere; the
    white CTA inherits the tint via `background: var(--fg)`.
    `tokens.css` `:root` and the pasted block in `index.html` stay
    value-identical per the paste contract.
18. **Single containment**: one border layer per contained thing.
    The hero `.finding` box drops its border (the kv hairline
    dividers already structure it; the outer `.panel` keeps its
    border). In the two install cards the inner `.codeblock` drops
    its border and `--surface` background — the numbered `.card` is
    the single frame.
19. **Rule-card eyebrow numbers dropped**: the 01–04 mono-cap
    numerals above the four rule cards are removed; headings and
    copy unchanged. The install cards keep their 1/2 numerals —
    they number tracks, not rules.
20. **Lens grid is a uniform 4-column matrix; the count-derived
    two-card tail is accepted**: every lens card is
    `grid-column: span 1`. At the shipped fourteen lenses the
    ≥1024px grid flows 4 / 4 / 4 / 2. The tail is a count artifact,
    not a hierarchy statement: the lenses are genuine peers, and
    per the [impeccable](https://github.com/pbakaus/impeccable) layout doctrine (variation only when content
    or priority changes) no card is widened. Copy-fit verified in
    Chromium at 1280px: 264px columns, zero clipped or scrolling
    cards, longest gist (ownership) fits. History: the twelve-lens
    grid was 3/3/3/3; the earlier `lens-card-wide` span on
    `ownership` was dropped for the same uniformity reason. A
    fifteenth lens flows 4/4/4/3; a change to the tail shape never
    reintroduces a span without a content reason.
21. **Agent install: paste prompts for AI CLIs/IDEs, plus the
    per-host list for manual preference**: the install card carries
    two copy-paste instructions the user's agent executes — the
    default installs into the portable `.agents` hub
    (`~/.agents/`, plain `.md`, created if missing), the second
    into VS Code's global `~/.copilot/agents/` renamed
    `<name>.agent.md`. The `.host-list` below, labeled "Manual
    process" over a hairline divider, keeps the manual rows
    (Agnostic → `~/.agents/`, Claude Code, VS Code); the
    OpenCode-specific row is dropped because the hub covers it. Only VS Code needs the
    rename; every other host reads the files as-is. The skills card
    mirrors the same manual pattern: its own "Manual process"
    host-list with each host's skills directory — Agnostic →
    `~/.agents/skills/`, Claude Code → `~/.claude/skills/`,
    VS Code → `~/.copilot/skills/` — no rename on any host,
    project scope shadowing global, full per-host table in
    `docs/CUSTOMIZING.md`. Each list opens with the instruction
    "Or copy the `skills/` folders / the `agents/*.md` files
    into one of these:" so it says what to copy before the rows.
22. **Docs cross-links**: prose links (muted text + accent link,
    the `.table-note` pattern) close the four-rules, lifecycle, and
    lens sections — ETHOS.md, ARCHITECTURE.md, LENS.md on GitHub.
    The final CTA's magenta button now reads "Read the docs" and
    points at the repo readme; ETHOS.md stays linked in the footer
    and after the rule cards.
23. **components.html parity**: the reference page loads Rubik
    (same preconnects + stylesheet link as index.html) and wires
    its copy buttons with the same `data-copy` targets and inline
    script/no-JS fallback.
24. **Copy hygiene pass**: lifecycle Attack row synced to the
    shipped lens count (fourteen); em-dashes out of titles and page
    copy (frozen oracle callout exempt); hero sub deduplicated to
    the ethos line (chip strip keeps the five cases); lifecycle sub
    and rule card 2 rewritten without re-quoting the callout;
    panel-note restructured to periods; gstack/pstack context clause
    in the footer bar; `color-scheme: dark` on the token root
    (paste parity: index.html and tokens.css); copy buttons render
    ALL-CAPS per the button pin; the host-list install card ported
    to components.html; dead CSS folded (`.codeblock` base,
    `.finding` radius); §12 nav order corrected to shipped.
25. **Rubik is self-hosted**: `fonts/fonts.css` declares the two
    variable woff2 files (roman + italic, weight 100–900,
    `font-display: swap`) vendored next to the page; both pages link
    it instead of fonts.googleapis.com. Removes the last
    third-party runtime dependency (ADR-0012); no build step —
    two files plus one stylesheet are the whole mechanism.
26. **The not-happy strip is unfenced, labeled, and spans the lens
    set**: the chip row lost its `border-block` hairlines — the
    fenced-band signature belongs to the install conversion moment
    alone — and gained a mono lead-in ("the not-happy cases it
    hunts:") so the pills read as the product's example failures,
    not floating tags. Nine pills: the README's canonical five plus
    four grounded in the shipped lenses' documented cases
    (ordering, idempotency, ownership, security). Rhythm unchanged
    (`--space-6`).
27. **Harden callout**: harden mode gets one aside, not a section —
    the oracle callout's anatomy (1px `--accent` border, `--surface`
    fill, accent lead word, 62ch) placed in the install band between
    the run-scope line and the footnote; inside the band its rhythm
    tightens to `--space-6`. Copy is new, so no em-dash per 24: the
    lead word takes a period. README carries the mirror as a
    blockquote in Running it, per its own oracle blockquote shape.
28. **Findings panel and lifecycle rows hold at 320px**: the findings
    `.kv` label column becomes `minmax(0, 7rem)`, values take
    `overflow-wrap: anywhere`, and `.panel-head` spans shrink-and-wrap —
    long mono tokens (`apply_discount(`, the findings path) wrapped
    instead of clipping under the panel's `overflow: hidden`.
    components.html gains the <820px two-column `.row` fallback
    index.html already had, and its agents paste-prompt is synced to
    README verbatim (`, overwriting files already there`).
    Install-card host lists wrap at the same width (`flex-wrap: wrap`
    on `.host-list li`): the VS Code agents path folds instead of
    pushing the page to 339px.
29. **Accent words are roman, and the family pitch lives once**: heading
    accent words drop the italic (a recognized generated-page tell; the
    accent color alone carries the emphasis). The final CTA's
    gstack/pstack sentence is removed; the footer bar is the single
    family mention.
