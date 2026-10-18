#!/usr/bin/env python3
"""Tool-free tests of skill_sims.py: its leak-pattern selection (Δ130, QPLAN §6
Q15), its case checks' parsers and its learner-state phase, on synthetic inputs,
and its plants against the shipped learner files.

No model is called, no clone is made, and no reference file is opened: the
patterns, records, prompts, twins and bank blocks below are invented for these
tests and match no course answer. The real leak patterns are never read here.
The plant test reads only the shipped learner files (learner-visible).

    python3 -B -m unittest discover -s tests/instructor/simulations -p 'test_*.py'
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("skill_sims", HERE / "skill_sims.py")
sims = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sims)

RECORDS = {
    "Q01": {"id": "Q01", "track": "Q", "tier": "survey"},
    "Q02": {"id": "Q02", "track": "Q", "tier": "intro"},
    "Q03": {"id": "Q03", "track": "Q", "tier": "intro"},
    "Q04": {"id": "Q04", "track": "Q", "tier": "moderate"},
    "Q07": {"id": "Q07", "track": "Q", "tier": "detailed"},
    "R01": {"id": "R01", "track": "R", "tier": ""},
}


class Selection(unittest.TestCase):
    def setUp(self):
        base = os.environ.get("DVL_TEST_TMP") or None
        if base:
            Path(base).mkdir(parents=True, exist_ok=True)
        self.tmp = Path(tempfile.mkdtemp(prefix="dvl0-sims-test-", dir=base))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        pdir = self.tmp / "patterns"
        pdir.mkdir()
        for mid in ("Q01", "Q02", "Q04", "R01"):
            (pdir / f"{mid}.txt").write_text(
                f"# from invented/{mid}.dfy\nzork{mid}\\d+\n\n^frob{mid}$\n", encoding="utf-8")
        (pdir / "README.txt").write_text("not a pattern file\n")
        self.pats = sims.leak_patterns(pdir)

    def pids(self, pats):
        return sorted(p["pid"] for p in pats)

    def test_reading(self):
        self.assertEqual(len(self.pats), 8)
        self.assertEqual({p["mid"] for p in self.pats}, {"Q01", "Q02", "Q04", "R01"})
        self.assertIn("Q04:2", self.pids(self.pats))
        self.assertIn("Q04:4", self.pids(self.pats))
        # applied under re.MULTILINE, as the README verifier reads them
        det = {"pats": self.pats, "tokens": [], "origin": []}
        self.assertEqual(sims.scan_text(det, "a line\nfrobQ04\nanother")[0], ["Q04:4"])
        with self.assertRaises(sims.Refusal):
            sims.leak_patterns(self.tmp / "empty-dir-that-is-missing")

    def test_tier_filter(self):
        sel = lambda mids: {p["mid"] for p in sims.patterns_for_case(  # noqa: E731
            self.pats, set(mids), RECORDS)}
        self.assertEqual(sel(["Q04"]), {"Q04", "R01"})          # lower Q tiers are exempt
        self.assertEqual(sel(["Q02"]), {"Q02", "Q04", "R01"})
        self.assertEqual(sel(["Q03"]), {"Q02", "Q04", "R01"})   # same tier as Q02
        self.assertEqual(sel(["Q01"]), {"Q01", "Q02", "Q04", "R01"})
        self.assertEqual(sel(["Q07"]), {"R01"})
        self.assertEqual(sel(["Q02", "Q04"]), {"Q02", "Q04", "R01"})   # several: the union
        self.assertEqual(sel([]), {"Q01", "Q02", "Q04", "R01"})        # none named: all
        self.assertEqual(sel(["R01"]), {"Q01", "Q02", "Q04", "R01"})   # the other track: all
        # the selection is calibrate.patterns_for's, not a copy of it
        self.assertEqual(self.pids(sims.patterns_for_case(self.pats, {"Q04"}, RECORDS)),
                         self.pids(sims.CAL.patterns_for("Q04", RECORDS, self.pats)))

    def test_refusals(self):
        with self.assertRaises(sims.Refusal):
            sims.patterns_for_case(self.pats, {"Q04"},
                                   {k: v for k, v in RECORDS.items() if k != "Q01"})
        bad = dict(RECORDS, Q04={"id": "Q04", "track": "Q", "tier": "nonsense"})
        with self.assertRaises(sims.Refusal):
            sims.patterns_for_case(self.pats, {"Q04"}, bad)
        # a case the filter leaves with no pattern proves nothing: refused
        q_only = [p for p in self.pats if p["mid"] != "R01"]
        with self.assertRaises(sims.Refusal) as cm:
            sims.patterns_for_case(q_only, {"Q07"}, RECORDS)
        self.assertIn("leaves no leak pattern for Q07", str(cm.exception))

    def test_case_modules_from_prompts(self):
        work = self.tmp / "work"
        (work / "runs" / "a").mkdir(parents=True)
        (work / "runs" / "a" / "t01.prompt.txt").write_text("/tutor Q04 I am stuck on Q04.H2d\n")
        (work / "runs" / "a" / "t02.prompt.txt").write_text("what about Q02 and Q99 then?\n")
        (work / "runs" / "a" / "t01.jsonl").write_text("{}\n")
        (work / "runs" / "g").mkdir()
        (work / "runs" / "g" / "t01.prompt.txt").write_text("/review\n")
        self.assertEqual(sims.case_modules(work, "a", RECORDS), {"Q02", "Q04"})
        self.assertEqual(sims.case_modules(work, "g", RECORDS), set())
        self.assertEqual(sims.case_modules(work, "missing", RECORDS), set())

    def test_registry_records(self):
        recs = sims.registry_records()
        self.assertEqual(recs["Q04"]["tier"], "moderate")
        self.assertEqual(recs["Q01"]["track"], "Q")


class LaneScratch(unittest.TestCase):
    def test_lane_scratch_blocks_a_simulation(self):
        """DV5c fix round: author lane scratch on the host refuses the set-up."""
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            for n in ("dvl0-dv5c-q18", "dvl0-dvr2-r09", "dvl0-ci-1000", "dvl0-sandbox-job-x",
                      "dvl0-dv5c-simulations", "other"):
                (base / n).mkdir()
            work = base / "dvl0-dv5c-simulations" / "w"
            work.mkdir()
            got = sorted(Path(x).name for x in sims.lane_scratch(base, exclude=[work]))
            self.assertEqual(got, ["dvl0-dv5c-q18", "dvl0-dvr2-r09"])

    def test_the_study_root_is_no_lane_scratch(self):
        """D20: setup's lane-scratch check does not refuse a study root, its own or
        another run's (/tmp/dvl0-study-<phase>-<lane>/)."""
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            for n in ("dvl0-study-dv5e-simulations", "dvl0-study-dv5c-q18", "dvl0-dv5e-simulations"):
                (base / n).mkdir()
            work = base / "dvl0-dv5e-simulations" / "w"
            work.mkdir()
            self.assertEqual(sims.lane_scratch(base, exclude=[work]), [])

    def test_an_orphaned_study_root_blocks_a_simulation(self):
        """DV5e review: a study root left behind (its WORK removed without `cleanup`)
        is outside the tripwire, so setup refuses while one is on the host; this run's
        own study root, and the path down to it, do not count."""
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            own = base / "dvl0-study-dv5e-simulations" / "q16"
            own.mkdir(parents=True)
            (base / "dvl0-dv5e-simulations").mkdir()
            self.assertEqual(sims.stale_study_roots(own, base), [])
            (base / "dvl0-study-dv2b2-calib" / "clone").mkdir(parents=True)
            (base / "dvl0-study-dv5e-simulations" / "q15").mkdir()
            got = sorted(Path(x).name for x in sims.stale_study_roots(own, base))
            self.assertEqual(got, ["dvl0-study-dv2b2-calib", "q15"])

    def test_case_scratch_keeps_one_case(self):
        """DV5e review: each case's DVL_SCRATCH is its own directory; another case's
        wrapper runs are removed before it starts, its own kept over resumed turns."""
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            base = Path(t) / "dvl"
            a = GD.case_scratch(base, "a")
            (a / "runs").mkdir()
            (a / "runs" / "probe.dfy").write_text("// a probe\n")
            (base / "runs").mkdir()                      # a pre-D20-review layout
            self.assertEqual(GD.case_scratch(base, "a"), a)
            self.assertTrue((a / "runs" / "probe.dfy").is_file())
            self.assertEqual(sorted(x.name for x in base.iterdir()), ["a"])
            b = GD.case_scratch(base, "b")
            self.assertEqual(sorted(x.name for x in base.iterdir()), ["b"])
            self.assertEqual(list(b.iterdir()), [])
            self.assertIsNone(GD.case_scratch(base))
            self.assertEqual(list(base.iterdir()), [])

    def test_a_dropin_never_outlives_its_case(self):
        """DV5e review: a drop-in still in the clone belongs to the case whose turn met
        it first; another case's turn is refused until `plant --restore`."""
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            clone = Path(t) / "clone"
            (clone / "paper").mkdir(parents=True)
            text = "% an invented drop-in\n"
            (clone / "paper/Q01_answers.tex").write_text(text)
            plants = [dict(name="dropin:Q01-gold", file="paper/Q01_answers.tex", new=text,
                           sha256=sims.sha(text))]
            self.assertEqual(len(sims.live_dropins(clone, plants)), 1)
            work = Path(t) / "work"
            work.mkdir()
            state = {"clone": str(clone), "plants": plants, "cases": {}, "prompts": [],
                     "dvl_scratch": str(Path(t) / "dvl")}
            from unittest import mock
            with mock.patch.object(sims, "mem_available_gib", return_value=10_000):
                with mock.patch.object(sims.subprocess, "run",
                                       side_effect=RuntimeError("no session in a test")):
                    with self.assertRaises(RuntimeError):
                        sims.phase_turn(work, state, "a", "single", "hi", 10)
                    self.assertEqual(plants[0]["case"], "a")
                    with self.assertRaisesRegex(sims.Refusal, "still in the clone"):
                        sims.phase_turn(work, state, "b", "single", "hi", 10)
            (clone / "paper/Q01_answers.tex").write_text("% the shipped skeleton\n")
            self.assertEqual(sims.live_dropins(clone, plants), [])


