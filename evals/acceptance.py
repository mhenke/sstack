#!/usr/bin/env python3
"""One entry point for preparing and grading cold-agent evaluations.

Usage:
  python3 evals/acceptance.py prepare seeded-py
  python3 evals/acceptance.py prepare-all
  python3 evals/acceptance.py grade path/to/report.json

`prepare` creates an isolated workspace and prints its path. The host
launches its cold agent there. `prepare-all` does this for every fixture.
`grade` scores a JSON report; it never launches or modifies an agent.
"""
import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVALS = ROOT / "evals"
FIXTURES = ("seeded-py", "seeded-ts", "seeded-js", "seeded-java", "seeded-cpp")
EXCLUDED = {".git", ".pytest_cache", "__pycache__", ".vite", "node_modules", "target", "build"}
LENSES = ("boundaries", "malformed", "missing", "ownership", "exceptional-conditions", "resource-exhaustion")


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

def prepare(fixture: str) -> Path:
    if fixture not in FIXTURES:
        raise SystemExit(f"unknown fixture: {fixture}; choose one of {', '.join(FIXTURES)}")
    if fixture == "seeded-java":
        ensure_junit()
    workspace = Path(tempfile.mkdtemp(prefix=f"sstack-{fixture}-"))
    copy_fixture(EVALS / fixture, workspace)
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
    )
    return workspace


def grade(report_path: Path) -> int:
    sys.path.insert(0, str(EVALS / "graders"))
    from seeded_acceptance import grade_file

    result = grade_file(str(report_path), str(EVALS / "goldens.jsonl"))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare", help="create one isolated cold-run workspace")
    prepare_parser.add_argument("fixture", choices=FIXTURES)
    sub.add_parser("prepare-all", help="create isolated workspaces for all fixtures")
    grade_parser = sub.add_parser("grade", help="grade a JSON cold-agent report")
    grade_parser.add_argument("report", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        print(prepare(args.fixture))
    elif args.command == "prepare-all":
        for fixture in FIXTURES:
            print(prepare(fixture))
    else:
        return grade(args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
