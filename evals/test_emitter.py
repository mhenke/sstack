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


def test_readme_runtime_claim_matches_the_tree():
    """README promises what the pack ships. It used to say 'it is
    Markdown' while the pack carried a Python script."""
    readme = (ROOT / "README.md").read_text()
    if "It is Markdown" in readme:
        raise AssertionError(
            "README claims the pack is Markdown-only; "
            f"the tree ships {EMITTER.relative_to(ROOT)}")
    assert "emit_findings.py" in readme or "Markdown plus" in readme


def test_custom_lens_contract_is_documented():
    """A cold agent must be able to run a target-repo lens without
    guessing. The pack documents where lenses live, how they are
    selected, and that they append rather than replace."""
    text = SKILL.read_text()
    section = re.search(r"## Custom lenses\n(.*?)\n## ", text, re.S)
    assert section, "SKILL.md has no Custom lenses section"
    body = section.group(1)
    for token in (".sstack/config.md", ".sstack/lenses/", "lenses.add",
                  "lenses.remove", "frontmatter"):
        assert token in body, f"Custom lenses never mentions {token}"
    assert "append" in body, "custom lens must append to the built-in rubric"


def test_custom_lens_files_stay_versionable():
    """Run output is ignored, authored config is not. If the negation
    is lost, a team's lenses vanish with the next clean."""
    probe = ROOT / ".sstack/config.md"
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", str(probe)],
        cwd=ROOT, capture_output=True)
    assert ignored.returncode != 0, (
        ".sstack/config.md is gitignored; authored lenses cannot be shared")


def test_every_attacker_scratch_path_follows_its_lens():
    """One attacker can run several lenses now. Its scratch path is
    parameterized so a custom lens never writes into a built-in's dir."""
    for attacker in sorted((ROOT / "agents").glob("sstack-*-attacker.md")):
        lens = attacker.name[len("sstack-"):-len("-attacker.md")]
        text = attacker.read_text()
        assert ".sstack/scratch/<lens>/" in text, (
            f"{attacker.name} still hardcodes one scratch directory")
        assert f"(this lens: `{lens}`)" in text, (
            f"{attacker.name} does not name its own lens")
        assert "appended custom lens" in text, (
            f"{attacker.name} does not route an appended lens elsewhere")