GD = sims.GD
CAL = sims.CAL
HOOK = sims.ROOT / ".claude" / "hooks" / "spoiler-guard.sh"


def fake_checkout(at):
    """A decoy checkout (scripts/gen_hook_fixtures.py --fake-root: decoy files only)
    with a decoy instructor CORE.md, for the hook to guard."""
    import subprocess
    subprocess.run([sys.executable, str(sims.ROOT / "scripts" / "gen_hook_fixtures.py"),
                    "--fake-root", str(at)], check=True, capture_output=True)
    core = Path(at) / GD.STUDY_CORE
    core.parent.mkdir(parents=True, exist_ok=True)
    core.write_text("# decoy skill core (test_skill_sims.py); not course material\n")
    return Path(at)


class StudyRoot(unittest.TestCase):
    """D20 (the user, 2026-10-13): the clone and DVL_SCRATCH under /tmp/dvl0-study-<phase>-
    <lane>/, state and streams under the lane's scratch, in all three tools. The hook
    calls run this worktree's hook on decoy checkouts made for the test (directly under
    /tmp, since the path's shape is what is tested); no model, no clone of the course."""
    TOOLS = {"skill_sims": sims, "calibrate": CAL, "guard_doors": GD}

    def tmpdir(self, prefix):
        import tempfile
        d = Path(tempfile.mkdtemp(prefix=prefix, dir="/tmp"))
        self.addCleanup(shutil.rmtree, d, True)
        return d

    def hook(self, root, tool, tinput, cwd=None):
        return GD.run_hook(root, tool, tinput, cwd=cwd, hook=HOOK)

    def test_derivation_and_refusals(self):
        self.assertEqual(GD.study_root("/tmp/dvl0-dv5e-simulations/q16-q18"),
                         Path("/tmp/dvl0-study-dv5e-simulations/q16-q18"))
        self.assertEqual(GD.study_root("/tmp/dvl0-dv5e-studyroot"), Path("/tmp/dvl0-study-dv5e-studyroot"))
        self.assertEqual(GD.study_root("/tmp/dvl0-dv5e-x/a/../b"), Path("/tmp/dvl0-study-dv5e-x/b"))
        for bad in ("/tmp/dvl0-q04", "/tmp/dvl0-ci-1000/w", "/tmp/dvl0-study-dv5e-x/w", "/tmp",
                    "/home/x/dvl0-dv5e-x", "/tmp/claude-1000/dvl0-dv5e-x", "/tmp/dvl0-dv5e-"):
            with self.assertRaises(ValueError, msg=bad):
                GD.study_root(bad)
        for mod in self.TOOLS.values():
            with self.assertRaises(mod.Refusal):
                mod.paths_of(Path("/tmp/dvl0-q04"))

    def test_each_tools_default_paths_sit_under_the_study_root(self):
        """(3) the clone and DVL_SCRATCH under the study root, which the lane-scratch
        pattern does not match; WORK (state, streams) under the pattern."""
        for name, mod in self.TOOLS.items():
            paths = mod.paths_of(mod.DEFAULT_WORK)
            root = paths["study_root"]
            self.assertTrue(str(root).startswith("/tmp/dvl0-study-dv"), name)
            for k in ("clone", "dvl"):
                self.assertTrue(paths[k].is_relative_to(root), f"{name}: {k}")
                self.assertIsNone(GD.RX_LANE_SCRATCH.search(str(paths[k]) + "/"), f"{name}: {k}")
                self.assertFalse(paths[k].is_relative_to(paths["work"]), f"{name}: {k}")
            self.assertIsNotNone(GD.RX_LANE_SCRATCH.search(str(paths["work"]) + "/"), name)
            self.assertEqual(paths["work"], Path(mod.DEFAULT_WORK))

    def test_the_mirrored_pattern_is_the_hooks(self):
        """GD.RX_LANE_SCRATCH is RX_SPOIL_DIR's lane-scratch alternative in the hook."""
        src = HOOK.read_text(encoding="utf-8")
        line = next(x for x in src.splitlines() if x.startswith("RX_SPOIL_DIR="))
        self.assertIn("|/tmp/dvl0-dv[0-9a-z]+-[^/]+)(/|\\$)", line)
        self.assertEqual(GD.RX_LANE_SCRATCH.pattern, r"/tmp/dvl0-dv[0-9a-z]+-[^/]+(/|$)")

    def test_the_hook_passes_a_study_clone_and_refuses_a_lane(self):
        """(1) a Read of <study clone>/.claude/skills/instructor/CORE.md and a Bash call
        whose cwd is the study clone pass; (2) a path under /tmp/dvl0-dv5e-<lane>/ is
        still refused (rule 1), from the study clone and as a checkout of its own."""
        sroot = self.tmpdir("dvl0-study-dvtest-")
        clone = fake_checkout(sroot / "clone")
        code, err = self.hook(clone, "Read", {"file_path": str(clone / GD.STUDY_CORE)})
        self.assertEqual(code, 0, err)
        code, err = self.hook(clone, "Bash", {"command": "ls .claude/skills/instructor"}, cwd=clone)
        self.assertEqual(code, 0, err)
        code, err = self.hook(clone, "Bash", {"command": "python3 scripts/check_course_map.py "
                                                         "--resolve Q16"}, cwd=clone)
        self.assertEqual(code, 0, err)
        for p in ("/tmp/dvl0-dv5e-studyroot/calls.log", "/tmp/dvl0-dv5e-simulations/runs/a/t01.jsonl"):
            code, err = self.hook(clone, "Read", {"file_path": p})
            self.assertEqual(code, 2, p)
            self.assertIn("(rule 1)", err)
        lane = self.tmpdir("dvl0-dv5e-simstest-")
        inside = fake_checkout(lane / "clone")
        code, err = self.hook(inside, "Read", {"file_path": str(inside / GD.STUDY_CORE)})
        self.assertEqual(code, 2, err)
        self.assertIn("(rule 1)", err)
        code, err = self.hook(inside, "Bash", {"command": "ls"}, cwd=inside)
        self.assertEqual(code, 2, err)
        self.assertIn("(rule 1)", err)
        self.assertNotIn(f"cd back to {inside}", err)     # rule 1's message fix (D20)

    def test_the_hook_on_each_tools_default_paths(self):
        """(1)-(3) on the paths each tool would use by default: from a decoy checkout,
        the default clone's CORE.md and its DVL_SCRATCH pass, the default WORK's
        calls.log is refused."""
        sroot = self.tmpdir("dvl0-study-dvtest-")
        clone = fake_checkout(sroot / "clone")
        for name, mod in self.TOOLS.items():
            paths = mod.paths_of(mod.DEFAULT_WORK)
            for p, want in ((paths["clone"] / GD.STUDY_CORE, 0), (paths["dvl"] / "runs" / "x.log", 0),
                            (paths["work"] / "calls.log", 2)):
                code, err = self.hook(clone, "Read", {"file_path": str(p)})
                self.assertEqual(code, want, f"{name}: {p}: {err}")

    def test_setups_probe(self):
        """The probe each setup runs: clean on a study clone; on a clone under WORK
        (DV5d's attempt 1) it names the refused calls."""
        lane = self.tmpdir("dvl0-dvtest-")
        work = lane / "sims"
        paths = GD.work_paths(work)
        self.addCleanup(shutil.rmtree, paths["study_root"].parent, True)
        clone = fake_checkout(paths["clone"])
        rows, problems = GD.probe_study_clone(paths, hook=HOOK)
        self.assertEqual(problems, [])
        self.assertEqual([r["exit"] for r in rows], [0, 0, 0, 2])
        old = dict(paths, clone=fake_checkout(work / "clone"), dvl=work / "dvl")
        rows, problems = GD.probe_study_clone(old, hook=HOOK)
        self.assertEqual(len(problems), 3, problems)
        self.assertTrue(clone.is_dir())

    def test_study_root_free(self):
        lane = self.tmpdir("dvl0-dvtest-")
        paths = GD.work_paths(lane / "a")
        top = paths["study_root"].parent
        self.addCleanup(shutil.rmtree, top, True)
        GD.check_study_root_free(paths["study_root"])          # absent: free
        paths["study_root"].mkdir(parents=True)
        GD.check_study_root_free(paths["study_root"])          # empty: free
        (paths["study_root"] / "left.txt").write_text("x")
        with self.assertRaises(ValueError):
            GD.check_study_root_free(paths["study_root"])
        (paths["study_root"] / "left.txt").unlink()
        (paths["study_root"] / "clone").mkdir()
        with self.assertRaises(ValueError):                    # a WORK nested in another's
            GD.check_study_root_free(GD.work_paths(lane / "a" / "b")["study_root"])

    def test_cleanup_removes_the_study_root(self):
        """Each tool's cleanup deletes the clone, DVL_SCRATCH, the study root and its
        empty parents; WORK keeps its records; a read-only cache directory is no
        obstacle. The state is synthetic (no session ran)."""
        import stat
        for name, mod in self.TOOLS.items():
            lane = self.tmpdir("dvl0-dvtest-")
            work = lane / "w"
            work.mkdir()
            (work / "calls.log").write_text("")
            paths = mod.paths_of(work)
            self.addCleanup(shutil.rmtree, paths["study_root"].parent, True)
            ro = paths["clone"] / "target" / "cache"
            ro.mkdir(parents=True)
            (ro / "f").write_text("x")
            ro.chmod(stat.S_IRUSR | stat.S_IXUSR)
            (paths["dvl"] / "runs").mkdir(parents=True)
            state = dict(clone=str(paths["clone"]), study_root=str(paths["study_root"]),
                         slug="-tmp-dvl0-study-dvtest-none", preexisting={"projects_slug": True,
                                                                           "tmp_slug": True})
            mod.phase_cleanup(work, state)
            self.assertFalse(paths["study_root"].exists(), name)
            self.assertFalse(paths["study_root"].parent.exists(), name)
            self.assertTrue((work / "calls.log").exists(), name)
            self.assertIn(str(paths["study_root"]), state["cleanup"]["deleted"], name)
        with self.assertRaises(ValueError):
            GD.remove_study_root("/tmp/dvl0-dv5e-x")
        with self.assertRaises(ValueError):
            GD.remove_study_root("/home")


