"""Tool-free tests for dvl.dafny and the Dafny half of scripts/dvl/pins.toml.

Nothing here runs Dafny: the parser, the lint, the spec hash, the refusal
list, target resolution of refused projects, and the output parsers on raw
outputs captured from the pinned Dafny 4.11.0 (fixtures/dafny/captured/,
2026-10-04). Run: python3 -m unittest discover -s tests/wrappers -p 'test_dafny*.py'
"""

import os
import re
import shutil
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("DVL_SCRATCH", f"/tmp/dvl-test-{os.getuid()}")

from dvl import common  # noqa: E402
from dvl import dafny as D  # noqa: E402
import gen_units as gu  # noqa: E402

FX = ROOT / "tests/wrappers/fixtures/dafny"
CAP = FX / "captured"
EXPECT = re.compile(r"//\s*expect:\s*([a-z-]+(?:\s+[a-z-]+)*)\s*$")


def expected_marks(path):
    want = defaultdict(set)
    for ln, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        if m := EXPECT.search(line):
            want[ln].update(m.group(1).split())
    return want


def by_line(findings):
    got = defaultdict(set)
    for f in findings:
        got[f.line].add(f.kind)
    return got


class Pins(unittest.TestCase):
    """pins.toml is the one pinned-settings source and agrees with VERSIONS.md."""

    @classmethod
    def setUpClass(cls):
        cls.pins = common.load_pins()
        cls.versions = (ROOT / "VERSIONS.md").read_text(encoding="utf-8")
        blocks = re.findall(r"```text\n(.*?)```", cls.versions, re.S)
        cls.wordings = {}
        for b in blocks:
            ids = re.findall(r"(?m)^\[(W-[DV]\d\d)\]", b)
            bodies = re.split(r"(?m)^\[W-[DV]\d\d\][^\n]*\n", b)[1:]
            cls.wordings.update(zip(ids, bodies))

    def test_course_pins(self):
        d, v = self.pins["dafny"], self.pins["verus"]
        self.assertEqual(d["resource_limit"], 5000000)            # Δ56
        self.assertEqual(d["resource_limit"], gu.DAFNY_RESOURCE_LIMIT)
        self.assertEqual(d["cores"], 2)                            # Δ59
        self.assertEqual(d["mem_gb"], 8)                           # CLAUDE.md §Resources
        self.assertEqual(d["jobs"], 1)
        self.assertEqual(d["seeds"], [1, 2, 3])
        self.assertEqual(d["solver"], "dafny/z3/bin/z3-4.12.1")    # Δ10
        self.assertEqual(d["always"], ["--allow-axioms", "false"])
        self.assertEqual(d["gate"], ["--allow-warnings", "false"])
        self.assertEqual(v["rlimit"], 2)                           # Δ56
        self.assertGreaterEqual(v["mem_gb"], 16)                   # Δ57
        self.assertEqual(v["num_threads"], 1)
        self.assertEqual(v["jobs"], 1)
        self.assertEqual(v["timeout_s"], v["wall_clock_s"])

    def test_unit_options_carry_the_same_pin(self):
        for tier in ("core", "std"):
            opts, errs = gu.load_options(ROOT)
            self.assertEqual(errs, [])
            self.assertEqual(opts[tier][0]["resource-limit"], self.pins["dafny"]["resource_limit"])

    def test_dafny_messages_are_verbatim(self):
        for wid, text in self.pins["dafny"]["messages"].items():
            base = wid.split("-")[0] + "-" + wid.split("-")[1]
            with self.subTest(wid=wid):
                self.assertIn(base, self.wordings)
                self.assertIn(text, self.wordings[base])

    def test_verus_messages_are_verbatim(self):
        for wid, text in self.pins["verus"]["messages"].items():
            with self.subTest(wid=wid):
                self.assertIn(wid, self.wordings)
                self.assertIn(text, self.wordings[wid])

    def test_dafny_patterns_match_their_captured_instances(self):
        pats = {k: re.compile(v) for k, v in self.pins["dafny"]["patterns"].items()}
        cases = {
            "W-D06": ["Method _module._default.Mth has no body so it cannot be compiled"],
            "W-D07": ["Dafny program verifier finished with 0 verified, 0 errors",
                      "Dafny program verifier finished with 6 verified, 1 error",
                      "Dafny program verifier finished with 1 verified, 0 errors, 1 out of resource",
                      "Dafny program verifier finished with 1 verified, 0 errors, 1 time out"],
            "W-D08": ["Dafny program verifier finished with 1 assertions verified, 0 errors"],
            "W-D11": ["Verification out of resource (Arith)"],
            "W-D13-resolution": ["1 resolution/type errors detected in spec.dfy"],
            "W-D13-parse": ["2 parse errors detected in dec_star.dfy"],
            "W-D21-result": ["PassOne: PASSED", "FailOne: FAILED"],
            "W-D21-halted": ["[Program halted] tests.dfy(2,0): Test failures occurred: see above."],
            "W-D25": ["module Std does not exist (position 0 in path Std.Wrappers)"],
            "W-D26": ["Option --manual-lemma-induction unrecognized or unsupported in ':options' "
                      "attributes."],
            "W-D12": ["Verification of 'DivMix' timed out after 30 seconds. (the limit can be "
                      "increased using --verification-time-limit)"],
        }
        for wid, lines in cases.items():
            for line in lines:
                with self.subTest(wid=wid, line=line):
                    self.assertIn(line, self.versions)
                    self.assertTrue(pats[wid].match(line))

    def test_audit_issue_texts_are_verbatim(self):
        for kind, text in self.pins["dafny"]["audit_issues"].items():
            if kind == "assume-cross-module-termination":
                continue   # first captured in DV1b (captured/audit_std_unit.txt)
            with self.subTest(kind=kind):
                self.assertIn(text, self.wordings["W-D14"])
        self.assertIn(self.pins["dafny"]["audit_issues"]["assume-cross-module-termination"],
                      (CAP / "audit_std_unit.txt").read_text(encoding="utf-8"))

    def test_load_pins_refuses_a_broken_file(self):
        bad = Path(common.scratch_dir("pins-test")) / "pins.toml"
        bad.write_text("[dafny]\nresource_limit = 1\n[verus]\n", encoding="utf-8")
        with self.assertRaises(common.DvlError):
            common._load_pins_cached(str(bad))
        self.assertIsNot(common.load_pins(), common.load_pins())   # a fresh copy each call


