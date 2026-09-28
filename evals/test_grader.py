"""Contract tests for the acceptance grader's two negative controls.

The grader decides whether a cold run counts as evidence. Two of its
gates were prose-only until this file existed, and both gate shapes were
observed succeeding on invalid runs:

  * bug-pinning — runs #1 and #7 reported 9 and 10 `confirmed` findings
    whose regressions were green because they asserted the defect. The
    grader matched them on the function name and passed them.
  * function-name matching — an unexecuted finding naming the surface
    matched a golden, so "content-matched" proved nothing about the
    defect.

These tests pin the rejects (a regression here is a grader that has
stopped catching an invalid run) and the accepts (a grader too strict
discards a real finding, which is the other failure).
"""
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "evals" / "graders"))

from seeded_acceptance import grade, matches_golden  # noqa: E402

GOLDENS = [json.loads(line) for line in (ROOT / "evals/goldens.jsonl").read_text().splitlines() if line.strip()]
PY = [g for g in GOLDENS if g["repo"] == "seeded-py"]
FIXTURE = ROOT / "evals/seeded-py"


def finding(**over):
    base = {
        "lens": "boundaries", "surface": "paginate",
        "case": "paginate(items, 0, 3) with page=0",
        "oracle": "ValueError: page must be >= 1",
        "observed": "returns [] silently", "verdict": "confirmed",
        "repro": "pytest -q tests/test_shop.py",
        "regression": {"file": "tests/test_shop.py", "test": "test_page_zero",
                       "before": "red", "after": "green"},
    }
    base.update(over)
    return base


SCRATCH = ROOT / ".sstack" / "scratch"


@pytest.fixture
def workspace():
    """A copy of the frozen seeded-py fixture, still buggy."""
    SCRATCH.mkdir(parents=True, exist_ok=True)
    ws = Path(tempfile.mkdtemp(prefix="sstack-grader-ws-", dir=SCRATCH))
    shutil.copytree(FIXTURE, ws, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("BUGS.md", "__pycache__", ".pytest_cache"))
    yield ws
    shutil.rmtree(ws, ignore_errors=True)


def land(ws, test_src):
    (ws / "tests").mkdir(exist_ok=True)
    (ws / "tests/test_shop.py").write_text(test_src)


ORACLE_TEST = (
    "import pytest\n"
    "from shop.pagination import paginate\n\n"
    "def test_page_zero():\n"
    "    with pytest.raises(ValueError, match='page must be >= 1'):\n"
    "        paginate([1, 2, 3], 0, 3)\n"
)
BUG_PINNING_TEST = (
    "from shop.pagination import paginate\n\n"
    "def test_page_zero():\n"
    "    assert paginate([1, 2, 3], 0, 3) == []  # asserts the defect\n"
)


# --- gate 1: an unexecuted or restating finding must not match -----------

def test_surface_only_finding_rejected():
    """Naming a function is not finding its defect."""
    assert not matches_golden(finding(case="", observed="", oracle=""), PY[0])


def test_keyword_soup_finding_rejected():
    soup = finding(surface="cart paginate order line_total", case="", observed="", oracle="")
    assert not any(matches_golden(soup, g) for g in PY)


def test_empty_oracle_rejected():
    assert not matches_golden(finding(oracle=""), PY[0])


def test_defect_shaped_oracle_rejected():
    """An oracle describing what the code DOES pins the bug it observed."""
    assert not matches_golden(finding(oracle="returns [] silently"), PY[0])


# --- gate 2: a real finding still matches, across lenses -----------------

@pytest.mark.parametrize("golden_id", ["py-1", "py-3", "py-7", "py-12", "py-15"])
def test_real_findings_still_match(golden_id):
    golden = next(g for g in GOLDENS if g["id"] == golden_id)
    probe = finding(
        case=f"{golden['trigger']} against the seeded surface",
        oracle=golden["oracle"],
        observed=golden["buggy"],
    )
    assert matches_golden(probe, golden), f"{golden_id} must remain matchable"


# --- gate 3: the negative control, end to end ---------------------------

def test_bug_pinned_run_fails(workspace):
    """The invalid shape of runs #1 and #7 must not pass the grader."""
    land(workspace, BUG_PINNING_TEST)
    result = grade({"fixture": "seeded-py", "findings": [finding()]}, PY, workspace, FIXTURE)
    assert result["pass"] is False
    assert "bug-pin" in (result.get("reason") or "")


def test_genuine_run_passes(workspace):
    """A regression asserting the oracle is red on unfixed source: the run counts."""
    land(workspace, ORACLE_TEST)
    result = grade({"fixture": "seeded-py", "findings": [finding()]}, PY, workspace, FIXTURE)
    assert result["pass"] is True
    assert result["seeded_matched"] == ["py-1"]


def test_no_workspace_leaves_the_negative_control_unrun(workspace):
    """Grading a bare report cannot execute anything, so it must not claim the control."""
    land(workspace, BUG_PINNING_TEST)
    result = grade({"fixture": "seeded-py", "findings": [finding()]}, PY, None, None)
    assert "bug-pin" not in (result.get("reason") or "")


# --- gate 4: evidence integrity ------------------------------------------
#
# The emitter computes the fingerprint itself, so a mismatch means the
# evidence file was edited after emit (ColdPy-19: 11 of 29 findings
# had recorded fingerprints that did not match recomputation from their
# own stdout+stderr). A graded PASS must not rest on such evidence.


def _seed_evidence(ws, fingerprint: str):
    findings = ws / ".sstack" / "findings"
    findings.mkdir(parents=True, exist_ok=True)
    evidence = {
        "command": "python3 -c \"print(1)\"",
        "stdout": "1\n",
        "stderr": "",
        "exit_code": 0,
        "fingerprint": fingerprint,
        "verdict": "confirmed",
    }
    (findings / "probe.json").write_text(json.dumps(evidence))


def test_fabricated_fingerprint_fails_grade(workspace):
    """A hand-edited fingerprint must fail the grade, not just replay."""
    land(workspace, ORACLE_TEST)
    _seed_evidence(workspace, "deadbeef00000000")
    result = grade({"fixture": "seeded-py", "findings": [finding()]}, PY, workspace, FIXTURE)
    assert result["pass"] is False
    assert "integrity" in (result.get("reason") or "")


def test_intact_fingerprint_still_passes(workspace):
    """A genuine emit re-derives to the same hash and must not be blocked."""
    land(workspace, ORACLE_TEST)
    _seed_evidence(workspace, "4355a46b19d348dc")  # sha256("1\n")[:16]
    result = grade({"fixture": "seeded-py", "findings": [finding()]}, PY, workspace, FIXTURE)
    assert result["pass"] is True
