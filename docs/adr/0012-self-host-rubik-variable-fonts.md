# ADR-0012: Self-host the Rubik variable fonts

**Status**: Accepted
**Date**: 2026-09-27
**Deciders**: Mike Henke

## Context

The site loaded Rubik from fonts.googleapis.com — its only
third-party runtime dependency. Two references forced the question:
the impeccable craft floor ("source and self-host a face …; the
closest installed font is a failure, not a fallback") and the
harden reference (network failure is a hardening dimension — on an
offline or filtered connection the page silently renders in
system-ui, which is exactly the drift fixed on components.html
earlier). The no-build constraint blocks npm tooling, but nothing
about self-hosting needs a build: Google's CSS2 API serves two
variable woff2 files for Rubik (roman and italic, weight 100–900),
which are ordinary static assets.

## Decision

We will vendor the two Rubik variable woff2 files into
`site/fonts/` and declare them in `site/fonts/fonts.css` (two
`@font-face` blocks, `font-display: swap`). Both pages link that
stylesheet instead of fonts.googleapis.com. No build step, no
request leaves the origin.

## Consequences

**Good**: the site works fully offline; no third-party dependency
remains; one request fewer on first load; consistent rendering
everywhere.

**Bad**: ~70KB of binary font data lives in the repo, and future
weight/style additions mean fetching new files by hand instead of
editing a CDN URL.

**Risks**: the files are snapshots of Google's v31 release; Rubik
upstream releases will not propagate. Revisit only if the brand
needs a newer cut of the face — re-download and replace the files.
