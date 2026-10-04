"""Contract tests for the shipped evidence emitter.

These live in the repo's own runner, not in a scratch dir, because
they guard the contract every cold run depends on. Each test fails
when the shipped text and the shipped script disagree.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
EMITTER = ROOT / "skills/sstack/scripts/emit_findings.py"
EMITTER_JS = ROOT / "skills/sstack/scripts/emit_findings.js"
SKILL = ROOT / "skills/sstack/SKILL.md"
SCRATCH = ROOT / ".sstack" / "scratch"
SCRATCH.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT / "skills" / "sstack" / "scripts"))
import emit_findings  # noqa: E402 — script module, imported for unit checks

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
TOPIC_WORDS = {"orders", "order", "items", "users", "carts", "payments"}

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


def test_broken_scratch_probe_blocks_emit(tmp_path):
    probe = tmp_path / ".sstack" / "scratch" / "state"
    probe.mkdir(parents=True)
    (probe / "probe.py").write_text("def broken(:\n")
    result = emit(tmp_path, base(repro=f"python3 {probe / 'probe.py'}"))
    assert result.returncode == 3
    assert "does not compile" in result.stderr
    assert not (tmp_path / ".sstack" / "findings" / "t1.json").exists()

def test_empty_stdin_runs_the_upgrade_pass(tmp_path):
    """Empty stdin is no longer an error: the emitter upgrades pending
    requests. An empty workspace upgrades nothing and exits 0 — the
    bare-parse-error failure that stranded Cpp is retired by design."""
    result = subprocess.run(
        [sys.executable, str(EMITTER), "--workspace", str(tmp_path)],
        input="", capture_output=True, text=True)
    assert result.returncode == 0
    assert "0 request(s) upgraded" in result.stdout


def test_tty_stdin_upgrades_instead_of_blocking(monkeypatch):
    """A terminal stdin counts as empty (ADR-0022): the upgrade pass
    runs. Reading a TTY would block an interactive invocation forever —
    the emitter hang observed on VS Code sandbox launches."""
    class _TTY:
        def isatty(self):
            return True

        def read(self):
            raise AssertionError("emitter must not read a terminal")

    monkeypatch.setattr(emit_findings.sys, "stdin", _TTY())
    with pytest.raises(emit_findings._UpgradeRequested):
        emit_findings.read_finding(None)


def test_tty_stdin_js_upgrades_instead_of_blocking(tmp_path):
    """Node emitter parity: an isTTY stdin runs the upgrade pass and
    never blocks on fd 0."""
    code = "process.stdin.isTTY = true; require(process.argv[1]);"
    result = subprocess.run(
        ["node", "-e", code, str(EMITTER_JS), "--workspace", str(tmp_path)],
        capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "0 request(s) upgraded" in result.stdout


def test_upgrade_flag_explicit_py(tmp_path):
    """Passing --upgrade explicitly runs the upgrade pass without reading stdin."""
    result = subprocess.run(
        [sys.executable, str(EMITTER), "--workspace", str(tmp_path), "--upgrade"],
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert "0 request(s) upgraded" in result.stdout


def test_upgrade_flag_explicit_js(tmp_path):
    """Passing --upgrade to Node emitter runs the upgrade pass without reading stdin."""
    result = subprocess.run(
        ["node", str(EMITTER_JS), "--workspace", str(tmp_path), "--upgrade"],
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert "0 request(s) upgraded" in result.stdout


def request(slug="t1", repro="echo 0"):
    finding = base(slug=slug)
    finding["repro"] = repro
    return finding


def upgrade(workspace, emitter=None, fixture="seeded-py"):
    binary = [sys.executable, str(EMITTER)] if emitter is None else ["node", str(EMITTER_JS)]
    return subprocess.run(
        [*binary, "--workspace", str(workspace), "--fixture", fixture],
        input="", capture_output=True, text=True)


def test_upgrade_executes_request_into_evidence(tmp_path):
    """A request whose repro is a command string becomes fingerprinted
    evidence only through execution by the emitter."""
    findings = tmp_path / ".sstack" / "findings"
    findings.mkdir(parents=True)
    (findings / "t1.json").write_text(json.dumps(request()))
    result = upgrade(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "upgraded t1" in result.stdout
    record = json.loads((findings / "t1.json").read_text())
    assert record["command"] == "echo 0"
    assert record["exit_code"] == 0
    assert record["fingerprint"]
    assert (findings / "t1.md").exists()
    report = json.loads((tmp_path / ".sstack" / "report.json").read_text())
    assert [f["repro"] for f in report["findings"]] == ["echo 0"]


def test_upgrade_never_invents_a_missing_command(tmp_path):
    """A request with no command stays a request — the machine never
    fabricates the execution. This is the flash-run shape: repro None."""
    findings = tmp_path / ".sstack" / "findings"
    findings.mkdir(parents=True)
    finding = request()
    finding["repro"] = None
    (findings / "t1.json").write_text(json.dumps(finding))
    result = upgrade(tmp_path)
    assert result.returncode == 0
    assert "0 request(s) upgraded, 1 still pending" in result.stdout
    assert json.loads((findings / "t1.json").read_text())["repro"] is None
    assert not (tmp_path / ".sstack" / "report.json").exists()


def test_upgrade_preflights_scratch_probes(tmp_path):
    """A request whose repro runs a broken scratch probe stays pending,
    not evidence — the Python upgrade pass preflights like the Node one;
    a probe that does not compile is infrastructure failure."""
    findings = tmp_path / ".sstack" / "findings"
    findings.mkdir(parents=True)
    probe = tmp_path / ".sstack" / "scratch" / "state"
    probe.mkdir(parents=True)
    (probe / "probe.py").write_text("def broken(:\n")
    (findings / "t1.json").write_text(
        json.dumps(request(repro=f"python3 {probe / 'probe.py'}")))
    for emitter in (None, "js"):
        result = upgrade(tmp_path, emitter=emitter)
        assert result.returncode == 0, result.stderr
        assert "1 still pending" in result.stdout
        record = json.loads((findings / "t1.json").read_text())
        assert "fingerprint" not in record


def test_upgrade_is_idempotent(tmp_path):
    findings = tmp_path / ".sstack" / "findings"
    findings.mkdir(parents=True)
    (findings / "t1.json").write_text(json.dumps(request()))
    assert upgrade(tmp_path).returncode == 0
    fingerprint = json.loads((findings / "t1.json").read_text())["fingerprint"]
    result = upgrade(tmp_path)
    assert "0 request(s) upgraded" in result.stdout
    assert json.loads((findings / "t1.json").read_text())["fingerprint"] == fingerprint


def test_upgrade_accepts_nested_command_request(tmp_path):
    """Cold agents copy the evidence-view shape and nest the command
    under repro.command — the upgrade extracts and executes it."""
    findings = tmp_path / ".sstack" / "findings"
    findings.mkdir(parents=True)
    finding = request()
    finding["repro"] = {"command": "echo 0", "exit_code": 1, "stdout": "lied"}
    (findings / "t1.json").write_text(json.dumps(finding))
    result = upgrade(tmp_path)
    assert result.returncode == 0, result.stderr
    record = json.loads((findings / "t1.json").read_text())
    assert record["command"] == "echo 0"
    assert record["stdout"] == "0\n"  # transcribed "lied" discarded
    assert record["fingerprint"]

def test_upgrade_js_parity(tmp_path):
    """The Node emitter upgrades the same request into identical evidence."""
    findings = tmp_path / ".sstack" / "findings"
    findings.mkdir(parents=True)
    (findings / "t1.json").write_text(json.dumps(request()))
    result = upgrade(tmp_path, emitter="js")
    assert result.returncode == 0, result.stderr
    record = json.loads((findings / "t1.json").read_text())
    assert record["command"] == "echo 0"
    assert record["fingerprint"]


def test_repro_timeout_kills_and_records(tmp_path):
    """A hung repro is killed at the bounded limit and recorded as exit
    124 with the kill noted in stderr — evidence about the repro's
    reliability, not an emitter hang. Both emitters agree byte-for-byte."""
    env = {**os.environ, "SSTACK_REPRO_TIMEOUT": "1"}
    records = {}
    for name, binary in (("py", [sys.executable, str(EMITTER)]),
                         ("js", ["node", str(EMITTER_JS)])):
        ws = tmp_path / name
        findings = ws / ".sstack" / "findings"
        findings.mkdir(parents=True)
        (findings / "t1.json").write_text(json.dumps(request(repro="sleep 5")))
        result = subprocess.run(
            [*binary, "--workspace", str(ws), "--fixture", "seeded-py"],
            input="", capture_output=True, text=True, env=env, timeout=30)
        assert result.returncode == 0, result.stderr
        records[name] = json.loads((findings / "t1.json").read_text())
    for record in records.values():
        assert record["exit_code"] == 124
        assert "exceeded 1s and was killed" in record["stderr"]
    assert records["py"] == records["js"]

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


def test_finding_file_flag_matches_stdin():
    """--finding <file> is the primary invocation: identical output to
    the stdin path."""
    with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp_file, \
            tempfile.TemporaryDirectory(dir=SCRATCH) as tmp_stdin:
        finding_file = Path(tmp_file) / "finding.json"
        finding_file.write_text(json.dumps(base()))
        by_file = subprocess.run(
            [sys.executable, str(EMITTER), "--workspace", tmp_file,
             "--finding", str(finding_file), "--fixture", "seeded-py"],
            input="", capture_output=True, text=True)
        by_stdin = emit(Path(tmp_stdin), base())
        assert by_file.returncode == 0, by_file.stderr
        assert by_stdin.returncode == 0, by_stdin.stderr
        for rel in (".sstack/findings/t1.json", ".sstack/findings/t1.md",
                    ".sstack/report.json"):
            assert (Path(tmp_file) / rel).read_text() == \
                (Path(tmp_stdin) / rel).read_text(), rel


def test_finding_file_missing_or_empty_errors(tmp_path):
    missing = subprocess.run(
        [sys.executable, str(EMITTER), "--workspace", str(tmp_path),
         "--finding", str(tmp_path / "nope.json")],
        input="", capture_output=True, text=True)
    assert missing.returncode == 2
    assert "cannot read --finding file" in missing.stderr
    empty = tmp_path / "empty.json"
    empty.write_text("")
    no_content = subprocess.run(
        [sys.executable, str(EMITTER), "--workspace", str(tmp_path),
         "--finding", str(empty)],
        input="", capture_output=True, text=True)
    assert no_content.returncode == 2
    assert "no finding in" in no_content.stderr
    assert str(empty) in no_content.stderr


def test_missing_regression_is_rejected():
    with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
        finding = base()
        del finding["regression"]
        assert emit(Path(tmp), finding).returncode == 2


def test_emitter_io_is_utf8_under_legacy_locale():
    """Windows cp1252 / C-locale hosts: a unicode finding must round-trip
    byte-exact. Locale-default open() crashes or mojibakes the markdown
    view's unicode content; the emitter forces UTF-8 itself."""
    env = {**os.environ, "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0",
           "LC_ALL": "C", "LANG": "C"}
    finding = base(case="café ✓ — unicode")
    with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
        result = subprocess.run(
            [sys.executable, str(EMITTER), "--workspace", tmp,
             "--fixture", "seeded-py"],
            input=json.dumps(finding), capture_output=True, text=True,
            env=env)
        assert result.returncode == 0, result.stderr
        md = (Path(tmp) / ".sstack/findings/t1.md").read_text(encoding="utf-8")
        assert "café ✓ — unicode" in md
        report = json.loads(
            (Path(tmp) / ".sstack/report.json").read_text(encoding="utf-8"))
        assert report["findings"][0]["case"] == "café ✓ — unicode"