class CaseChecks(unittest.TestCase):
    """The parsers behind `check hole`, `check pp` and `check viva` (DV3k)."""

    def test_twin_hole_lines_markers(self):
        twin = ("lemma Zork()\n"
                "  // @hole-begin Q77.H1d\n"
                "  ensures frob(1)\n"
                "  // @hole-end Q77.H1d\n"
                "{\n"
                "  // @hole-begin Q77.H2d\n"
                "  other();\n"
                "  // @hole-end Q77.H2d\n"
                "  // @hole-begin Q77.H1d\n"
                "  frob_more();\n"
                "  // @hole-end Q77.H1d\n"
                "}\n")
        self.assertEqual([x.strip() for x in sims.twin_hole_lines(twin, "Q77.H1d")],
                         ["ensures frob(1)", "frob_more();"])
        self.assertEqual(sims.twin_hole_lines(twin, "Q77.H9d"), [])

    def test_twin_hole_lines_python(self):
        twin = ('# item: Q77.H1py S1\n'
                'def zork(a: int,\n'
                '         b: int) -> int:\n'
                '    """Docstring line one.\n'
                '\n'
                '    More docstring.\n'
                '    """\n'
                '    c = a + b\n'
                '    return c * 2\n'
                '# triv: return 0\n'
                '\n'
                '# item: Q77.H2py S1\n'
                'def frob() -> int:\n'
                '    """One line."""\n'
                '    return 7\n')
        self.assertEqual([x.strip() for x in sims.twin_hole_lines(twin, "Q77.H1py")],
                         ["c = a + b", "return c * 2"])
        self.assertEqual([x.strip() for x in sims.twin_hole_lines(twin, "Q77.H2py")],
                         ["return 7"])

    def test_twin_hole_lines_bodyless(self):
        # a Dafny or Verus item with no markers (DV5b): the body under `// item:`
        twin = ("// item: Q77.H1d S1\n"
                "// uses: zork\n"
                "/** Doc with a brace { that is not code. */\n"
                "lemma Zork(a: nat)\n"
                "  ensures frob(a)  // a { in a comment\n"
                "{\n"
                "  if a > 0 {\n"
                "    Zork(a - 1);\n"
                "  }\n"
                "}\n"
                "\n"
                "// item: Q77.H2v S1\n"
                "#[verifier::opaque]\n"
                "pub proof fn frob_it()\n"
                "    ensures true,\n"
                "{ }\n")
        self.assertEqual([x.strip() for x in sims.twin_hole_lines(twin, "Q77.H1d")],
                         ["if a > 0 {", "Zork(a - 1);", "}"])
        self.assertEqual(sims.twin_hole_lines(twin, "Q77.H2v"), [])
        self.assertEqual(sims.twin_hole_lines(twin, "Q77.H3d"), [])

    def test_pp_block_and_notes(self):
        bank = ("## Parallel problems\n\n"
                "### PP1 — parallel to Q77.H1d (zork)\n"
                "**Isolates:** `zork`\n\n"
                "```dafny\nlemma Zork() {}\n```\n"
                "**Done =** it verifies.\n\n"
                "**Author-verified (2099-01-01, invented):** a note.\n\n"
                "**Diagnostic.** another note.\n\n"
                "### PP2 — parallel to Q77.H2d\n"
                "```rust\nfn frob() {}\n```\n")
        b1 = sims.pp_block(bank, "PP1")
        self.assertIn("lemma Zork() {}", b1)
        self.assertNotIn("frob", b1)
        labels = [sims.NOTE_RX.match(x.strip()).group(1) for x in b1.splitlines()
                  if sims.NOTE_RX.match(x.strip())]
        self.assertEqual(labels, ["Done =", "Author-verified", "Diagnostic"])
        self.assertIsNone(sims.NOTE_RX.match("**Isolates:** `zork`"))
        self.assertIn("fn frob() {}", sims.pp_block(bank, "PP2"))
        with self.assertRaises(sims.Refusal):
            sims.pp_block(bank, "PP3")

    def test_stmt_regex(self):
        rx = sims.STMT_RX
        for line in ("  method Grow(a: seq<nat>) returns (r: seq<nat>)", "    ensures |r| > 0",
                     "    requires x < 3", "  lemma Frob(n: nat)", "pub proof fn lemma_frob(n: nat)",
                     "  ghost function Zork(x: int): int", "fn plain(x: u8)"):
            self.assertTrue(rx.match(line), line)
        for line in ("    var r := Grow(a);", "    assert r == [1];", "  // ensures nothing",
                     "an ensures clause in prose"):
            self.assertFalse(rx.match(line), line)

    def test_contract_header(self):
        tmp = Path(tempfile.mkdtemp(prefix="dvl0-sims-test-", dir=os.environ.get("DVL_TEST_TMP")))
        self.addCleanup(shutil.rmtree, tmp, True)
        f = tmp / "zork.dfy"
        f.write_text("/* CONTRACT\ngoal: frob the zork, never weakened\nallowed-files:\n"
                     "  - a/zork.dfy\nacceptance:\n  - `vcheck a/zork.dfy` is green\n"
                     "  - no other file\n*/\nmodule Z {}\n", encoding="utf-8")
        old_root = sims.ROOT
        sims.ROOT = tmp
        try:
            goal, bullets = sims.contract_header("zork.dfy")
        finally:
            sims.ROOT = old_root
        self.assertEqual(goal, "frob the zork, never weakened")
        self.assertEqual(bullets, ["`vcheck a/zork.dfy` is green", "no other file"])

    def test_viva_regexes(self):
        text = "**Question 1 of 5 (Q77.K2, predict)** then Q77.K1; grades: SHAKY, MISSED, SOLID."
        self.assertEqual(sims.SCOPED_ID.findall(text), ["Q77.K2", "Q77.K1"])
        self.assertEqual(sims.QNUM_RX.findall(text), ["1"])
        self.assertEqual(sims.VERDICT_RX.findall(text), ["SHAKY", "MISSED", "SOLID"])


