"""scripts/dvl/python.py, tool-free: holes, the lint, the shipping lint,
statement hashes, TRIV bodies, the acceptance-test map, the file lists, the
summary line, the CLI's static commands, and the drift guards between the
frozen core (harness/fvh/) and the course tools (dvl.common's verdicts,
course_items' grammar, firsttry's calibration rows). No test here runs pytest.

Run: python3 -B -m unittest discover -s tests/harness_adapter -p 'test_python_static.py'
"""

import ast
import importlib.machinery
import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import adapter_common as A  # noqa: E402
from adapter_common import P  # noqa: E402
import course_items as ci  # noqa: E402
from dvl import common  # noqa: E402


def load_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FVH = A.ROOT / "harness" / "fvh"
records = load_file("_adapter_fvh_records", FVH / "records.py")
fholes = load_file("_adapter_fvh_holes", FVH / "holes.py")


def load_vcheck():
    if "vcheck" in sys.modules:
        return sys.modules["vcheck"]
    loader = importlib.machinery.SourceFileLoader("vcheck", str(A.SCRIPTS / "vcheck"))
    spec = importlib.util.spec_from_loader("vcheck", loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["vcheck"] = mod
    loader.exec_module(mod)
    return mod


class RootCase(unittest.TestCase):
    def setUp(self):
        self.base = A.tmpdir("py-static-")
        self.root = A.build_root(self.base)
        self.learner = self.root / A.LEARNER_REL
        self.twin = self.root / A.TWIN_REL

    def tearDown(self):
        A.remove(self.base)

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p


class Holes(RootCase):
    def test_the_learner_file_ships_two_counted_holes(self):
        got = P.holes(self.learner, root=self.root)
        self.assertEqual([(h.label, h.line, h.kind) for h in got],
                         [("Q98.H1py", 10, "raise-not-implemented"),
                          ("Q98.H2py", 16, "raise-not-implemented")])
        self.assertTrue(all(h.file == str(self.learner) for h in got))

    def test_the_twin_has_none(self):
        self.assertEqual(P.holes(self.twin, root=self.root), [])

    def test_a_file_that_does_not_parse_cannot_be_counted(self):
        p = self.write("harness/q/fvh_q/broken.py", "def f(:\n")
        with self.assertRaises(P.HoleCountError) as cm:
            P.holes(p, root=self.root)
        self.assertEqual((cm.exception.result.verdict, cm.exception.result.stage),
                         ("failed", "parse"))

    def test_a_missing_file_is_refused(self):
        with self.assertRaises(P.Refused):
            P.holes(self.root / "harness/q/fvh_q/nope.py", root=self.root)


class Lint(RootCase):
    def kinds(self, text, mode="learner", rel="harness/q/fvh_q/x.py"):
        p = self.write(rel, text)
        return sorted(f.kind for f in P.lint([p], mode, root=self.root))

    def test_the_shipped_files_are_clean(self):
        self.assertEqual(P.lint([self.learner], root=self.root), [])
        self.assertEqual(P.lint([self.twin], "reference", root=self.root), [])

    def test_imports_stay_in_the_tier(self):
        self.assertEqual(self.kinds("import numpy\nimport fvh_r\n"),
                         ["import-outside-tier", "import-outside-tier"])
        self.assertEqual(self.kinds("import fvh_q\nfrom fvh import stats\nimport json\n"), [])
        self.assertEqual(self.kinds("import fvh_q\n", rel="harness/r/fvh_r/x.py"),
                         ["import-outside-tier"])
        self.assertEqual(self.kinds("from .sibling import f\n"), [])
        ref_pkg = "solu" + "tions_harness"     # spelled apart: a reference import form
        self.assertEqual(self.kinds(f"import {ref_pkg}\n"), ["reference-import"])

    def test_path_and_dynamic_imports(self):
        self.assertEqual(self.kinds("import sys\nsys.path.insert(0, '..')\n"), ["sys-path"])
        self.assertEqual(self.kinds("m = __import__('json')\n"), ["sys-path"])
        self.assertEqual(self.kinds("import importlib\nm = importlib.import_module('json')\n"),
                         ["sys-path"])

    def test_statistics_code_stays_in_the_core(self):
        self.assertEqual(self.kinds("def wilson_interval(s, n):\n    return (0.0, 1.0)\n"),
                         ["stats-reimplementation"])
        self.assertEqual(self.kinds("import math\nx = math.comb(5, 2)\n"),
                         ["stats-reimplementation"])
        self.assertEqual(self.kinds("from statistics import NormalDist\n"),
                         ["stats-reimplementation"])
        self.assertEqual(self.kinds("import statistics\nx = statistics.fmean([1.0])\n"), [])

    def test_hole_like_code_comes_from_the_core(self):
        text = "# item: Q98.H1py S9\ndef f():\n    pass\n"
        self.assertEqual(self.kinds(text), ["empty-body"])

    def test_reference_mode_reports_holes(self):
        self.assertEqual([f.kind for f in P.lint([self.learner], "reference", root=self.root)],
                         ["hole", "hole"])

    def test_unknown_mode(self):
        with self.assertRaises(ValueError):
            P.lint([self.learner], "agent", root=self.root)


class Hollow(RootCase):
    def test_the_shipped_learner_file_is_hollow(self):
        self.assertEqual(P.lint_hollow(self.learner, root=self.root), [])

    def test_a_filled_file_is_not(self):
        p = self.write(A.LEARNER_REL, A.TWIN)
        self.assertEqual([f.kind for f in P.lint_hollow(p, root=self.root)],
                         ["hole-missing", "hole-missing"])

    def test_a_second_hole_and_a_stray_one(self):
        text = A.LEARNER.replace(
            "# item: Q98.H2py S13",
            'def extra():\n    raise NotImplementedError("Q98.H1py")\n\n\n# item: Q98.H2py S13')
        text = text.replace("# SLOT: CHECK P1py",
                            '# SLOT: CHECK P1py\ndef p():\n    raise NotImplementedError("Q98.P1py")')
        kinds = sorted(f.kind for f in P.lint_hollow(self.write(A.LEARNER_REL, text),
                                                     root=self.root))
        self.assertEqual(kinds, ["duplicate-hole", "duplicate-hole", "hole-count", "stray-hole"])

    def test_a_marker_grammar_error(self):
        text = A.LEARNER.replace("# item: Q98.H2py S13", "# item: Q98.H2py S99")
        kinds = {f.kind for f in P.lint_hollow(self.write(A.LEARNER_REL, text), root=self.root)}
        self.assertIn("marker-grammar", kinds)


class SpecHash(RootCase):
    def test_learner_and_twin_share_their_statements(self):
        a, b = P.spec_hash(self.learner), P.spec_hash(self.twin)
        self.assertEqual(set(a), {"double", "significant"})
        self.assertEqual(a, b)

    def test_a_changed_signature_changes_the_hash_and_a_body_does_not(self):
        base = P.spec_hash(self.learner)
        p = self.write("harness/q/fvh_q/sig.py", A.LEARNER.replace("def double(x: int) -> int:",
                                                                   "def double(x: int, y=1) -> int:"))
        self.assertNotEqual(P.spec_hash(p)["double"], base["double"])
        self.assertEqual(P.spec_hash(p)["significant"], base["significant"])
        q = self.write("harness/q/fvh_q/body.py", A.LEARNER.replace('"""Twice x."""',
                                                                    '"""Another docstring."""'))
        self.assertEqual(P.spec_hash(q), base)

    def test_methods_classes_and_the_symbol_filter(self):
        p = self.write("harness/q/fvh_q/cls.py", "class C(object):\n    def m(self, a): ...\n")
        got = P.spec_hash(p)
        self.assertEqual(set(got), {"C", "C.m"})
        self.assertEqual(set(P.spec_hash(p, ["C.m"])), {"C.m"})


class Triv(RootCase):
    def test_declared_bodies(self):
        self.assertEqual(P.triv_bodies(A.TWIN, root=self.root),
                         {"Q98.H1py": "return 0",
                          "Q98.H2py": "flags = [False] * len(pvalues)\nreturn flags"})

    def test_the_body_after_the_docstring_is_replaced(self):
        core = P._core_holes(self.root)
        out = P._with_body(A.TWIN, "Q98.H1py", "return 0", core)
        tree = ast.parse(out)
        fns = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        body = fns["double"].body
        self.assertEqual(ast.get_docstring(fns["double"]), "Twice x.")
        self.assertEqual(ast.unparse(body[1]), "return 0")
        self.assertEqual(len(body), 2)
        self.assertEqual(ast.unparse(fns["significant"].body[1]), "return stats.holm(pvalues)")
        two = P._with_body(A.TWIN, "Q98.H2py", "flags = [False] * len(pvalues)\nreturn flags",
                          core)
        self.assertEqual(len(ast.parse(two).body[-1].body), 3)

    def test_an_item_without_a_function(self):
        with self.assertRaises(P.Refused):
            P._with_body(A.TWIN, "Q98.P1py", "return 0", P._core_holes(self.root))


class Acceptance(RootCase):
    def test_the_registry_file_maps_to_its_tests(self):
        self.assertEqual(P.acceptance_tests(self.learner, root=self.root), [Path(A.TESTS_REL)])

    def test_subpackages_and_the_r_track(self):
        reg = (self.root / "MODULES.toml").read_text(encoding="utf-8")
        reg += '\n[[module]]\nid = "R98"\nstatus = "authoring"\nharness = ["harness/r/fvh_r/sub/x.py"]\n'
        self.write("MODULES.toml", reg)
        p = self.write("harness/r/fvh_r/sub/x.py", "x = 1\n")
        self.write("harness/tests/r/sub/test_x.py", "def test_x():\n    pass\n")
        self.assertEqual(P.acceptance_tests(p, root=self.root),
                         [Path("harness/tests/r/sub/test_x.py")])

    def test_refusals(self):
        for rel in ("harness/fvh/stats.py", "harness/q/fvh_r/x.py", "elsewhere/x.py"):
            p = self.write(rel, "x = 1\n") if not (self.root / rel).exists() else self.root / rel
            with self.assertRaises(P.Refused, msg=rel):
                P.acceptance_tests(p, root=self.root)
        unlisted = self.write("harness/q/fvh_q/unlisted.py", "x = 1\n")
        with self.assertRaisesRegex(P.Refused, "no module lists it"):
            P.acceptance_tests(unlisted, root=self.root)
        (self.root / A.TESTS_REL).unlink()
        with self.assertRaisesRegex(P.Refused, "do not exist"):
            P.acceptance_tests(self.learner, root=self.root)

    def test_test_and_check_refuse_without_running(self):
        unlisted = self.write("harness/q/fvh_q/unlisted.py", "x = 1\n")
        self.assertEqual(P.test(unlisted, root=self.root).verdict, "refused")
        self.assertEqual(P.check(self.root / "MODULES.toml", root=self.root).verdict, "refused")


class Files(RootCase):
    def test_on_disk_and_armed(self):
        self.write("harness/q/fvh_q/sub/more.py", "x = 1\n")
        self.assertEqual(P.learner_files(self.root),
                         [A.LEARNER_REL, "harness/q/fvh_q/sub/more.py"])
        # Q97 is planned: its file is not listed, although it is missing too
        self.assertEqual(P.learner_files(self.root, armed=True), [A.LEARNER_REL])


class Summary(unittest.TestCase):
    def test_the_vcheck_summary_line(self):
        r = common.Result("python", "f.py", 1, "failed", "test",
                          holes=[common.Hole("f.py", 3, 1, P.HOLE_KIND, "Q98.H1py")],
                          per_symbol={"a": "passed", "b": "failed", "c": "error"})
        self.assertEqual(P.summary_line(r, "f.py", "learner loop"),
                         "vcheck: f.py [python, learner loop]: failed — 1 passed, 2 failed, 1 hole")
        r = common.Result("python", "f.py", 0, "verified", "test", per_symbol={"a": "passed"})
        self.assertEqual(P.summary_line(r, "f.py", "gate"),
                         "vcheck: f.py [python, gate]: verified — 1 passed, 0 failed, 0 holes")
        r = common.Result("python", "f.py", None, "failed", "parse")
        self.assertIn("stage parse", P.summary_line(r, "f.py", "gate"))
        r = common.Result("python", "f.py", None, "refused", "cli")
        self.assertEqual(P.summary_line(r, "f.py", "gate"),
                         "vcheck: f.py [python, gate]: refused (no tool ran)")


class Cli(RootCase):
    def run_cli(self, *args, env=None):
        e = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
             "GIT_CEILING_DIRECTORIES": str(self.root.parent)}
        e.pop("CI", None)
        e.update(env or {})
        p = subprocess.run([sys.executable, "-B", str(A.SCRIPTS / "dvl" / "python.py"), *args],
                           capture_output=True, text=True, env=e, cwd=str(self.root), timeout=300)
        return p.returncode, p.stdout, p.stderr

    def test_holes_hollow_lint_files(self):
        rc, out, _ = self.run_cli("holes", "--root", str(self.root), A.LEARNER_REL)
        self.assertEqual((rc, out), (0, f"{A.LEARNER_REL}: 2 hole(s)\n"))
        rc, out, _ = self.run_cli("hollow", "--root", str(self.root), A.LEARNER_REL)
        self.assertEqual((rc, out.splitlines()[-1]),
                         (0, "python.py hollow: 1 file(s), 0 finding(s)"))
        self.write("harness/q/fvh_q/bad.py", "import numpy\n")
        rc, out, _ = self.run_cli("lint", "--root", str(self.root), "harness/q/fvh_q/bad.py")
        self.assertEqual(rc, 1)
        self.assertIn("harness/q/fvh_q/bad.py:1: import-outside-tier", out)
        rc, out, _ = self.run_cli("files", "--armed", "--root", str(self.root))
        self.assertEqual((rc, out), (0, A.LEARNER_REL + "\n"))

    def test_author_only_commands_refuse_outside_the_authors_context(self):
        for cmd in (["ref", A.TWIN_REL], ["triv", A.TWIN_REL]):
            rc, out, err = self.run_cli(cmd[0], "--root", str(self.root), *cmd[1:])
            self.assertEqual(rc, 3, (cmd, out, err))
            self.assertIn("author-only", err)

    def test_usage(self):
        self.assertEqual(self.run_cli()[0], 2)
        self.assertEqual(self.run_cli("check", "a.py", "b.py")[0], 2)
        self.assertEqual(self.run_cli("bogus", "x")[0], 2)