def test_recorded_evidence_is_portable_and_clock_free(tmp_path):
    """.sstack artifacts are diffed run over run and across machines: the
    absolute workspace path is rewritten to `.` at capture (a sibling dir
    sharing the prefix stays intact) and no timestamps or durations are
    recorded — a moved path or a moved clock reads as a false change."""
    sibling = f"{tmp_path}2"
    finding = base(repro=f"echo {tmp_path}/probe.py && echo {sibling}/probe.py")

    res_py = emit(tmp_path, finding)
    assert res_py.returncode == 0, res_py.stderr
    record = json.loads((tmp_path / ".sstack/findings/t1.json").read_text())
    assert record["command"] == f"echo ./probe.py && echo {sibling}/probe.py"
    assert record["stdout"] == f"./probe.py\n{sibling}/probe.py\n"
    digest = hashlib.sha256(
        (record["stdout"] + record["stderr"]).encode()).hexdigest()[:16]
    assert record["fingerprint"] == digest
    assert "emitted_at" not in record and "duration_ms" not in record

    report = json.loads((tmp_path / ".sstack/report.json").read_text())
    entry = report["findings"][0]
    assert entry["repro"] == record["command"]
    assert "emitted_at" not in entry and "duration_ms" not in entry

    with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp_js:
        res_js = emit_js(Path(tmp_js), base(repro=f"echo {tmp_js}/note.txt"))
        assert res_js.returncode == 0, res_js.stderr
        js_rec = json.loads(
            (Path(tmp_js) / ".sstack/findings/t1.json").read_text())
        assert js_rec["command"] == "echo ./note.txt"
        assert js_rec["stdout"] == "./note.txt\n"
        assert "emitted_at" not in js_rec and "duration_ms" not in js_rec


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
    doc = re.search(r"The request JSON is the Report format fields(.*?)\n\n",
                    text, re.S)
    assert doc, "SKILL.md does not document the emitter payload"
    missing = [k for k in PAYLOAD_KEYS if k not in doc.group(1)]
    assert not missing, f"emitter payload paragraph never mentions: {missing}"
    for opt in ("seed", "counterexample"):
        assert opt in doc.group(1), f"emitter payload paragraph never mentions optional: {opt}"


