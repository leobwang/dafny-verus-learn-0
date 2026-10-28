"""Tool-free tests for dvl.verus, dvl.verus_spec and the Verus half of
scripts/dvl/pins.toml.

Nothing here runs Verus: the tokenizer and item parser, the lint, the spec
hash and freeze check, the argument policy, target resolution, the
empty-body rewrites, and the output classifier on raw outputs captured from
the pinned Verus 0.2026.09.27.3cf1832 (fixtures/verus/captured/, captured
2026-10-04 by `python3 tests/wrappers/test_verus_tool.py --recapture`).
Run: python3 -m unittest discover -s tests/wrappers -p 'test_verus_static.py'
"""

import json
import os
import re
import sys
import tempfile
import unittest
from unittest import mock
from collections import defaultdict
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("DVL_SCRATCH", f"/tmp/dvl-test-{os.getuid()}")

from dvl import common  # noqa: E402
from dvl import verus as V  # noqa: E402
from dvl import verus_spec as vs  # noqa: E402

FX = ROOT / "tests/wrappers/fixtures/verus"
CAP = FX / "captured"
EXPECT = re.compile(r"//\s*expect:\s*([a-z-]+(?:\s+[a-z-]+)*)\s*$")


def expected_marks(path):
    want = defaultdict(set)
    for ln, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        if m := EXPECT.search(line):
            want[ln].update(m.group(1).split())
    return dict(want)


def by_line(findings):
    got = defaultdict(set)
    for f in findings:
        got[f.line].add(f.kind)
    return dict(got)


def captured(name):
    return ((CAP / f"{name}.stdout").read_text(), (CAP / f"{name}.stderr").read_text(),
            int((CAP / f"{name}.exit").read_text()))


def classify(name, crate, gate=False, partial=None, min_verified=None):
    """_classify over a captured run, as if run with the fixtures as cwd."""
    out, err, rc = captured(name)
    run = V.Run(FX, str(FX / f"{crate}.rs"))
    run.files = [(FX / f"{crate}.rs", "", False)]
    job = V.Job("target", ["verus"], rc, out, err, FX)
    return V._classify(run, job, crate, gate, min_verified, [], partial)


class Pins(unittest.TestCase):
    def test_course_pins(self):
        p = V.pins()
        self.assertEqual((p["rlimit"], p["num_threads"]), (2, 1))          # Δ56
        self.assertGreaterEqual(p["mem_gb"], 16)                            # Δ57
        self.assertEqual(p["rust_toolchain"], "1.98.1-x86_64-unknown-linux-gnu")
        self.assertEqual(p["seed_smt_option"], "smt.random_seed")           # Δ13
        self.assertTrue(p["seeds"])
        for k in ("--no-verify", "--no-lifetime", "--no-erasure-check",
                  "-V no-solver-version-check", "-V allow-inline-air"):
            self.assertIn(k, p["refused_args"])
        self.assertTrue({"VERUS_Z3_PATH", "VERUS_EXTRA_ARGS", "RUSTFLAGS", "RUSTC_WRAPPER"}
                        <= set(p["scrub_env"]))
        self.assertTrue({"W-V05", "W-V14"} <= set(p["patterns"]))       # captured variants
        self.assertFalse(hasattr(V, "OBSERVED_PATTERNS"))               # one source: the pins

    def test_job_environment(self):
        with tempfile.TemporaryDirectory() as d:
            saved = dict(os.environ)
            os.environ.update({"VERUS_Z3_PATH": "/x", "VERUS_EXTRA_ARGS": "--no-verify",
                               "RUSTFLAGS": "--cfg verus_only", "RUSTC_WRAPPER": "/x"})
            try:
                env = V.job_env(d)
            finally:
                os.environ.clear()
                os.environ.update(saved)
        for k in ("VERUS_Z3_PATH", "VERUS_EXTRA_ARGS", "RUSTFLAGS", "RUSTC_WRAPPER"):
            self.assertNotIn(k, env)
        self.assertEqual(env["RUSTUP_TOOLCHAIN"], V.pins()["rust_toolchain"])
        self.assertTrue(env["PATH"].endswith("/usr/bin:/bin"))

    def test_message_ids(self):
        for line, mid in (("error: assume/admit not allowed with --no-cheating", "W-V07"),
                          ("error: external_body/assume_specification not allowed with "
                           "--no-cheating", "W-V08"),
                          ("error: aborting due to 4 previous errors", "W-V14"),
                          ("error: aborting due to 1 previous error; 1 warning emitted", "W-V14"),
                          ("error: assert_nonlinear_by: Resource limit (rlimit) exceeded; "
                           "consider rerunning with --profile for more details", "W-V05"),
                          ("error: function body check: Resource limit (rlimit) exceeded; "
                           "consider rerunning with --profile for more details", "W-V05"),
                          ("Error: --verify-function option requires --verify-only-module or "
                           "--verify-root", "W-V16"),
                          ("error: something else", "")):
            self.assertEqual(V.message_id(line), mid, line)


class Tokenizer(unittest.TestCase):
    def test_comments_strings_chars(self):
        src = ('/* a /* nested */ comment */ fn f<\'a>(x: &\'a u8) -> char {\n'
               '  let s = r#"a "quoted" } {"#; let b = b\'{\'; let c = \'}\';\n'
               '  let e = \'\\\'\'; let t = x.0.1; // } line comment\n  \'a\' }\n')
        toks = vs.tokenize(src)
        texts = [t.text for t in toks]
        self.assertNotIn("nested", texts)
        self.assertIn('r#"a "quoted" } {"#', texts)
        self.assertIn("b'{'", texts)
        self.assertIn("'}'", texts)
        self.assertIn("'\\''", texts)
        self.assertEqual([t.kind for t in toks if t.text == "'a"], ["life", "life"])
        self.assertEqual(vs.match_brackets(toks)[texts.index("{")], len(toks) - 1)
        last = toks[-2]
        self.assertEqual((last.text, last.line, last.col), ("'a'", 4, 3))

    def test_unbalanced(self):
        with self.assertRaises(vs.ParseError):
            vs.parse("verus! { fn f() { }")
        with self.assertRaises(vs.ParseError):
            vs.tokenize('fn f() { "open }')


