#!/usr/bin/env python3
"""One entry point for preparing and grading cold-agent evaluations.

Usage:
  python3 evals/acceptance.py prepare seeded-py
  python3 evals/acceptance.py prepare-all
  python3 evals/acceptance.py grade path/to/workspace

`prepare` creates an isolated workspace and prints its path. The host
launches its cold agent there. `prepare-all` does this for every fixture.
`grade` scores a JSON report; it never launches or modifies an agent.
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVALS = ROOT / "evals"
FIXTURES = ("seeded-py", "seeded-ts", "seeded-js", "seeded-java", "seeded-cpp")
EXCLUDED = {".git", ".sstack", ".pytest_cache", "__pycache__", ".vite", "node_modules", "target", "build"}
LENSES = ("boundaries", "malformed", "missing", "ownership", "exceptional-conditions", "resource-exhaustion", "state", "ordering", "concurrency", "idempotency", "dependency-failure", "contract", "security", "agent")


def copy_fixture(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination, dirs_exist_ok=True, ignore=shutil.ignore_patterns(*EXCLUDED, "BUGS.md"))


JUNIT_JAR = "junit-console.jar"
JUNIT_URL = "https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/1.10.2/junit-platform-console-standalone-1.10.2.jar"


def ensure_junit() -> Path:
    """The java fixture needs a JUnit launcher; Maven is not installed. Fetch on demand, never commit."""
    jar = EVALS / "seeded-java" / JUNIT_JAR
    if not jar.exists():
        import urllib.request

        urllib.request.urlretrieve(JUNIT_URL, jar)
    return jar

# Outside the repo on purpose: a conforming cold run deletes its own
# `scratch/` at run end (SKILL.md, run-end checks), so a workspace under
# the sstack repo's `.sstack/` sits inside the blast radius of a correct
# run, not only a misbehaving one. Containment becomes filesystem-enforced.
SCRATCH = Path(tempfile.gettempdir()) / "sstack-cold"


def prepare(fixture: str) -> Path:
    if fixture not in FIXTURES:
        raise SystemExit(f"unknown fixture: {fixture}; choose one of {', '.join(FIXTURES)}")
    if fixture == "seeded-java":
        ensure_junit()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix=f"sstack-{fixture}-", dir=SCRATCH))
    copy_fixture(EVALS / fixture, workspace)
    if (EVALS / fixture / "node_modules").exists():
        (workspace / "node_modules").symlink_to(EVALS / fixture / "node_modules")
    skills = workspace / "skills"
    agents = workspace / "agents"
    skills.mkdir()
    agents.mkdir()
    shutil.copytree(ROOT / "skills" / "sstack", skills / "sstack")
    for lens in LENSES:
        shutil.copytree(ROOT / "skills" / f"sstack-{lens}", skills / f"sstack-{lens}")
    shutil.copytree(ROOT / "agents", agents, dirs_exist_ok=True)
    (workspace / ".sstack-host-repo").write_text(
        "This file marks the host repo for a cold sstack run. The directory\n"
        "containing this file is the root every relative path resolves\n"
        "against. Do not write anywhere else.\n"
        f"Fixture name: {fixture}. Pass it verbatim to emit_findings.py\n"
        "--fixture; the grader rejects any other name.\n"
    )
    # Pre-create the artifact tree. A run that opens with a failing write
    # (`cat > .sstack/report.json: No such file or directory`) repairs by
    # `rm -rf .sstack && mkdir -p ...`, erasing its own map and findings —
    # 91 such calls in ColdMusePy4. The directory is part of the contract,
    # so the harness satisfies it rather than the agent rediscovering it.
    for sub in ("findings", "scratch", "pristine-src", "learn"):
        (workspace / ".sstack" / sub).mkdir(parents=True, exist_ok=True)
    # The skill resolves a bare `/sstack` from the working-tree code diff and
    # asks when no diff names a target (ADR-0020). Without a repo that
    # precondition can never hold, so a bare-invocation run stalls on a
    # question instead of attacking. Committed after the pack copy so the
    # baseline diff describes the target repo, not the skill's own arrival.
    subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
    subprocess.run(
        ["git", "add", "-A", "--", ":(exclude).sstack"], cwd=workspace, check=True
    )
    subprocess.run(
        ["git", "-c", "user.email=cold@sstack", "-c", "user.name=cold",
         "commit", "-qm", "cold-run baseline"],
        cwd=workspace, check=True,
    )
    return workspace


def resolve_report(path: Path) -> tuple[Path, Path | None]:
    """Accept the workspace dir or the report file; canonical location is .sstack/report.json."""
    if path.is_dir():
        for candidate in (path / ".sstack" / "report.json", path / "report.json"):
            if candidate.is_file():
                return candidate, path
        raise SystemExit(f"no report.json under {path} (checked .sstack/ then root)")
    return path, None


def grade_workspace(report_path: Path) -> dict:
    sys.path.insert(0, str(EVALS / "graders"))
    from seeded_acceptance import grade_file

    report, workspace = resolve_report(report_path)
    fixture_name = None
    view_is_valid = False
    try:
        parsed = json.loads(report.read_text())
        view_is_valid = isinstance(parsed, dict) and isinstance(parsed.get("findings"), list)
        if view_is_valid:
            fixture_name = parsed.get("fixture")
    except (json.JSONDecodeError, OSError):
        pass
    if workspace is not None and not view_is_valid:
        # The report view is missing, malformed, or foreign (ColdEvalPy2
        # clobbered it with its own schema). The view is derived state:
        # re-derive it from evidence with the emitter's own rebuild, so
        # authoring report.json cannot affect the outcome. Evidence
        # records self-describe their fixture (stamped at emit).
        evidence_dir = workspace / ".sstack" / "findings"
        if evidence_dir.is_dir():
            sys.path.insert(0, str(EVALS.parent / "skills" / "sstack" / "scripts"))
            from emit_findings import rebuild_report
            for record in sorted(evidence_dir.glob("*.json")):
                try:
                    stamp = json.loads(record.read_text(encoding="utf-8", errors="replace")).get("fixture")
                except (json.JSONDecodeError, OSError):
                    continue
                if stamp:
                    fixture_name = stamp
                    break
            if fixture_name in FIXTURES:
                rebuild_report(evidence_dir, workspace, fixture_name)
    fixture_dir = EVALS / fixture_name if fixture_name in FIXTURES else None
    return grade_file(
        str(report),
        str(EVALS / "goldens.jsonl"),
        str(workspace) if workspace else None,
        str(fixture_dir) if fixture_dir else None,
    )


def grade(report_path: Path) -> int:
    result = grade_workspace(report_path)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


def run_eval(
    fixture: str,
    agent_cmd: str | None = None,
    model: str | None = None,
    prompt_override: str | None = None,
    timeout: int = 600,
) -> int:
    workspace = prepare(fixture)
    prompt = prompt_override or (
        f"Your workspace root is `{workspace}`.\n"
        f"Read `skills/sstack/SKILL.md` inside that workspace and execute `/sstack shop` against the codebase.\n"
        f"All file reads, file edits, and commands must be executed within `{workspace}`.\n"
        f"Report your findings when finished."
    )

    if not agent_cmd:
        print(f"Prepared workspace: {workspace}\n")
        print("To run an agent against this fixture, pass --agent-cmd with your command:")
        print(f"  python3 evals/acceptance.py eval {fixture} --model <name> --agent-cmd \"claude -p '{{prompt}}'\"")
        print("\nPrompt template:")
        print(prompt)
        return 0

    cmd = agent_cmd.format(prompt=prompt, workspace=str(workspace))
    print(f"Running agent in {workspace}...")
    try:
        subprocess.run(
            cmd,
            shell=True,
            cwd=workspace,
            timeout=timeout,
            text=True,
            input=prompt if "{prompt}" not in agent_cmd else None,
        )
    except subprocess.TimeoutExpired:
        print(f"Agent execution timed out after {timeout}s", file=sys.stderr)
        return 2

    # Score output
    try:
        grade_res = grade_workspace(workspace)
    except (Exception, SystemExit) as e:
        grade_res = {"pass": False, "error": str(e)}

    sys.path.insert(0, str(EVALS))
    from replay import replay_workspace
    replay_res = replay_workspace(workspace)

    import datetime
    summary = {
        "model": model or "unspecified",
        "fixture": fixture,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "pass": grade_res.get("pass", False),
        "grade": grade_res,
        "replay": {
            "intact": sum(1 for r in replay_res if r.get("integrity") == "intact"),
            "total": len(replay_res),
            "findings": replay_res,
        },
    }

    print("\n==> Evaluation Summary:")
    print(json.dumps(summary, indent=2))

    if model:
        baseline_file = EVALS / f"baseline-{model}.json"
        baseline_file.write_text(json.dumps(summary, indent=2) + "\n")
        print(f"Recorded baseline token: {baseline_file}")

    return 0 if summary["pass"] else 1


def test_fixture(fixture: str) -> int:
    """Run a fixture's suite. `fixture` is a name under evals/ or a directory path.

    The grader's bug-pin check stages a temp copy of the frozen fixture and
    needs the same runner, so accept a path as readily as a name.
    """
    import subprocess
    candidate = Path(fixture).resolve()
    fdir = candidate if candidate.is_dir() else EVALS / fixture
    name = fdir.name
    for fix in FIXTURES:
        if fix in name:
            name = fix
            break
    if name == "seeded-py":
        return subprocess.run(["pytest", "-q"], cwd=fdir).returncode
    elif name == "seeded-ts":
        return subprocess.run(["bun", "run", "test"], cwd=fdir).returncode
    elif name == "seeded-js":
        return subprocess.run(["npm", "test"], cwd=fdir).returncode
    elif name == "seeded-java":
        jar = fdir / JUNIT_JAR
        if not jar.exists():
            shutil.copy2(EVALS / "seeded-java" / JUNIT_JAR, jar)
        tclasses = fdir / "target" / "classes"
        ttclasses = fdir / "target" / "test-classes"
        tclasses.mkdir(parents=True, exist_ok=True)
        ttclasses.mkdir(parents=True, exist_ok=True)
        sources = sorted(str(p.relative_to(fdir)) for p in (fdir / "src/main/java/com/sstack").glob("*.java"))
        c1 = subprocess.run(["javac", "-d", str(tclasses), *sources], cwd=fdir)
        if c1.returncode != 0:
            return c1.returncode
        test_sources = sorted(str(p.relative_to(fdir)) for p in (fdir / "src/test/java/com/sstack").glob("*.java"))
        c2 = subprocess.run(["javac", "-cp", f"{tclasses}:{jar}", "-d", str(ttclasses), *test_sources], cwd=fdir)
        if c2.returncode != 0:
            return c2.returncode
        return subprocess.run(["java", "-jar", str(jar), "execute", "--class-path", f"{tclasses}:{ttclasses}", "--scan-class-path"], cwd=fdir).returncode
    elif name == "seeded-cpp":
        build_dir = fdir / "build"
        if not (build_dir / "Makefile").exists():
            subprocess.run(["cmake", "-B", "build"], cwd=fdir)
        c1 = subprocess.run(["cmake", "--build", "build"], cwd=fdir)
        if c1.returncode != 0:
            return c1.returncode
        return subprocess.run(["ctest", "--test-dir", "build", "--output-on-failure"], cwd=fdir).returncode
    return 1


def test_all() -> int:
    failed = []
    for fixture in FIXTURES:
        print(f"==> Testing {fixture}...")
        rc = test_fixture(fixture)
        if rc != 0:
            failed.append(fixture)
    if failed:
        print(f"FAIL: {', '.join(failed)}")
        return 1
    print("ALL FIXTURES GREEN")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare", help="create one isolated cold-run workspace")
    prepare_parser.add_argument("fixture", choices=FIXTURES)
    sub.add_parser("prepare-all", help="create isolated workspaces for all fixtures")
    test_parser = sub.add_parser("test", help="run baseline tests for a fixture")
    test_parser.add_argument("fixture", choices=FIXTURES)
    sub.add_parser("test-all", help="run baseline tests for all fixtures")
    grade_parser = sub.add_parser("grade", help="grade a JSON cold-agent report")
    grade_parser.add_argument("report", type=Path)
    replay_parser = sub.add_parser("replay", help="re-verify .sstack/findings/*.json evidence, no agent")
    replay_parser.add_argument("workspace", type=Path)
    eval_parser = sub.add_parser("eval", help="run end-to-end evaluation against an agent/model")
    eval_parser.add_argument("fixture", choices=FIXTURES)
    eval_parser.add_argument("--agent-cmd", help="command template to execute the agent, supporting {prompt} and {workspace}")
    eval_parser.add_argument("--model", help="model name (writes evals/baseline-<model>.json)")
    eval_parser.add_argument("--prompt", help="override default cold agent prompt")
    eval_parser.add_argument("--timeout", type=int, default=600, help="max execution seconds (default 600)")
    args = parser.parse_args()
    if args.command == "prepare":
        print(prepare(args.fixture))
    elif args.command == "prepare-all":
        for fixture in FIXTURES:
            print(prepare(fixture))
    elif args.command == "test":
        return test_fixture(args.fixture)
    elif args.command == "test-all":
        return test_all()
    elif args.command == "replay":
        sys.path.insert(0, str(EVALS))
        from replay import main as replay_main
        return replay_main([str(args.workspace)])
    elif args.command == "eval":
        return run_eval(
            args.fixture,
            agent_cmd=args.agent_cmd,
            model=args.model,
            prompt_override=args.prompt,
            timeout=args.timeout,
        )
    else:
        return grade(args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