class LearnerState(unittest.TestCase):
    """`learner <spec.json>`: a learner state kept outside the repo (DV3k)."""

    def setUp(self):
        base = os.environ.get("DVL_TEST_TMP") or None
        self.tmp = Path(tempfile.mkdtemp(prefix="dvl0-sims-test-", dir=base))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / "clone" / "slots").mkdir(parents=True)
        (self.tmp / "clone" / "slots" / "Q77.slots").write_text("# head\nP1 = ???\nP2 = ???\n")

    def test_applies_and_records(self):
        if sims.ROOT in self.tmp.resolve().parents:
            self.skipTest("DVL_TEST_TMP lies inside the repo")
        spec = self.tmp / "spec.json"
        spec.write_text(json.dumps({"name": "zork", "edits": [
            ["slots/Q77.slots", "\nP1 = ???\n", '\nP1 = "a"\n']]}))
        state = {"clone": str(self.tmp / "clone"), "plants": []}
        sims.phase_learner(self.tmp, state, spec)
        self.assertIn('P1 = "a"', (self.tmp / "clone/slots/Q77.slots").read_text())
        self.assertEqual(state["plants"][0]["name"], "learner:zork")
        self.assertEqual(state["plants"][0]["new"], '\nP1 = "a"\n')
        with self.assertRaises(sims.Refusal):   # the anchor is gone now
            sims.phase_learner(self.tmp, state, spec)

    def test_refuses_a_spec_inside_the_repo(self):
        state = {"clone": str(self.tmp / "clone"), "plants": []}
        with self.assertRaises(sims.Refusal):
            sims.phase_learner(self.tmp, state, sims.ROOT / "tests" / "spec.json")