class Parser(unittest.TestCase):
    SRC = """use vstd::prelude::*;
mod a;
#[cfg(test)]
mod tests;
verus! {
pub open spec(checked) fn s(x: int) -> int { x }
pub proof fn p(x: nat)
    requires x > 0,
    ensures match x { 0 => false, _ => true }, if x > 1 { true } else { x == 1 },
    decreases x,
{ }
pub mod inner {
    pub struct T { pub v: u64 }
    impl T {
        pub fn get(&self) -> (r: u64) ensures r == self.v { self.v }
    }
    pub trait Tr { spec fn m(&self) -> int; }
    impl Tr for T { open spec fn m(&self) -> int { 0 } }
}
pub broadcast group g { p }
pub assume_specification[ core::cmp::max ](a: u64, b: u64) -> (r: u64);
} // verus!
fn outside() {}
"""

    def test_items(self):
        src = vs.parse(self.SRC)
        fns = {vs.item_symbol(it): it for it in src.walk() if it.kind == "fn"}
        self.assertEqual(sorted(fns), ["inner::<T as Tr>::m", "inner::T::get", "inner::Tr::m",
                                       "outside", "p", "s"])
        p = fns["p"]
        self.assertEqual(p.mode, "proof")
        self.assertEqual([k for k, _, _ in p.clauses], ["requires", "ensures", "decreases"])
        self.assertEqual(src.line_of(p.body[0]), 11)
        self.assertEqual(len(vs.clause_exprs(src, p, "ensures")), 2)
        self.assertEqual(fns["s"].mode, "spec")
        self.assertEqual(fns["inner::T::get"].mode, "exec")
        self.assertEqual(vs.broadcast_groups(src), [("", "g")])
        self.assertEqual([s for s, it in vs.mod_decls(src)], [["a"], ["tests"]])
        self.assertEqual([it.name for it in vs.outside_verus_items(src)], ["outside"])
        self.assertIn("assume_specification", [it.kind for it in src.walk()])

    def test_crate_files_and_resolution(self):
        files = V.crate_files(FX / "chain/tmod/src/lib.rs")
        self.assertEqual([(f.name, m, t) for f, m, t in files],
                         [("lib.rs", "", False), ("sub.rs", "sub", False),
                          ("tests.rs", "tests", True)])
        with tempfile.TemporaryDirectory(dir=common.scratch_root()) as d:
            run = V.Run(Path(d))
            plan = V.resolve(FX / "chain/tmod", run)
            self.assertEqual([c.name for c in plan.crate.chain()], ["tla", "tlb"])
            plan = V.resolve(FX / "chain/tmod/src/exit.rs", run)
            self.assertEqual((plan.crate.name, plan.standalone), ("tmod_exit", True))
            self.assertEqual([c.name for c in plan.crate.chain()], ["tla", "tlb"])
            plan = V.resolve(FX / "chain/tmod/src/sub.rs", run)
            self.assertEqual((plan.crate.name, plan.crate.root.name), ("tmod", "lib.rs"))
            plan = V.resolve(FX / "specimens/Q04/P9v.rs.specimen", run)
            self.assertEqual((plan.crate.name, plan.layer, plan.crate.root.name),
                             ("p9v", "L3", "P9v.rs"))
            self.assertEqual(run.orig(str(plan.crate.root)),
                             str(FX / "specimens/Q04/P9v.rs.specimen"))
            for bad in (FX / "nosuch.rs", FX / "README.md", FX / "lint"):
                with self.assertRaises(V.Refused):
                    V.resolve(bad, run)

    def test_given_layer_chain(self):
        # A specimen under specimens/<ID>/ and a standalone file with a layer get
        # the given crates that exist under GIVEN_ROOT (verus/given/; here the
        # checker's armed tree, which holds L1-L3).
        given = ROOT / "tests/course_map/armed/tree/verus/given"
        with mock.patch.object(V, "GIVEN_ROOT", given), \
                tempfile.TemporaryDirectory(dir=common.scratch_root()) as d:
            run = V.Run(Path(d))
            plan = V.resolve(FX / "specimens/Q04/P9v.rs.specimen", run)
            self.assertEqual([c.name for c in plan.crate.chain()],
                             ["qg_bignat_l1", "qg_bignat_l2", "qg_bignat_l3"])
            plan = V.resolve(FX / "clean.rs", run, layer="L2")
            self.assertEqual([c.name for c in plan.crate.chain()],
                             ["qg_bignat_l1", "qg_bignat_l2"])
            plan = V.resolve(FX / "clean.rs", run, layer="L7")   # L4-L7 do not exist there
            self.assertEqual(len(plan.crate.chain()), 3)
        with tempfile.TemporaryDirectory(dir=common.scratch_root()) as d:
            run = V.Run(Path(d))
            with mock.patch.object(V, "GIVEN_ROOT", Path(d) / "none"):
                plan = V.resolve(FX / "specimens/Q04/P9v.rs.specimen", run)
            self.assertEqual(plan.crate.chain(), [])

    def test_layer_chain_follows_the_targets_course_root(self):
        # No GIVEN_ROOT override: a throwaway course root (MODULES.toml plus the
        # armed tree's L1-L3 crates) gives its own specimens and probes their
        # chain; the scripts' checkout (no verus/given/ yet) gives none.
        import shutil
        with tempfile.TemporaryDirectory(dir=common.scratch_root()) as d:
            croot = Path(d) / "course"
            shutil.copytree(ROOT / "tests/course_map/armed/tree/verus", croot / "verus")
            (croot / "MODULES.toml").write_text((ROOT / "MODULES.toml").read_text())
            spec = croot / "specimens/Q04/P9v.rs.specimen"
            spec.parent.mkdir(parents=True)
            shutil.copyfile(FX / "specimens/Q04/P9v.rs.specimen", spec)
            probe = croot / "instructor/scratch/probe.rs"
            probe.parent.mkdir(parents=True)
            shutil.copyfile(FX / "clean.rs", probe)
            outside = Path(d) / "probe.rs"                 # in no course tree
            shutil.copyfile(FX / "clean.rs", outside)
            self.assertIsNone(V.GIVEN_ROOT)
            self.assertEqual(V.course_root(probe), croot.resolve())
            self.assertIsNone(V.course_root(outside))
            self.assertEqual(V.root_for(outside), V.REPO)
            self.assertEqual(V.root_for(outside, croot), croot.resolve())
            run = V.Run(Path(d) / "run")
            run.dir.mkdir()
            names = lambda plan: [c.name for c in plan.crate.chain()]  # noqa: E731
            self.assertEqual(names(V.resolve(spec, run)),
                             ["qg_bignat_l1", "qg_bignat_l2", "qg_bignat_l3"])
            self.assertEqual(names(V.resolve(probe, run, layer="L2")),
                             ["qg_bignat_l1", "qg_bignat_l2"])
            # a probe outside the tree takes the chain of the root the caller names
            self.assertEqual(names(V.resolve(outside, run, layer="L2", root=croot)),
                             ["qg_bignat_l1", "qg_bignat_l2"])
            self.assertEqual(V.given_crates(croot),
                             [croot.resolve() / "verus/given" / f"qg_bignat_l{k}"
                              for k in (1, 2, 3)])
            # the scripts' checkout ships no given crate yet (DV2 writes them)
            if not (V.REPO / "verus/given/qg_bignat_l1/Cargo.toml").is_file():
                self.assertEqual(names(V.resolve(FX / "specimens/Q04/P9v.rs.specimen", run)),
                                 [])

    def test_trust_allowlist_follows_the_course_root(self):
        # The default allowlist is <course root>/expected/verus_trust.toml and its
        # paths are relative to that root (each entry carries its absolute path).
        import shutil
        with tempfile.TemporaryDirectory(dir=common.scratch_root()) as d:
            croot = Path(d).resolve()
            shutil.copytree(ROOT / "tests/course_map/armed/tree/verus", croot / "verus")
            (croot / "MODULES.toml").write_text("")
            self.assertEqual(V.load_trust(root=croot), [])          # absent: empty
            (croot / "expected").mkdir()
            lib = "verus/given/qg_bignat_l1/src/lib.rs"
            (croot / lib).write_text("use vstd::prelude::*;\n\nverus! {\n\n"
                                     "pub proof fn lemma_trusted()\n    ensures true,\n{\n"
                                     "    assume(false);\n}\n\n} // verus!\n")
            (croot / "expected/verus_trust.toml").write_text(
                f'[[trust]]\npath = "{lib}"\nsymbol = "nosuch"\nkind = "assume"\n'
                'reason = "test"\n')
            with self.assertRaises(V.TrustError) as cm:
                V.load_trust(root=croot)
            self.assertIn("symbol names no fn", cm.exception.problems[0][1])
            self.assertEqual(V._trust_symbols(lib, croot), {"lemma_trusted"})
            sym = "lemma_trusted"
            (croot / "expected/verus_trust.toml").write_text(
                f'[[trust]]\npath = "{lib}"\nsymbol = "{sym}"\nkind = "assume"\n'
                'reason = "test"\n')
            got = V.load_trust(root=croot)
            self.assertEqual(got[0]["_abs"], str(croot / lib))
            if not (V.REPO / lib).is_file():   # not a file of the scripts' checkout
                with self.assertRaises(V.TrustError):
                    V.load_trust(croot / "expected/verus_trust.toml")

    def test_bad_manifests(self):
        with tempfile.TemporaryDirectory() as d:
            c = Path(d) / "c"
            (c / "src").mkdir(parents=True)
            (c / "src/lib.rs").write_text("")
            for extra in ('[patch.crates-io]\nvstd = { path = "x" }\n',
                          '[dependencies]\nserde = "1"\n'):
                (c / "Cargo.toml").write_text('[package]\nname = "c"\n' + extra)
                with self.assertRaises(V.Refused):
                    V.load_crate(c)


