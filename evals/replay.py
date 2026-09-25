#!/usr/bin/env python3
"""Re-verify sstack evidence files with no agent in the loop.

Usage:
  python3 evals/acceptance.py replay <workspace>

For each `.sstack/findings/<slug>.json` recorded by a finished run:

  integrity  recompute sha256[:16](stdout+stderr) and compare to the
             recorded fingerprint. A mismatch means the evidence file
             was fabricated or edited after capture — the recorded
             bytes are not what the command produced.
  drift      re-run the recorded command and note whether output
             still matches. Drift is EXPECTED for confirmed findings
             whose fix landed (the source changed); it is evidence
             against refuted findings and a free post-fix observation
             for confirmed ones.

Exit 0 when every evidence file is intact.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REQUIRED_KEYS = {"command", "exit_code", "stdout", "verdict"}


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode(errors="replace")).hexdigest()[:16]


def replay_one(path: Path) -> dict:
    try:
        ev = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return {"finding": path.stem, "integrity": "unparseable", "detail": str(e)}
    missing = REQUIRED_KEYS - ev.keys()
    if missing:
        return {"finding": path.stem, "integrity": "incomplete", "missing": sorted(missing)}
    recorded = ev.get("fingerprint")
    computed = fingerprint(ev["stdout"] + ev.get("stderr", ""))
    integrity = "intact" if recorded == computed else "fabricated"
    result = {"finding": path.stem, "integrity": integrity}
    if integrity == "fabricated":
        result["fingerprint"] = {"recorded": recorded, "computed": computed}
    try:
        run = subprocess.run(ev["command"], shell=True, capture_output=True, text=True,
                             cwd=path.parents[2], timeout=120)
        result["drift"] = (run.returncode != ev["exit_code"]
                           or fingerprint(run.stdout + run.stderr) != computed)
    except (subprocess.TimeoutExpired, OSError) as e:
        result["drift"] = f"error: {e.__class__.__name__}"
    return result


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    ws = Path(argv[0])
    findings = sorted((ws / ".sstack" / "findings").glob("*.json"))
    if not findings:
        print(f"no evidence JSONs under {ws}/.sstack/findings/", file=sys.stderr)
        return 1
    results = [replay_one(f) for f in findings]
    for r in results:
        print(json.dumps(r, sort_keys=True))
    return 0 if all(r["integrity"] == "intact" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
