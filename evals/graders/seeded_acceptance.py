"""Deterministic grader for the seeded-acceptance bucket.

Seed labels are self-reported and cold runs proved agents fill them
unreliably (null, malformed, wrong). The grader therefore matches a
finding to a golden by CONTENT: the trigger's function name appearing in
the finding's EXECUTED text (`case` + `observed`), never a bare `surface`
restatement, and the finding's oracle must state a behavior the seed's
buggy output does not already satisfy — otherwise naming a function
scores identically to finding its defect.

A pass needs a confirmed red→green finding that content-matches a
golden of the report's fixture, whose regression file was MODIFIED in
the workspace (exists, contains the named test, and differs from the
frozen fixture original — a claim naming an existing test in an
untouched file is a false claim, ColdTs-2), and whose named test was
observed RED against the frozen fixture (bug-pinning: a `confirmed`
finding whose test is green on the unfixed source asserts the buggy
behavior — runs #1 and #7, ColdPy6). The recorded seed_id, when
present, must not contradict the content match.
"""
from __future__ import annotations

import hashlib

import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from acceptance import EXCLUDED, test_fixture  # noqa: E402 — needs the path above

SCRATCH = Path(__file__).resolve().parents[2] / ".sstack" / "scratch"

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
    "with", "from", "into", "that", "this", "when", "then", "call", "calls",
}

# A `surface` is a label; `case` and `observed` are what was executed. A
# finding earns a match only by executing the trigger's function, so the
# match never reads `surface` alone.
EXECUTED_FIELDS = ("case", "observed")

# Words that appear in essentially any defect description. A golden's
# oracle restated verbatim by the finding proves nothing, so matching on
# these alone is refused.
GENERIC_ORACLE_WORDS = {
    "error", "raise", "raises", "raise", "throws", "throw", "must", "value",
    "invalid", "return", "returns", "should", "expected", "instead", "rather",
    "not", "no", "is", "be", "of", "a", "an", "to", "the",
}


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower())


def _trigger_function(trigger: str) -> str | None:
    match = re.search(r"([A-Za-z_]\w*)\s*\(", trigger)
    return match.group(1).lower() if match else None


def _trigger_words(trigger: str) -> set[str]:
    words = {w for w in _norm(trigger).split() if len(w) > 2} - STOPWORDS
    return words


def _executed_text(finding: dict) -> str:
    return _norm(" ".join(str(finding.get(k, "")) for k in EXECUTED_FIELDS))


def _content(text: str) -> set[str]:
    return {w for w in _norm(text).split() if len(w) > 2} - GENERIC_ORACLE_WORDS


def _oracle_contradicts_buggy(finding: dict, golden: dict) -> bool:
    """The oracle must be contract-shaped, not defect-shaped.

    A finding that describes what the code DOES (`returns [] silently`)
    has restated the bug, and a test built on it pins the bug — the
    invalid shape of runs #1 and #7. A finding that describes what the
    code MUST do reaches the seed's recorded contract. Require the
    oracle to overlap the golden's `oracle` strictly more than it
    overlaps the golden's `buggy`, and to name at least one word of the
    contract, so neither an empty oracle nor a reworded crash passes.

    ponytail: demands the finding reach the recorded contract's wording.
    A genuinely independent phrasing still lands a word or two; one that
    shares nothing is indistinguishable from describing the crash, so it
    is refused rather than guessed at.
    """
    oracle = _content(str(finding.get("oracle", "")))
    if not oracle:
        return False
    contract = _content(str(golden.get("oracle", "")))
    buggy = _content(str(golden.get("buggy", "")))
    return len(oracle & contract) >= 1 and len(oracle & contract) > len(oracle & buggy)


def matches_golden(finding: dict, golden: dict) -> bool:
    """True when the finding EXECUTED the golden's trigger on its own terms.

    Three gates, each closing a real false-positive the old matcher
    accepted:
      1. The trigger's function name (or every distinctive trigger word)
         must appear in `case` or `observed` — what was run and printed,
         never `surface`, which is a label an agent can write without
         executing anything.
      2. The finding's oracle must be non-empty.
      3. That oracle must demand a behavior `buggy` does not already
         produce, so restating the defect cannot pass as a contract.
    """
    text = _executed_text(finding)
    if not text:
        return False
    function = _trigger_function(golden["trigger"])
    hit = bool(function) and (function in text or function in str(finding.get("case", "")) or function in str(finding.get("observed", "")))
    if not hit:
        words = _trigger_words(golden["trigger"])
        hit = bool(words) and words <= set(text.split())
    if not hit:
        return False
    return _oracle_contradicts_buggy(finding, golden)


def _regression_lands(finding: dict, workspace: Path | None, pristine: Path | None = None) -> bool:
    regression = finding.get("regression")
    if not isinstance(regression, dict) or regression.get("before") != "red" or regression.get("after") != "green":
        return False
    if workspace is None:
        return True
    file = regression.get("file") or ""
    test = regression.get("test") or ""
    candidate = (workspace / file) if file else None
    if not (candidate and candidate.is_file() and (not test or test in candidate.read_text(errors="replace"))):
        return False
    if pristine and file:
        original = pristine / file
        if original.is_file() and original.read_bytes() == candidate.read_bytes():
            return False
    return True

_TEST_MARKERS = ("/test/", "/tests/", "test_", ".test.", "_test.", "Test.java")
_CONFIG_NAMES = ("CMakeLists.txt", "package.json", "tsconfig.json", "pom.xml",
                 "build.gradle", "Makefile", "settings.gradle")