class Lint(unittest.TestCase):
    def check(self, rel, mode, **kw):
        got = by_line(V.lint([FX / rel], mode, **kw))
        self.assertEqual(got, expected_marks(FX / rel), rel)

    def test_learner(self):
        self.check("lint/learner.rs", "learner", layer="L2")
        self.check("lint/clean.rs", "learner")

    def test_reference_and_agent(self):
        found = V.lint([FX / "lint/reference.rs"], "reference")
        need = [f for f in found if f.kind == "need-missing"]
        self.assertEqual([(f.line, f.message.split(":")[0]) for f in need], [(42, "Q04.X2v")])
        self.check_without(found, "need-missing", FX / "lint/reference.rs")
        agent = by_line(V.lint([FX / "lint/reference.rs"], "agent"))
        want = expected_marks(FX / "lint/reference.rs")
        want = {k: v - {"slot-in-reference"} for k, v in want.items() if v - {"slot-in-reference"}}
        self.assertEqual(agent, want)

    def check_without(self, found, kind, path):
        self.assertEqual(by_line([f for f in found if f.kind != kind]), expected_marks(path))

    def test_layer_from_path(self):
        src = "use vstd::prelude::*;\nuse qg_bignat_l3::*;\nuse qg_bignat_l4::*;\nverus! {}\n"
        for path, want in (("/c/verus/q/q04_x/src/lib.rs", [3]),       # Q04: L3
                           ("/c/verus/q/q02_x/src/lib.rs", [2, 3]),    # Q02: L2
                           ("/c/verus/given/qg_bignat_l3/src/lib.rs", [2, 3]),
                           ("/c/specimens/Q07/P1.rs.specimen", []),   # Q07: L4
                           ("/c/elsewhere.rs", [])):
            got = [f.line for f in V.lint_source(src, path, "learner") if f.kind == "later-layer"]
            self.assertEqual(got, want, path)

    def test_reserved_and_reference_names(self):
        name = "solutions" + "_policy"
        src = (f"use vstd::prelude::*;\nmod {name};\nuse {name}::x;\nextern crate Solutions_First;\n"
               "verus! { pub fn f() { let solutions_policy_note = 1; } }\n")
        got = [(f.line, f.kind) for f in V.lint_source(src, f"/x/{name}.rs", "reference")]
        self.assertEqual(sorted(got), [(1, "reserved-name"), (2, "reserved-name"),
                                       (3, "reserved-name"), (4, "reserved-name")])
        got = {f.kind for f in V.lint_source("use " + "solutions" + "_q04::*;\nverus! {}\n",
                                             "/x/a.rs", "learner")}
        self.assertEqual(got, {"reference-crate"})

    def test_manifest_names(self):
        name = "solutions" + "-first"
        with tempfile.TemporaryDirectory() as d:
            m = Path(d) / "Cargo.toml"
            m.write_text(f'[package]\nname = "{name}"\n\n[dependencies]\nvstd = "1"\n'
                         f'x = {{ path = "../x", package = "{name.upper()}" }}\n')
            self.assertEqual([(f.line, f.kind) for f in V.lint([m], "reference")],
                             [(2, "reserved-name"), (6, "reserved-name")])
        self.assertEqual(V.lint_manifest(FX / "chain/tmod/Cargo.toml"), [])

    def test_messages_never_quote_code(self):
        for f in V.lint([FX / "lint"], "reference", layer="L2"):
            self.assertTrue(f.message in V.RULES.values() or f.kind == "need-missing", f)

    def test_inputs(self):
        with self.assertRaises(ValueError):
            V.lint([], "learner")
        with self.assertRaises(ValueError):
            V.lint([FX / "clean.rs"], "student")
        self.assertEqual([f.kind for f in V.lint_source("verus! { fn f() { ", "/x.rs", "learner")],
                         ["parse-error"])
        crate = V.lint([FX / "chain/tmod"], "learner")          # tests.rs is test-only
        self.assertEqual(crate, [])