class DropIn(unittest.TestCase):
    """The drop-in splice (DV5c) on invented files: the skeleton's header comment,
    then the fixture from its documentclass line on; a calibration marker refuses."""
    def setUp(self):
        base = os.environ.get("DVL_TEST_TMP") or None
        if base:
            Path(base).mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="dvl0-sims-test-", dir=base))
        self.addCleanup(shutil.rmtree, self.root, True)
        (self.root / "paper").mkdir()
        (self.root / "tests/instructor/fixtures").mkdir(parents=True)
        (self.root / "paper/Q99_answers.tex").write_text(
            "% skeleton header\n\\documentclass{article}\nskeleton body\n", encoding="utf-8")

    def fixture(self, body):
        (self.root / "tests/instructor/fixtures/Q99_flawed_answers.tex").write_text(
            "% EXPECTED[B1][x][2]: invented\n\\documentclass{article}\n" + body, encoding="utf-8")

    def test_splice(self):
        self.fixture("graded body\n")
        text = sims.dropin_text("Q99", "flawed", root=self.root)
        self.assertEqual(text, "% skeleton header\n\\documentclass{article}\ngraded body\n")

    def test_refusals(self):
        self.fixture("a body that names a fixture\n")
        with self.assertRaises(sims.Refusal):
            sims.dropin_text("Q99", "flawed", root=self.root)
        with self.assertRaises(sims.Refusal):
            sims.dropin_text("Q99", "empty", root=self.root)
        with self.assertRaises(sims.Refusal):
            sims.dropin_text("Q98", "flawed", root=self.root)

    def test_every_shipped_fixture_makes_a_drop_in(self):
        """The 36 shipped calibration fixtures (flawed and gold, Q01-Q18) each splice into a
        drop-in with no calibration marker left (a body word such as `fixture` refused the
        lab modules' drop-ins until the basic fix round)."""
        import tomllib
        reg = tomllib.loads((sims.ROOT / "MODULES.toml").read_text(encoding="utf-8"))
        mids = [m["id"] for m in reg["module"] if m.get("status") == "shipped"
                and m["id"].startswith("Q")]
        self.assertEqual(len(mids), 18)
        for mid in mids:
            for kind in sims.DROPIN_KINDS:
                with self.subTest(module=mid, kind=kind):
                    self.assertIn("\\documentclass", sims.dropin_text(mid, kind))

    def test_prereg_line(self):
        rx = sims.PREREG_LINE_RX
        self.assertEqual(rx.findall("PREREG Q99: HELD — budget-parity at 2"), [("Q99", "HELD")])
        self.assertEqual(rx.findall("x\nPREREG Q99: UNLOCKED — every method dimension"),
                         [("Q99", "UNLOCKED")])
        self.assertEqual(rx.findall("prereg Q99 held"), [])


