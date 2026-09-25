#!/usr/bin/env python3
"""Re-verify sstack findings from evidence alone — no agent in the loop.

Usage:
  python3 evals/replay.py <workspace>

Reads <workspace>/.sstack/findings/*.json (the machine view the skill
requires), re-runs each finding's recorded command, and compares the
live result against the recorded exit code and output fingerprint.

Per-finding verdicts:
  verified   command re-ran, exit code and fingerprint match the record
  mismatch   command re-ran, result differs from the record
  unverifiable  evidence missing fields the replay needs
Exit 0 when every finding is verified.
"""
import json
import sys
from pathlib import Path


def fingerprint(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode(errors="replace")).hexdigest()[:16]


def replay_one(path: Path) -> dict:
    ev = json.loads(path.read_text())
    need = ("command", "exit_code", "stdout", "verdict")
    missing = [k for k in need if k not in ev]
    if missing:
        return {"finding": path.stem, "verdict": "unverifiable", "missing": missing}
    import subprocess

    run = subprocess.run(ev["command"], shell=True, capture_output=True, text=True, cwd=path.parents[2], timeout=120)
    live_fp = fingerprint(run.stdout + run.stderr)
    recorded_fp = ev.get("fingerprint") or fingerprint(ev["stdout"])
    ok = run.returncode == ev["exit_code"] and live_fp == recorded_fp
    return {"finding": path.stem, "verdict": "verified" if ok else "mismatch",
            "exit": (ev["exit_code"], run.returncode), "fingerprint": (recorded_fp, live_fp)}


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
    return 0 if all(r["verdict"] == "verified" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