class Freeze(unittest.TestCase):
    def test_cosmetic_changes_keep_the_hash(self):
        base = V.spec_hash(FX / "freeze/base.rs")
        cos = V.spec_hash(FX / "freeze/cosmetic.rs")
        self.assertEqual(sorted(base), ["Pair", "lemma_gone", "lemma_total", "sum", "total"])
        self.assertEqual({k: cos[k] for k in base}, base)
        self.assertEqual(V.freeze_check(FX / "freeze/base.rs", FX / "freeze/cosmetic.rs"), [])
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{64}", h) for h in base.values()))

    def test_changes_are_found(self):
        found = V.freeze_check(V.spec_hash(FX / "freeze/base.rs"), FX / "freeze/changed.rs")
        self.assertEqual([(f.kind, f.line, f.message.split()[-5] if f.kind == "freeze-changed"
                           else f.message.split()[2]) for f in found],
                         [("freeze-missing", 0, "lemma_gone"), ("freeze-changed", 15, "lemma_total"),
                          ("freeze-changed", 23, "sum"), ("freeze-changed", 11, "total")])

    def test_symbols_mapping_files_and_crates(self):
        base = V.spec_hash(FX / "freeze/base.rs", symbols=["sum", "nosuch"])
        self.assertEqual(list(base), ["sum"])
        with tempfile.TemporaryDirectory() as d:
            js = Path(d) / "frozen.json"
            js.write_text(json.dumps(base))
            self.assertEqual(V.freeze_check(js, FX / "freeze/cosmetic.rs"), [])
        self.assertEqual([f.kind for f in V.freeze_check({}, FX / "freeze/base.rs")],
                         ["freeze-empty"])
        crate = V.spec_hash(FX / "chain/tmod")
        self.assertEqual(sorted(crate), ["add_two", "eight", "sub::six"])

    def test_external_body_and_levers_are_not_statements(self):
        a = "verus! {\npub fn f(x: u64) -> (r: u64)\n    ensures r == x,\n{ x }\n}\n"
        b = ("verus! {\n#[verifier::external_body]\n#[verifier::rlimit(4)]\npub fn f(x: u64) "
             "-> (r: u64) ensures r == x { unimplemented!() }\n}\n")
        c = "verus! {\n#[verifier::opaque]\npub fn f(x: u64) -> (r: u64)\n    ensures r == x,\n{ x }\n}\n"
        h = [vs.statements(vs.parse(s))[0][1] for s in (a, b, c)]
        self.assertEqual(h[0], h[1])
        self.assertNotEqual(h[0], h[2])


class Args(unittest.TestCase):
    def test_policy(self):
        ok = (["--expand-errors"], ["--multiple-errors", "0"], ["--rlimit", "2"], ["--rlimit=2.0"],
              ["--smt-option", "smt.random_seed=3"], ["--triggers-mode", "selective"])
        for a in ok:
            self.assertEqual(V.check_args(a), [], a)
        for a in (["--no-verify"], ["--no-lifetime"], ["--no-erasure-check"],
                  ["-V", "no-solver-version-check"], ["-Vallow-inline-air"],
                  ["--rlimit", "20"], ["--rlimit", "infinity"], ["--smt-option", "smt.arith=1"],
                  ["--smt-option", "smt.random_seed"], ["--verify-root"], ["--log", "smt"],
                  ["--num-threads", "8"], ["--cfg", "verus_only"], ["--compile"], ["foo.rs"]):
            self.assertTrue(V.check_args(a), a)
        self.assertTrue(V.check_args(["--expand-errors"], gate=True))
        self.assertEqual(V.check_args(["--smt-option", "smt.random_seed=3"], gate=True), [])
        self.assertIn("refused by the pins", V.check_args(["--no-verify"])[0])

    def test_fast_channel_args(self):
        self.assertEqual(V._fast_args("f"), ["--verify-root", "--verify-function", "f"])
        self.assertEqual(V._fast_args("a::b::f"),
                         ["--verify-only-module", "a::b", "--verify-function", "f"])
        self.assertEqual(V._fast_args("m::*::get"),
                         ["--verify-only-module", "m", "--verify-function", "*::get"])
        for bad in ("", "a::", "f x", "a-b::f"):
            with self.assertRaises(V.Refused):
                V._fast_args(bad)


