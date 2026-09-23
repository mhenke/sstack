#!/usr/bin/env sh
# Copy a seeded eval repo to a fresh temp dir without BUGS.md,
# for cold acceptance runs. Usage: run-acceptance.sh <seeded-py|seeded-ts>
set -eu
repo="${1:?usage: run-acceptance.sh <seeded-py|seeded-ts>}"
case "$repo" in
  seeded-py | seeded-ts) ;;
  *) echo "unknown repo: $repo" >&2; exit 1 ;;
esac
dir=$(mktemp -d "${TMPDIR:-/tmp}/sstack-$repo-XXXXXX")
cd "$(dirname "$0")"
rsync -a --exclude BUGS.md "$repo/" "$dir/"
echo "$dir"
