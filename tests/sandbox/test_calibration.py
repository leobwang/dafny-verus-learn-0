"""The public-answer check's calibration set (DV4-PLAN §5.4 item 4): no
shipped file of an armed module (the given layers' text excluded) shares the
pinned number of windows with any installed public answer, and a public task
form staged as a run's editable file is not flagged (its own shipped form is
excluded). Runs only where scripts/get_bench.sh has installed sets; it says so
and skips otherwise (they are fetched, never committed)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sandbox_common as sc  # noqa: E402
from dvl import sandbox  # noqa: E402

INSTALLED = sandbox.public_answer_files(sc.ROOT)


@unittest.skipUnless(INSTALLED, "no benchmark set is installed (scripts/get_bench.sh --all): "
                                "the calibration set needs the public answers")
class Calibration(unittest.TestCase):
    def test_no_shipped_course_file_is_flagged(self):
        rows = sandbox.calibration(sc.ROOT)
        self.assertTrue(rows)
        over = [r for r in rows if r[0] >= sandbox.WINDOW_THRESHOLD]
        self.assertEqual(over, [], f"{len(over)} shipped file(s) reach the threshold")

    def test_a_public_task_form_is_not_flagged_as_staged(self):
        # two of the first set's, and one that a second set derives from the
        # first (vericoding's DD0099 shares over a thousand windows with a
        # DafnyBench answer once its own text is not excluded)
        tasks = sorted(p for p in (sc.ROOT / "bench" / "public").glob("*/tasks/*")
                       if p.suffix in (".dfy", ".rs") and p.is_file())[:2]
        derived = sc.ROOT / "bench/public/vericoding/tasks/DD0099.dfy"
        tasks += [derived] if derived.is_file() else []
        if not tasks:
            self.skipTest("no installed set has task files")
        runs = sc.tmpdir("dvl0-sandbox-calib-")
        self.addCleanup(sc.cleanup, runs)
        for t in tasks:
            rel = t.relative_to(sc.ROOT).as_posix()
            raw = sc.verify_manifest(sc.ROOT, module="Q04", file=[sc.entry(sc.ROOT, rel, "editable")])
            m = sandbox.validate(raw, sc.ROOT, check_image=False)
            run = sandbox.materialize(m, sc.ROOT, base=runs)
            self.addCleanup(sandbox.remove_run, run)
            rep = sandbox.selftest(m, run, sc.ROOT, answers=INSTALLED)
            self.assertTrue(rep["checks"]["public-answers"]["ok"], (rel, rep["checks"]["public-answers"]))


if __name__ == "__main__":
    unittest.main()
