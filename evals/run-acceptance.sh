#!/usr/bin/env sh
# Copy a seeded eval repo AND a BUGS.md-free copy of the skill to a fresh
# temp workspace, so a cold agent never needs to touch the sstack repo at
# all. Usage: run-acceptance.sh <seeded-py|seeded-ts>
set -eu
repo="${1:?usage: run-acceptance.sh <seeded-py|seeded-ts>}"
case "$repo" in
  seeded-py | seeded-ts) ;;
  *) echo "unknown repo: $repo" >&2; exit 1 ;;
esac
dir=$(mktemp -d "${TMPDIR:-/tmp}/sstack-$repo-XXXXXX")
cd "$(dirname "$0")"
rsync -a --exclude BUGS.md "$repo/" "$dir/"
mkdir -p "$dir/skills/sstack"
rsync -a ../skills/sstack/ "$dir/skills/sstack/"
echo "$dir"
