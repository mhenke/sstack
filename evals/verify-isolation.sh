#!/usr/bin/env sh
# Enforce and verify cold-run containment.
#
# A cold agent launched from the sstack repo can resolve a relative
# `.sstack/` path or a test write back into the repo it started in.
# Prompt discipline has not stopped that (it happened five times, and
# the marker file only redirects a cooperating agent). This script
# makes the boundary mechanical instead of advisory:
#
#   lock      chmod the worktree read-only, so the run physically
#             cannot write into the sstack repo. Temp workspaces stay
#             writable. Reversible via unlock.
#   snapshot  record the repo's tracked state (read-only; works while
#             locked)
#   check     compare current state to a snapshot; any drift after
#             unlock means the run escaped
#   unlock    restore write permission
#
# Usage:
#   evals/verify-isolation.sh snapshot > /tmp/snap
#   evals/verify-isolation.sh lock
#   <run the cold agent against its temp workspace>
#   evals/verify-isolation.sh unlock
#   evals/verify-isolation.sh check /tmp/snap
#
# Exit 0 = contained, 1 = drift detected, 2 = usage error.
set -eu
repo_root=$(cd "$(dirname "$0")/.." && pwd -P)

snapshot() {
	# Tracked-file content plus working-tree status, excluding the
	# run-artifact and process dirs that are allowed to churn.
	git -C "$repo_root" status --porcelain \
		-- . ':!.sstack' ':!docs/superpowers' ':!.superpowers'
	git -C "$repo_root" diff --stat
}

lock() {
	# Read-only on every file and directory in the worktree, so
	# neither an edit to a tracked file nor a new file can land in
	# the repo. .git stays writable so git plumbing keeps working.
	find "$repo_root" -type f -not -path "$repo_root/.git/*" -exec chmod a-w {} +
	find "$repo_root" -type d -not -path "$repo_root/.git*" -exec chmod a-w {} +
	echo "locked: sstack worktree is read-only"
}

unlock() {
	find "$repo_root" -type f -not -path "$repo_root/.git/*" -exec chmod u+w {} +
	find "$repo_root" -type d -not -path "$repo_root/.git*" -exec chmod u+w {} +
	echo "unlocked: sstack worktree is writable"
}

case "${1:-}" in
snapshot)
	snapshot
	;;
lock)
	lock
	;;
unlock)
	unlock
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
	echo "usage: verify-isolation.sh snapshot|lock|unlock|check <snapshot-file>" >&2
	exit 2
	;;
esac