class Tokenizer(unittest.TestCase):
    def test_comments_strings_chars_and_primes(self):
        toks = D.tokenize('x\' := "a // b" /* c /* nested */ d */ + \'q\' + @"v""w" // e\n...')
        self.assertEqual([t.text for t in toks],
                         ["x'", ":=", '"a // b"', "+", "'q'", "+", '@"v""w"', "..."])
        self.assertEqual(toks[-1].line, 2)

    def test_positions_are_one_based(self):
        t = D.tokenize("module M {\n  lemma L()\n}")
        lemma = next(x for x in t if x.text == "lemma")
        self.assertEqual((lemma.line, lemma.col), (2, 3))


class Parser(unittest.TestCase):
    def decl(self, text, name):
        return D.parse_source(text).decl(name)

    def test_set_display_in_ensures_is_not_a_body(self):
        src = "module M {\n lemma A(s: set<int>)\n  ensures s + {1} == {1} + s\n lemma B() ensures true {}\n}"
        self.assertIsNone(self.decl(src, "M.A").body)
        self.assertIsNotNone(self.decl(src, "M.B").body)

    def test_cardinality_and_generic_return_types(self):
        src = ("module M {\n function F(s: seq<int>): seq<int> { s }\n"
               " lemma L(s: seq<int>) ensures |F(s)| == |s|\n {\n }\n"
               " lemma H(s: seq<int>) ensures |s| >= 0\n lemma Z() ensures true {}\n}")
        self.assertIsNotNone(self.decl(src, "M.F").body)
        self.assertIsNotNone(self.decl(src, "M.L").body)
        self.assertIsNone(self.decl(src, "M.H").body)

    def test_decreases_star_match_and_by_method(self):
        src = ("module M {\n method Loop() decreases * { while true decreases * {} }\n"
               " function G(x: int): int ensures match x { case 0 => true case _ => true }"
               " { x }\n function P(x: nat): nat { x } by method { return x; }\n}")
        self.assertIsNotNone(self.decl(src, "M.Loop").body)
        g = self.decl(src, "M.G")
        self.assertIsNotNone(g.body)
        self.assertEqual(g.ensures, 1)
        self.assertIsNotNone(self.decl(src, "M.P").by_method)

    def test_modules_refinement_attributes_imports(self):
        src = ('include "x.dfy"\nabstract module A { lemma L() ensures true }\n'
               "module {:options \"--function-syntax:4\"} B refines A {\n import opened Std.Wrappers\n"
               " lemma {:induction false} L ...\n {\n }\n class C { method M() {} }\n}")
        s = D.parse_source(src)
        self.assertEqual([(m.qual, m.abstract, m.refines) for m in s.modules],
                         [("A", True, None), ("B", False, "A")])
        self.assertEqual(s.includes, [1])
        self.assertEqual(s.imports, [(4, "Std.Wrappers")])
        self.assertEqual(sorted((a.style, a.name) for a in s.attrs),
                         [("{:", "induction"), ("{:", "options")])
        self.assertIsNotNone(s.decl("B.L").body)
        self.assertEqual(s.decl("B.C.M").container_kind, "class")
        self.assertEqual(s.decl("A.L").container_kind, "abstract-module")

    def test_next_member_attribute_ends_a_bodyless_header(self):
        src = "module M {\n lemma A() ensures true\n {:axiom} lemma B() ensures true\n}"
        s = D.parse_source(src)
        self.assertIsNone(s.decl("M.A").body)
        self.assertEqual([a.name for a in s.decl("M.B").attrs], ["axiom"])