class Classify(unittest.TestCase):
    """The verdict, stage and hole map on captured outputs (Δ7, Δ8, Δ12, Δ13)."""

    def test_holes_and_real_failure(self):
        r = classify("holes_nc", "holes")
        self.assertEqual((r.verdict, r.stage, r.verified_count), ("failed", "verify", None))
        self.assertEqual([(h.line, h.kind, h.label) for h in r.holes],
                         [(11, "external_body", "exec_hole"), (30, "assume", "Q04.H1v"),
                          (38, "admit", "Q04.H2v")])
        self.assertEqual([d.code for d in r.diagnostics], ["W-V04"])
        g = classify("holes_nc", "holes", gate=True)
        self.assertEqual(g.verdict, "failed")
        # the normal run does not see the holes: only --no-cheating counts them (Δ7)
        n = classify("holes_normal", "holes")
        self.assertEqual((n.holes, n.verified_count), ([], 2))

    def test_kinds(self):
        r = classify("kinds_nc", "kinds")
        self.assertEqual([h.kind for h in r.holes],
                         ["uninterp", "bodyless_spec", "axiom", "assume_specification",
                          "assume_termination", "external_body", "assume"])
        self.assertNotIn("W-V14", [d.code for d in r.diagnostics])

    def test_gate_on_clean(self):
        r = classify("clean_nc", "clean", gate=True)
        self.assertEqual((r.verdict, r.verified_count), ("verified", 2))
        r = classify("clean_nc", "clean", gate=True, min_verified=5)
        self.assertEqual(r.verdict, "failed")

    def test_gate_needs_every_key(self):
        out, err, rc = captured("clean_nc")
        doc = json.loads(out)
        for key in ("success", "is-verifying-entire-crate", "encountered-vir-error", "verified"):
            d = json.loads(out)
            del d["verification-results"][key]
            run = V.Run(FX, "clean")
            r = V._classify(run, V.Job("t", [], rc, json.dumps(d), err, FX), "clean", True, None,
                            [], None)
            self.assertEqual(r.verdict, "failed", key)
            self.assertIn(f"lacks '{key}'", r.diagnostics[-1].message)
        self.assertTrue(doc["verification-results"]["success"])

    def test_stages_and_rlimit(self):
        for name, crate, verdict, stage in (("parse_nc", "stages_parse", "failed", "parse"),
                                            ("type_nc", "stages_type", "failed", "resolve"),
                                            ("vir_nc", "stages_vir", "failed", "resolve"),
                                            ("rlimit_nc", "rlimit", "inconclusive", "verify")):
            r = classify(name, crate)
            self.assertEqual((r.verdict, r.stage), (verdict, stage), name)

    def test_a_build_failure_after_verification_is_compile_or_link(self):
        """--compile runs whose verification found nothing (verified > 0, errors 0, no VIR
        error) and that still fail: the native linker's message is stage link, any other
        rustc error stage compile; the same outputs from a run without --compile, an error
        count, or a front-end error code keep their old stages."""
        doc = {"verification-results": {"encountered-error": True, "encountered-vir-error": False,
                                        "success": False, "verified": 1, "errors": 0,
                                        "is-verifying-entire-crate": True}}

        def diag(message, code=None):
            return json.dumps({"$message_type": "diagnostic", "message": message,
                               "code": {"code": code, "explanation": None} if code else None,
                               "level": "error", "spans": [], "children": [],
                               "rendered": f"error: {message}\n"})

        link = diag("linking with `cc` failed: exit status: 1")
        lint = diag("literal out of range for `u8`", "overflowing_literals")
        typed = diag("mismatched types", "E0308")
        run = V.Run(FX, "x")
        compiling = ["verus", "x.rs", "--compile", "--test"]
        for argv, d, err, want in ((compiling, doc, link, "link"),
                                   (compiling, doc, lint, "compile"),
                                   (compiling, doc, typed, "resolve"),
                                   (["verus", "x.rs"], doc, lint, "verify")):
            with self.subTest(want=want, argv=argv):
                r = V._classify(run, V.Job("t", argv, 1, json.dumps(d), err, FX), "x", False,
                                None, [], None)
                self.assertEqual((r.verdict, r.stage), ("failed", want))
        failed = json.loads(json.dumps(doc))
        failed["verification-results"]["errors"] = 1
        r = V._classify(run, V.Job("t", compiling, 1, json.dumps(failed), link, FX), "x",
                        False, None, [], None)
        self.assertEqual(r.stage, "verify")
        self.assertIn("link", common.STAGES)

    def test_kills_and_exit_codes(self):
        run = V.Run(FX, "x")
        for rc, verdict, stage in ((137, "killed(memory)", "verify"),
                                   (143, "killed(memory)", "verify"),
                                   (common.WALL_CLOCK_EXIT, "inconclusive", "verify"),
                                   (255, "error", "cli"), (134, "error", "cli"), (7, "error", "cli")):
            r = V._classify(run, V.Job("t", [], rc, "", "", FX), "x", True, None, [], None)
            self.assertEqual((r.verdict, r.stage), (verdict, stage), rc)

    def test_rlimit_counts(self):
        out, _, _ = captured("clean_nc")
        counts = V.rlimit_counts(out)
        self.assertEqual(sorted(counts), ["clean::add_one", "clean::lemma_double"])
        self.assertTrue(all(isinstance(v, int) and v > 0 for v in counts.values()))
        self.assertEqual(V.rlimit_counts(captured("holes_nc")[0]), {})   # a hole: no breakdown

    def test_proof_notes(self):
        self.assertEqual(V.proof_notes(captured("holes_nc")[0]), (set(), {"Q04.H1v"}))
        self.assertEqual(V.proof_notes(captured("holes_normal")[0]), (set(), set()))

    def test_normalize(self):
        out, err, _ = captured("holes_nc")
        norm = V.normalize_output(out, err)
        self.assertNotIn("times-ms", norm["json"])
        self.assertNotIn("verus", norm["json"])
        self.assertEqual(list(norm["json"]), sorted(norm["json"]))
        self.assertEqual(len(norm["diagnostics"]), 4)
        self.assertEqual({d["file"] for d in norm["diagnostics"]}, {"holes.rs"})