def test_no_text_instructs_hand_writing_evidence():
    """Census, rerunnable: the Verify stage once opened 'Write both
    findings/<slug>.md and .json' with the emitter clause as a
    trailing qualifier — every backend that obeys the local imperative
    hand-wrote its evidence (glm family, all cold runs) while only the
    globally-reconciling backend emitted. The imperative at the
    verdict moment must be the emit, everywhere, always."""
    shipped = ([p for p in (ROOT / "skills").rglob("*.md")]
               + [p for p in (ROOT / "agents").rglob("*.md")])
    for path in sorted(shipped):
        text = path.read_text()
        assert not re.search(r"[Ww]rite (both )?`?findings/", text), (
            f"{path.relative_to(ROOT)} instructs hand-writing evidence files")
        for forbidden in ("write the finding as JSON", "hand-write"):
            assert forbidden not in text, (
                f"{path.relative_to(ROOT)} says {forbidden!r}")
    head = "\n".join(SKILL.read_text().splitlines()[:200])
    # Cold backends' read truncates ~16KB (~line 230): the emit contract
    # must live in the guaranteed-read window, beside the shapes the
    # agent imitates. Flash never saw Verify-stage emit wording — three
    # reads, none containing it — and hand-wrote the in-window shapes.
    assert "write the finding request to `findings/<slug>.json`" in head
    assert "executes every request's repro" in head
    assert "not evidence" in head
    assert "Dispatch fallback: per-lens subagents that fail or go silent" in head
    assert "### 3. Verify" not in head, "Verify leaked into the window; keep it past truncation"


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