class Lint(unittest.TestCase):
    def test_learner_fixture_marks(self):
        f = FX / "lint/learner.dfy"
        self.assertEqual(by_line(D.lint([f], "learner")), expected_marks(f))

    def test_agent_fixture_marks(self):
        f = FX / "lint/strict.dfy"
        self.assertEqual(by_line(D.lint([f], "agent")), expected_marks(f))

    def test_reference_adds_slots_and_need_lines(self):
        f = FX / "lint/strict.dfy"
        want = expected_marks(f)
        want[20].add("need-missing")       # Q04.X1d's need: names a lemma the block lacks
        want[34].add("slot-in-reference")  # a leftover SLOT: line (spec §3.8.4 H6)
        self.assertEqual(by_line(D.lint([f], "reference")), want)

    def test_learner_mode_allows_loud_holes_only(self):
        kinds = {f.kind for f in D.lint([FX / "holes.dfy"], "learner")}
        self.assertEqual(kinds, {"multi-ensures-hole"})    # Δ5: two ensures count twice
        strict = by_line(D.lint([FX / "holes.dfy"], "agent"))
        self.assertEqual(strict, {9: {"assume"}, 18: {"bodyless"}, 22: {"bodyless"},
                                  27: {"bodyless"}})

    def test_silent_kinds_fixture(self):
        got = by_line(D.lint([FX / "silent.dfy"], "learner"))
        self.assertEqual(got, {4: {"bodyless-silent"}, 6: {"bodyless-silent"},
                               9: {"bodyless-silent"}, 11: {"axiom-attribute"},
                               18: {"assume-axiom"}, 22: {"decreases-star"},
                               25: {"decreases-star"}, 34: {"expect-outside-test"},
                               37: {"trait"}, 38: {"bodyless-abstract"},
                               43: {"abstract-module"}, 44: {"bodyless-abstract"}})

    def test_a_trait_a_class_implements_in_full_is_allowed(self):
        # DV5c (Q17.H1d): a trait that a class of the same file implements in full is
        # a statement, not a silent hole; anything less stays a finding (Δ3, G3)
        src = ("module M {\n"
               "  trait T {\n"
               "    ghost predicate P() reads this\n"
               "    method Put(x: nat) requires P() modifies this ensures P()\n"
               "  }\n"
               "  class C extends T {\n"
               "    ghost predicate P() reads this { true }\n"
               "    method Put(x: nat) requires P() modifies this ensures P() { }\n"
               "  }\n"
               "}\n")
        for mode in ("learner", "agent"):
            self.assertEqual(D.lint_source(src, "/x/a.dfy", mode), [], mode)
        part = src.replace("    method Put(x: nat) requires P() modifies this ensures P() { }\n", "")
        self.assertEqual(sorted((f.line, f.kind) for f in D.lint_source(part, "/x/a.dfy", "learner")),
                         [(2, "trait"), (3, "bodyless-abstract"), (4, "bodyless-abstract")])
        alone = src[:src.index("  class C")] + "}\n"
        self.assertEqual(sorted((f.line, f.kind) for f in D.lint_source(alone, "/x/a.dfy", "learner")),
                         [(2, "trait"), (3, "bodyless-abstract"), (4, "bodyless-abstract")])

    def test_the_audit_keeps_an_implemented_trait_s_members_as_statements(self):
        # DV5c: `dafny audit`'s bodyless rows on such a trait's members are dropped;
        # the helper names exactly those members' lines
        tmp = Path(tempfile.mkdtemp(prefix="dvl-trait-"))
        try:
            f = tmp / "a.dfy"
            f.write_text("module M {\n  trait T {\n    method Put(x: nat) ensures x >= 0\n  }\n"
                         "  class C extends T {\n    method Put(x: nat) ensures x >= 0 { }\n  }\n"
                         "  method Loose(x: nat) ensures x >= 0\n}\n")
            prog = SimpleNamespace(own=[str(f)], path_map={})
            self.assertEqual(D._implemented_trait_lines(prog, tmp), {(str(f.resolve()), 3)})
        finally:
            shutil.rmtree(tmp)

    def test_reserved_names(self):
        name = "solutions" + "_policy"
        src = (f"module {name.title()} {{ }}\nmodule M {{ import opened solutions_first }}\n"
               "module N refines Solutions_First {}\n")
        got = D.lint_source(src, f"/x/{name}.dfy", "reference")
        self.assertEqual(sorted((f.line, f.kind) for f in got),
                         [(1, "reserved-name"), (1, "reserved-name"), (2, "reserved-name"),
                          (3, "reserved-name")])
        self.assertEqual(D.lint_source("module SolutionsPolicyNotes {}", "/x/a.dfy", "learner"), [])

    def test_messages_never_quote_code(self):
        rule_texts = set(D.LEARNER_RULES.values()) | set(D.STRICT_RULES.values()) | \
            set(D.GIVEN_RULES.values()) | {t for _, t in D.ATTR_RULES.values()}
        for f in D.lint([FX / "lint/learner.dfy", FX / "silent.dfy"], "agent"):
            self.assertIn(f.message, rule_texts)
        for f in D.lint([FX / "given"], "given"):
            self.assertIn(f.message, rule_texts)

    def test_empty_list_and_bad_mode_fail(self):
        with self.assertRaises(ValueError):
            D.lint([], "learner")
        with self.assertRaises(ValueError):
            D.lint([FX / "ok.dfy"], "loose")

    def test_directories_are_walked(self):
        got = D.lint([FX / "freeze"], "learner")
        self.assertEqual({(Path(f.file).name, f.kind) for f in got},
                         {("spec.dfy", "abstract-module"), ("spec.dfy", "bodyless-abstract"),
                          ("axiom.dfy", "axiom-attribute"), ("axiom.dfy", "bodyless-silent")})