class EmptyBodyRewrites(unittest.TestCase):
    def variant(self, rel, name, mode, groups=()):
        text = (FX / rel).read_text()
        src = vs.parse(text)
        return V.eb_variant(text, src, vs.find_fn(src, name), mode, groups)

    def test_proof_modes(self):
        e0 = self.variant("eb.rs", "lemma_tri_closed", "E0")
        it = vs.find_fn(vs.parse(e0), "lemma_tri_closed")
        self.assertEqual(e0.count("nonlinear_arith"), 0)
        self.assertIsNotNone(it.body)
        nl = self.variant("eb.rs", "lemma_tri_closed", "NL")
        self.assertIn("assert((2 * tri(n) == n * (n + 1))) by (nonlinear_arith);", nl)
        e1 = self.variant("eb.rs", "lemma_tri_closed", "E1", V.SEQ_GROUPS)
        self.assertIn("broadcast use " + ", ".join(V.SEQ_GROUPS) + ";", e1)
        self.assertIsNone(self.variant("eb.rs", "lemma_tri_closed", "INV"))
        self.assertIsNone(self.variant("eb.rs", "lemma_tri_closed", "TRIV"))

    def test_exec_modes(self):
        e0 = self.variant("eb_exec.rs", "count_up", "E0")
        inv = self.variant("eb_exec.rs", "count_up", "INV")
        triv = self.variant("eb_exec.rs", "count_up", "TRIV")
        for v in (e0, inv):
            self.assertNotIn("invariant", v)
            self.assertIn("decreases n - i", v)
            self.assertIn("i = i + 1;", v)
        self.assertNotIn("assert(i == n);", e0)
        self.assertIn("assert(i == n);", inv)
        self.assertIn("{\n    0\n}", triv)
        self.assertIsNone(self.variant("eb_exec.rs", "count_up", "NL"))

    def test_levers_stripped(self):
        text = ("verus! {\n#[verifier::external_body]\n#[verifier::rlimit(4)]\n"
                "pub fn f(x: u64) -> (r: u64)\n    ensures r == x,\n{\n    unimplemented!()\n}\n}\n")
        src = vs.parse(text)
        v = V.eb_variant(text, src, vs.find_fn(src, "f"), "TRIV")
        self.assertNotIn("external_body", v)
        self.assertNotIn("rlimit", v)

    def test_triv_body_for_a_structure_return(self):
        text = ("verus! {\npub struct B { pub v: Vec<u64> }\n#[verifier::external_body]\n"
                "pub fn mk(x: u64) -> (r: B)\n    ensures r.v@.len() == 1,\n{\n"
                "    unimplemented!()\n}\n}\n")
        src = vs.parse(text)
        it = vs.find_fn(src, "mk")
        self.assertIsNone(V.eb_variant(text, src, it, "TRIV"))     # no default for a struct
        v = V.eb_variant(text, src, it, "TRIV", triv_body="{ B { v: Vec::new() } }")
        self.assertIn("{ B { v: Vec::new() } }", v)
        self.assertNotIn("unimplemented", v)

    def test_proof_blocks_after_block_like_statements(self):
        """QPLAN §6 Q9: a `proof { }` block that directly follows an if/else
        (or a match) is a statement of its own, so E0 strips it with the ghost
        lets it uses, and INV keeps both (only the invariant goes)."""
        text = ("verus! {\npub fn f(a: &Vec<u64>, x: u64) -> (r: u64)\n    ensures r >= x,\n{\n"
                "    let mut carry: u64 = x;\n    let ghost mut c: Seq<nat> = seq![x as nat];\n"
                "    let mut i: usize = 0;\n    while i < a.len()\n        invariant\n"
                "            c.len() > 0,\n        decreases a.len() - i,\n    {\n"
                "        if a[i] <= 5 {\n            carry = 0;\n        } else if a[i] == 7 {\n"
                "            carry = 2;\n        } else {\n            carry = 1;\n        }\n"
                "        proof {\n            c = c.push(carry as nat);\n        }\n"
                "        match carry { 0 => { i = i + 1; } _ => { i = i + 1; } }\n"
                "        proof { c = c.push(0); }\n    }\n    if carry != 0 {\n"
                "        carry = 0;\n    }\n    proof {\n        lemma_x(c);\n    }\n    x\n}\n}\n")
        src = vs.parse(text)
        e0 = V.eb_variant(text, src, vs.find_fn(src, "f"), "E0")
        for gone in ("proof", "ghost", "c.push", "lemma_x", "invariant"):
            self.assertNotIn(gone, e0)
        for kept in ("} else {\n            carry = 1;\n        }", "match carry",
                     "decreases a.len() - i", "if carry != 0", "    x\n}"):
            self.assertIn(kept, e0)
        inv = V.eb_variant(text, src, vs.find_fn(src, "f"), "INV")
        self.assertNotIn("invariant", inv)
        self.assertEqual(inv.count("proof {"), 3)
        self.assertIn("lemma_x(c);", inv)

    def test_region_mode(self):
        """QPLAN §6 Q18: RGN blanks the item's learner regions of a twin and keeps
        everything else; it applies only with an item id that owns a region."""
        text = (FX / "eb_regions.rs").read_text()
        src = vs.parse(text)
        it = vs.find_fn(src, "count_to")
        v = V.eb_variant(text, src, it, "RGN", item_id="Q09.H4v")
        self.assertNotIn("i <= n,", v)
        for kept in ("r == i,", "decreases n - i,", "// @hole-begin Q09.H4v", "// @hole-end Q09.H4v",
                     "assert(n + n == 2 * n);"):
            self.assertIn(kept, v)
        self.assertEqual(v.count("\n"), text.count("\n"))     # locations still match the twin
        self.assertIsNone(V.eb_variant(text, src, it, "RGN"))                     # no item id
        self.assertIsNone(V.eb_variant(text, src, it, "RGN", item_id="Q09.H7v"))  # no region
        lem = V.eb_variant(text, src, vs.find_fn(src, "lemma_double"), "RGN", item_id="Q09.H5v")
        self.assertNotIn("assert(n + n == 2 * n);", lem)
        self.assertIn("i <= n,", lem)
        self.assertIn("RGN", V.EB_MODES)
        self.assertNotIn("RGN", V.EB_PROOF + V.EB_EXEC)        # never a default mode

    def test_region_mode_drops_a_dangling_clause_keyword(self):
        """DV3a follow-up (Δ137 Open): a region that holds a whole clause list
        must not leave its keyword dangling (the variant would not parse);
        a keyword whose list keeps a given clause stays."""
        text = (FX / "eb_regions.rs").read_text()
        src = vs.parse(text)
        v = V.eb_variant(text, src, vs.find_fn(src, "walk_to"), "RGN", item_id="Q09.H6v")
        vsrc = vs.parse(v)                                      # it parses
        walk = vs.find_fn(vsrc, "walk_to")
        body = v[vsrc.toks[walk.body[0]].start:vsrc.toks[walk.body[1]].end]
        self.assertNotIn("invariant", body)
        self.assertIn("decreases m - k,", body)
        self.assertEqual(v.count("\n"), text.count("\n"))     # locations still match the twin
        lines = v.split("\n")
        k = text.split("\n").index("            // @hole-begin Q09.H6v")
        self.assertEqual(lines[k - 1].strip(), "")              # the keyword's line, now blank
        self.assertEqual(lines[k - 2].strip(), "while k < m")
        # count_to's list keeps `r == i,`: its keyword stays (H4v's variant)
        v4 = V.eb_variant(text, src, vs.find_fn(src, "count_to"), "RGN", item_id="Q09.H4v")
        self.assertEqual(v4.count("invariant"), text.count("invariant"))
        # the header lists too, one region after another and a keyword on its own line
        hdr = ("verus! {\n// item: Q09.H8v S3\npub fn f(x: u64) -> (r: u64)\n    requires\n"
               "        // @hole-begin Q09.H8v\n        x < 10,\n        // @hole-end Q09.H8v\n"
               "        // @hole-begin Q09.H8v\n        x > 1,\n        // @hole-end Q09.H8v\n"
               "    ensures\n        // @hole-begin Q09.H8v\n        r == x,\n"
               "        // @hole-end Q09.H8v\n{\n    x\n}\n} // verus!\n")
        hsrc = vs.parse(hdr)
        hv = V.eb_variant(hdr, hsrc, vs.find_fn(hsrc, "f"), "RGN", item_id="Q09.H8v")
        hf = vs.find_fn(vs.parse(hv), "f")
        self.assertEqual(hf.clauses, [])
        self.assertNotIn("requires", hv)
        self.assertNotIn("ensures", hv)
        self.assertEqual(hv.count("\n"), hdr.count("\n"))
        self.assertEqual(V.rgn_drop_dangling(hdr, "Q09.H9v"), hdr)   # no region: unchanged

    def test_mode_wall_clocks(self):
        """BV runs under its own short wall clock (pins.toml eb_mode_timeout_s);
        the other modes under the course net; a caller may only shorten."""
        p = V.pins()
        self.assertEqual(p["eb_mode_timeout_s"], {"BV": 120})
        self.assertEqual(V.eb_timeout("BV", None, p), 120)
        self.assertEqual(V.eb_timeout("E0", None, p), None)
        self.assertEqual(V.eb_timeout("BV", 60, p), 60)
        self.assertEqual(V.eb_timeout("BV", 600, p), 120)
        self.assertEqual(V.eb_timeout("NL", 600, p), 600)