# --- drift guards between the frozen core and the course tools -------------------------

class Vocabulary(unittest.TestCase):
    def test_run_verdicts_are_the_tools_verdicts(self):
        self.assertEqual(records.VERDICTS, common.VERDICTS)

    def test_item_ids_follow_the_one_grammar(self):
        self.assertEqual(records.ITEM_ID.pattern, ci.ITEM_ID_RE)
        self.assertEqual(fholes.ITEM_ID_RE, ci.ITEM_ID_RE)

    def test_the_marker_grammar_is_course_items(self):
        ref = ci.marker_re("#")
        lines = ["# item: Q06.H5py S9", "# item: Q06.P7py S13 verdict", "# item: Q06.H5py",
                 "# item: Q06.C1py S2 write:property-test", "# item: Q06.X1py S12 verdict min=2",
                 "# item: Q06.C2py S1 diverge:q06-c2", "# item: R05.H1py",
                 "#item: Q06.H5py S9", "# item: Q06.H5py S14", "# item: Q6.H5py S9",
                 "# item: Q06.H05py S9", "# item: Q06.H5py S9 extra", "# item:Q06.H5py",
                 "# item: Q06.H5py S9 verdict min=0"]
        for line in lines:
            self.assertEqual(bool(fholes.MARKER.fullmatch(line)), bool(ref.fullmatch(line)), line)
            self.assertEqual(bool(fholes.MARKER_LIKE.match(line)),
                             bool(re_marker_like().match(line)), line)

    def test_calibration_rows_round_trip_through_the_writer(self):
        core = load_vcheck()
        base = A.tmpdir("py-calib-")
        try:
            rows = [["Q98.P1dv", "predict", "pass", "2026-10-05", "a" * 64],
                    ["Q98.P2d", "observed", "fail", "2026-10-05", "b" * 64],
                    ["Q98.X1v", "exit", "pass", "2026-10-06", "c" * 64],
                    ["Q98.P1dv", "predict", "fail", "2026-10-07", "d" * 64]]
            core.append_calib(base, "Q98", rows)
            path = core.calib_path(base, "Q98")
            got = records.load_calib(path)
            self.assertEqual([tuple(dataclass_values(r)) for r in got],
                             [tuple(r) for r in rows[:3]])
            first = core.read_calib(base, "Q98")
            self.assertEqual({r.item: (r.kind, r.verdict) for r in got},
                             {k: (v["kind"], v["verdict"]) for k, v in first.items()})
        finally:
            A.remove(base)

    def test_firsttry_writes_only_the_cores_kinds_and_verdicts(self):
        kinds, verdicts, sites = firsttry_row_words()
        self.assertGreaterEqual(sites, 3, "firsttry's calibration rows were not found")
        self.assertTrue(kinds and verdicts)
        self.assertLessEqual(kinds, set(records.CALIB_KINDS), kinds)
        self.assertLessEqual(verdicts, set(records.CALIB_VERDICTS), verdicts)
        self.assertEqual(records.CALIB_VERDICTS[0], "pass")


