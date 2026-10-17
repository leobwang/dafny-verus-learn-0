"""The verify manifests of DV4's remainder (no Docker): the Python acceptance run's
support files, the lab gate's task form (`--lab-task`), the files read at a commit
(`--rev`), the memory cap held to the language's bound, and the container's size
from its editable files. Built on this checkout's registry and files; nothing runs."""

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from dvl import sandbox  # noqa: E402

PY = "harness/q/fvh_q/policies.py"
CARD = "bench/local/q/lab1/dh4-tonat-mono/tasks/dh4-tonat-mono.dfy"


def gate(path, *extra):
    return ["scripts/vcheck", "--json", "--gate", *extra, path]


def card_path():
    hits = sorted((ROOT / "bench/local/q/lab1").glob("*/tasks/*.dfy"))
    return hits[0].relative_to(ROOT).as_posix() if hits else CARD


class PythonRun(unittest.TestCase):
    def setUp(self):
        self.raw, self.rel = sandbox.build_verify(ROOT, PY, gate(PY))
        self.files = {f["dst"]: f for f in self.raw["file"]}

    def test_the_support_files_are_staged_read_only(self):
        self.assertEqual(self.files[PY]["role"], "editable")
        for need in ("harness/fvh/protocol.py", "harness/fvh/tools/runners.py",
                     "harness/tests/conftest.py", "harness/tests/q/test_policies.py",
                     "harness/q/fvh_q/__init__.py", "harness/pyproject.toml", "harness/uv.lock"):
            self.assertIn(need, self.files)
            self.assertNotEqual(self.files[need]["role"], "editable", need)
        self.assertIn("expected/Q12.battery", self.files)
        fixtures = [d for d in self.files if d.startswith("harness/tests/q/fixtures/")]
        self.assertTrue(fixtures)
        self.assertTrue(all(d.startswith("harness/tests/q/fixtures/q12/") for d in fixtures))
        others = [d for d in self.files if d.startswith("harness/q/fvh_q/")
                  and not d.endswith("__init__.py") and d != PY]
        self.assertEqual(others, [], "another learner file entered")
        self.assertFalse(any(d.startswith("harness/tests/q/test_") and d != "harness/tests/q/"
                             "test_policies.py" for d in self.files))

    def test_it_validates_and_is_sized_for_python(self):
        m = sandbox.validate(self.raw, ROOT)
        self.assertEqual(m.pools(), ["python"])
        self.assertEqual(m.limits["mem_gb"], sandbox.memory_bound_gb("verify", ["python"]))

    def test_the_tests_class_still_never_enters(self):
        self.assertFalse(any(d.startswith("tests/") for d in self.files))


class LabTask(unittest.TestCase):
    def test_the_task_form_is_staged_where_the_command_names_it(self):
        card = card_path()
        work = Path(tempfile.mkdtemp(prefix="dvl0-labtask-"))
        try:
            (work / card).parent.mkdir(parents=True)
            (work / card).write_text((ROOT / card).read_text() + "\n// a delivery\n")
            staged = f"{sandbox.LAB_TASK_DIR}/{card}"
            raw, rel = sandbox.build_verify(ROOT, work / card, gate(card, "--lab-task", staged),
                                            lab_task=card)
        finally:
            import shutil
            shutil.rmtree(work, ignore_errors=True)
        self.assertEqual(rel, card)
        files = {f["dst"]: f for f in raw["file"]}
        self.assertEqual(files[staged]["role"], "task")
        self.assertEqual(files[staged]["text"], (ROOT / card).read_text())
        self.assertNotEqual(files[card]["text"], files[staged]["text"])
        m = sandbox.validate(raw, ROOT)
        self.assertEqual(m.commands[0], tuple(gate(card, "--lab-task", staged)))

    def test_a_command_that_does_not_name_it_is_refused(self):
        card = card_path()
        with self.assertRaises(sandbox.ManifestError):
            sandbox.build_verify(ROOT, card, gate(card), lab_task=card)

    def test_only_a_benchmark_task_is_a_lab_task(self):
        with self.assertRaises(sandbox.ManifestError):
            sandbox.build_verify(ROOT, PY, gate(PY, "--lab-task", f"lab-task/{PY}"), lab_task=PY)