def _is_test_path(rel: str) -> bool:
    p = "/" + rel.replace("\\", "/").lstrip("/")
    name = p.rsplit("/", 1)[-1]
    return any(marker in p for marker in _TEST_MARKERS) or name.endswith("Test.java")


def _is_config_path(rel: str) -> bool:
    return rel.replace("\\", "/").rsplit("/", 1)[-1] in _CONFIG_NAMES


def _bug_pin_verdict(workspace: Path | None, fixture_dir: Path | None) -> dict | None:
    """Run the agent's tests against the UNFIXED source. All green means pinned.

    A `confirmed` finding claims a test that was red on the defect. Copy
    the frozen fixture (pristine, still buggy) into a temp dir, drop in
    only the agent's test files and its build-config edits, and run the
    suite. Green means every claimed red→green test actually asserts the
    buggy behavior — the invalid shape of runs #1 and #7 and ColdPy6,
    which until now only a human reading a transcript could catch.

    Returns a failure dict, or None when the run is clean or unverifiable.
    ponytail: whole-suite green/non-green, not per-test. That is exactly
    the invalid shape (all confirmed tests passing on unfixed source);
    split per-test only if a run is ever legitimately mixed.
    """
    if not (workspace and fixture_dir and fixture_dir.is_dir()):
        return None
    SCRATCH.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="sstack-bugpin-", dir=SCRATCH)) / fixture_dir.name
    staging.mkdir(parents=True)
    try:
        shutil.copytree(fixture_dir, staging, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(*EXCLUDED, "BUGS.md"))
        src_dep = fixture_dir / "node_modules"
        if src_dep.exists() and not (staging / "node_modules").exists():
            (staging / "node_modules").symlink_to(src_dep)
        for path in workspace.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(workspace).as_posix()
            if not (_is_test_path(rel) or _is_config_path(rel)):
                continue
            target = staging / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        if test_fixture(str(staging)) == 0:
            return {
                "pass": False,
                "reason": "bug-pinned: every confirmed finding's regression is GREEN "
                          "against the unfixed source — the tests assert the defect",
            }
        return None
    finally:
        shutil.rmtree(staging.parent, ignore_errors=True)


def _fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode(errors="replace")).hexdigest()[:16]


def _evidence_integrity(findings_dir: Path) -> str | None:
    """Re-derive each finding's fingerprint from its recorded stdout+stderr.

    The emitter computes the fingerprint itself, so a mismatch means the
    evidence file was edited after emit (hand-typed fingerprint, tampered
    bytes). A graded PASS must not rest on evidence the machine cannot
    verify. Returns a reason string on failure, else None.
    """
    for path in sorted(findings_dir.glob("*.json")):
        try:
            ev = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if "fingerprint" not in ev:
            continue
        recorded = ev.get("fingerprint")
        computed = _fingerprint(ev.get("stdout", "") + ev.get("stderr", ""))
        if recorded != computed:
            return f"evidence integrity failure in {path.name}: recorded fingerprint {recorded} != computed {computed} (file edited after emit)"
    return None


def grade(report: object, goldens: list[dict], workspace: Path | None = None, fixture_dir: Path | None = None) -> dict:
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
    # Evidence integrity: a PASS must not rest on a finding whose
    # fingerprint the machine cannot re-derive (post-emit edit, tampered
    # bytes). Run before the bug-pin control so a corrupted run fails
    # loudly instead of passing on claims we cannot replay.
    if workspace is not None:
        evidence_dir = workspace / ".sstack" / "findings"
        if confirmed and not any(evidence_dir.glob("*.json")):
            return {"pass": False,
                    "reason": "confirmed findings but no evidence files under .sstack/findings — evidence wiped or never emitted",
                    "fixture": fixture, "confirmed": len(confirmed),
                    "red_green_claimed": len(claimed)}
        integrity_fail = _evidence_integrity(evidence_dir)
        if integrity_fail:
            return {"pass": False, "reason": integrity_fail, "fixture": fixture,
                    "confirmed": len(confirmed), "red_green_claimed": len(claimed)}
        unlanded = [f for f in claimed if not _regression_lands(f, workspace, fixture_dir)]
        if unlanded:
            return {"pass": False,
                    "reason": f"{len(unlanded)} confirmed finding(s) claim a red→green regression that never landed on disk",
                    "fixture": fixture, "confirmed": len(confirmed),
                    "red_green_claimed": len(claimed)}
    # The negative control: every confirmed finding's regression must be
    # RED against the unfixed source. Run before matching so a bug-pinned
    # run fails loudly instead of passing on a function name.
    pinned = _bug_pin_verdict(workspace, fixture_dir) if claimed else None
    if pinned:
        return {"pass": False, **pinned, "fixture": fixture,
                "confirmed": len(confirmed), "red_green_claimed": len(claimed)}
    matched: list[str] = []
    contradicted: list[str] = []
    for golden in pool:
        for finding in claimed:
            if not matches_golden(finding, golden):
                continue
            label = finding.get("seed_id")
            if label and label != "other" and label != golden["id"]:
                contradicted.append(f"{label}!={golden['id']}")
            if _regression_lands(finding, workspace, fixture_dir):
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


def grade_file(report_path: str, goldens_path: str, workspace: str | None = None, fixture_dir: str | None = None) -> dict:
    try:
        report = json.loads(Path(report_path).read_text())
    except json.JSONDecodeError as e:
        return {"pass": False, "reason": f"invalid report JSON: {e.msg} at line {e.lineno} col {e.colno}"}
    goldens = [json.loads(line) for line in Path(goldens_path).read_text().splitlines() if line]
    return grade(
        report,
        goldens,
        Path(workspace) if workspace else None,
        Path(fixture_dir) if fixture_dir else None,
    )
