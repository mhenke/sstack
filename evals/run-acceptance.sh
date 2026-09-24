#!/usr/bin/env sh
# Build an isolated cold-run workspace: the seeded fixture (no answer
# key, no caches) plus a copy of the skill, and a marker file that
# tells the cold agent which directory is the host repo. The skill
# anchors every relative path to that marker, so a stray `.sstack/`
# cannot resolve back into the sstack repo the agent was launched from.
# Usage: run-acceptance.sh <seeded-py|seeded-ts>
set -eu
repo="${1:?usage: run-acceptance.sh <seeded-py|seeded-ts>}"
case "$repo" in
  seeded-py | seeded-ts) ;;
  *) echo "unknown repo: $repo" >&2; exit 1 ;;
esac
dir=$(mktemp -d "${TMPDIR:-/tmp}/sstack-$repo-XXXXXX")
cd "$(dirname "$0")"
rsync -a --exclude BUGS.md --exclude '.pytest_cache' --exclude '__pycache__' --exclude '.vite' "$repo/" "$dir/"
mkdir -p "$dir/skills/sstack"
rsync -a ../skills/sstack/ "$dir/skills/sstack/"
cat > "$dir/.sstack-host-repo" <<'MARKER'
This file marks the host repo for a cold sstack run. The directory
containing this file is the root every relative path resolves
against. Do not write anywhere else.
MARKER
echo "$dir"