class GivenRole(unittest.TestCase):
    """The given-role lint (Δ3, Δ44): a frozen abstract spec that concrete modules
    of the same program refine in full is allowed in a given layer or a declared
    statement, and nowhere else. Fixtures: fixtures/dafny/given/ (invented)."""

    G = FX / "given"
    REFINED_SPEC = {3: {"abstract-module"}, 5: {"uninitialized-const"},
                    6: {"bodyless-abstract"}, 7: {"bodyless-abstract"},
                    8: {"bodyless-abstract"}, 10: {"bodyless-abstract"},
                    13: {"bodyless-abstract"}}

    def lint(self, names, mode, **kw):
        return by_line(D.lint([self.G / n for n in names], mode, **kw))

    def test_a_full_refinement_is_allowed_only_in_the_given_role(self):
        self.assertEqual(self.lint(["refined.dfy"], "given"), {})
        for mode in ("learner", "agent", "reference"):
            self.assertEqual(self.lint(["refined.dfy"], mode), self.REFINED_SPEC, mode)

    def test_a_refinement_chain_through_an_abstract_module(self):
        self.assertEqual(self.lint(["chain.dfy"], "given"), {})
        self.assertEqual(self.lint(["chain.dfy"], "learner"),
                         {3: {"abstract-module"}, 4: {"bodyless-abstract"},
                          5: {"bodyless-abstract"}, 7: {"bodyless-abstract"},
                          11: {"abstract-module"}})

    def test_a_statement_left_without_a_body_is_named(self):
        self.assertEqual(self.lint(["partial.dfy"], "given"),
                         {3: {"abstract-not-refined"}, 9: {"bodyless-abstract"}})

    def test_nothing_concrete_refines_it_and_traits_stay_findings(self):
        self.assertEqual(self.lint(["unrefined.dfy"], "given"),
                         {3: {"abstract-not-refined"}, 4: {"uninitialized-const"},
                          5: {"bodyless-abstract"}, 7: {"bodyless-abstract"},
                          11: {"abstract-not-refined"}, 15: {"trait"},
                          16: {"bodyless-abstract"}})

    def test_the_refiner_may_live_in_another_file_of_the_program(self):
        alone = {3: {"abstract-not-refined"}, 4: {"bodyless-abstract"}, 6: {"bodyless-abstract"}}
        self.assertEqual(self.lint(["spec_only.dfy"], "given"), alone)
        self.assertEqual(self.lint(["spec_only.dfy"], "given",
                                   context=[self.G / "impl_only.dfy"]), {})
        self.assertEqual(self.lint(["spec_only.dfy", "impl_only.dfy"], "given"), {})
        self.assertEqual(self.lint(["spec_only.dfy"], "learner",
                                   context=[self.G / "impl_only.dfy"]),
                         {3: {"abstract-module"}, 4: {"bodyless-abstract"},
                          6: {"bodyless-abstract"}})

    def test_the_role_comes_from_the_course_path(self):
        """In every mode, a course tree's given layer and a registry-declared
        statement (Δ73) get the given role; the same text elsewhere does not."""
        root = common.scratch_dir("dafny-given-role") / "root"
        try:
            (root / "dafny/options").mkdir(parents=True)
            st = "Challenges/Q19_Fx/Q19_FxStatement.dfy"
            (root / "MODULES.toml").write_text(
                f'schema = 1\n\n[[module]]\nid = "Q19"\n'
                f'statements = [{{ path = "{st}", sha256 = "PENDING" }}]\n', encoding="utf-8")
            places = {"dafny/given/Q/QG_L4_FxSpec.dfy": "refined.dfy",
                      "dafny/Q/Q08_Fx/Q08_Fx.dfy": "refined.dfy",
                      st: "spec_only.dfy",
                      "Challenges/Q19_Fx/Q19_OtherStatement.dfy": "spec_only.dfy"}
            for rel, name in places.items():
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_text((self.G / name).read_text(), encoding="utf-8")
            got = lambda rel, mode="learner": by_line(D.lint([root / rel], mode))  # noqa: E731
            for mode in ("learner", "reference"):
                self.assertEqual(got("dafny/given/Q/QG_L4_FxSpec.dfy", mode), {}, mode)
                self.assertEqual(got(st, mode), {}, mode)   # a statement: abstract by design
            self.assertEqual(got("dafny/Q/Q08_Fx/Q08_Fx.dfy"), self.REFINED_SPEC)
            self.assertEqual(got("Challenges/Q19_Fx/Q19_OtherStatement.dfy"),
                             {3: {"abstract-module"}, 4: {"bodyless-abstract"},
                              6: {"bodyless-abstract"}})
            outside = root.parent / "dafny/given/Q/QG_L4_FxSpec.dfy"   # no course root above
            outside.parent.mkdir(parents=True)
            outside.write_text((self.G / "refined.dfy").read_text(), encoding="utf-8")
            self.assertEqual(by_line(D.lint([outside], "learner")), self.REFINED_SPEC)
        finally:
            import shutil
            shutil.rmtree(root.parent, ignore_errors=True)