class Plants(unittest.TestCase):
    """Every plant applies to the shipped learner file, once per anchor, in the order
    the README gives (a stacked plant after the one it builds on)."""
    ORDER = [["h2d-weak", "h2d-normalized-prefix"],
             ["q05-h2d-copied-frame", "q05-h2d-split-assert"],
             ["q06-h6py-all-attempts"],
             ["q08-a1d-length-only"],
             ["q09-h2py-one-reason"],
             ["q10-h4d-bounds-only"],
             ["q11-h7d-forwards"],
             ["q13-h2d-front-recursion"],
             ["q16-h1d-plain-induction"]]

    def test_plants_apply_in_order(self):
        self.assertEqual(sorted(n for chain in self.ORDER for n in chain), sorted(sims.PLANTS))
        for chain in self.ORDER:
            files = {}
            for name in chain:
                for rel, old, new in sims.PLANTS[name]:
                    text = files.get(rel) or (sims.ROOT / rel).read_text(encoding="utf-8")
                    self.assertEqual(text.count(old), 1, f"{name}: anchor in {rel}")
                    files[rel] = text.replace(old, new)


def _rl(status, seven, overage=False):
    return json.dumps({"type": "rate_limit_event", "rate_limit_info": {
        "status": status, "isUsingOverage": overage, "overageStatus": "rejected",
        "unifiedWindows": {"five_hour": {"utilization": 0.1},
                           "seven_day": {"utilization": seven}}}})