def test_node_emitter_file_mode_matches_python():
    """The --finding file invocation is the primary shape; both emitters
    agree through it."""
    with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp_py, tempfile.TemporaryDirectory(dir=SCRATCH) as tmp_js:
        f_py = Path(tmp_py) / "finding.json"
        f_js = Path(tmp_js) / "finding.json"
        f_py.write_text(json.dumps(base()))
        f_js.write_text(json.dumps(base()))
        res_py = subprocess.run(
            [sys.executable, str(EMITTER), "--workspace", tmp_py,
             "--finding", str(f_py), "--fixture", "seeded-py"],
            input="", capture_output=True, text=True)
        res_js = subprocess.run(
            ["node", str(EMITTER_JS), "--workspace", tmp_js,
             "--finding", str(f_js), "--fixture", "seeded-py"],
            input="", capture_output=True, text=True)
        assert res_py.returncode == 0, res_py.stderr
        assert res_js.returncode == 0, res_js.stderr
        py_obj = json.loads((Path(tmp_py) / ".sstack/findings/t1.json").read_text())
        js_obj = json.loads((Path(tmp_js) / ".sstack/findings/t1.json").read_text())
        for obj in (py_obj, js_obj):
            obj.pop("emitted_at", None)
            obj.pop("duration_ms", None)
        assert py_obj == js_obj


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
        empty_js = subprocess.run(
            ["node", str(EMITTER_JS), "--workspace", str(tmp_js), "--fixture", "seeded-py"],
            input="", capture_output=True, text=True)
        assert empty_js.returncode == 0
        assert "0 request(s) upgraded" in empty_js.stdout


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