class SpecHash(unittest.TestCase):
    def test_layout_comments_attributes_and_proofs_do_not_count(self):
        self.assertEqual(D.spec_hash(FX / "hash/base.dfy"), D.spec_hash(FX / "hash/reformatted.dfy"))

    def test_every_changed_statement_changes_its_hash(self):
        a, b = D.spec_hash(FX / "hash/base.dfy"), D.spec_hash(FX / "hash/changed.dfy")
        self.assertEqual(sorted(a), ["Fx_Hash.Halve", "Fx_Hash.Twice", "Fx_Hash.TwiceGrows"])
        self.assertTrue(all(a[k] != b[k] for k in a))

    def test_symbol_filter_and_digest_shape(self):
        h = D.spec_hash(FX / "hash/base.dfy", symbols=["Fx_Hash.Twice"])
        self.assertEqual(list(h), ["Fx_Hash.Twice"])
        self.assertRegex(h["Fx_Hash.Twice"], r"^[0-9a-f]{64}$")

    def test_a_frozen_file_with_no_statement_is_freeze_empty(self):
        """DV6 fix round: as Verus's freeze-empty, a frozen file that freezes nothing fails."""
        import tempfile
        d = Path(tempfile.mkdtemp(prefix="dvl0-freeze-"))
        self.addCleanup(__import__("shutil").rmtree, d, True)
        (d / "empty.dfy").write_text("// nothing frozen here\nmodule Fx_Empty {\n}\n")
        got = D.freeze_check(d / "empty.dfy", FX / "hash/base.dfy")
        self.assertEqual([f.kind for f in got], ["freeze-empty"])

    def test_hash_mode_freeze(self):
        self.assertEqual(D.freeze_check(FX / "hash/base.dfy", FX / "hash/reformatted.dfy"), [])
        got = D.freeze_check(FX / "hash/base.dfy", FX / "hash/changed.dfy")
        self.assertEqual([(f.line, f.kind) for f in got],
                         [(3, "freeze-changed"), (5, "freeze-changed"), (11, "freeze-changed")])
        got = D.freeze_check(D.spec_hash(FX / "hash/base.dfy"), FX / "ok.dfy")
        self.assertEqual([f.kind for f in got], ["freeze-missing"] * 3)
        with self.assertRaises(ValueError):
            D.freeze_check({}, FX / "ok.dfy")


class CheckArgs(unittest.TestCase):
    def test_refused_everywhere(self):
        for args in (["/compile:0"], ["/allowAxioms:0"], ["--no-verify"], ["--allow-warnings"],
                     ["--allow-axioms"], ["--allow-external-contracts"], ["--boogie", "/x"],
                     ["--solver-option", "x"], ["--plugin", "p.dll"], ["--library", "l.dfy"],
                     ["--solver-path", "/usr/bin/z3"], ["--verification-time-limit", "0"],
                     ["--verification-time-limit=0"], ["--resource-limit", "1"], ["--cores", "16"],
                     ["--prelude", "p.bpl"], ["--bprint", "x"], ["--find-project"],
                     ["--manual-lemma-induction"], ["--unknown-flag"]):
            for gate in (False, True):
                with self.subTest(args=args, gate=gate):
                    self.assertTrue(D.check_args(args, gate))

    def test_paths_are_not_options(self):
        self.assertEqual(D.check_args(["/home/x/unit/a.dfy", "b.dfy"], True), [])
        self.assertEqual(len(D.check_args(["/print:/tmp/x.bpl"], False)), 1)

    def test_filters_only_in_the_loop(self):
        for args in (["--filter-symbol", "M.L"], ["--filter-position", "a.dfy:3"],
                     ["--isolate-assertions"], ["--filter-symbol=M.L"]):
            with self.subTest(args=args):
                self.assertEqual(D.check_args(args, False), [])
                self.assertTrue(D.check_args(args, True))


class Targets(unittest.TestCase):
    """Refusals that happen before any tool runs."""

    def assertRefused(self, target, fragment):
        with self.assertRaises(D.Refused) as cm:
            D.program(target)
        self.assertIn(fragment, str(cm.exception))

    def test_poisoned_projects(self):
        self.assertRefused(FX / "projects/poison_base", "'base' is refused")
        self.assertRefused(FX / "projects/poison_solver", "'solver-path' is refused")
        self.assertRefused(FX / "projects/poison_options", "'allow-warnings' is refused")
        self.assertRefused(FX / "projects/empty_glob", "match no file")
        self.assertRefused(FX / "projects/wrongname/project.toml", "W-D30")
        self.assertRefused(FX / "projects", "not a unit")
        self.assertRefused(FX / "README.md", "not a Dafny file")
        self.assertRefused(FX / "nowhere.dfy", "no such file")

    def test_unit_and_file_targets(self):
        p = D.program(FX / "projects/unit_ok/unit.dfy")
        self.assertEqual(p.kind, "project")
        self.assertEqual(p.project, (FX / "projects/unit_ok/dfyconfig.toml").resolve())
        self.assertEqual(p.inputs(), [str(p.project)])
        self.assertEqual(p.options, {"resource-limit": 5000000, "manual-lemma-induction": True})
        f = D.program(FX / "ok.dfy")
        self.assertEqual((f.kind, f.inputs(), f.std), ("files", [str((FX / "ok.dfy").resolve())],
                                                       False))
        s = D.program(FX / "p1.dfy.specimen")
        try:
            self.assertEqual(Path(s.files[0]).name, "p1.dfy")
            self.assertEqual(s.path_map, [(str(s.files[0]),
                                           str((FX / "p1.dfy.specimen").resolve()))])
        finally:
            D.discard(s)
        self.assertFalse(Path(s.files[0]).exists())


