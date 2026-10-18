"""The public-answer check's calibration (DV4-PLAN §5.4 item 4).

Hermetic part (always runs, the same with or without installed benchmark sets): on a
throwaway course root with an invented armed module, a given layer and an invented
public set, dvl.sandbox.calibration flags a shipped file that copies at least the
pinned number of windows from a public answer and no other file, never counts the given
layers' windows, and a public task form staged as an editable file is not flagged
against its own answer (its task file's windows are excluded).

Installed-set audit (opt-in, DVL_CALIBRATION_INSTALLED=1): the same calibration over
this checkout's armed modules and whatever scripts/get_bench.sh installed. Its result
depends on which sets are installed, so CI never runs it; the author runs it after a
set or a shipped file changes and records what it reports.
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sandbox_common as sc  # noqa: E402
from dvl import sandbox  # noqa: E402

N = sandbox.WINDOW_TOKENS


def words(tag, k):
    """k distinct tokens unique to `tag` (each window over them is new text)."""
    return " ".join(f"{tag}_{i}" for i in range(k))


ANSWER = "method Pub()\n{\n  " + words("pub", 6 * N) + "\n}\n"
TASK = "method Pub()\n{\n  " + words("pub", N) + "\n}\n"           # the answer's own task form
GIVEN = "module G {\n  " + words("given", 3 * N) + "\n}\n"


class HermeticCalibration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=sc.TMP_BASE)
        self.addCleanup(self.tmp.cleanup)
        r = self.root = Path(self.tmp.name)
        (r / "MODULES.toml").write_text(
            '[[module]]\nid = "Q98"\nstatus = "authoring"\n'
            'exercises = ["dafny/Q/Q98/copy.dfy", "dafny/Q/Q98/own.dfy", "dafny/Q/Q98/given_use.dfy"]\n'
            'exits = []\nagentic = []\nharness = []\n')
        files = {
            "dafny/given/Q/QG_Fixture.dfy": GIVEN,
            "bench/public/fixset/answers/p.dfy": ANSWER,
            "bench/public/fixset/tasks/p.dfy": TASK,
            # copies a stretch of the answer beyond its task form: flagged
            "dafny/Q/Q98/copy.dfy": "method Mine()\n{\n  " + " ".join(ANSWER.split()[N + 5:4 * N]) + "\n}\n",
            # its own text only: never flagged
            "dafny/Q/Q98/own.dfy": "method Own()\n{\n  " + words("own", 4 * N) + "\n}\n",
            # the given layer's text plus a little of the answer, under the threshold
            "dafny/Q/Q98/given_use.dfy": GIVEN + "\n" + " ".join(ANSWER.split()[2 * N:2 * N + N + 1]) + "\n",
        }
        for rel, text in files.items():
            p = r / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)

    def test_only_the_copy_reaches_the_threshold(self):
        rows = {f: (k, a) for k, f, a in sandbox.calibration(self.root)}
        self.assertGreaterEqual(rows["dafny/Q/Q98/copy.dfy"][0], sandbox.WINDOW_THRESHOLD)
        self.assertEqual(rows["dafny/Q/Q98/copy.dfy"][1], "bench/public/fixset/answers/p.dfy")
        self.assertEqual(rows["dafny/Q/Q98/own.dfy"][0], 0)
        self.assertLess(rows["dafny/Q/Q98/given_use.dfy"][0], sandbox.WINDOW_THRESHOLD)
        self.assertEqual(rows["dafny/given/Q/QG_Fixture.dfy"][0], 0)

    def test_a_staged_public_task_form_is_not_flagged_against_its_own_answer(self):
        answers = sandbox.public_answer_files(self.root)
        self.assertEqual([(a.name, t.name if t else None) for a, t in answers], [("p.dfy", "p.dfy")])
        task = (self.root / "bench/public/fixset/tasks/p.dfy").read_bytes()
        self.assertEqual(sandbox.public_answer_check({"w/p.dfy": task}, answers), [])
        copy = (self.root / "dafny/Q/Q98/copy.dfy").read_bytes()
        hits = sandbox.public_answer_check({"w/copy.dfy": copy}, answers)
        self.assertEqual([h["file"] for h in hits], ["w/copy.dfy"])

    def test_no_installed_set_means_an_empty_calibration(self):
        shutil.rmtree(self.root / "bench")
        self.assertEqual(sandbox.calibration(self.root), [])


INSTALLED = sandbox.public_answer_files(sc.ROOT) if os.environ.get("DVL_CALIBRATION_INSTALLED") == "1" else []


@unittest.skipUnless(INSTALLED, "installed-set audit: opt in with DVL_CALIBRATION_INSTALLED=1 where "
                                "scripts/get_bench.sh has installed sets (never in CI)")
class InstalledSetsAudit(unittest.TestCase):
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
