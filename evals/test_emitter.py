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
EMITTER_JS = ROOT / "skills/sstack/scripts/emit_findings.js"
SKILL = ROOT / "skills/sstack/SKILL.md"
SCRATCH = ROOT / ".sstack" / "scratch"
SCRATCH.mkdir(parents=True, exist_ok=True)

PAYLOAD_KEYS = ["slug", "lens", "surface", "case", "oracle", "verdict",
                "repro", "fix", "regression"]

GENERIC = {
    "get", "set", "add", "run", "main", "init", "load", "save", "read",
    "write", "count", "total", "index", "apply", "reset", "update", "delete",
    "create", "remove", "parse", "print", "value", "values", "items", "data",
}


# Domain nouns that are ordinary English and a plausible thing for a lens
# to say in prose — a generic topic word, not a leaked surface. A seed
# array like `export const orders: Order[]` parses as an identifier but
# is never called, so naming "orders" leaks nothing.
TOPIC_WORDS = {"orders", "order", "items", "users", "carts", "payments",
               "inventory"}

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
    with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
        result = emit(Path(tmp), base())
        assert result.returncode == 0, result.stderr
        record = json.loads((Path(tmp) / ".sstack/findings/t1.json").read_text())
        digest = hashlib.sha256(
            (record["stdout"] + record["stderr"]).encode()).hexdigest()[:16]
        assert record["fingerprint"] == digest


def test_missing_regression_is_rejected():
    with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
        finding = base()
        del finding["regression"]
        assert emit(Path(tmp), finding).returncode == 2


def test_state_tokens_must_be_literal():
    with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
        finding = base()
        finding["regression"]["before"] = "test failed with AssertionError"
        assert emit(Path(tmp), finding).returncode == 2


def test_seven_field_report_format_alone_is_rejected():
    """The Report format block is seven fields; the emitter payload is
    not. This pins why SKILL.md must document the extras separately."""
    report_fields = ("lens", "surface", "case", "oracle", "verdict", "repro")
    with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
        result = emit(Path(tmp), {k: v for k, v in base().items() if k in report_fields})
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
    for opt in ("seed", "counterexample"):
        assert opt in doc.group(1), f"emitter payload paragraph never mentions optional: {opt}"


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
        with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
            result = emit(Path(tmp), base(lens=hostile, slug=None))
            assert result.returncode == 2, f"{hostile!r} was accepted"
            assert "filename fragment" in result.stderr, result.stderr
            assert not list(Path(tmp).parent.glob("etc*"))
    with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
        assert emit(Path(tmp), base(lens="", slug=None)).returncode == 2
    with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
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
    fixture_ids = {n for n in fixture_ids if len(n) >= 6 and n not in GENERIC and n not in TOPIC_WORDS}
    assert fixture_ids, "no fixture identifiers parsed; the check is broken"
    for path in shipped:
        text = path.read_text()
        for name in sorted(fixture_ids):
            assert not re.search(rf"\b{re.escape(name)}\b", text), (
                f"{path.relative_to(ROOT)} names fixture identifier {name!r}")


def emit_js(workspace, finding, fixture="seeded-py"):
    return subprocess.run(
        ["node", str(EMITTER_JS), "--workspace", str(workspace),
         "--fixture", fixture],
        input=json.dumps(finding), capture_output=True, text=True)


def test_node_emitter_contract_parity():
    """emit_findings.js must match emit_findings.py byte-for-byte across schema,
    validation, fingerprinting, and report rebuilding."""
    with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp_py, tempfile.TemporaryDirectory(dir=SCRATCH) as tmp_js:
        finding = base()
        res_py = emit(Path(tmp_py), finding)
        res_js = emit_js(Path(tmp_js), finding)
        assert res_js.returncode == 0, res_js.stderr
        assert res_py.returncode == 0
        py_json = (Path(tmp_py) / ".sstack/findings/t1.json").read_text()
        js_json = (Path(tmp_js) / ".sstack/findings/t1.json").read_text()
        py_obj, js_obj = json.loads(py_json), json.loads(js_json)
        for obj in (py_obj, js_obj):
            obj.pop("emitted_at", None)
            obj.pop("duration_ms", None)
        assert py_obj == js_obj
        py_md = (Path(tmp_py) / ".sstack/findings/t1.md").read_text()
        js_md = (Path(tmp_js) / ".sstack/findings/t1.md").read_text()
        assert py_md == js_md
        py_rep = (Path(tmp_py) / ".sstack/report.json").read_text()
        js_rep = (Path(tmp_js) / ".sstack/report.json").read_text()
        py_rep_obj, js_rep_obj = json.loads(py_rep), json.loads(js_rep)
        for f in py_rep_obj.get("findings", []) + js_rep_obj.get("findings", []):
            f.pop("emitted_at", None)
            f.pop("duration_ms", None)
        assert py_rep_obj == js_rep_obj

        bad_finding = base()
        del bad_finding["regression"]
        assert emit_js(Path(tmp_js), bad_finding).returncode == 2

        bad_token = base()
        bad_token["regression"]["before"] = "fail"
        assert emit_js(Path(tmp_js), bad_token).returncode == 2

        bad_slug = base(slug="../../escape")
        assert emit_js(Path(tmp_js), bad_slug).returncode == 2


def test_pbt_seed_and_counterexample_parity():
    """Optional seed and counterexample fields are recorded in json, rendered in md,
    rebuilt into report.json, and identical across python and node emitters."""
    with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp_py, tempfile.TemporaryDirectory(dir=SCRATCH) as tmp_js:
        finding = base(seed=42891234, counterexample='""')
        res_py = emit(Path(tmp_py), finding)
        res_js = emit_js(Path(tmp_js), finding)
        assert res_py.returncode == 0, res_py.stderr
        assert res_js.returncode == 0, res_js.stderr

        py_rec = json.loads((Path(tmp_py) / ".sstack/findings/t1.json").read_text())
        js_rec = json.loads((Path(tmp_js) / ".sstack/findings/t1.json").read_text())
        assert py_rec["seed"] == 42891234
        assert py_rec["counterexample"] == '""'
        for obj in (py_rec, js_rec):
            obj.pop("emitted_at", None)
            obj.pop("duration_ms", None)
        assert py_rec == js_rec

        py_md = (Path(tmp_py) / ".sstack/findings/t1.md").read_text()
        js_md = (Path(tmp_js) / ".sstack/findings/t1.md").read_text()
        assert "## PBT" in py_md
        assert "seed: `42891234`" in py_md
        assert 'counterexample: `""`' in py_md
        assert py_md == js_md

        py_rep = json.loads((Path(tmp_py) / ".sstack/report.json").read_text())
        js_rep = json.loads((Path(tmp_js) / ".sstack/report.json").read_text())
        assert py_rep["findings"][0]["seed"] == 42891234
        assert py_rep["findings"][0]["counterexample"] == '""'
        for f in py_rep.get("findings", []) + js_rep.get("findings", []):
            f.pop("emitted_at", None)
            f.pop("duration_ms", None)
        assert py_rep == js_rep

        from evals.replay import replay_one
        rep_res = replay_one(Path(tmp_py) / ".sstack/findings/t1.json")
        assert rep_res["seed"] == 42891234
        assert rep_res["integrity"] == "intact"