def re_marker_like():
    import re
    return re.compile(r"\s*#\s*item\s*:")


def dataclass_values(r):
    return [r.item, r.kind, r.verdict, r.date, r.slot_hash]


def firsttry_row_words():
    """(kind words, verdict words, row sites) that scripts/firsttry.py can write
    into a calibration file: the string constants that reach the 2nd and 3rd
    element of every `rows.append([...])` list, following a name to its
    assignments in the same function and a tuple unpacked from a module
    function to that function's returns."""
    tree = ast.parse((A.SCRIPTS / "firsttry.py").read_text(encoding="utf-8"))
    fns = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}

    def consts(expr, scope, depth=0):
        if depth > 4 or expr is None:
            return set()
        if isinstance(expr, ast.Constant):
            return {expr.value} if isinstance(expr.value, str) else set()
        if isinstance(expr, ast.IfExp):
            return consts(expr.body, scope, depth + 1) | consts(expr.orelse, scope, depth + 1)
        if isinstance(expr, ast.BoolOp):
            return set().union(*(consts(v, scope, depth + 1) for v in expr.values))
        if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and \
                expr.func.id in fns:
            return returns(fns[expr.func.id], None, depth + 1)
        if isinstance(expr, ast.Name):
            out = set()
            for node in ast.walk(scope):
                if not isinstance(node, ast.Assign):
                    continue
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name) and tgt.id == expr.id:
                        out |= consts(node.value, scope, depth + 1)
                    elif isinstance(tgt, ast.Tuple):
                        for i, el in enumerate(tgt.elts):
                            if isinstance(el, ast.Name) and el.id == expr.id:
                                v = node.value
                                if isinstance(v, ast.Tuple) and i < len(v.elts):
                                    out |= consts(v.elts[i], scope, depth + 1)
                                elif isinstance(v, ast.Call) and isinstance(v.func, ast.Name) \
                                        and v.func.id in fns:
                                    out |= returns(fns[v.func.id], i, depth + 1)
            return out
        return set()

    def returns(fn, index, depth):
        out = set()
        for node in ast.walk(fn):
            if isinstance(node, ast.Return) and node.value is not None:
                v = node.value
                if index is not None and isinstance(v, ast.Tuple) and index < len(v.elts):
                    out |= consts(v.elts[index], fn, depth)
                elif index is None:
                    out |= consts(v, fn, depth)
        return out

    kinds, verdicts, sites = set(), set(), 0
    for fn in fns.values():
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and \
                    node.func.attr == "append" and isinstance(node.func.value, ast.Name) and \
                    node.func.value.id == "rows" and node.args and \
                    isinstance(node.args[0], ast.List) and len(node.args[0].elts) == 5:
                sites += 1
                kinds |= consts(node.args[0].elts[1], fn)
                verdicts |= consts(node.args[0].elts[2], fn)
    return kinds, verdicts, sites


if __name__ == "__main__":
    unittest.main()
