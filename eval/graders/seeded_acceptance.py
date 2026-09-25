"""Deterministic grader for the seeded-acceptance bucket.

A report passes when every finding has the required evidence fields and
at least one confirmed finding has a red-then-green regression. A harness
error is not a confirmed finding.
"""
from __future__ import annotations

import json
from pathlib import Path

REQUIRED = {
    "lens",
    "surface",
    "case",
    "oracle",
    "observed",
    "verdict",
    "repro",
}
VERDICTS = {"confirmed", "refuted", "inconclusive"}


def grade(report: object, goldens: list[dict]) -> dict:
    findings = report.get("findings", []) if isinstance(report, dict) else []
    if not isinstance(findings, list):
        return {"pass": False, "reason": "findings must be a list"}

    known = {g["id"] for g in goldens}
    for finding in findings:
        if not isinstance(finding, dict) or not REQUIRED <= finding.keys():
            return {"pass": False, "reason": "finding missing required evidence fields"}
        if finding["verdict"] not in VERDICTS:
            return {"pass": False, "reason": f"unknown verdict: {finding['verdict']}"}

    confirmed = [f for f in findings if f["verdict"] == "confirmed"]
    red_green = [
        f for f in confirmed
        if f.get("regression", {}).get("before") == "red"
        and f.get("regression", {}).get("after") == "green"
    ]
    seeded = [f for f in red_green if f.get("seed_id") in known]
    return {
        "pass": bool(seeded),
        "confirmed": len(confirmed),
        "red_green": len(red_green),
        "seeded_red_green": len(seeded),
        "reason": None if seeded else "no confirmed seeded finding with red→green regression",
    }


def grade_file(report_path: str, goldens_path: str) -> dict:
    report = json.loads(Path(report_path).read_text())
    goldens = [json.loads(line) for line in Path(goldens_path).read_text().splitlines() if line]
    return grade(report, goldens)
