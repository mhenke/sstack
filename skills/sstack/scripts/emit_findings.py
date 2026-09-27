#!/usr/bin/env python3
"""Evidence emitter: the only writer of .sstack/findings/* and .sstack/report.json.

Run once per finding, as each case verifies. The finding arrives as JSON on
stdin; the repro is executed for real, and stdout, stderr, exit code, and
fingerprint come from that execution and never from transcription.
report.json is rebuilt from the evidence files on disk after every emit, so
the run survives a crash with everything already verified still recorded.

    python3 scripts/emit_findings.py --workspace <host-repo> --fixture <fixture> <<'JSON'
    {"slug": "checkout-page-zero", "lens": "boundaries", "surface": "checkout",
     "case": "checkout(items=[], page=0)",
     "oracle": "ValueError naming page", "verdict": "confirmed",
     "repro": "<command that reproduces it>",
     "fix": "raise when page < 1",
     "regression": {"file": "tests/test_checkout.py", "test": "test_page_zero",
                    "before": "red", "after": "green"}}
    JSON

Optional keys: "fix" (confirmed only, and only when a fix was applied).
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

VERDICTS = ("confirmed", "refuted", "inconclusive")
STATES = ("red", "green")
SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def safe_slug(value: str, field: str) -> str:
    """A slug becomes a filename under .sstack/findings/. A lens name can
    come from user-authored frontmatter, so `lens: ../../etc` would
    otherwise write outside the workspace."""
    if not SAFE.match(value) or value in {".", ".."}:
        raise ValueError(
            f"{field} must be a plain filename fragment "
            f"(letters, digits, dot, dash, underscore): {value!r}")
    return value


def read_finding() -> dict:
    finding = json.load(sys.stdin)
    if not isinstance(finding, dict):
        raise ValueError("finding must be a JSON object")
    missing = [k for k in ("lens", "surface", "case", "oracle", "verdict", "repro") if not finding.get(k)]
    if missing:
        raise ValueError(f"missing fields: {', '.join(missing)}")
    if finding["verdict"] not in VERDICTS:
        raise ValueError(f"verdict must be one of {', '.join(VERDICTS)}")
    regression = finding.get("regression")
    if not isinstance(regression, dict):
        raise ValueError("regression must name file, test, before, after")
    absent = [k for k in ("file", "test", "before", "after") if not regression.get(k)]
    if absent:
        raise ValueError(f"regression missing: {', '.join(absent)}")
    for state in ("before", "after"):
        if regression[state] not in STATES:
            raise ValueError(f"regression.{state} must be the literal token 'red' or 'green'")
    return finding


def run_repro(command: str, workspace: Path) -> dict:
    done = subprocess.run(command, shell=True, cwd=workspace, capture_output=True, text=True, errors="replace")
    stdout, stderr = done.stdout, done.stderr
    return {
        "command": command,
        "exit_code": done.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "fingerprint": hashlib.sha256((stdout + stderr).encode()).hexdigest()[:16],
    }


def render_markdown(finding: dict, run: dict) -> str:
    observed = (run["stdout"] + run["stderr"]).strip("\n")
    parts = [
        f"# {finding['surface']} — {finding['case']}",
        "",
        f"lens: {finding['lens']} | verdict: {finding['verdict']}",
        "",
        "## Case",
        finding["case"],
        "",
        "## Oracle",
        finding["oracle"],
        "",
        "## Observed",
        "```",
        observed,
        "```",
        "",
        "## Repro",
        "```",
        finding["repro"],
        "```",
        f"exit {run['exit_code']}, fingerprint {run['fingerprint']}",
    ]
    regression = finding["regression"]
    if finding["verdict"] == "confirmed" and finding.get("fix"):
        parts += ["", "## Fix", finding["fix"]]
    parts += [
        "",
        "## Regression",
        f"`{regression['file']}::{regression['test']}` — {regression['before']} → {regression['after']}",
    ]
    return "\n".join(parts) + "\n"


def rebuild_report(findings_dir: Path, workspace: Path, fixture: str) -> int:
    entries = []
    for evidence in sorted(findings_dir.glob("*.json")):
        record = json.loads(evidence.read_text(errors="replace"))
        entries.append(
            {
                "seed_id": record.get("seed_id", "other"),
                "lens": record["lens"],
                "surface": record["surface"],
                "case": record["case"],
                "oracle": record["oracle"],
                "observed": record["stdout"] + record["stderr"],
                "verdict": record["verdict"],
                "repro": record["command"],
                "regression": record["regression"],
            }
        )
    (workspace / ".sstack" / "report.json").write_text(json.dumps({"fixture": fixture, "findings": entries}, indent=2) + "\n")
    return len(entries)


def warn_unlanded(finding: dict, workspace: Path) -> None:
    """Advisory only: during Verify the regression test may legitimately not exist yet."""
    regression = finding["regression"]
    path = workspace / regression["file"]
    if not path.is_file():
        print(f"warning: {regression['file']} not on disk yet", file=sys.stderr)
    elif regression["test"] not in path.read_text(errors="replace"):
        print(f"warning: {regression['test']!r} not found in {regression['file']} yet", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workspace", type=Path, required=True, help="host repo holding .sstack/")
    parser.add_argument("--fixture", help="fixture name; required on the first emit, then preserved")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    stack = workspace / ".sstack"
    stack.mkdir(parents=True, exist_ok=True)
    findings_dir = stack / "findings"
    findings_dir.mkdir(exist_ok=True)

    try:
        finding = read_finding()
    except (json.JSONDecodeError, ValueError) as error:
        print(f"invalid finding: {error}", file=sys.stderr)
        return 2

    report = stack / "report.json"
    fixture = args.fixture or (json.loads(report.read_text()).get("fixture") if report.is_file() else None)
    if not fixture:
        print("first emit needs --fixture", file=sys.stderr)
        return 2

    try:
        slug = safe_slug(finding.get("slug") or
                         f"{safe_slug(finding['lens'], 'lens')}-{safe_slug(finding['surface'], 'surface')}",
                         "slug")
    except ValueError as error:
        print(f"invalid finding: {error}", file=sys.stderr)
        return 2
    run = run_repro(finding["repro"], workspace)
    record = {"seed_id": finding.get("seed_id", "other"), "lens": finding["lens"], "surface": finding["surface"],
              "case": finding["case"], "oracle": finding["oracle"], "verdict": finding["verdict"], **run,
              "regression": finding["regression"]}
    if finding.get("fix"):
        record["fix"] = finding["fix"]

    (findings_dir / f"{slug}.json").write_text(json.dumps(record, indent=2) + "\n")
    (findings_dir / f"{slug}.md").write_text(render_markdown(finding, run))
    total = rebuild_report(findings_dir, workspace, fixture)
    warn_unlanded(finding, workspace)
    print(f"emitted {slug}: {finding['verdict']}, exit {run['exit_code']}, fingerprint {run['fingerprint']}; report.json now {total} finding(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
