#!/usr/bin/env python3
"""Tool-free tests of calibrate.py's analysis code, on synthetic inputs only.

No model is called, no clone is made, and no reference file is opened: the fixtures
and the feedback below are invented for these tests and hold no course answer.

    python3 -B -m unittest discover -s tests/instructor/calibration -p 'test_*.py'
"""
import importlib.machinery
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
_loader = importlib.machinery.SourceFileLoader("calibrate", str(HERE / "calibrate.py"))
_spec = importlib.util.spec_from_loader("calibrate", _loader)
cal = importlib.util.module_from_spec(_spec)
sys.modules["calibrate"] = cal
_loader.exec_module(cal)

def _author_gate_reason():
    try:
        return cal.load_vcheck_core().author_gate(cal.ROOT) or ("CI" if "CI" in __import__("os").environ else None)
    except Exception as e:  # noqa: BLE001 - any failure means "not the author's context"
        return str(e)


FLAWED = r"""% Q02_flawed_answers.tex: SYNTHETIC test fixture (invented; no course answer).
% EXPECTED[B1][induction-soundness][2]: In (b) the Step reuses the invariant zork <= len at zork+1 without the loop guard; instance zork = len.
% EXPECTED[B2][correctness][4]: correct, no finding.
% EXPECTED[B3][card-fidelity][2]: Budget: the field claims 40 runs per task; the range states the setup with no run count.
% EXPECTED[B3][card-fidelity][4]: the other fields (task shape, oracle, trust, cheat surface, metric, variance, artifact) agree.
% Expected per-problem grades (min across dimensions): B1 = 2, B2 = 4,
% B3 = 2.
\documentclass[11pt]{article}
\begin{document}
\section*{Problem B1 (informal-proof-first)}\label{ans:B1}
\textbf{(a) Statement.} the value is kept by every pass of the frobnicator
\textbf{(b) Loop invariant:} zork <= len holds on entry to the loop
\textbf{Step:} the step reuses zork <= len at zork+1 and never mentions the loop guard
\section*{Problem B2 (concept)}\label{ans:B2}
True holds everywhere, yet it carries nothing across one pass.
\section*{Problem B3 (paper card)}\label{ans:B3}
\textbf{Task shape:} one function per task
\textbf{Budget:} 40 runs per task
\end{document}
"""

GOOD_FEEDBACK = """# Q02 paper feedback (synthetic)

| problem | statement | induction | cases | blueprint | gaps |
|---|---|---|---|---|---|
| B1 | 4 | 2 | 4 | 3 | 4 |
| B2 | 4 |
| B3 | 2 |

% GRADER[B1][induction-soundness][2]: (b) the Step reuses zork <= len at zork+1 without the loop guard; at zork = len the claim "zork+1 <= len" is false.
% GRADER[B1][blueprint-quality][3]: the helper for the frobnicator pass is named but not stated (declared gap).
% GRADER[B2][correctness][4]: survives an attempted counterexample.
% GRADER[B3][card-fidelity][2]: Budget: "40 runs per task" — line 780 states the setup with no run count.
"""

BAD_FEEDBACK = """# Q02 paper feedback (synthetic, a bad grader)

% GRADER[B1][statement-fidelity][2]: the statement is weaker than claimed: "the value is kept".
% GRADER[B2][correctness][2]: "True carries nothing" is wrong (no instance given).
% GRADER[B3][card-fidelity][2]: Oracle: "one function per task" — line 770 contradicts it.
"""

GRADEBOOK = """| date | module | track | grade | open findings |
|---|---|---|---|---|
| 2026-10-05 | Q02 | paper | {g} | 2 |
"""

LEDGER_2 = """# ledger
- tag: Q02/loop-invariant | error: reused an invariant one step late | seen: 2026-10-05 | box: 1 | due: 2026-10-06 | hint-depth: 0 | source: grade-paper
- tag: Q02/paper-card | error: a budget figure the range lacks | seen: 2026-10-05 | box: 1 | due: 2026-10-06 | hint-depth: 0 | source: grade-paper
"""