class CrateLabTask(unittest.TestCase):
    """Lab 3's layout (the DV5c gaps lane): the task form is a crate card's directory,
    staged file by file under lab-task/<card dir>/, and the delivery's course path is the
    card's tasks directory itself."""

    def test_a_crate_card_is_staged_file_by_file(self):
        import sandbox_common as sc
        root = sc.make_root()
        work = Path(tempfile.mkdtemp(prefix="dvl0-cratecard-"))
        try:
            card = "bench/local/q/lab9/c1/tasks"
            sc.write(root, "bench/local/q/lab9/STRATUM.toml", 'schema = 1\nlab = "Q98"\n')
            for rel, text in (("Cargo.toml", '[package]\nname = "decoy_c1"\n'),
                              ("frozen.rs", "// decoy statements\n"),
                              ("src/lib.rs", "// decoy task form\n")):
                sc.write(root, f"{card}/{rel}", text)
                sc.write(work, f"{card}/{rel}", text if rel != "src/lib.rs"
                         else "// a decoy delivery\n")
            self.assertTrue(sandbox.bench_task(card))
            staged = f"{sandbox.LAB_TASK_DIR}/{card}"
            raw, rel = sandbox.build_verify(root, work / card, gate(card, "--lab-task", staged),
                                            lab_task=card)
            self.assertEqual(rel, card)
            files = {f["dst"]: f for f in raw["file"]}
            for r in ("Cargo.toml", "frozen.rs", "src/lib.rs"):
                self.assertEqual(files[f"{staged}/{r}"]["role"], "task", r)
                self.assertEqual(files[f"{card}/{r}"]["role"], "editable", r)
            self.assertEqual(files[f"{staged}/src/lib.rs"]["text"], "// decoy task form\n")
            self.assertEqual(files[f"{card}/src/lib.rs"]["text"], "// a decoy delivery\n")
            # the command's --lab-task names the staged directory, which validates
            m = sandbox.validate(raw, root, check_image=False)
            self.assertEqual(m.commands[0], tuple(gate(card, "--lab-task", staged)))
        finally:
            import shutil
            shutil.rmtree(work, ignore_errors=True)
            sc.cleanup(root)


class AtACommit(unittest.TestCase):
    def test_every_staged_course_file_is_read_at_the_commit(self):
        raw, _ = sandbox.build_verify(ROOT, PY, gate(PY), rev="HEAD")
        at = sandbox._tree_files(ROOT, ".", "HEAD")
        for f in raw["file"]:
            if "text" in f:
                continue
            self.assertEqual(f.get("rev"), "HEAD", f["dst"])
            self.assertIn(f["src"], at)
            blob = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{f['src']}"],
                                  capture_output=True, check=True).stdout
            self.assertEqual(hashlib.sha256(blob).hexdigest(), f["sha256"], f["src"])
        sandbox.validate(raw, ROOT)


class MemoryCap(unittest.TestCase):
    def test_a_requested_cap_is_held_to_the_languages_bound(self):
        card = card_path()
        work = Path(tempfile.mkdtemp(prefix="dvl0-cap-"))
        try:
            (work / card).parent.mkdir(parents=True)
            (work / card).write_text((ROOT / card).read_text())
            raw, _ = sandbox.build_verify(ROOT, work / card, gate(card), mem_gb=16)
        finally:
            import shutil
            shutil.rmtree(work, ignore_errors=True)
        self.assertEqual(raw["limits"]["mem_gb"], sandbox.memory_bound_gb("verify", ["dafny"]))
        raw, _ = sandbox.build_verify(ROOT, PY, gate(PY), mem_gb=2)
        self.assertEqual(raw["limits"]["mem_gb"], 2.0)


if __name__ == "__main__":
    unittest.main()
