"""scripts/challenge_gate.sh / scripts/dvl/challenge.py (QPLAN §31.1, §31.5; Δ402) on an
invented armed challenge in a throwaway git repository. The instruments are replaced by a
fake (no solver, no pytest): each case plants one failure per check, plus the passing
delivery, a planned module, a memory kill, the gradebook row and --abandon.

Run: python3 -B -m unittest discover -s tests/wrappers -p 'test_challenge_gate_static.py'
"""
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from dvl import challenge as CG  # noqa: E402

ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
           GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid",
           GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")

D = "Challenges/Agentic/Q31_GateBench"
STMT_D = f"{D}/Q31_GateBenchStatement.dfy"
EX_D = f"{D}/Q31_GateBench.dfy"
CRATE = f"{D}/q31_gate_bench"
STMT_V = f"{CRATE}/src/statements.rs"
MAN = f"{D}/Q31_Statement.toml"
PY = "agents/q31_gate_bench/bench.py"

MANIFEST = f'''schema = 1
module = "Q31"
trust = "research/TRUST.md"
solver_swap = true
distinction = "grader"
[min_verified]
"{EX_D}" = 2
[[against]]
statement = "{STMT_D}"
file = "{EX_D}"
[reach]
deny_names = ["LemmaMulComm"]
require = ["Witness1"]
'''


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def registry(status, pins, bar="harness"):
    st = ", ".join(f'{{ path = "{p}", sha256 = "{s}" }}' for p, s in pins)
    return f'''[[module]]
id = "Q31"
status = "{status}"
tier = "challenge"
review_bar = "{bar}"
exercises = ["{EX_D}", "{CRATE}/src/lib.rs"]
harness = ["{PY}"]
statements = [{st}]
'''


class Fake(CG.Tools):
    def __init__(self, root):
        super().__init__(root)
        self.gate = {EX_D: (0, {"verdict": "verified", "holes": [], "verified_count": 2}),
                     CRATE: (0, {"verdict": "verified", "holes": [], "verified_count": 3})}
        self.audit = {EX_D: {"findings": []}, CRATE: {"findings": []}}
        self.sweep = {t: {"verdicts": {"1": "verified", "2": "verified", "3": "verified"},
                          "stable": True, "spread": [{"cv": 0.01}], "flagged": []}
                      for t in (EX_D, CRATE)}
        self.against = 0
        self.pyholes = []
        self.pycheck = "verified"
        self.calls = []

    def vcheck_gate(self, t):
        return self.gate[t]

    def vaudit(self, t):
        return 0, self.audit[t]

    def brittleness(self, t, solvers):
        self.calls.append(("brittleness", t, solvers))
        return 0, self.sweep[t]

    def specfreeze_against(self, s, f):
        return self.against

    def python_holes(self, rel):
        return self.pyholes

    def python_check(self, rel):
        return self.pycheck