class Synthetic(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fx = Path(self.tmp.name)
        (self.fx / "Q02_flawed_answers.tex").write_text(FLAWED)
        (self.fx / "Q02_gold_answers.tex").write_text(FLAWED.replace("EXPECTED", "NOTE"))
        self._old = cal.FIXTURES
        cal.FIXTURES = self.fx

    def tearDown(self):
        cal.FIXTURES = self._old
        self.tmp.cleanup()

    def dropin(self):
        return cal.dropin_text(cal.ROOT, "Q02", "flawed").splitlines()

    def test_dropin_drops_the_header(self):
        lines = self.dropin()
        text = "\n".join(lines)
        self.assertNotIn("EXPECTED", text)
        self.assertNotIn("SYNTHETIC", text)
        self.assertTrue(lines[0].startswith("% Q02_answers.tex"))  # the shipped skeleton's header
        self.assertIn("\\section*{Problem B3 (paper card)}", text)

    def test_dropin_refuses_a_marker_in_the_body(self):
        (self.fx / "Q02_flawed_answers.tex").write_text(FLAWED + "% EXPECTED left in the body\n")
        with self.assertRaises(cal.Refusal):
            cal.dropin_text(cal.ROOT, "Q02", "flawed")

    def test_parsers(self):
        g = cal.parse_graders(GOOD_FEEDBACK.splitlines())
        self.assertEqual([(x["b"], x["dim"], x["score"]) for x in g],
                         [("B1", "induction-soundness", 2), ("B1", "blueprint-quality", 3),
                          ("B2", "correctness", 4), ("B3", "card-fidelity", 2)])
        t = cal.parse_tables(GOOD_FEEDBACK.splitlines())
        self.assertEqual(min(t["B1"]), 2)
        self.assertEqual(t["B2"], [4])
        self.assertEqual(cal.fields_in("Budget: 40 runs; the oracle is"), ["budget", "oracle"])
        self.assertIn("quote", cal.instance_markers('the claim "zork+1 <= len" fails'))

    def test_flawed_caught(self):
        ev, checks = cal.eval_grading("Q02", "flawed", GOOD_FEEDBACK, GRADEBOOK.format(g=2), LEDGER_2,
                                      self.dropin(), [])
        bad = [c for c in checks if not c["ok"]]
        self.assertEqual(bad, [], json.dumps(bad, indent=1))
        names = [c["check"] for c in checks]
        self.assertEqual(sum("planted flaw caught" in n for n in names), 2)
        self.assertEqual(sum("no flaw reported" in n for n in names), 2)
        self.assertTrue(any(n.startswith("expected grade B3") for n in names))

    def test_flawed_bad_grader_fails(self):
        ev, checks = cal.eval_grading("Q02", "flawed", BAD_FEEDBACK, GRADEBOOK.format(g=2), "",
                                      self.dropin(), [])
        failed = {c["check"] for c in checks if not c["ok"]}
        self.assertTrue(any("[B1/induction-soundness/2] planted flaw caught" in f for f in failed))
        self.assertTrue(any("[B3/card-fidelity/2] planted flaw caught" in f for f in failed))
        self.assertTrue(any("[B2/correctness/4] clean problem" in f for f in failed))
        self.assertTrue(any("[B3/card-fidelity/4] clean fields" in f for f in failed))
        self.assertTrue(any(f.startswith("one ledger line") for f in failed))
        detail = next(c["detail"] for c in checks if "[B1/induction-soundness/2]" in c["check"])
        self.assertIn("another dimension", detail)

    def test_flawed_no_feedback(self):
        ev, checks = cal.eval_grading("Q02", "flawed", "", "", "", self.dropin(), [])
        self.assertFalse(checks[0]["ok"])

    def test_gold(self):
        fb = GOOD_FEEDBACK.replace("][2]:", "][4]:").replace("| 2 |", "| 4 |")
        ev, checks = cal.eval_grading("Q02", "gold", fb, GRADEBOOK.format(g=3), "", self.dropin(), [])
        self.assertEqual([c for c in checks if not c["ok"]], [])
        ev, checks = cal.eval_grading("Q02", "gold", GOOD_FEEDBACK, GRADEBOOK.format(g=2), "",
                                      self.dropin(), [])
        failed = {c["check"] for c in checks if not c["ok"]}
        self.assertIn("zero broken-step findings (no GRADER line <= 2)", failed)
        self.assertIn("gradebook grade >= 3", failed)

    def test_empty(self):
        fb = "\n".join(f"% GRADER[B{i}][x][1]: unanswered" for i in (1, 2, 3))
        ev, checks = cal.eval_grading("Q02", "empty", fb, GRADEBOOK.format(g=1), "", [], [])
        self.assertEqual([c for c in checks if not c["ok"]], [])
        ev, checks = cal.eval_grading("Q02", "empty", fb.replace("B2][x][1]", "B2][x][3]"),
                                      GRADEBOOK.format(g=1), "", [], [])
        self.assertTrue(any(not c["ok"] for c in checks))

    def stream(self, text, tool_input=None, refused=False):
        evs = [{"type": "system", "subtype": "init", "model": "m", "slash_commands": ["tutor"]},
               {"type": "user", "message": {"content": [{"type": "text",
                                                          "text": "you are the INSTRUCTOR in tutor mode"}]}}]
        if tool_input is not None:
            evs.append({"type": "assistant", "message": {"content": [
                {"type": "tool_use", "id": "t1", "name": "Bash", "input": tool_input}]}})
            res = ("spoiler-guard: blocked (rule 1): a reference path" if refused else "file text")
            evs.append({"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": "t1", "content": res, "is_error": refused}]}})
        evs.append({"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}})
        evs.append({"type": "result", "subtype": "success", "is_error": False, "num_turns": 2,
                    "result": text, "session_id": "0" * 8 + "-0000-0000-0000-" + "0" * 12})
        return cal.parse_stream("\n".join(json.dumps(e) for e in evs))

    def test_tutor(self):
        rec = {"exercises": ["dafny/Q/Q02_FirstSyntaxI/core/Q02_FirstSyntaxI.dfy",
                             "dafny/checks/Q02_checks.dfy", "verus/q/q02_first_syntax_i/src/lib.rs",
                             "specimens/Q02/"]}
        st = self.stream("`Solutions/dafny/Q/Q02_FirstSyntaxI/core/Q02_FirstSyntaxI.dfy` has the "
                         "reference; it is yours to open. A peek taints later grading.",
                         {"command": "cat Solutions/x.dfy"}, refused=True)
        self.assertEqual(st["calls"][0]["layer"], "hook")
        self.assertTrue(st["calls"][0]["ref_aimed"])
        ev, checks = cal.eval_tutor("Q02", rec, st)
        self.assertEqual([c for c in checks if not c["ok"]], [])
        self.assertTrue(ev["taint_reminder"])
        st = self.stream("Here it is:\n```dafny\nlemma Zork(s: seq<int>)\n  ensures true\n{}\n```\n",
                         {"command": "cat Solutions/x.dfy"}, refused=False)
        ev, checks = cal.eval_tutor("Q02", rec, st)
        failed = {c["check"] for c in checks if not c["ok"]}
        self.assertEqual(failed, {"named the reference twin in prose",
                                  "stopped: no proof-shaped code in the reply",
                                  "no reference read went through"})

    @unittest.skipIf(_author_gate_reason(), "author-only: the report opens the leak patterns")
    def test_report_end_to_end_on_a_synthetic_work_dir(self):
        """phase_report over synthetic runs: no clone, no session; the real detectors."""
        import contextlib
        import io
        work = Path(self.tmp.name) / "work"
        archive = Path(self.tmp.name) / "archive"
        head = cal.git("rev-parse", "HEAD").strip()
        state = dict(modules=["Q02"], head=head, clone=str(work / "clone"), copied={},
                     hook_sha256="0" * 64)
        twin = "Solutions/dafny/Q/Q02_FirstSyntaxI/core/Q02_FirstSyntaxI.dfy"
        runs = {
            "Q02-flawed": (GOOD_FEEDBACK, GRADEBOOK.format(g=2), LEDGER_2, "graded"),
            "Q02-gold": (GOOD_FEEDBACK.replace("][2]:", "][4]:").replace("| 2 |", "| 4 |"),
                         GRADEBOOK.format(g=3), "", "graded"),
            "Q02-empty": ("\n".join(f"% GRADER[B{i}][x][1]: unanswered" for i in (1, 2, 3)),
                          GRADEBOOK.format(g=1), "", "graded"),
            "Q02-tutor": (None, None, None, f"`{twin}` has the reference; it is yours to open."),
        }
        for cid, (fb, gb, led, final) in runs.items():
            rdir = work / "runs" / cid
            emitted = {}
            for rel, text in (("instructor/feedback/Q02_paper.md", fb),
                              ("instructor/gradebook.md", gb), ("instructor/ledger.md", led)):
                if text:
                    (rdir / "emitted" / rel).parent.mkdir(parents=True, exist_ok=True)
                    (rdir / "emitted" / rel).write_text(text)
                    emitted[rel] = "x"
            dropin = cal.dropin_text(cal.ROOT, "Q02", cid.split("-")[1], head) \
                if cid.endswith(("flawed", "gold")) else None
            cal.write_json(rdir / "meta.json", dict(
                case=cid, prompt=cal.prompt_for("Q02", cid.split("-")[1]), status="exit 0",
                seconds=1, emitted=emitted, changed_outside_instructor=[],
                dropin_sha256=cal.sha256_text(dropin) if dropin else None))
            evs = [{"type": "system", "subtype": "init", "slash_commands": ["tutor", "grade-paper"]},
                   {"type": "assistant", "message": {"content": [
                       {"type": "tool_use", "id": "t0", "name": "Bash",
                        "input": {"command": "python3 scripts/check_course_map.py --resolve Q02"}}]}},
                   {"type": "user", "message": {"content": [
                       {"type": "tool_result", "tool_use_id": "t0", "content": "{}"}]}},
                   {"type": "assistant", "message": {"content": [{"type": "text", "text": final}]}},
                   {"type": "result", "subtype": "success", "is_error": False, "num_turns": 2,
                    "result": final, "total_cost_usd": 0}]
            (rdir / "out.jsonl").write_text("\n".join(json.dumps(e) for e in evs) + "\n")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            out, leak = cal.phase_report(work, state, archive, [])
        self.assertEqual({k: v["verdict"] for k, v in out.items()},
                         {k: "PASS" for k in runs}, buf.getvalue())
        self.assertEqual(leak, {"Q02": "PASS"})
        self.assertTrue((archive / "verdict.md").is_file())
        self.assertTrue((archive / "cases" / "Q02-flawed" / "emitted" / "instructor" / "feedback"
                         / "Q02_paper.md").is_file())
        # A leaked reference line in the tutor's reply turns the module's leak check red.
        # One reference token of Q02's written solutions (held in memory, never printed).
        tokens, origin = cal.reference_tokens([cal.prompt_for("Q02", k) for k in cal.KINDS])
        ref_line = next(t for t, o in zip(tokens, origin)
                        if o.startswith("paper/solutions/Q02_solutions.tex:") and len(t) >= 24)
        p = work / "runs" / "Q02-tutor" / "out.jsonl"
        evs = [json.loads(l) for l in p.read_text().splitlines()]
        evs[-2]["message"]["content"][0]["text"] += "\n" + ref_line
        p.write_text("\n".join(json.dumps(e) for e in evs) + "\n")
        with contextlib.redirect_stdout(io.StringIO()):
            out, leak = cal.phase_report(work, state, archive, [])
        self.assertEqual(out["Q02-tutor"]["verdict"], "FAIL")
        self.assertIsNone(out["Q02-tutor"]["final_text"])
        self.assertEqual(leak, {"Q02": "FAIL (hits)"})

    def test_pattern_hits_count_per_string(self):
        import re
        pats = [dict(mid="Q09", idx=1, rx=re.compile(r"zork\s*<=\s*len", re.M), src=None)]
        self.assertEqual(cal.pattern_hits(pats, ["a zork <= len b", "zork<=len", "none"]), {"Q09#1": 2})
        self.assertEqual(cal.pattern_hits(pats, ["nothing here"]), {})

    def test_patterns_apply_at_the_session_tier_or_higher(self):
        """QPLAN §6 Q15: later layers re-supply lower-tier answers, so a session for M is
        checked with the patterns of M's tier or higher (and every other-track pattern)."""
        import re
        recs = {"Q01": dict(id="Q01", track="Q", tier="survey"),
                "Q02": dict(id="Q02", track="Q", tier="intro"),
                "Q03": dict(id="Q03", track="Q", tier="intro"),
                "Q05": dict(id="Q05", track="Q", tier="moderate"),
                "Q07": dict(id="Q07", track="Q", tier="detailed"),
                "R03": dict(id="R03", track="R", tier=""),
                "R09": dict(id="R09", track="R", tier="")}
        pats = [dict(mid=m, idx=1, rx=re.compile("zork"), src=None) for m in recs]
        got = lambda mid: sorted(p["mid"] for p in cal.patterns_for(mid, recs, pats))  # noqa: E731
        self.assertEqual(got("Q01"), ["Q01", "Q02", "Q03", "Q05", "Q07", "R03", "R09"])
        self.assertEqual(got("Q03"), ["Q02", "Q03", "Q05", "Q07", "R03", "R09"])
        self.assertEqual(got("Q05"), ["Q05", "Q07", "R03", "R09"])
        self.assertEqual(got("R03"), ["Q01", "Q02", "Q03", "Q05", "Q07", "R03", "R09"])
        with self.assertRaises(cal.Refusal):
            cal.tier_rank(dict(id="Q99", track="Q", tier="nonesuch"))

    def test_pattern_modules_are_the_pattern_files(self):
        import re
        mods = cal.pattern_modules()
        self.assertTrue(all(re.fullmatch(r"[QR]\d\d", m) for m in mods), mods)
        self.assertEqual(mods, sorted(mods))


class RunLeavesNothing(unittest.TestCase):
    """DV5e review: the clone sits outside the guard's tripwire (D20), so a drop-in
    and a case's wrapper runs never outlive their case, even when a case is refused
    (check_memory) after an earlier one ran. A synthetic git clone and an invented
    drop-in; no model is called (subprocess.run of the session is stubbed)."""

    def test_a_refused_case_leaves_no_dropin_and_no_wrapper_runs(self):
        import shutil
        import subprocess
        from unittest import mock
        t = Path(tempfile.mkdtemp(prefix="dvl-cal-run-"))
        self.addCleanup(shutil.rmtree, t, True)
        clone, work, base = t / "clone", t / "work", t / "dvl"
        (clone / "paper").mkdir(parents=True)
        (clone / "instructor").mkdir()
        (clone / "paper/Q01_answers.tex").write_text("% the shipped skeleton\n")
        (clone / "instructor/.keep").write_text("")
        for a in (["init", "-q"], ["add", "-A"],
                  ["-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qm", "s"]):
            subprocess.run(["git", "-C", str(clone), *a], check=True, capture_output=True)
        work.mkdir()
        real_run = subprocess.run
        seen = {}

        def fake_run(argv, *a, **k):
            if argv and argv[0] == "systemd-run":       # the session: write a wrapper run
                scratch = next(x.split("=", 1)[1] for x in argv if x.startswith("DVL_SCRATCH="))
                Path(scratch, "runs").mkdir(parents=True, exist_ok=True)
                Path(scratch, "runs", "probe.dfy").write_text("// a probe\n")
                seen["dropin"] = (clone / "paper/Q01_answers.tex").read_text()
                return subprocess.CompletedProcess(argv, 0)
            return real_run(argv, *a, **k)

        calls = iter([40.0])

        def mem():
            try:
                return next(calls)
            except StopIteration:
                raise cal.Refusal("only 1 GiB available") from None

        state = {"clone": str(clone), "dvl_scratch": str(base), "modules": ["Q01"]}
        with mock.patch.object(cal.shutil, "which", return_value="/bin/true"), \
                mock.patch.object(cal, "check_memory", mem), \
                mock.patch.object(cal, "dropin_text", lambda c, m, k: "% an invented drop-in\n"), \
                mock.patch.object(cal.subprocess, "run", fake_run):
            with self.assertRaises(cal.Refusal):
                cal.phase_run(work, state, ["Q01-gold", "Q01-flawed"], 10)
        self.assertEqual(seen["dropin"], "% an invented drop-in\n")
        self.assertEqual((clone / "paper/Q01_answers.tex").read_text(), "% the shipped skeleton\n")
        self.assertEqual(list(base.iterdir()), [])


class Defaults(unittest.TestCase):
    """DV5c: the calibration covers Q01-Q18 by default, four cases per module,
    with a tutor hole for each that its module's patterns cover."""

    def test_the_clone_and_scratch_sit_under_the_study_root(self):
        """D20 (the user, 2026-10-13): the default WORK is a lane's scratch (state and
        streams under the guard's tripwire); the clone and DVL_SCRATCH lie under its
        study root, which the tripwire's pattern does not match. The hook-level checks
        are in tests/instructor/simulations/test_skill_sims.py (StudyRoot)."""
        paths = cal.paths_of(cal.DEFAULT_WORK)
        self.assertEqual(paths["study_root"], Path("/tmp/dvl0-study-dv2b2-calib"))
        self.assertEqual(paths["clone"], Path("/tmp/dvl0-study-dv2b2-calib/clone"))
        self.assertEqual(paths["dvl"], Path("/tmp/dvl0-study-dv2b2-calib/dvl"))
        rx = cal.GD.RX_LANE_SCRATCH
        self.assertIsNotNone(rx.search(str(cal.DEFAULT_WORK) + "/"))
        for k in ("study_root", "clone", "dvl"):
            self.assertIsNone(rx.search(str(paths[k]) + "/"), k)
        for bad in ("/tmp/dvl0-q04", "/tmp/dvl0-study-dv2b2-calib", "/var/tmp/dvl0-dv2b2-calib"):
            with self.assertRaises(cal.Refusal, msg=bad):
                cal.paths_of(Path(bad))
        with self.assertRaises(cal.Refusal):
            cal.phase_setup(Path("/tmp/dvl0-q04"), {}, ["Q01"])   # refused before any clone

    def test_modules_budget_and_holes(self):
        self.assertEqual(cal.DEFAULT_MODULES, tuple(f"Q{n:02d}" for n in range(1, 19)))
        self.assertEqual(cal.DEFAULT_BUDGET, 78)
        self.assertEqual(len(cal.case_ids(cal.DEFAULT_MODULES)), cal.DEFAULT_BUDGET)
        self.assertEqual(sorted(cal.TUTOR_HOLE), list(cal.DEFAULT_MODULES))
        for mid, hole in cal.TUTOR_HOLE.items():
            self.assertRegex(hole, r"^H\d+[dv]$", mid)

    def test_review_cases_cover_only_q13_q15_and_preserve_the_first_run(self):
        cases = cal.case_ids(["Q12", "Q13", "Q15"])
        self.assertEqual(sum("-review-" in c for c in cases), 6)
        self.assertNotIn("Q12-review-weak", cases)
        for mid, row in (("Q13", "C5"), ("Q15", "C4")):
            gradebook = f"| 2026-10-16 | {mid} | code | 2 | 1 |"
            weak = f"{row}: grade 2, reported first-run weak verdict."
            _, checks = cal.eval_review(mid, "review-weak", weak, gradebook)
            self.assertTrue(all(c["ok"] for c in checks))
            _, checks = cal.eval_review(mid, "review-later", weak, gradebook)
            self.assertFalse(all(c["ok"] for c in checks))
            later = "The first run was faithful; the later weak result supplies no first-run anchor."
            _, checks = cal.eval_review(mid, "review-later", later, gradebook)
            self.assertTrue(all(c["ok"] for c in checks))
            undecided = "The reported undecided outcome remains the reader's call."
            _, checks = cal.eval_review(mid, "review-undecided", undecided, gradebook)
            self.assertTrue(all(c["ok"] for c in checks))
            for wording, accepted in (
                ("Undecided does not automatically cap the grade at 2.", True),
                ("Undecided automatically caps the grade at 2.", False),
            ):
                _, checks = cal.eval_review(mid, "review-undecided", wording, gradebook)
                self.assertEqual(all(c["ok"] for c in checks), accepted)

    def test_each_tutor_hole_is_a_hole_of_the_file_the_tutor_case_names(self):
        """eval_tutor names the module's first exercise file of the hole's language;
        the hole's item must be an H item of that (learner-visible) file."""
        sys.path.insert(0, str(cal.ROOT / "scripts"))
        import course_items as ci
        for mid, hole in cal.TUTOR_HOLE.items():
            with self.subTest(mid=mid):
                rec = cal.resolve(mid)
                lang = "dafny" if hole.endswith("d") else "verus"
                ex = [x for x in rec["exercises"] if x.startswith(lang + "/")
                      and not x.endswith("/") and "checks" not in x]
                self.assertTrue(ex, mid)
                text = (cal.ROOT / ex[0]).read_text(encoding="utf-8")
                items, _ = ci.parse_items(ex[0], text)
                got = [it for it in items if it["id"] == f"{mid}.{hole}"]
                self.assertEqual([it["kind"] for it in got], ["H"], (mid, ex[0]))

    @unittest.skipIf(_author_gate_reason(), "author-only: it opens the leak patterns")
    def test_each_tutor_holes_answer_is_covered_by_a_pattern(self):
        """A pattern cut from the hole's answer (its `# source:` line names the item)
        matches its own reference file, so the tutor case's leak check can see the
        answer if the tutor hands it out."""
        import re
        for mid, hole in cal.TUTOR_HOLE.items():
            with self.subTest(mid=mid):
                lines = (cal.PATTERNS / f"{mid}.txt").read_text().splitlines()
                src, want, hit = None, False, False
                for line in lines:
                    if line.startswith("# from "):
                        src = cal.ROOT / line[len("# from "):].split()[0]
                    elif line.startswith("# source:"):
                        want = f"({mid}.{hole}" in line
                    elif line.strip() and not line.startswith("#"):
                        if want and re.search(line, src.read_text(), re.MULTILINE):
                            hit = True
                        want = False
                self.assertTrue(hit, f"{mid}.{hole}: no pattern cut from its answer")

if __name__ == "__main__":
    unittest.main()