class WindowRule(unittest.TestCase):
    """The window rule the three author harnesses share (guard_doors.window_*; DV6)."""
    GD = sims.GD

    def test_verdicts(self):
        v = self.GD.window_verdict
        self.assertEqual(v(_rl("allowed", 0.3))["verdict"], "ok")
        self.assertEqual(v(_rl("allowed_warning", 0.58))["verdict"], "defer")
        self.assertEqual(v(_rl("allowed", 0.6))["verdict"], "defer")
        self.assertEqual(v(_rl("allowed", 0.3, overage=True))["verdict"], "stop")
        self.assertEqual(v('{"type": "result"}')["verdict"], "stop")
        # the worst event of a stream wins
        self.assertEqual(v(_rl("allowed", 0.3) + "\n" + _rl("allowed_warning", 0.58))["verdict"],
                         "defer")

    def test_record_and_gate(self):
        state = {}
        self.assertEqual(self.GD.window_record(state, _rl("allowed", 0.3), "a/t01")["verdict"], "ok")
        self.GD.window_gate(state)
        with self.assertRaises(self.GD.Refusal):
            self.GD.window_record(state, _rl("allowed_warning", 0.58), "a/t02")
        self.assertEqual(state["window"]["verdict"], "defer")
        with self.assertRaises(self.GD.Refusal):
            self.GD.window_gate(state)
        self.GD.window_gate(state, ack=True)          # the author's --window-ack
        self.assertEqual(state["window"], {})
        self.assertEqual(len(state["window_acks"]), 1)
        self.GD.window_gate(state)