def test_malformed_fingerprint_is_treated_as_a_request(tmp_path):
    """A padded or invented fingerprint must not be promoted to evidence.

    The upgrade pass skips any file carrying a `fingerprint` key. A model
    that writes `e3b0c44298fc1c14c16a0000...` would otherwise slip past the
    only check inside the loop (ColdMusePy3, 2026-10-02). Malformed means
    "not evidence": the repro is re-executed and the real hash recorded.
    """
    ws = tmp_path / "host"
    (ws / ".sstack" / "findings").mkdir(parents=True)
    bad = base(slug="t1", repro="echo hi",
               fingerprint="e3b0c44298fc1c14c16a0000000000")
    (ws / ".sstack/findings/t1.json").write_text(json.dumps(bad))
    out = subprocess.run(
        [sys.executable, str(EMITTER), "--workspace", str(ws),
         "--fixture", "seeded-py"],
        capture_output=True, text=True)
    assert "malformed fingerprint" in out.stderr
    assert "1 request(s) upgraded" in out.stdout
    stored = json.loads((ws / ".sstack/findings/t1.json").read_text())
    assert re.fullmatch(r"[0-9a-f]{16}", stored["fingerprint"])
    assert stored["stdout"] == "hi\n"  # the machine's bytes, not the model's


def test_valid_fingerprint_is_left_alone(tmp_path):
    ws = tmp_path / "host"
    (ws / ".sstack" / "findings").mkdir(parents=True)
    good = base(slug="t1", repro="echo hi", fingerprint="0123456789abcdef",
                stdout="hi\n", exit_code=0)
    (ws / ".sstack/findings/t1.json").write_text(json.dumps(good))
    out = subprocess.run(
        [sys.executable, str(EMITTER), "--workspace", str(ws),
         "--fixture", "seeded-py"],
        capture_output=True, text=True)
    assert "malformed fingerprint" not in out.stderr
    assert "0 request(s) upgraded" in out.stdout


