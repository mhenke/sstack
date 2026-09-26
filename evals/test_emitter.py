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

GENERIC = {
    "get", "set", "add", "run", "main", "init", "load", "save", "read",
    "write", "count", "total", "index", "apply", "reset", "update", "delete",
    "create", "remove", "parse", "print", "value", "values", "items", "data",
}


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


def test_customization_contract_is_documented():
    """A user must be able to extend sstack without editing a file the
    pack ships, and without guessing the naming rule. The contract is
    the `sstack-` prefix across skills and agents dirs."""
    text = SKILL.read_text()
    section = re.search(r"## Customization\n(.*?)\n## ", text, re.S)
    assert section, "SKILL.md has no Customization section"
    body = section.group(1)
    for token in ("sstack-<lens>", "sstack-<lens>-attacker.md",
                  ".agents/skills", "~/.agents/skills", "lenses.remove",
                  "disable-model-invocation", "applies-when",
                  "filename fragment"):
        assert token in body, f"Customization never mentions {token}"
    assert "append" in body, "a custom lens appends, never replaces"
    assert "replaced wholesale on update" in body, (
        "the pack's own skills/ and agents/ must be declared off-limits "
        "for user files, or an update silently deletes their work")
    assert ".sstack/lenses" not in text, (
        "the old bespoke lens directory is gone; a lens is a skill")
    assert "lenses.add" not in body, (
        "presence in the tree opts a lens in; no add directive exists")
    assert re.search(r"host-repo>/\.agents/skills", text), (
        "the skills dir is never resolved against the host repo, so a "
        "cold agent has no path to look in")
    assert "sstack-<stage>" not in text, (
        "stages live in the orchestrator's own text and are not "
        "extensible; a seam for them is a promise nothing implements")
    assert "unused" in body, (
        "an agent with no lens silently does nothing unless the run "
        "reports it, which is a weakened run reading as a clean one")


def test_lens_name_cannot_escape_the_findings_dir():
    """A lens name reaches a filename. It comes from user-authored
    frontmatter now that custom lenses exist, so `lens: ../../etc`
    would otherwise write outside the workspace."""
    for hostile in ("../../etc", "a/b", "..", "/abs"):
        with tempfile.TemporaryDirectory() as tmp:
            result = emit(Path(tmp), base(lens=hostile, slug=None))
            assert result.returncode == 2, f"{hostile!r} was accepted"
            assert "filename fragment" in result.stderr, result.stderr
            assert not list(Path(tmp).parent.glob("etc*"))
    with tempfile.TemporaryDirectory() as tmp:
        assert emit(Path(tmp), base(lens="", slug=None)).returncode == 2
    with tempfile.TemporaryDirectory() as tmp:
        result = emit(Path(tmp), base(slug="../../pwn"))
        assert result.returncode == 2
        assert "filename fragment" in result.stderr


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


def test_shipped_text_names_no_fixture_identifier():
    """A worked example that names a fixture's function or class lets a
    cold run match a golden by echoing the prompt instead of finding the
    bug. This has shipped three times: the ownership lens named
    `search_orders`, the state lens named `Cart`, and the missing and
    malformed lenses both named `line_total`/`lineTotal` with the three
    planted pricing oracles."""
    shipped = [p for p in list((ROOT / "skills").rglob("*.md"))
               + list((ROOT / "agents").rglob("*.md"))]
    fixture_ids = set()

    patterns = (r"^\s*(?:class|def)\s+([A-Za-z_]\w{4,})",
                r"export\s+(?:function|const|class)\s+([A-Za-z_]\w{4,})",
                r"\b(?:public|private)?\s*(?:function|def)\s+([A-Za-z_]\w{4,})")
    for path in (ROOT / "evals").glob("seeded-*/*/*"):
        if path.suffix not in (".py", ".ts", ".js", ".java", ".cpp"):
            continue
        text = path.read_text(errors="replace")
        for pattern in patterns:
            fixture_ids.update(re.findall(pattern, text, re.M))
    # Short, generic method names ("count", "get") collide with ordinary
    # English and every host language; only distinctive names can leak an
    # answer. Contamination that matters names a domain noun.
    fixture_ids = {n for n in fixture_ids if len(n) >= 6 and n not in GENERIC}
    assert fixture_ids, "no fixture identifiers parsed; the check is broken"
    for path in shipped:
        text = path.read_text()
        for name in sorted(fixture_ids):
            assert not re.search(rf"\b{re.escape(name)}\b", text), (
                f"{path.relative_to(ROOT)} names fixture identifier {name!r}")