class Parsers(unittest.TestCase):
    """The output parsers on raw outputs captured from the pinned Dafny."""

    def test_json_lines_fill_templates_and_keep_related(self):
        diags, status, _ = D.parse_json_lines((CAP / "verify_resolve_error.jsonl").read_text())
        self.assertEqual([(Path(d.file).name, d.line, d.col, d.severity, d.message) for d in diags],
                         [("resolve_error.dfy", 4, 13, "error", "unresolved identifier: Undefined")])
        self.assertEqual(status, ["1 resolution/type errors detected in resolve_error.dfy"])
        diags, status, _ = D.parse_json_lines((CAP / "verify_fails.jsonl").read_text())
        self.assertEqual([(d.line, d.col, d.severity, d.code) for d in diags],
                         [(12, 3, "error", "W-D10"), (11, 20, "related", "W-D10"),
                          (17, 5, "error", "W-D09")])
        self.assertIn("Dafny program verifier finished with 2 verified, 2 errors", status)
        self.assertTrue(all(Path(d.file).is_absolute() for d in diags))   # from the uri

    def test_csv_per_symbol_and_out_of_resource(self):
        rows = D.parse_csv_log(CAP / "verify_fails.csv")
        diags, _, _ = D.parse_json_lines((CAP / "verify_fails.jsonl").read_text())
        self.assertEqual(D.per_symbol_status(rows, diags),
                         {"Fx_Fails.Inc": "verified", "Fx_Fails.Good": "verified",
                          "Fx_Fails.Bad": "failed", "Fx_Fails.BadAssert": "failed"})
        rows = D.parse_csv_log(CAP / "verify_oor.csv")
        diags, _, _ = D.parse_json_lines((CAP / "verify_oor.jsonl").read_text())
        self.assertEqual(D.per_symbol_status(rows, diags), {"Fx_Oor.Hard": "inconclusive"})
        self.assertEqual(diags[0].code, "W-D11")
        rows = D.parse_csv_log(CAP / "measure_fails_seed1.csv")
        self.assertEqual(sum(1 for _, o, _ in rows if o == "Passed"), 2)

    def test_filtered_runs(self):
        """--filter-position prints W-D08 and counts assertions (Δ39); a filter
        that matches nothing exits 0 but fails (Δ11, G8). Outputs captured from
        sym.dfy runs (cmd lines as the wrapper built them)."""
        def classify(name, cmd, csv=None, symbol=None):
            diags, status, errors = D.parse_json_lines((CAP / name).read_text())
            rows = D.parse_csv_log(CAP / csv) if csv else []
            res = common.Result("dafny", "t", 0, "error", "verify", None, [], diags, [],
                                D.per_symbol_status(rows, diags), None, cmd)
            D._classify_verify(res, status + errors, rows, False, symbol, False)
            return res, [f.kind for f in res.findings]

        base = ["/d/dafny", "verify", "/x/sym.dfy", "--json-output"]
        r, k = classify("verify_filter_position.jsonl", base + ["--filter-position", "sym.dfy:5"],
                        "verify_filter_position.csv")
        self.assertEqual((r.verdict, r.verified_count, D.count_unit(r), k, r.per_symbol),
                         ("verified", 1, "assertions", [], {"Fx_Sym.Good": "verified"}))
        r, k = classify("verify_filter_position_nomatch.jsonl",
                        base + ["--filter-position=sym.dfy:99"])
        self.assertEqual((r.verdict, r.verified_count, D.count_unit(r), k),
                         ("failed", 0, "assertions", ["filter-matched-nothing"]))
        r, k = classify("verify_filter_symbol_nomatch.jsonl", base + ["--filter-symbol", "Nope"])
        self.assertEqual((r.verdict, r.verified_count, D.count_unit(r), k),
                         ("failed", 0, "tasks", ["filter-matched-nothing"]))
        r, k = classify("verify_filter_symbol_nomatch.jsonl", base)   # no filter: a note only
        self.assertEqual((r.verdict, k), ("verified", ["nothing-verified"]))
        seeded = common.Result("dafny", "t", 0, "verified", "verify",
                               cmd=["/d/dafny", "measure-complexity", "/x/a.dfy"])
        self.assertEqual(D.count_unit(seeded), "passed-tasks")

    def test_holes_from_resolve_text_dedupe_by_position(self):
        text = (CAP / "resolve_holes.txt").read_text()
        diags, _ = D.parse_text(text)
        holes = D.holes_from(diags, label_files=False)
        self.assertEqual([(h.line, h.col, h.kind) for h in holes],
                         [(9, 5, "assume"), (19, 20, "bodyless-method"),
                          (23, 20, "bodyless-method"), (24, 20, "bodyless-method"),
                          (28, 29, "bodyless-function")])
        doubled = "\n".join(line for line in text.splitlines() for _ in (0, 1))
        self.assertEqual(len(D.holes_from(D.parse_text(doubled)[0], label_files=False)), 5)

    def test_only_the_exact_pinned_wordings_count(self):
        near = "This ensures clause is part of a bodyless lemma. Add the {:axiom} attribute"
        diags = [common.Diag("/x.dfy", 3, 5, "warning", near, ""),
                 common.Diag("/x.dfy", 4, 5, "warning", "assume statement has no {:axiom} annotation",
                             "W-D03"),
                 common.Diag("/x.dfy", 5, 5, "error", "assume statement has no {:axiom} annotation",
                             "W-D03")]
        self.assertEqual([h.line for h in D.holes_from(diags, label_files=False)], [4])

    def test_audit_rows_stdlib_excluded_and_pinned(self):
        text = (CAP / "audit_std_unit.txt").read_text()
        prog = D.Program(Path("/x"), "project", None, [], [], {}, None, None, True)
        got = D.audit_findings(text, prog, "/tmp")
        self.assertEqual([(Path(f.file).name, f.line, f.kind) for f in got],
                         [("Q04_Library.dfy", 8, "audit-bodyless-ghost")])
        prog.std = False   # a core unit may not see standard-library rows at all
        self.assertIn("audit-stdlib-drift", [f.kind for f in D.audit_findings(text, prog, "/tmp")])
        cut = "\n".join(text.splitlines()[:-4])   # rows but no summary line
        self.assertIn("audit-error", [f.kind for f in D.audit_findings(cut, prog, "/tmp")])

    def test_test_output(self):
        out = (CAP / "test_tests.txt").read_text()
        prog = D.Program(Path("/x/tests.dfy"), "files", None, [], [], {}, None, None, False)
        res = D._parse_test(out, 3, prog, "/tmp/none", "tests.dfy", [], [])
        self.assertEqual(res.per_symbol, {"Fx_Tests.PassOne": "passed",
                                          "Fx_Tests.FailOne": "failed",
                                          "Fx_Tests.PassTwo": "passed"})
        self.assertEqual((res.verdict, res.stage), ("failed", "test"))
        self.assertEqual([(d.line, d.message) for d in res.diagnostics],
                         [(2, "Test failures occurred: see above."), (11, "two doubled")])

    def test_printing_tests(self):
        """A test's own output lands between "<Name>: " and its status (DV2b-2:
        a printing pass read as "no test ran", a printing failure lost its
        FAILED line). Captured from tests_print.dfy on the pinned 4.11.0."""
        prog = D.Program(Path("/x/tests_print.dfy"), "files", None, [], [], {}, None, None, False)
        run = lambda cap, rc, names: D._parse_test((CAP / cap).read_text(), rc, prog,  # noqa: E731
                                                   "/tmp/none", "tests_print.dfy", [], names)
        res = run("test_print_pass.txt", 0, ["PrintsThenPasses"])
        self.assertEqual((res.verdict, res.stage, res.per_symbol, res.findings),
                         ("verified", "test", {"Fx_PrintTests.PrintsThenPasses": "passed"}, []))
        res = run("test_print_fail.txt", 3, ["PrintsThenFails"])
        self.assertEqual((res.verdict, res.stage, res.per_symbol, res.findings),
                         ("failed", "test", {"Fx_PrintTests.PrintsThenFails": "failed"}, []))
        self.assertEqual([(d.line, d.message) for d in res.diagnostics],
                         [(3, "Test failures occurred: see above."), (14, "two doubled")])
        res = run("test_print_all.txt", 3, [])
        self.assertEqual(res.per_symbol, {"Fx_PrintTests.PrintsThenPasses": "passed",
                                          "Fx_PrintTests.PrintsThenFails": "failed",
                                          "Fx_PrintTests.PrintsNoNewline": "passed",
                                          "Fx_PrintTests.Quiet": "passed"})
        self.assertEqual((res.verdict, res.stage, res.findings), ("failed", "test", []))

    def test_test_status_edges(self):
        """Edits of the captured shape: diagnostics before the verifier summary
        are never results, a FAILED after an output line that ends in PASSED
        still fails its test, and a test that never reports is failed."""
        head = ("x.dfy(4,4): Warning: assume statement has no {:axiom} annotation\n\n"
                "Dafny program verifier finished with 1 verified, 0 errors\n")
        self.assertEqual(D._test_statuses(head + "M.A: says PASSED\nFAILED\n"
                                          "\tx.dfy(9,4): boom\nM.B: PASSED\n"),
                         {"M.A": "failed", "M.B": "passed"})
        self.assertEqual(D._test_statuses(head + "M.A: PASSED\nM.B: started\n"),
                         {"M.A": "passed", "M.B": "failed"})
        self.assertEqual(D._test_statuses(head), {})