class LeakTokens(unittest.TestCase):
    """guard_doors.code_line: prose lines are no line tokens (DV6)."""

    def test_code_line(self):
        cl = sims.GD.code_line
        self.assertFalse(cl("prints only the invented summary line."))
        self.assertFalse(cl("The invented helper sums every entry of the list"))
        self.assertTrue(cl("invariant 0 <= k <= |zs|"))
        self.assertTrue(cl("the helper zork_count proves it"))
        self.assertTrue(cl("the helper zorkCount proves it"))


class ContractDelivery(unittest.TestCase):
    """split_delivery: an allowed file's writes and reads go to the patterns only (DV6)."""

    def events(self, clone):
        return [
            {"type": "assistant", "message": {"content": [
                {"type": "text", "text": "plan: zorkline"},
                {"type": "tool_use", "id": "w1", "name": "Write",
                 "input": {"file_path": f"{clone}/dafny/Q/QX/agent/A.dfy", "content": "DELIVERED"}},
                {"type": "tool_use", "id": "e1", "name": "Edit",
                 "input": {"file_path": f"{clone}/dafny/Q/QX/core/B.dfy", "old_string": "x",
                           "new_string": "OUTSIDE"}},
                {"type": "tool_use", "id": "r1", "name": "Read",
                 "input": {"file_path": f"{clone}/dafny/Q/QX/agent/A.dfy"}}]}},
            {"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": "r1", "content": "READBACK"}]}},
        ]

    def test_split(self):
        clone = "/tmp/invented-clone"
        ev, d = sims.split_delivery(self.events(clone), {"dafny/Q/QX/agent/A.dfy"}, clone)
        hay = "\n".join(sims.GD.strings_of(ev, []))
        self.assertIn("DELIVERED", d)
        self.assertIn("READBACK", d)
        self.assertNotIn("DELIVERED", hay)
        self.assertNotIn("READBACK", hay)
        self.assertIn("OUTSIDE", hay)          # a write outside the allowed files keeps both
        self.assertIn("zorkline", hay)

    def test_no_contract_no_split(self):
        clone = "/tmp/invented-clone"
        ev, d = sims.split_delivery(self.events(clone), set(), clone)
        self.assertEqual(d, "")
        self.assertIn("DELIVERED", "\n".join(sims.GD.strings_of(ev, [])))

    def test_contract_files(self):
        work = Path(tempfile.mkdtemp(prefix="dvl0-sims-test-"))
        self.addCleanup(shutil.rmtree, work, True)
        (work / "runs" / "c").mkdir(parents=True)
        (work / "runs" / "c" / "t01.prompt.txt").write_text("/contract Q04\n")
        (work / "runs" / "d").mkdir(parents=True)
        (work / "runs" / "d" / "t01.prompt.txt").write_text("/tutor Q04\n")
        recs = dict(RECORDS)
        recs["Q04"] = dict(recs["Q04"], agentic=["dafny/Q/QX/agent/A.dfy"])
        self.assertEqual(sims.contract_files(work, "c", recs), {"dafny/Q/QX/agent/A.dfy"})
        self.assertEqual(sims.contract_files(work, "d", recs), set())


if __name__ == "__main__":
    unittest.main()
