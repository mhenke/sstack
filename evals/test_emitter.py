"""Contract tests for the shipped evidence emitter.

These live in the repo's own runner, not in a scratch dir, because
they guard the contract every cold run depends on. Each test fails
when the shipped text and the shipped script disagree.
"""
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EMITTER = ROOT / "skills/sstack/scripts/emit_findings.py"
SKILL = ROOT / "skills/sstack/SKILL.md"

PAYLOAD_KEYS = ["slug", "lens", "surface", "case", "oracle", "verdict",
                "repro", "fix", "regression"]


def emit(workspace, finding, fixture="seeded-py"):
    return subprocess.run(
        [sys.executable, str(EMITTER), "--workspace", str(workspace),
         "--fixture", fixture],
        input=json.dumps(finding), capture_output=True, text=True)


def base(**over):
    finding = {
        "slug": "t1", "lens": "state", "surface": "Cart.count",
        "case": "track then count", "oracle": "returns 2",
        "verdict": "confirmed", "repro": "echo 0",
        "fix": "recompute in count()",
        "regression": {"file": "tests/test_x.py", "test": "t",
                       "before": "red", "after": "green"},
    }
    finding.update(over)
    return finding


def test_documented_payload_emits_and_replays():
    """The documented payload is accepted, and the recorded fingerprint
    is the hash of the recorded output."""
    with tempfile.TemporaryDirectory() as tmp:
        result = emit(Path(tmp), base())
        assert result.returncode == 0, result.stderr
        record = json.loads((Path(tmp) / ".sstack/findings/t1.json").read_text())
        digest = hashlib.sha256(
            (record["stdout"] + record["stderr"]).encode()).hexdigest()[:16]
        assert record["fingerprint"] == digest


def test_missing_regression_is_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        finding = base()
        del finding["regression"]
        assert emit(Path(tmp), finding).returncode == 2


def test_state_tokens_must_be_literal():
    with tempfile.TemporaryDirectory() as tmp:
        finding = base()
        finding["regression"]["before"] = "test failed with AssertionError"
        assert emit(Path(tmp), finding).returncode == 2


def test_seven_field_report_format_alone_is_rejected():
    """The Report format block is seven fields; the emitter payload is
    not. This pins why SKILL.md must document the extras separately."""
    seven = ("lens", "surface", "case", "oracle", "verdict", "repro")
    with tempfile.TemporaryDirectory() as tmp:
        result = emit(Path(tmp), {k: v for k, v in base().items() if k in seven})
        assert result.returncode == 2
        assert "regression" in result.stderr


def test_skill_documents_every_required_payload_key():
    """A cold agent that follows SKILL.md verbatim must produce a
    payload the emitter accepts."""
    text = SKILL.read_text()
    doc = re.search(r"The JSON you pipe is the Report format fields(.*?)\n\n",
                    text, re.S)
    assert doc, "SKILL.md does not document the emitter payload"
    missing = [k for k in PAYLOAD_KEYS if k not in doc.group(1)]
    assert not missing, f"emitter payload paragraph never mentions: {missing}"