class Gate(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory(prefix="dvl-challenge-")
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.git("init", "-q", "-b", "dv7")
        self.write(STMT_D, "module S { predicate Witness1() { true } }\n")
        self.write(EX_D, "module E { predicate Witness1() { true } }\n")
        self.write(STMT_V, "verus! { spec fn s() -> bool { true } }\n")
        self.write(f"{CRATE}/src/lib.rs", "verus! { fn ok() {} }\n")
        self.write(MAN, MANIFEST)
        self.write(PY, "x = 1\n")
        self.write("instructor/gradebook.md", "# Gradebook\n\n| date | module | track | grade | open findings |\n|---|---|---|---|---|\n")
        self.write("instructor/ledger.md", "# Error ledger\n")
        self.write("research/runs/Q31/grader/result.json", '{"module": "Q31", "word": "PASS"}')
        self.pin()
        self.fake = Fake(self.root)

    def git(self, *a):
        return subprocess.run(["git", "-C", str(self.root), *a], check=True, capture_output=True,
                              text=True, env=ENV).stdout.strip()

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def pin(self, status="authoring", bar="harness"):
        pins = [(p, sha(self.root / p)) for p in (MAN, STMT_D, STMT_V)]
        self.write("MODULES.toml", registry(status, pins, bar))
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "fixture", "--allow-empty")

    def run_gate(self):
        return CG.gate(self.root, "Q31", self.fake)

    def failed(self, rep):
        return {c for c, ok, _ in rep.lines if not ok}

    def test_the_passing_delivery(self):
        rep = self.run_gate()
        self.assertEqual(rep.word, "PASS", rep.lines)
        self.assertEqual([c for c, _, _ in rep.lines], list(CG.CHECKS))
        self.assertIn(CG.LABEL, rep.labels)
        self.assertIn("verus: one solver", rep.labels)
        # Dafny gets the bundled solvers too; Verus has one solver
        self.assertIn(("brittleness", EX_D, True), self.fake.calls)
        self.assertIn(("brittleness", CRATE, False), self.fake.calls)

    def test_distinction_comes_from_the_grader_record(self):
        self.write("research/runs/Q31/grader/result.json", '{"module": "Q31", "word": "DISTINCTION"}')
        self.assertEqual(self.run_gate().word, "DISTINCTION")

    def test_statements(self):
        self.write(STMT_D, "module S { predicate Witness1() { false } }\n")     # working copy
        self.assertEqual(self.failed(self.run_gate()), {"statements"})
        self.git("checkout", "--", STMT_D)
        self.fake.against = 1
        self.assertEqual(self.failed(self.run_gate()), {"statements"})

    def test_an_uncommitted_pin(self):
        self.write(STMT_V, "verus! { spec fn s() -> bool { false } }\n")
        pins = [(p, sha(self.root / p)) for p in (MAN, STMT_D, STMT_V)]
        self.write("MODULES.toml", registry("authoring", pins))   # pinned, never committed
        self.assertEqual(self.failed(self.run_gate()), {"statements"})

    def test_pending_is_refused_as_a_failure(self):
        self.write("MODULES.toml", registry("authoring", [(MAN, sha(self.root / MAN)),
                                                         (STMT_D, "PENDING")]))
        self.assertIn("statements", self.failed(self.run_gate()))

    def test_holes_in_each_language(self):
        self.fake.gate[EX_D] = (1, {"verdict": "failed", "holes": [{"line": 1}], "verified_count": 2})
        self.assertEqual(self.failed(self.run_gate()), {"holes"})
        self.fake.gate[EX_D] = (0, {"verdict": "verified", "holes": [], "verified_count": 2})
        self.fake.pyholes = ["Q31.bench"]
        rep = self.run_gate()
        self.assertEqual(self.failed(rep), {"holes"})
        self.assertIn("python 1", dict((c, d) for c, _, d in rep.lines)["holes"])

    def test_an_unlisted_audit_finding(self):
        self.fake.audit[CRATE] = {"findings": [{"file": str(self.root / CRATE / "src/lib.rs"),
                                                "line": 1, "kind": "external-body"}]}
        self.assertEqual(self.failed(self.run_gate()), {"audit"})
        self.fake.audit[CRATE] = {}
        self.assertEqual(self.failed(self.run_gate()), {"audit"})

    def test_a_listed_leap_passes_the_audit_and_the_lint(self):
        self.write(f"{CRATE}/src/lib.rs", "verus! {\n#[verifier::external_body]\nfn clock() -> u64 { 0 }\n}\n")
        self.fake.audit[CRATE] = {"findings": [{"file": str(self.root / CRATE / "src/lib.rs"),
                                                "line": 2, "kind": "external-body"}]}
        self.assertEqual(self.failed(self.run_gate()), {"trust-leap", "audit"})
        self.write("research/TRUST.md", "## Q31\n\n| file | symbol | construct | why |\n|---|---|---|---|\n"
                   f"| {CRATE}/src/lib.rs | clock | external-body | the OS clock is outside the proof |\n")
        self.assertEqual(self.run_gate().word, "PASS")

    def test_a_seed_flip_and_the_cv_rule(self):
        self.fake.sweep[EX_D] = {"verdicts": {"1": "verified", "2": "failed", "3": "verified"},
                                 "stable": False, "spread": [], "flagged": []}
        self.assertEqual(self.failed(self.run_gate()), {"seeds"})
        self.fake.sweep[EX_D] = {"verdicts": {"1": "verified", "2": "verified", "3": "verified"},
                                 "stable": True, "spread": [{"cv": 0.4}], "flagged": ["X"]}
        self.assertEqual(self.run_gate().word, "PASS")       # flagged, not gated by default
        self.write(MAN, MANIFEST.replace("solver_swap = true", "solver_swap = true\ncv_gates = true"))
        self.pin()
        self.assertEqual(self.failed(self.run_gate()), {"seeds"})

    def test_reach(self):
        self.write(EX_D, "module E { predicate Witness1() { true } lemma L() { LemmaMulComm(); } }\n")
        self.assertEqual(self.failed(self.run_gate()), {"reach"})
        self.write(EX_D, "module E { }\n")
        self.assertEqual(self.failed(self.run_gate()), {"reach"})      # the required root

    def test_completeness(self):
        self.fake.gate[CRATE] = (0, {"verdict": "verified", "holes": []})
        self.assertEqual(self.failed(self.run_gate()), {"completeness"})
        self.fake.gate[CRATE] = (0, {"verdict": "verified", "holes": [], "verified_count": 3})
        self.fake.gate[EX_D] = (0, {"verdict": "verified", "holes": [], "verified_count": 1})
        self.assertEqual(self.failed(self.run_gate()), {"completeness"})

    def test_the_harness_stage(self):
        (self.root / "research/runs/Q31/grader/result.json").unlink()
        self.assertEqual(self.failed(self.run_gate()), {"harness"})
        self.write("research/runs/Q31/grader/result.json", '{"module": "Q31", "word": "FAIL"}')
        self.assertEqual(self.failed(self.run_gate()), {"harness"})
        self.write("research/runs/Q31/grader/result.json", '{"module": "Q31", "word": "PASS"}')
        self.fake.pycheck = "failed"
        self.assertEqual(self.failed(self.run_gate()), {"harness"})
        self.pin(bar="production")                 # not harness-graded: no harness stage
        self.assertNotIn("harness", [c for c, _, _ in self.run_gate().lines])

    def test_planned_and_killed(self):
        self.pin(status="planned")
        with self.assertRaisesRegex(CG.Refused, "planned"):
            self.run_gate()
        self.pin()

        class K(Fake):
            def vcheck_gate(self, t):
                raise CG.Killed(137, "vcheck")
        with self.assertRaises(CG.Killed):
            CG.gate(self.root, "Q31", K(self.root))

    def test_the_gradebook_row(self):
        self.write("instructor/ledger.md", "# L\n- tag: Q31/gate | error: x | seen: 2026-10-20 | box: 1 | "
                   "due: 2026-10-21 | hint-depth: 2 | source: tutor\n")
        rep = self.run_gate()
        row = CG.gradebook_row(rep, "2026-10-20")
        self.assertTrue(row.startswith("| 2026-10-20 | Q31 | challenge | PASS; manifest "))
        self.assertIn("not independent checking", row)
        self.assertIn("assisted (max hint-depth 2)", row)
        CG.append_row(self.root, row)
        self.assertTrue((self.root / "instructor/gradebook.md").read_text().endswith(row + "\n"))

    def test_abandon(self):
        with self.assertRaisesRegex(CG.Refused, "write the retrospective"):
            CG.abandon(self.root, "Q31")
        body = " ".join(["word"] * 16)
        self.write("research/q31_retrospective.md", "# Q31\n\n" + "\n\n".join(
            f"{h}\n\n{body}" for h in CG.RETRO_HEADINGS[:3]) + "\n")
        with self.assertRaisesRegex(CG.Refused, "four sections"):
            CG.abandon(self.root, "Q31")
        self.write("research/q31_retrospective.md", "# Q31\n\n" + "\n\n".join(
            f"{h}\n\n{body}" for h in CG.RETRO_HEADINGS) + "\n")
        mid, grade = CG.abandon(self.root, "Q31")
        self.assertEqual(mid, "Q31")
        self.assertTrue(grade.startswith("abandoned (retrospective "))

    def test_the_manifest_is_strict(self):
        self.write(MAN, "extra = 1\n" + MANIFEST)
        self.pin()
        with self.assertRaisesRegex(CG.Refused, "unknown key"):
            self.run_gate()
        self.write(MAN, MANIFEST + "\nextra = [\"x\"]\n")      # inside [reach]
        self.pin()
        with self.assertRaisesRegex(CG.Refused, "reach"):
            self.run_gate()


if __name__ == "__main__":
    unittest.main()