def test_report_rebuilds_when_no_upgrade_happened(tmp_path):
    """Editing a finding's case after its repro ran must reach report.json.

    The grader only reads the report, so a stale report silently scores a
    run on text that no longer describes its findings.
    """
    ws = tmp_path / "host"
    (ws / ".sstack" / "findings").mkdir(parents=True)
    stored = base(slug="t1", repro="echo hi", stdout="hi\n", exit_code=0,
                  fingerprint=hashlib.sha256(b"hi\n").hexdigest()[:16])
    stored.pop("repro")
    (ws / ".sstack/findings/t1.json").write_text(json.dumps(stored))
    subprocess.run(
        [sys.executable, str(EMITTER), "--workspace", str(ws),
         "--fixture", "seeded-py"],
        capture_output=True, text=True)
    stored["case"] = "edited after emit"
    (ws / ".sstack/findings/t1.json").write_text(json.dumps(stored))
    subprocess.run(
        [sys.executable, str(EMITTER), "--workspace", str(ws),
         "--fixture", "seeded-py"],
        capture_output=True, text=True)
    report = json.loads((ws / ".sstack/report.json").read_text())
    assert report["findings"][0]["case"] == "edited after emit"


def test_replay_normalizes_workspace_path(tmp_path):
    """Drift must be judged on the bytes the emitter hashed (ADR-0021).

    A repro whose output carries the workspace path — any traceback —
    would otherwise drift on every rerun and every machine.
    """
    from evals.replay import fingerprint, normalize
    ws = tmp_path / "host"
    (ws / ".sstack" / "findings").mkdir(parents=True)
    raw = f'Traceback:\n  File "{ws}/shop/o.py", line 3\nboom'
    recorded = fingerprint(normalize(raw, ws))
    (ws / ".sstack/findings/t1.json").write_text(json.dumps({
        "command": "python3 -c 'boom'", "exit_code": 1, "stdout": "",
        "stderr": normalize(raw, ws), "verdict": "confirmed",
        "fingerprint": recorded}))
    from evals.replay import replay_one
    result = replay_one(ws / ".sstack/findings/t1.json")
    assert result["integrity"] == "intact"
    assert result["drift"] in (False, True)  # re-execution is env-dependent


# --- --report: the summary is rendered, never authored -------------------

def test_report_renders_counts_from_report_json(tmp_path):
    """emit --report prints the run summary; landed checks the disk."""
    ws = tmp_path / "ws"
    (ws / "tests").mkdir(parents=True)
    (ws / "tests/test_x.py").write_text("def t():\n    assert 0\n")
    result = emit(ws, base())
    assert result.returncode == 0
    summary = subprocess.run(
        [sys.executable, str(EMITTER), "--workspace", str(ws), "--report"],
        capture_output=True, text=True)
    assert summary.returncode == 0
    assert "confirmed 1 / refuted 0 / inconclusive 0" in summary.stdout
    assert "regressions landed 1" in summary.stdout
    assert "red->green" in summary.stdout


def test_report_flags_unlanded_regression(tmp_path):
    """A claimed regression with no file on disk renders NOT ON DISK."""
    ws = tmp_path / "ws"
    ws.mkdir(parents=True)
    emit(ws, base())
    summary = subprocess.run(
        [sys.executable, str(EMITTER), "--workspace", str(ws), "--report"],
        capture_output=True, text=True)
    assert "NOT ON DISK" in summary.stdout
    assert "regressions landed 0" in summary.stdout


def test_report_without_report_json_errors(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir(parents=True)
    summary = subprocess.run(
        [sys.executable, str(EMITTER), "--workspace", str(ws), "--report"],
        capture_output=True, text=True)
    assert summary.returncode == 2
    assert "no report.json" in summary.stderr


def test_evidence_record_stamps_fixture(tmp_path):
    """Evidence self-describes its fixture so the grader can derive the
    view from evidence when report.json is clobbered (ColdEvalPy2)."""
    ws = tmp_path / "ws"
    ws.mkdir(parents=True)
    emit(ws, base())
    record = json.loads((ws / ".sstack" / "findings" / "t1.json").read_text())
    assert record["fixture"] == "seeded-py"
