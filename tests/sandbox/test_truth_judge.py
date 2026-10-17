"""The grader container's judging mode (DV4-PLAN §5.9, QPLAN §30 Q49): no Docker, no key,
no solver, and nothing of any real hidden truth. Invented snippets, an invented lab
Q99 and a stand-in oracle module written here:

  - dvl.judge reads a candidate's declaration (its parameters, results, requires and
    ensures as written) and its file's definitions (methods, lemmas, exec and proof
    fns removed; Verus doc comments made plain), in both languages;
  - a candidate whose file changes what its task fixes is sent as a stub, and a
    spec that names reference material, mixes languages or names an unknown card is
    refused;
  - the judging manifest validates: the one grader command, the candidates inline,
    a card's task form editable, the [truth] table, one language;
  - mksandbox-run's judge arguments: --truth-check judge takes --judge and nothing of
    validate's;
  - truthcheck's judge mode, run in-process over a stand-in archive whose reference
    clauses carry a canary token and a stand-in verifier: the verdict rows are
    verdict words only, and the canary never reaches stdout or stderr, whether the
    run judges, the reference is malformed, the oracle module raises with the canary
    in its message, or main itself raises;
  - a study session's tools cannot start a judging run (the guard refuses the
    command line, which names the sealed archive: mksandbox-run's, and
    `fvh report --judge`'s, which must name it too)."""

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from dvl import judge as J  # noqa: E402
from dvl import sandbox  # noqa: E402

CANARY = "DVLCANARY-judge-test-0f3c"   # an invented token: no real canary's hash

DAFNY = """module M {
  function F(x: nat): nat { x + 1 }
  /** A doc comment. */
  method Target(a: nat, ghost b: seq<int>) returns (r: nat, s: bool)
    requires a > 0
    requires {:id "x"} |b| == a
    ensures r == F(a)
  {
    r := a + 1;
    s := true;
  }
  lemma Helper(n: nat) ensures n + 0 == n {}
  method Use() { var r, s := Target(1, [0]); }
  predicate P(x: nat) { x > 2 }
}
"""

VERUS = """use vstd::prelude::*;

verus! {

pub open spec fn f(x: nat) -> nat { x + 1 }

/// Its doc comment.
pub fn target(a: u64, v: Seq<Map<int, u64>>) -> (r: u64)
    requires
        a < 10,
        forall|i: int, j: int| 0 <= i < j ==> i < j,
    ensures
        r as nat == f(a as nat),
{
    a + 1
}

/// A witness.
fn witness() {
}

pub proof fn helper(n: nat)
    ensures n == n,
{
}

} // verus!
"""


class Extraction(unittest.TestCase):
    def test_dafny_declaration_and_definitions(self):
        c = J.candidate(DAFNY, "dafny", "Target")
        self.assertEqual(c["params"], [["a", "nat"], ["b", "seq<int>"]])
        self.assertEqual(c["results"], [["r", "nat"], ["s", "bool"]])
        self.assertEqual(c["requires"], ["a > 0", "|b| == a"])
        self.assertEqual(c["ensures"], ["r == F(a)"])
        ctx = c["header"] + c["footer"]
        self.assertIn("function F(x: nat)", ctx)
        self.assertIn("predicate P(x: nat)", ctx)
        for gone in ("method Target", "lemma Helper", "method Use", "r := a + 1"):
            self.assertNotIn(gone, ctx)
        self.assertTrue(c["header"].endswith("\n"))
        self.assertIn("function F", c["header"])
        self.assertIn("predicate P", c["footer"])

    def test_verus_declaration_and_definitions(self):
        c = J.candidate(VERUS, "verus", "target")
        self.assertEqual(c["params"], [["a", "u64"], ["v", "Seq<Map<int, u64>>"]])
        self.assertEqual(c["results"], [["r", "u64"]])
        self.assertEqual(len(c["requires"]), 1)       # one entry per clause keyword
        self.assertIn("forall|i: int, j: int|", c["requires"][0])
        self.assertFalse(c["requires"][0].endswith(","))
        self.assertEqual(c["ensures"], ["r as nat == f(a as nat)"])
        ctx = c["header"] + c["footer"]
        self.assertIn("pub open spec fn f", ctx)
        for gone in ("pub fn target", "fn witness", "proof fn helper", "a + 1\n}"):
            self.assertNotIn(gone, ctx)
        self.assertNotIn("///", ctx)                  # no dangling doc comment
        self.assertIn("} // verus!", c["footer"])

    def test_a_missing_or_doubled_declaration_is_not_read(self):
        with self.assertRaises(J.JudgeInputError):
            J.candidate(DAFNY, "dafny", "Nope")
        with self.assertRaises(J.JudgeInputError):
            J.candidate(VERUS + VERUS.split("verus! {", 1)[1].replace("} // verus!", ""),
                        "verus", "target")
        with self.assertRaises(J.JudgeInputError):
            J.candidate("x", "python", "x")


