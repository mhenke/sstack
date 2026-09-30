#!/usr/bin/env python3
"""Evidence emitter: the only writer of .sstack/findings/* and .sstack/report.json.

Two invocation modes: a finding JSON in a file passed with --finding, or
on stdin, emits that one finding immediately; empty stdin runs the
upgrade pass — every findings/<slug>.json whose repro is a command
string is executed and fingerprinted now (requests become evidence only
through execution). The repro is executed for
real, and stdout, stderr, exit code, and
fingerprint come from that execution and never from transcription.
Recorded paths are rewritten host-repo-relative at capture, so evidence
diffs clean across machines and checkouts.
report.json is rebuilt from the evidence files on disk after every emit, so

    echo '{"slug": "checkout-page-zero", ...}' > finding.json
    python3 scripts/emit_findings.py --workspace <host-repo> --finding finding.json --fixture <fixture>
    (the finding JSON may instead be piped on stdin)

Optional keys: "fix" (confirmed only, and only when a fix was applied),
"seed" (integer or token for PBT replay), and "counterexample" (the minimal
failing input).
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


_STDIN = object()


class _UpgradeRequested(Exception):
    """No --finding and nothing on stdin: run the upgrade pass."""


def read_finding(path: str | None) -> dict:
    if path is None or path is _STDIN:
        raw = sys.stdin.read()
        if not raw.strip():
            raise _UpgradeRequested
    else:
        try:
            raw = Path(path).read_text()
        except OSError as error:
            print(f"cannot read --finding file: {error}", file=sys.stderr)
            raise SystemExit(2) from error
    if not raw.strip():
        print(
            f"no finding in {path} — write the finding JSON to a file and pass --finding <file>, e.g.:\n"
            "python3 scripts/emit_findings.py --workspace <host-repo> --finding finding.json [--fixture <fixture>]\n"
            '{"slug": "checkout-page-zero", "lens": "boundaries", "surface": "checkout",\n'
            ' "case": "checkout(items=[], page=0)", "oracle": "ValueError naming page",\n'
            ' "verdict": "confirmed", "repro": "<command that reproduces it>",\n'
            ' "regression": {"file": "tests/test_checkout.py", "test": "test_page_zero",\n'
            '                "before": "red", "after": "green"}}',
            file=sys.stderr,
        )
        raise SystemExit(2)
    finding = json.loads(raw)
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


PROBE_COMPILE = {".py": [sys.executable, "-m", "py_compile"], ".js": ["node", "--check"]}


def preflight_probe(command: str, workspace: Path) -> bool:
    """A scratch probe that does not compile is infrastructure failure, not evidence.

    Truncated or half-written probes once reached findings as observed
    behavior. Compile every referenced scratch probe before anything is
    recorded; refusal exits 3 and writes nothing.
    """
    for token in command.split():
        candidate = Path(token)
        path = candidate if candidate.is_absolute() else workspace / candidate
        if path.suffix not in PROBE_COMPILE or "scratch" not in path.parts:
            continue
        check = subprocess.run(PROBE_COMPILE[path.suffix] + [str(path)], capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
        if check.returncode != 0:
            print(f"scratch probe does not compile — repair it before emitting: {path}\n{check.stderr}", file=sys.stderr)
            return False
    return True


def normalize(text: str, workspace: Path) -> str:
    """Evidence is diffed run over run, so the recorded bytes must not
    carry the absolute workspace path: it differs on every machine and
    every temp checkout, and a path that moved reads as a false change.
    Rewrite it to `.` on path boundaries — a sibling directory sharing
    the prefix stays intact."""
    return re.sub(re.escape(str(workspace)) + r"(?![\w.-])", ".", text)


def run_repro(command: str, workspace: Path) -> dict:
    done = subprocess.run(command, shell=True, cwd=workspace, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    stdout = normalize(done.stdout, workspace)
    stderr = normalize(done.stderr, workspace)
    return {
        "command": normalize(command, workspace),
        "exit_code": done.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "fingerprint": hashlib.sha256((stdout + stderr).encode("utf-8")).hexdigest()[:16],
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
    if finding.get("seed") is not None or finding.get("counterexample") is not None:
        pbt_lines = []
        if finding.get("seed") is not None:
            pbt_lines.append(f"seed: `{finding['seed']}`")
        if finding.get("counterexample") is not None:
            pbt_lines.append(f"counterexample: `{finding['counterexample']}`")
        parts += ["", "## PBT", "\n".join(pbt_lines)]
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
        record = json.loads(evidence.read_text(encoding="utf-8", errors="replace"))
        if "command" not in record:
            continue  # a request (no executed repro yet) is not evidence
        entry = {
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
        if record.get("seed") is not None:
            entry["seed"] = record["seed"]
        if record.get("counterexample") is not None:
            entry["counterexample"] = record["counterexample"]
        entries.append(entry)
    (workspace / ".sstack" / "report.json").write_text(json.dumps({"fixture": fixture, "findings": entries}, indent=2) + "\n", encoding="utf-8")
    return len(entries)


def warn_unlanded(finding: dict, workspace: Path) -> None:
    """Advisory only: during Verify the regression test may legitimately not exist yet."""
    regression = finding["regression"]
    path = workspace / regression["file"]
    if not path.is_file():
        print(f"warning: {regression['file']} not on disk yet", file=sys.stderr)
    elif regression["test"] not in path.read_text(encoding="utf-8", errors="replace"):
        print(f"warning: {regression['test']!r} not found in {regression['file']} yet", file=sys.stderr)


def upgrade_requests(findings_dir: Path, workspace: Path, fixture: str | None) -> int:
    """Requests become evidence only through execution. A request whose
    repro is a command string is executed here, the run dict replaces the
    string, and the evidence view is written; a request without a command
    stays a request — the machine never invents the missing command."""
    upgraded = pending = 0
    for path in sorted(findings_dir.glob("*.json")):
        finding = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        if "command" in finding:
            continue  # already evidence
        repro = finding.get("repro")
        if not isinstance(repro, str) or not repro.strip():
            pending += 1
            continue
        if not preflight_probe(repro, workspace):
            pending += 1
            continue
        run = run_repro(repro, workspace)
        record = {k: v for k, v in finding.items() if k != "repro"}
        record.update(run)
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        (findings_dir / f"{path.stem}.md").write_text(
            render_markdown(finding, run), encoding="utf-8")
        warn_unlanded(finding, workspace)
        print(f"upgraded {path.stem}: exit {run['exit_code']}, fingerprint {run['fingerprint']}")
        upgraded += 1
    if upgraded and fixture:
        total = rebuild_report(findings_dir, workspace, fixture)
        print(f"report.json now {total} finding(s)")
    print(f"{upgraded} request(s) upgraded, {pending} still pending (no executable repro)")
    return 0


def main() -> int:
    # Hosts with a legacy locale (Windows cp1252, C) must not change what
    # the emitter can read or write; evidence is UTF-8 everywhere.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--finding", help="file holding the finding JSON; stdin if omitted"
    )
    parser.add_argument("--workspace", type=Path, required=True, help="host repo holding .sstack/")
    parser.add_argument("--fixture", help="fixture name; required on the first emit, then preserved")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    stack = workspace / ".sstack"
    stack.mkdir(parents=True, exist_ok=True)
    findings_dir = stack / "findings"
    findings_dir.mkdir(exist_ok=True)

    report = stack / "report.json"
    try:
        finding = read_finding(args.finding if args.finding else _STDIN)
    except _UpgradeRequested:
        fixture = args.fixture or (json.loads(report.read_text(encoding="utf-8")).get("fixture") if report.is_file() else None)
        return upgrade_requests(findings_dir, workspace, fixture)
    except (json.JSONDecodeError, ValueError) as error:
        print(f"invalid finding: {error}", file=sys.stderr)
        return 2

    fixture = args.fixture or (json.loads(report.read_text(encoding="utf-8")).get("fixture") if report.is_file() else None)
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
    if not preflight_probe(finding["repro"], workspace):
        return 3
    run = run_repro(finding["repro"], workspace)
    record = {"seed_id": finding.get("seed_id", "other"), "lens": finding["lens"], "surface": finding["surface"],
              "case": finding["case"], "oracle": finding["oracle"], "verdict": finding["verdict"], **run,
              "regression": finding["regression"]}
    if finding.get("fix"):
        record["fix"] = finding["fix"]
    if finding.get("seed") is not None:
        record["seed"] = finding["seed"]
    if finding.get("counterexample") is not None:
        record["counterexample"] = finding["counterexample"]

    (findings_dir / f"{slug}.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    (findings_dir / f"{slug}.md").write_text(render_markdown(finding, run), encoding="utf-8")
    total = rebuild_report(findings_dir, workspace, fixture)
    warn_unlanded(finding, workspace)
    print(f"emitted {slug}: {finding['verdict']}, exit {run['exit_code']}, fingerprint {run['fingerprint']}; report.json now {total} finding(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