class Trust(unittest.TestCase):
    """load_trust's validation, check_trust and audit on a bad allowlist: no
    tool runs (a bad allowlist stops before any job; no given crate, no job)."""

    TDEP = "tests/wrappers/fixtures/verus/trusted/tdep/src/lib.rs"
    ROOTS = ("tests/wrappers/fixtures/verus/trusted/",)

    def write(self, d, text):
        p = Path(d) / "trust.toml"
        p.write_text(text)
        return p

    def entry(self, path=TDEP, symbol="copy_small", kind="external_body", reason="test",
              extra=""):
        out = "[[trust]]\n"
        for k, v in (("path", path), ("symbol", symbol), ("kind", kind), ("reason", reason)):
            if v is not None:
                out += f'{k} = "{v}"\n'
        return out + extra + "\n"

    def problems(self, text, roots=None):
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(V, "TRUST_ROOTS", roots or V.TRUST_ROOTS):
            with self.assertRaises(V.TrustError) as cm:
                V.load_trust(self.write(d, text))
        return cm.exception.problems

    def test_valid_and_empty(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(V, "TRUST_ROOTS", self.ROOTS):
            got = V.load_trust(self.write(d, self.entry() + self.entry(symbol="lemma_assumed",
                                                                      kind="assume")))
            self.assertEqual([(e["symbol"], e["kind"]) for e in got],
                             [("copy_small", "external_body"), ("lemma_assumed", "assume")])
            self.assertEqual(V.load_trust(self.write(d, "# nothing trusted\n")), [])

    def test_every_problem_is_reported_with_its_line(self):
        text = (self.entry()                                                   # line 1
                + self.entry(path="verus/given/qg_bignat_l9/src/lib.rs")       # line 7
                + self.entry(path="../outside.rs")                             # line 13
                + self.entry(kind="external-body")                             # line 19
                + self.entry(reason=None)                                      # line 25
                + self.entry(symbol="lemma_trusted", extra='sybmol = "x"\n')  # line 30
                + self.entry(symbol="nosuch"))                                 # line 37
        # the default roots (verus/given/ only): a fixture path lies outside them
        got = defaultdict(list)
        for ln, m in self.problems(text):
            got[ln].append(m)
        self.assertEqual(sorted(got), [1, 7, 13, 19, 25, 30, 37])
        self.assertTrue(all("outside verus/given/" in got[ln][-1] for ln in (1, 19, 30, 37)))
        self.assertIn("names no file", got[7][0])
        self.assertIn("repo-relative", got[13][0])
        self.assertIn("is not a hole kind", got[19][0])
        self.assertEqual(len(got[25]), 1)
        self.assertIn("lacks reason", got[25][0])
        self.assertIn("unknown key(s) sybmol", got[30][0])
        # with the fixture root allowed, only the real faults remain
        got = self.problems(text, self.ROOTS)
        self.assertEqual([ln for ln, _ in got], [7, 13, 19, 25, 30, 37])
        self.assertIn("outside", got[0][1])        # verus/given/ is no longer a root
        self.assertIn("symbol names no fn", got[-1][1])

    def test_file_level_problems(self):
        self.assertEqual([ln for ln, _ in self.problems("[[trust]\n")], [1])
        got = self.problems('version = 1\n' + self.entry(), self.ROOTS)
        self.assertEqual(got, [(0, "unknown top-level key 'version' (only [[trust]] tables)")])
        got = self.problems(self.entry() + self.entry(reason="again"), self.ROOTS)
        self.assertEqual(got, [(7, "entry 2 repeats entry 1")])

    def test_bad_allowlist_runs_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            bad = self.write(d, self.entry(path="verus/given/qg_bignat_l9/src/lib.rs"))
            for found in (V.audit(FX / "clean.rs", allowlist=bad), V.check_trust(bad)):
                self.assertEqual([(f.file, f.line, f.kind) for f in found],
                                 [(str(bad), 1, "bad-trust-entry")])

    def test_check_trust_without_given_crates(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(V, "TRUST_ROOTS", self.ROOTS), \
                mock.patch.object(V, "GIVEN_ROOT", Path(d) / "given"):
            self.assertEqual(V.check_trust(self.write(d, "")), [])
            found = V.check_trust(self.write(d, self.entry()))
        # nothing audits the entry's file: a waiver that matches nothing is an error
        self.assertEqual([(f.file, f.line, f.kind) for f in found],
                         [(str(ROOT / self.TDEP), 0, "stale-trust-entry")])

    def test_dedup(self):
        F = common.Finding
        got = V._dedup([F("b", 2, "hole-assume", "x"), F("a", 9, "hole-external-body", "y"),
                        F("a", 9, "hole-external-body", "y"), F("a", 9, "stale-trust-entry", "z")])
        self.assertEqual([(f.file, f.line, f.kind) for f in got],
                         [("a", 9, "hole-external-body"), ("a", 9, "stale-trust-entry"),
                          ("b", 2, "hole-assume")])


class TestDepsStatic(unittest.TestCase):
    """D98 (Δ316): the pinned compiled-test dependency and the test-todo hole kind
    (no tool runs)."""

    def test_the_pin_and_its_manifest_agree(self):
        import tomllib
        allowed = V.test_dep_pins()
        self.assertEqual(allowed, {"regex": "=1.13.1"})
        man = ROOT / V.pins()["test_deps"]["manifest"]
        meta = tomllib.loads(man.read_text())
        self.assertEqual(meta["dependencies"], allowed)
        lock = tomllib.loads((man.parent / "Cargo.lock").read_text())
        vers = {pk["name"]: pk["version"] for pk in lock["package"]}
        self.assertEqual(vers["regex"], allowed["regex"].lstrip("="))
        self.assertFalse((man.parent / "target").exists())

    def test_load_crate_reads_and_refuses_dev_dependencies(self):
        c = V.load_crate(FX / "testdeps_crate")
        self.assertEqual(c.dev_deps, {"regex": "=1.13.1"})
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "src").mkdir()
            (Path(d) / "src/lib.rs").write_text("")
            for dev in ('regex = "1"', 'regex = "=1.12.0"', 'serde = "=1.0.0"',
                        'regex = { version = "=1.13.1" }'):
                (Path(d) / "Cargo.toml").write_text(
                    f'[package]\nname = "x"\nversion = "0.1.0"\n[dev-dependencies]\n{dev}\n')
                with self.subTest(dev=dev), self.assertRaises(V.Refused) as e:
                    V.load_crate(d)
                self.assertIn("pinned test dependencies", str(e.exception))

    def test_r15_crate_declares_the_pin(self):
        self.assertEqual(V.load_crate(ROOT / "verus/r/r15_verifier_loop").dev_deps,
                         {"regex": "=1.13.1"})

    def test_test_todos(self):
        text = (
            'use vstd::prelude::*;\n'
            'verus! {\n'
            'pub fn f() { todo!("NOT.A") }\n'
            '}\n'
            'fn plain() { todo!("NOT.B") }\n'
            '#[cfg(test)]\n'
            'mod tests {\n'
            '    fn h() -> u8 { todo!("R15.H2v") }\n'
            '    fn bare() { todo!() }\n'
            '    mod deeper { fn g() { todo!("R15.H3v") } }\n'
            '}\n'
            '#[test]\n'
            'fn t() { let _ = todo!("X.T1v"); }\n')
        self.assertEqual(V.test_todos(text), [(8, "R15.H2v"), (9, ""), (10, "R15.H3v"),
                                              (13, "X.T1v")])
        self.assertEqual(V.test_todos('fn h() { todo!("Y") }\n', test_only=True), [(1, "Y")])
        self.assertEqual(V.test_todos('#[cfg(test)]\nmod t { fn h() { unimplemented!() } }\n'),
                         [])


class Scratch(unittest.TestCase):
    """_discard keeps a run's job logs only, and only inside the scratch root."""

    def tree(self, d):
        d = Path(d)
        for rel in ("01-dep-x/cmd.txt", "01-dep-x/stdout.txt", "01-dep-x/stderr.txt",
                    "01-dep-x/exit.txt", "01-dep-x/rustc-tmp/x.o", "02-target/stdout.txt",
                    "src/P9v.rs", "deps/x.vir", "deps/libx.rlib", "variant-E0/lib.rs",
                    "testbin", "rustcAbc/t"):
            (d / rel).parent.mkdir(parents=True, exist_ok=True)
            (d / rel).write_text("x")
        return sorted(p.relative_to(d).as_posix() for p in d.rglob("*") if p.is_file())

    def test_discard(self):
        with tempfile.TemporaryDirectory(dir=common.scratch_root()) as d:
            self.tree(d)
            V._discard(V.Run(Path(d)))
            self.assertEqual(sorted(p.relative_to(d).as_posix() for p in Path(d).rglob("*")
                                    if p.is_file()),
                             ["01-dep-x/cmd.txt", "01-dep-x/exit.txt", "01-dep-x/stderr.txt",
                              "01-dep-x/stdout.txt", "02-target/stdout.txt"])
        with tempfile.TemporaryDirectory(dir=common.scratch_root()) as d:
            run = V.Run(Path(d) / "never-ran")
            run.dir.mkdir()
            V._discard(run)
            self.assertFalse(run.dir.exists())

    def test_never_outside_the_scratch_root(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(Path(d).resolve().is_relative_to(common.scratch_root().resolve()))
            before = self.tree(d)
            V._discard(V.Run(Path(d)))
            self.assertEqual(sorted(p.relative_to(d).as_posix() for p in Path(d).rglob("*")
                                    if p.is_file()), before)


if __name__ == "__main__":
    unittest.main()