class Candidates(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dvl0-judge-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def spec(self, cands):
        p = self.tmp / "spec.json"
        p.write_text(json.dumps({"candidates": cands}))
        return J.load_spec(p)

    def test_a_shipped_prose_file_is_read_and_a_frozen_change_is_a_stub(self):
        rel, name = J.prose_item(ROOT, "Q15.H3d")
        text = (ROOT / rel).read_text(encoding="utf-8")
        same = self.tmp / "same.dfy"
        same.write_text(text)
        changed = self.tmp / "changed.dfy"
        changed.write_text(text.replace("requires |s| == 5", "requires |s| == 4"))
        got, lang = J.candidates(ROOT, "Q15", self.spec([
            {"id": "a", "item": "Q15.H3d", "file": str(same)},
            {"id": "b", "item": "Q15.H3d", "file": str(changed)}]))
        self.assertEqual(lang, "dafny")
        self.assertEqual(got[0]["name"], name)
        self.assertNotIn("refused", got[0])
        self.assertEqual(got[1]["refused"], "freeze")

    def test_a_card_whose_definitions_change_is_a_stub(self):
        cards = J.lab_cards(ROOT, "Q15")
        cid = sorted(c for c in cards if cards[c][0] == "dafny")[0]
        lang, name, form = cards[cid]
        text = (ROOT / form).read_text(encoding="utf-8")
        ok = self.tmp / "ok.dfy"
        ok.write_text(text)
        bad = self.tmp / "bad.dfy"
        bad.write_text(text.replace("18446744073709551616", "18446744073709551615"))
        lever = self.tmp / "lever.dfy"
        lever.write_text(text.replace(f"method {name}(", f"method {{:resource_limit 9}} {name}("))
        got, _ = J.candidates(ROOT, "Q15", self.spec([
            {"id": "ok", "card": cid, "file": str(ok)}, {"id": "bad", "card": cid, "file": str(bad)},
            {"id": "lev", "card": cid, "file": str(lever)}]))
        self.assertTrue(got[0]["signature_ok"])
        self.assertEqual(got[0]["target"], form)
        self.assertEqual([g.get("refused") for g in got], [None, "task-form", "task-form"])

    def test_malformed_specs_are_refused(self):
        rel, _ = J.prose_item(ROOT, "Q15.H3v")
        f = self.tmp / "x.rs"
        f.write_text((ROOT / rel).read_text(encoding="utf-8"))
        d = self.tmp / "x.dfy"
        d.write_text((ROOT / J.prose_item(ROOT, "Q15.H3d")[0]).read_text(encoding="utf-8"))
        bad = [
            [{"id": "a", "item": "Q15.H3v", "file": str(f)},
             {"id": "b", "item": "Q15.H3d", "file": str(d)}],          # two languages
            [{"id": "a", "card": "no-such-card", "file": str(f)}],
            [{"id": "a", "item": "Q15.H3v", "card": "x", "file": str(f)}],
            [{"id": "a", "item": "Q13.H3v", "file": str(f)}],           # another lab's item
            [{"id": "a", "item": "Q15.H3v", "file": str(ROOT / "Solutions" / "x.rs")}],
            [{"id": "a b", "item": "Q15.H3v", "file": str(f)}],
        ]
        for cands in bad:
            with self.assertRaises(J.JudgeInputError, msg=cands):
                J.candidates(ROOT, "Q15", self.spec(cands))


class JudgeManifest(unittest.TestCase):
    def test_the_manifest_validates_with_one_grader_command(self):
        tmp = Path(tempfile.mkdtemp(prefix="dvl0-judge-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        cards = J.lab_cards(ROOT, "Q15")
        cid = sorted(c for c in cards if cards[c][0] == "verus")[0]
        f = tmp / "c.rs"
        f.write_text((ROOT / cards[cid][2]).read_text(encoding="utf-8"))
        spec = tmp / "s.json"
        spec.write_text(json.dumps({"candidates": [{"id": "r1", "card": cid, "file": str(f)}]}))
        cands, lang = J.candidates(ROOT, "Q15", J.load_spec(spec))
        raw = J.build_judge(ROOT, "Q15", cands, lang, mem_gb=16)
        m = sandbox.validate(raw, ROOT, check_image=False)
        self.assertEqual(m.commands, ((sandbox.TRUTHCHECK, "judge", "Q15"),))
        self.assertEqual(m.truth["lab"], "Q15")
        self.assertEqual(m.limits["mem_gb"], 16.0)
        by = {e.dst: e for e in m.files}
        self.assertEqual(by[J.CANDIDATES].role, "task")
        self.assertEqual(json.loads(by[J.CANDIDATES].text)["candidates"][0]["id"], "r1")
        self.assertEqual(by[cards[cid][2]].role, "editable")
        self.assertFalse(any(e.src and e.src.startswith(("Hidden/", "Solutions/"))
                             for e in m.files))

    def test_build_truth_leaves_judge_to_dvl_judge(self):
        with self.assertRaises(sandbox.ManifestError):
            sandbox.build_truth(ROOT, "Q15", "judge")

    def test_the_command_line_pairs_judge_with_its_spec(self):
        base = [sys.executable, "-B", str(ROOT / "scripts" / "mksandbox-run"), "--truth",
                "Hidden/labs/Q15/verdicts.tar.age"]
        for extra in (["--truth-check", "judge"],
                      ["--truth-check", "validate", "--judge", "x.json"],
                      ["--truth-check", "judge", "--judge", "x.json", "--cards", "a"],
                      ["--truth-check", "judge", "--judge", "x.json", "--truth-lang", "dafny"]):
            p = subprocess.run(base + extra, capture_output=True, text=True, timeout=60)
            self.assertEqual(p.returncode, 2, (extra, p.stderr))


# --- truthcheck's judge mode, in-process ------------------------------------------------------

STAND_IN = '''
import enum, os, tempfile
from dataclasses import dataclass
from fvh import tools
OUTCOMES = ("proved", "failed", "unknown")
class Verdict(enum.Enum):
    FAITHFUL = "faithful"; WEAK = "weak"; STRONG = "strong"; VACUOUS = "vacuous"
    UNDECIDED = "undecided"
@dataclass(frozen=True)
class Task:
    id: str; lang: str; name: str; params: tuple; results: tuple; body: str; header: str
    footer: str
@dataclass(frozen=True)
class Spec:
    task: Task; requires: tuple = (); ensures: tuple = ()
@dataclass(frozen=True)
class Implication:
    spec_implies_ref: str; ref_implies_spec: str
def outcome(result):
    return result.document.get("stand_in", "unknown")
def render_lemma(task, name, params, requires, ensures):
    if "RAISE" in "".join(requires) + "".join(ensures):
        raise RuntimeError("stand-in failure quoting " + task.header + " ".join(ensures))
    return task.header + "LEMMA " + name + " REQ " + " ; ".join(requires) + " ENS " + \\
        " ; ".join(ensures) + "\\n" + task.footer
def write_target(text, lang, workdir=None):
    fd, path = tempfile.mkstemp(suffix=".dfy", dir=workdir)
    with os.fdopen(fd, "w") as f:
        f.write(text)
    return path
def vacuity(spec, *, run=None, workdir=None):
    if not spec.requires:
        return "failed"
    return outcome(run("g", write_target(render_lemma(spec.task, "V", (), spec.requires,
                                                      ("false",)), "dafny", workdir)))
def implication(spec, ref, *, run=None, workdir=None):
    if "RAISE" in "".join(spec.ensures):
        raise RuntimeError("stand-in failure quoting " + " ".join(ref.ensures))
    return Implication("proved", "proved")
def classify(imp, vacuous):
    return Verdict.UNDECIDED
'''


def load_truthcheck():
    spec = importlib.util.spec_from_file_location("truthcheck_under_test",
                                                  ROOT / "sandbox" / "image" / "truthcheck.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TruthcheckJudge(unittest.TestCase):
    """Every row is verdict words; the canary in the stand-in reference never leaves."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dvl0-judge-tc-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.tc = load_truthcheck()
        self.tc.WORK = str(self.tmp / "work")
        self.tc.PROBES = str(self.tmp / "probes")
        (self.tmp / "work" / "judge").mkdir(parents=True)
        self.ref = (f'lang = "dafny"\nname = "Target"\nparams = [["a", "nat"]]\nresults = []\n'
                    f'requires = ["a > 0 && {CANARY}"]\nensures = ["{CANARY} == a"]\n'
                    f'definitions = ["function {CANARY}x(n: nat): nat {{ n }}"]\n')
        self.files = {"labs/Q99/MANIFEST.sha256": b"", "labs/Q99/judge/oracles.py":
                      STAND_IN.encode(), "labs/Q99/prose/Q99.H1d.toml": self.ref.encode()}
        self.mods = dict(sys.modules)

    def tearDown(self):
        for k in [k for k in sys.modules if k not in self.mods]:
            del sys.modules[k]
        sys.modules.update({k: v for k, v in self.mods.items() if k in ("fvh", "fvh.tools")})

    def cand(self, cid, ensures=("a == a",), **over):
        c = {"id": cid, "item": "Q99.H1d", "card": None, "lang": "dafny", "name": "Target",
             "params": [["a", "nat"]], "results": [], "requires": ["a > 0"],
             "ensures": list(ensures), "header": "module M {\n", "footer": "}\n",
             "target": None, "signature_ok": None}
        c.update(over)
        return c

    def run_judge(self, cands, files=None, verdict_of=None):
        (self.tmp / "work" / "judge" / "candidates.json").write_text(
            json.dumps({"schema": 1, "lab": "Q99", "lang": "dafny", "candidates": cands}))
        seen = []

        def fake_run(argv, **k):
            text = (Path(k.get("cwd", ".")) / argv[-1]).read_text()
            seen.append(text)
            word = (verdict_of or (lambda t: "failed" if "LEMMA V " in t else "proved"))(text)
            doc = {"verdict": "verified", "stand_in": word, "lines": [text]}
            return subprocess.CompletedProcess(argv, 0, json.dumps(doc).encode(), text.encode())
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(self.tc, "unseal", lambda lab: (dict(files or self.files), None)), \
                mock.patch.object(self.tc.subprocess, "run", fake_run), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.tc.entry(["judge", "Q99"])
        return code, out.getvalue(), err.getvalue(), seen

    def assert_clean(self, *texts):
        for t in texts:
            self.assertNotIn(CANARY, t)
            self.assertNotIn("DVLCANARY", t)

    def test_rows_are_verdict_words_and_the_canary_stays_inside(self):
        def verdict_of(text):          # the candidate's own requires: not the reference's
            return "failed" if "LEMMA Target_DvlReqToRef" in text or "LEMMA V " in text \
                else "proved"
        code, out, err, seen = self.run_judge(
            [self.cand("c1"), self.cand("c2", refused="freeze"),
             self.cand("c3", params=[["z", "int"]])], verdict_of=verdict_of)
        self.assertEqual(code, 0, out)
        doc = json.loads(out)
        rows = {r["id"]: r for r in doc["judged"]}
        self.assertEqual(rows["c1"]["verdict"], "strong")
        self.assertEqual(rows["c1"]["req_to_ref"], "failed")
        self.assertEqual(rows["c2"]["verdict"], "mismatch")
        self.assertEqual(rows["c3"]["verdict"], "mismatch")
        self.assertTrue(any(CANARY in s for s in seen))    # the lemmas did use the reference
        self.assertTrue(any(f"dvl_ref_{CANARY}x" in s for s in seen))   # its names prefixed
        self.assert_clean(out, err)
        for r in doc["judged"]:
            self.assertLessEqual(set(r), {"id", "item", "card", "verdict", "base", "vacuity",
                                          "spec_implies_ref", "ref_implies_spec", "req_from_ref",
                                          "ens_to_ref", "req_to_ref", "ens_from_ref", "why"})
        self.assertFalse(Path(self.tc.PROBES).exists())

    def test_a_definition_the_candidate_states_word_for_word_is_its_own(self):
        same = self.cand("c1", header="module M {\n  // the learner's\n  function "
                         f"{CANARY}x(n: nat):\n    nat {{ n }}\n")
        other = self.cand("c2", header="module M {\n  function "
                          f"{CANARY}x(n: nat): nat {{ n + 0 }}\n")
        code, out, err, seen = self.run_judge([same, other])
        self.assertEqual(code, 0, out)
        first = [t for t in seen if "LEMMA Target_DvlEnsToRef" in t]
        self.assertEqual(len(first), 2)
        self.assertNotIn("dvl_ref_", first[0])    # used as it stands
        self.assertIn("dvl_ref_", first[1])       # another body: the reference's, renamed
        self.assert_clean(out, err)

    def test_a_card_gets_the_oracles_verdict(self):
        files = dict(self.files)
        files["labs/Q99/tasks/c01/reference.toml"] = (
            self.ref + 'task_form = "bench/local/q/x/c01/tasks/c01.dfy"\n').encode()
        form = self.tmp / "work" / "bench/local/q/x/c01/tasks/c01.dfy"
        form.parent.mkdir(parents=True)
        form.write_text("shipped form\n")
        c = self.cand("k1", item=None, card="c01", target="bench/local/q/x/c01/tasks/c01.dfy",
                      signature_ok=True)
        code, out, err, _ = self.run_judge([c], files=files)
        self.assertEqual(code, 0, out)
        self.assertEqual(json.loads(out)["judged"][0]["verdict"], "undecided")
        self.assertEqual(form.read_text(), "shipped form\n")   # restored
        self.assert_clean(out, err)

    def test_an_oracle_failure_is_a_fixed_error_row(self):
        code, out, err, _ = self.run_judge([self.cand("c1", ensures=("RAISE",)),
                                            self.cand("c2")])
        self.assertEqual(code, 1)
        rows = {r["id"]: r for r in json.loads(out)["judged"]}
        self.assertEqual(rows["c1"]["verdict"], "error")
        self.assertEqual(rows["c1"]["why"], "the judge failed on this candidate")
        self.assert_clean(out, err)

    def test_a_malformed_reference_or_module_never_quotes_it(self):
        files = dict(self.files)
        files["labs/Q99/prose/Q99.H1d.toml"] = f'requires = ["{CANARY}\n'.encode()
        code, out, err, _ = self.run_judge([self.cand("c1")], files=files)
        self.assertEqual(code, 1)
        self.assert_clean(out, err)
        files = dict(self.files)
        files["labs/Q99/judge/oracles.py"] = f"raise SystemExit('{CANARY}')\n".encode()
        code, out, err, _ = self.run_judge([self.cand("c1")], files=files)
        self.assertEqual(code, 3)
        self.assert_clean(out, err)
        files["labs/Q99/judge/oracles.py"] = f"def f(:\n  '{CANARY}'\n".encode()
        code, out, err, _ = self.run_judge([self.cand("c1")], files=files)
        self.assertEqual(code, 3)
        self.assert_clean(out, err)

    def test_an_escaping_exception_is_a_fixed_refusal(self):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(self.tc, "main", side_effect=KeyError(CANARY)), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.tc.entry(["judge", "Q99"])
        self.assertEqual(code, 3)
        self.assert_clean(out.getvalue(), err.getvalue())
        self.assertEqual(json.loads(out.getvalue()), {"error": "the grader stopped on an "
                                                               "internal error"})

    def test_a_malformed_candidates_file_is_refused(self):
        code, out, err, _ = self.run_judge([{"id": "x y", "item": "Q99.H1d"}])
        self.assertEqual(code, 3)
        self.assert_clean(out, err)


class StudySessionGuard(unittest.TestCase):
    """The judging run's command line names the sealed archive: rule 1c refuses it."""

    def test_the_judge_command_line_is_refused_in_a_study_session(self):
        tmp = Path(tempfile.mkdtemp(prefix="dvl0-judgeguard-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        root, home = tmp / "study", tmp / "home"
        root.mkdir()
        gen = ROOT / "scripts" / "gen_hook_fixtures.py"
        sid = "11111111-2222-4333-8444-555555555556"
        slug = "".join(c if c.isascii() and c.isalnum() else "-" for c in str(root))
        subprocess.run([sys.executable, str(gen), "--fake-root", str(root)], check=True,
                       capture_output=True)
        subprocess.run([sys.executable, str(gen), "--fake-home", str(home), f"--slug={slug}",
                        f"--sid={sid}"], check=True, capture_output=True)
        for cmd in ("scripts/mksandbox-run --truth Hidden/labs/Q15/verdicts.tar.age "
                    "--truth-check judge --judge judge.toml",
                    "scripts/mksandbox-run --truth Hidden/labs/Q13/verdicts.tar.age "
                    "--truth-check judge --judge /tmp/x.json --mem-gb 16",
                    "uv run --offline --frozen --directory harness python -m fvh report Q15 "
                    "--judge all --truth Hidden/labs/Q15/verdicts.tar.age"):
            inp = {"session_id": sid,
                   "transcript_path": f"{home}/.claude/projects/{slug}/{sid}.jsonl",
                   "tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": str(root)}
            env = {k: v for k, v in os.environ.items()
                   if k not in ("CLAUDE_CODE_SESSION_ID", "CLAUDE_CONFIG_DIR", "TMPDIR",
                                "SPOILER_GUARD_NO_JQ")}
            env.update(HOME=str(home), CLAUDE_PROJECT_DIR=str(root))
            p = subprocess.run(["bash", str(ROOT / ".claude" / "hooks" / "spoiler-guard.sh")],
                               input=json.dumps(inp), capture_output=True, text=True, env=env,
                               timeout=60)
            self.assertEqual(p.returncode, 2, p.stderr)
            self.assertIn("rule 1c", p.stderr)


if __name__ == "__main__":
    unittest.main()