class HoleRegions(unittest.TestCase):
    """QPLAN §6 Q18: the learner regions of a twin (dvl.common) and the Dafny
    empty-body variants built from them, and the by-method variant."""

    def test_regions_and_strip(self):
        text = ("a\n  // @hole-begin Q09.H1d\n  x\n  y\n  // @hole-end Q09.H1d\nb\n"
                "# @hole-begin Q09.H2d\nz\n# @hole-end Q09.H2d\n  // @hole-begin Q09.H1d\n"
                "w\n  // @hole-end Q09.H1d\n")
        self.assertEqual(common.hole_regions(text), [("Q09.H1d", 2, 5), ("Q09.H2d", 7, 9),
                                                     ("Q09.H1d", 10, 12)])
        self.assertEqual(common.hole_regions(text, "Q09.H2d"), [("Q09.H2d", 7, 9)])
        out = common.strip_regions(text, "Q09.H1d").split("\n")
        self.assertEqual(out[2:4] + out[10:11], ["", "", ""])
        self.assertEqual(out[7], "z")
        self.assertEqual(len(out), len(text.split("\n")))
        with self.assertRaises(ValueError):
            common.strip_regions(text, "Q09.H3d")                  # owns no region
        for bad, why in (("// @hole-begin A.H1d\n// @hole-begin A.H2d\n", "never nest"),
                         ("// @hole-end A.H1d\n", "without its @hole-begin"),
                         ("// @hole-begin A.H1d\n// @hole-end A.H2d\n", "closes the region"),
                         ("x\n// @hole-begin A.H1d\n", "never closed")):
            with self.assertRaisesRegex(ValueError, why):
                common.hole_regions(bad)

    def test_dafny_variants(self):
        src = D.parse_file(FX / "eb_regions.dfy")
        d = next(x for x in src.decls if x.name == "TriLoop")
        whole = D._empty_body_text(src, d, False)
        self.assertIn("function TriLoop(n: nat): nat {\n    Tri(n)\n  } by method {}", whole)
        region = D._empty_body_text(src, d, False, "Q09.H4d")
        self.assertNotIn("invariant", region)
        self.assertIn("r := r + i;", region)
        self.assertEqual(region.count("\n"), src.text.count("\n"))
        h = next(x for x in src.decls if x.name == "Half")
        self.assertNotIn("requires n % 2 == 0", D._empty_body_text(src, h, False, "Q09.H5d"))
        self.assertIn("r := n / 2;", D._empty_body_text(src, h, False, "Q09.H5d"))


