#!/usr/bin/env python3
"""Evidence emitter: the only writer of .sstack/findings/* and .sstack/report.json.

Two invocation modes: a finding JSON in a file passed with --finding, or
on stdin, emits that one finding immediately; empty stdin runs the
upgrade pass — every findings/<slug>.json whose repro is a command
string is executed and fingerprinted now (requests become evidence only
through execution). The repro is executed for real, and stdout, stderr,
exit code, and fingerprint come from that execution and never from
transcription. Recorded paths are rewritten host-repo-relative at
capture, so evidence diffs clean across machines and checkouts.
report.json is rebuilt from the evidence files on disk after every
emit, so requests never appear in it — evidence only.

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
import os
import re
import select
import subprocess
import sys
from pathlib import Path

VERDICTS = ("confirmed", "refuted", "inconclusive")
STATES = ("red", "green")
SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

# Repro execution is bounded: a hung repro is killed and recorded as
# exit 124 with the kill noted in stderr (SSTACK_REPRO_TIMEOUT, seconds).
try:
    REPRO_TIMEOUT = max(1, int(os.environ.get("SSTACK_REPRO_TIMEOUT", "120")))
except ValueError:
    REPRO_TIMEOUT = 120


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


def _stdin_is_empty() -> bool:
    if getattr(sys.stdin, "isatty", lambda: True)():
        return True
    try:
        r, _, _ = select.select([sys.stdin], [], [], 0.0)
        if not r:
            return True
    except (OSError, ValueError):
        pass
    return False


def read_finding(path: str | None) -> dict:
    if path is None or path is _STDIN:
        # A TTY or pipe without immediate data counts as empty:
        # reading would block forever.
        raw = "" if _stdin_is_empty() else sys.stdin.read()
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


def fingerprint_is_wellformed(value: object) -> bool:
    """A fingerprint is 16 lowercase hex characters, or absent.

    The upgrade pass treats any file carrying a `fingerprint` key as
    evidence and skips it. A model that pads or invents one therefore
    promotes its own guess past the only check that runs inside the loop,
    and nothing catches it until replay. Malformed means "not evidence":
    the file stays a request and the upgrade pass executes its repro.
    """
    return value is None or (isinstance(value, str)
                             and re.fullmatch(r"[0-9a-f]{16}", value) is not None)


def normalize(text: str, workspace: Path) -> str:
    """Evidence is diffed run over run, so the recorded bytes must not
    carry the absolute workspace path: it differs on every machine and
    every temp checkout, and a path that moved reads as a false change.
    Rewrite it to `.` on path boundaries — a sibling directory sharing
    the prefix stays intact."""
    return re.sub(re.escape(str(workspace)) + r"(?![\w.-])", ".", text)


def run_repro(command: str, workspace: Path) -> dict:
    # ponytail: the timeout kills the shell, not detached grandchildren —
    # a repro that spawns daemons can outlive it.
    try:
        done = subprocess.run(command, shell=True, cwd=workspace, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=REPRO_TIMEOUT)
    except subprocess.TimeoutExpired:
        stderr = f"emitter: repro exceeded {REPRO_TIMEOUT}s and was killed\n"
        return {
            "command": normalize(command, workspace),
            "exit_code": 124,
            "stdout": "",
            "stderr": stderr,
            "fingerprint": hashlib.sha256(stderr.encode("utf-8")).hexdigest()[:16],
        }
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
        run["command"],
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
        # Evidence requires a fingerprint to exist AND be well-formed; the
        # validator alone says a request's absent key is fine.
        if not record.get("fingerprint") or not fingerprint_is_wellformed(record["fingerprint"]):
            continue  # a request (no executed repro yet) is not evidence
        entry = {
            "seed_id": record.get("seed_id", "other"),
            "lens": record.get("lens", "other"),
            "surface": record.get("surface", ""),
            "case": record.get("case", ""),
            "oracle": record.get("oracle", ""),
            "observed": record.get("stdout", "") + record.get("stderr", ""),
            "verdict": record.get("verdict", "inconclusive"),
            "repro": record.get("command", ""),
            "regression": record.get("regression"),
        }
        if record.get("seed") is not None:
            entry["seed"] = record["seed"]
        if record.get("counterexample") is not None:
            entry["counterexample"] = record["counterexample"]
        entries.append(entry)
    if not entries:
        return 0  # no evidence yet: writing an empty report would grade as a clean run
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


def render_summary(stack: Path, workspace: Path) -> int:
    """Render the chat summary from report.json. The agent relays this;
    it never counts findings itself, so counts cannot be invented."""
    report_path = stack / "report.json"
    if not report_path.is_file():
        print("no report.json — nothing emitted yet", file=sys.stderr)
        return 2
    data = json.loads(report_path.read_text(encoding="utf-8"))
    findings = data.get("findings", [])
    counts = {"confirmed": 0, "refuted": 0, "inconclusive": 0}
    fixes = landed = hardened = 0
    for f in findings:
        v = f.get("verdict", "inconclusive")
        counts[v] = counts.get(v, 0) + 1
        reg = f.get("regression") or {}
        rfile, rtest = reg.get("file", ""), reg.get("test", "")
        path = workspace / rfile if rfile else None
        on_disk = bool(path and path.is_file()
                       and (not rtest or rtest in path.read_text(encoding="utf-8", errors="replace")))
        if v == "confirmed":
            kind = f"regression ({rfile}::{rtest}, {'red->green' if on_disk else 'NOT ON DISK'})"
            if on_disk:
                landed += 1
        else:
            kind = f"hardening ({rfile}::{rtest}, {'green' if on_disk else 'NOT ON DISK'})"
            if on_disk:
                hardened += 1
        print(f"{f.get('seed_id', 'other')} | {f.get('lens', 'other')} | "
              f"{f.get('surface', '')} | {v} | {kind}")
        if f.get("fix"):
            fixes += 1
    print(f"confirmed {counts['confirmed']} / refuted {counts['refuted']} / "
          f"inconclusive {counts['inconclusive']}; fixes applied {fixes}; "
          f"regressions landed {landed}; hardening tests added {hardened}")
    return 0


def upgrade_requests(findings_dir: Path, workspace: Path, fixture: str | None) -> int:
    """Requests become evidence only through execution. A request whose
    repro is a command string is executed here, the run dict replaces the
    string, and the evidence view is written; a request without a command
    stays a request — the machine never invents the missing command."""
    upgraded = pending = 0
    for path in sorted(findings_dir.glob("*.json")):
        finding = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        if "fingerprint" in finding:
            if fingerprint_is_wellformed(finding["fingerprint"]):
                continue  # already evidence
            print(f"{path.stem}: malformed fingerprint — treating as a request "
                  f"and re-executing its repro", file=sys.stderr)
        repro = finding.get("repro")
        # A request may spell the command as a string or nest it under
        # "command" — the evidence view's shape invites the object form.
        # Either way the machine executes it; it never invents one.
        if isinstance(repro, dict):
            repro = repro.get("command")
        if not isinstance(repro, str) or not repro.strip() or not preflight_probe(repro, workspace):
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
    # Rebuild whenever there is evidence to report, not only when something
    # was upgraded: editing a finding's case/oracle after its repro already
    # ran leaves the evidence file and report.json out of step, and the
    # grader only ever reads the report.
    if fixture and any(fingerprint_is_wellformed(
            json.loads(p.read_text(encoding="utf-8", errors="replace")).get("fingerprint"))
                       for p in findings_dir.glob("*.json")):
        total = rebuild_report(findings_dir, workspace, fixture)
        if upgraded:
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
    parser.add_argument("--report", action="store_true",
                        help="print the run summary from report.json and exit")
    parser.add_argument("--upgrade", action="store_true",
                        help="run the upgrade pass over pending finding requests")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    stack = workspace / ".sstack"
    stack.mkdir(parents=True, exist_ok=True)
    findings_dir = stack / "findings"
    findings_dir.mkdir(exist_ok=True)

    if args.report:
        return render_summary(stack, workspace)

    report = stack / "report.json"
    if args.upgrade:
        fixture = args.fixture or (json.loads(report.read_text(encoding="utf-8")).get("fixture") if report.is_file() else None)
        return upgrade_requests(findings_dir, workspace, fixture)

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
              "regression": finding["regression"], "fixture": fixture}
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
