#!/usr/bin/env sh
# Assert a cold run stayed inside its workspace.
#
# A cold agent launched from the sstack repo can resolve a relative
# `.sstack/` path or a test write back into the repo it started in.
# Prompt discipline has not stopped that (it happened twice). This
# checks mechanically: snapshot the sstack repo's tracked state, run
# the cold agent, then re-check. Any drift means the run escaped.
#
# Usage:
#   evals/verify-isolation.sh snapshot          > /tmp/snap
#   <run the cold agent against the workspace>
#   evals/verify-isolation.sh check /tmp/snap
#
# Exit 0 = contained, exit 1 = the run wrote into the sstack repo.
set -eu
repo_root=$(cd "$(dirname "$0")/.." && pwd -P)

snapshot() {
	# Tracked-file content plus working-tree status, excluding the
	# run-artifact and process dirs that are allowed to churn.
	git -C "$repo_root" status --porcelain \
		-- . ':!.sstack' ':!docs/superpowers' ':!.superpowers'
	git -C "$repo_root" diff --stat
}

case "${1:-}" in
snapshot)
	snapshot
	;;
check)
	snap="${2:?usage: verify-isolation.sh check <snapshot-file>}"
	now=$(mktemp)
	snapshot >"$now"
	if ! cmp -s "$snap" "$now"; then
		echo "CONTAINMENT BROKEN: the cold run modified the sstack repo" >&2
		echo "--- drift ---" >&2
		diff "$snap" "$now" >&2 || true
		rm -f "$now"
		exit 1
	fi
	rm -f "$now"
	echo "contained: sstack repo unchanged"
	;;
*)
	echo "usage: verify-isolation.sh snapshot | check <snapshot-file>" >&2
	exit 2
	;;
esac