class FileTier(unittest.TestCase):
    """QPLAN §6 Q13: a module file outside a unit builds in the tier its
    [module.imports] entry declares; an undeclared one (a probe) is std when
    it imports Std or a std-tier layer. D.program runs no tool."""

    def setUp(self):
        sys.path.insert(0, str(ROOT / "tests/wrappers"))
        import test_tools_common as C
        self.C = C
        self.root = C.build_root(overlay=False)
        self.agent = self.root / "dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy"

    def tearDown(self):
        self.C.remove_root(self.root)

    def names(self, prog):
        return [Path(f).name for f in prog.files]

    def test_declared_tier_wins(self):
        prog = D.program(self.agent)                         # declared core, no Std import
        self.assertEqual((self.names(prog), prog.std),
                         (["Q04_AgentRetriever.dfy", "QG_L1_BigNat.dfy", "QG_L2_BigNat.dfy"], False))
        reg = self.root / "MODULES.toml"
        rel = "dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy"
        reg.write_text(reg.read_text().replace(f'"{rel}" = "core"', f'"{rel}" = "std"'))
        prog = D.program(self.agent)                         # declared std: L3 and the library
        self.assertEqual(self.names(prog), ["Q04_AgentRetriever.dfy", "QG_L1_BigNat.dfy",
                                            "QG_L2_BigNat.dfy", "QG_L3_BigNat.dfy"])
        self.assertTrue(prog.std)
        self.assertIn("--standard-libraries", prog.cli_options())
        self.assertEqual(D.file_tier(self.root, self.agent, rel), "std")
        reg.write_text(reg.read_text().replace(f'"{rel}" = "std"', f'"{rel}" = "std-all"'))
        self.assertEqual(D.file_tier(self.root, self.agent, rel), "std")

    def test_undeclared_files_infer_the_tier(self):
        probe = self.root / "dafny/Q/Q04_ProofCraft/agent/Q04_Probe.dfy"
        rel = "dafny/Q/Q04_ProofCraft/agent/Q04_Probe.dfy"
        probe.write_text("module Q04_Probe {\n  import opened QG_L3_BigNat\n}\n")
        self.assertIsNone(D.registry_tier(self.root, rel))
        self.assertEqual(D.file_tier(self.root, probe, rel), "std")
        self.assertIn("QG_L3_BigNat.dfy", self.names(D.program(probe)))
        probe.write_text("module Q04_Probe {\n  import opened QG_L2_BigNat\n}\n")
        self.assertEqual(D.file_tier(self.root, probe, rel), "core")
        probe.write_text("module Q04_Probe {\n  import Std.Wrappers\n}\n")
        self.assertEqual(D.file_tier(self.root, probe, rel), "std")


class CommonStatic(unittest.TestCase):
    def test_result_vocabulary(self):
        with self.assertRaises(ValueError):
            common.Result("dafny", "t", 0, "green", "verify")
        with self.assertRaises(ValueError):
            common.Result("dafny", "t", 0, "verified", "elaborate")
        r = common.Result("dafny", "t", 0, "verified", "verify", 2)
        self.assertIn('"verdict": "verified"', common.to_json(r))

    def test_pools_and_jobs(self):
        self.assertEqual(common.pool_of(["/a/dafny/dafny", "verify"]), "dafny")
        self.assertEqual(common.pool_of(["/a/verus-x86-linux/verus"]), "verus")
        self.assertEqual(common.pool_of(["/a/verus-x86-linux/cargo-verus"]), "verus")
        old = os.environ.get("DVL_DAFNY_JOBS")
        try:
            os.environ.pop("DVL_DAFNY_JOBS", None)
            self.assertEqual(common.jobs("dafny"), 1)
            os.environ["DVL_DAFNY_JOBS"] = "2"
            self.assertEqual(common.jobs("dafny"), 2)
            os.environ["DVL_DAFNY_JOBS"] = "0"
            with self.assertRaises(common.DvlError):
                common.jobs("dafny")
        finally:
            if old is None:
                os.environ.pop("DVL_DAFNY_JOBS", None)
            else:
                os.environ["DVL_DAFNY_JOBS"] = old

    def test_scratch_never_inside_the_course_tree(self):
        old = os.environ.get("DVL_SCRATCH")
        try:
            os.environ["DVL_SCRATCH"] = str(ROOT / "instructor/scratch/dvl")
            with self.assertRaises(common.DvlError):
                common.scratch_root()
        finally:
            os.environ["DVL_SCRATCH"] = old


if __name__ == "__main__":
    unittest.main()
