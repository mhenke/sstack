#!/usr/bin/env sh
# Build an isolated cold-run workspace: the seeded fixture (no answer
# key, no caches) plus a copy of the skills and agents, and a marker
# file that tells the cold agent which directory is the host repo. The
# skill anchors every relative path to that marker, so a stray
# `.sstack/` cannot resolve back into the sstack repo the agent was
# launched from.
# Usage: run-acceptance.sh <seeded-py|seeded-ts|seeded-js|seeded-java|seeded-cpp>
set -eu
repo="${1:?usage: run-acceptance.sh <seeded-py|seeded-ts|seeded-js|seeded-java|seeded-cpp>}"
case "$repo" in
  seeded-py | seeded-ts | seeded-js | seeded-java | seeded-cpp) ;;
  *) echo "unknown repo: $repo" >&2; exit 1 ;;
esac
dir=$(mktemp -d "${TMPDIR:-/tmp}/sstack-$repo-XXXXXX")
cd "$(dirname "$0")"
rsync -a --exclude BUGS.md --exclude '.pytest_cache' --exclude '__pycache__' --exclude '.vite' --exclude node_modules --exclude target --exclude build "$repo/" "$dir/"
mkdir -p "$dir/skills" "$dir/agents"
rsync -a ../skills/sstack/ "$dir/skills/sstack/"
for lens in boundaries malformed missing resource-exhaustion; do
  rsync -a "../skills/sstack-$lens/" "$dir/skills/sstack-$lens/"
done
rsync -a ../agents/ "$dir/agents/"
cat > "$dir/.sstack-host-repo" <<'MARKER'
This file marks the host repo for a cold sstack run. The directory
containing this file is the root every relative path resolves
against. Do not write anywhere else.
MARKER
echo "$dir"
