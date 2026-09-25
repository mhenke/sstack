"""Deterministic grader for the seeded-acceptance bucket.

Seed labels are self-reported and cold runs proved agents fill them
unreliably (null, malformed, wrong). The grader therefore matches a
finding to a golden by CONTENT: the trigger's function name or its
distinctive words appearing in the finding's surface + case + oracle.
A pass needs a confirmed red→green finding that content-matches a
golden of the report's fixture, whose regression file exists in the
workspace and contains the named test. The recorded seed_id, when
present, must not contradict the content match.
"""
from __future__ import annotations

import json
import re
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
STOPWORDS = {
    "items", "list", "string", "input", "the", "and", "very", "as",
    "returns", "throw", "named", "domain", "error", "behavior", "silently",
}


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower())


def _trigger_function(trigger: str) -> str | None:
    match = re.search(r"([A-Za-z_]\w*)\s*\(", trigger)
    return match.group(1).lower() if match else None


def _trigger_words(trigger: str) -> set[str]:
    words = {w for w in _norm(trigger).split() if len(w) > 2} - STOPWORDS
    return words


def matches_golden(finding: dict, golden: dict) -> bool:
    text = _norm(" ".join(str(finding.get(k, "")) for k in ("surface", "case", "oracle")))
    function = _trigger_function(golden["trigger"])
    if function and function in text:
        return True
    words = _trigger_words(golden["trigger"])
    return bool(words) and words <= set(text.split())


def _regression_lands(finding: dict, workspace: Path | None) -> bool:
    regression = finding.get("regression")
    if not isinstance(regression, dict) or regression.get("before") != "red" or regression.get("after") != "green":
        return False
    if workspace is None:
        return True
    file = regression.get("file") or ""
    test = regression.get("test") or ""
    candidate = (workspace / file) if file else None
    return bool(
        candidate and candidate.is_file() and (not test or test in candidate.read_text(errors="replace"))
    )


def grade(report: object, goldens: list[dict], workspace: Path | None = None) -> dict:
    findings = report.get("findings", []) if isinstance(report, dict) else []
    if not isinstance(findings, list):
        return {"pass": False, "reason": "findings must be a list"}
    for finding in findings:
        if not isinstance(finding, dict) or not REQUIRED <= finding.keys():
            return {"pass": False, "reason": "finding missing required evidence fields"}
        if finding["verdict"] not in VERDICTS:
            return {"pass": False, "reason": f"unknown verdict: {finding['verdict']}"}

    fixture = report.get("fixture") if isinstance(report, dict) else None
    pool = [g for g in goldens if not fixture or g["repo"] == fixture]
    if fixture and not pool:
        return {"pass": False, "reason": f"unknown fixture: {fixture}"}

    confirmed = [f for f in findings if f["verdict"] == "confirmed"]
    claimed = [
        f for f in confirmed
        if isinstance(f.get("regression"), dict)
        and f["regression"].get("before") == "red"
        and f["regression"].get("after") == "green"
    ]
    matched: list[str] = []
    contradicted: list[str] = []
    for golden in pool:
        for finding in claimed:
            if not matches_golden(finding, golden):
                continue
            label = finding.get("seed_id")
            if label and label != "other" and label != golden["id"]:
                contradicted.append(f"{label}!={golden['id']}")
            if _regression_lands(finding, workspace):
                matched.append(golden["id"])
            break

    return {
        "pass": bool(matched),
        "fixture": fixture,
        "confirmed": len(confirmed),
        "red_green_claimed": len(claimed),
        "seeded_matched": sorted(set(matched)),
        "label_contradictions": sorted(set(contradicted)),
        "reason": None if matched else "no confirmed content-matched golden with a landed red→green regression",
    }


def grade_file(report_path: str, goldens_path: str, workspace: str | None = None) -> dict:
    try:
        report = json.loads(Path(report_path).read_text())
    except json.JSONDecodeError as e:
        return {"pass": False, "reason": f"invalid report JSON: {e.msg} at line {e.lineno} col {e.colno}"}
    goldens = [json.loads(line) for line in Path(goldens_path).read_text().splitlines() if line]
    return grade(report, goldens, Path(workspace) if workspace else None)
