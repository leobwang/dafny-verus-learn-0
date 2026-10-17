"""The grader container's truth mode (DV4-PLAN §5.9, QPLAN §30 Q49): the host side
only, no Docker and no key. On throwaway roots with an invented lab pin, an
invented "sealed" archive (random bytes: nothing here is real hidden truth) and
an invented key file in a temporary HOME:

  - the manifest rules: a [truth] table only in a verification container,
    only with the pinned archive and sha256, and with the grader's commands
    and nothing else; the grader only with a [truth] table;
  - materialization copies the archive and the key unread (0400, in a 0700
    truth/ directory outside in/), the docker argv binds that directory
    read-only at /run/dvl-truth and nowhere else, and no host step runs a
    decryption (every subprocess the host side starts is recorded);
  - a study session's tools cannot reach the truth: the guard
    (.claude/hooks/spoiler-guard.sh), replayed in study mode against a decoy
    checkout (scripts/gen_hook_fixtures.py --fake-root), refuses the truth
    run's command line, a read of the archive, a read of the key and a
    decryption, and lets the plain access check through."""

import hashlib
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

from dvl import sandbox  # noqa: E402

LAB = "Q15"


def make_root(tmp, *, sha=None):
    """A copy of the course files a truth manifest needs, with an invented pin."""
    root = tmp / "course"
    for rel in ("MODULES.toml", "scripts", "dafny/given", "dafny/options", "sandbox/images.lock"):
        src = ROOT / rel
        dst = root / rel
        if src.is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    arc = root / "Hidden" / "labs" / LAB / "verdicts.tar.age"
    arc.parent.mkdir(parents=True)
    data = b"age-encryption.org/v1\n" + os.urandom(256)
    arc.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    (root / "sandbox" / "truth.toml").write_text(
        "schema = 1\n[[lab]]\n"
        f'id = "{LAB}"\narchive = "Hidden/labs/{LAB}/verdicts.tar.age"\n'
        'recipient = "age1invented"\nidentity = "~/.keys/invented.agekey"\n'
        f'sha256 = "{sha or digest}"\nfiles = 1\n')
    return root, digest


def truth_manifest(root, digest, **over):
    raw = {"schema": 1, "run_id": "truth-test", "module": LAB, "kind": "verify",
           "image": next(k for k in sandbox.read_images_lock(root) if k.startswith("dvl-toolchain@")),
           "network": "none", "limits": {"wall_clock_s": 600},
           "file": [{"src": "scripts/vcheck", "dst": "scripts/vcheck", "role": "tool",
                     "sha256": hashlib.sha256((root / "scripts/vcheck").read_bytes()).hexdigest()}],
           "return": [], "command": [{"argv": [sandbox.TRUTHCHECK, "manifest", LAB]}],
           "truth": {"lab": LAB, "archive": f"Hidden/labs/{LAB}/verdicts.tar.age",
                     "sha256": digest}}
    raw.update(over)
    return raw


class TruthManifest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dvl0-truth-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root, self.digest = make_root(self.tmp)

    def problems(self, raw):
        try:
            sandbox.validate(raw, self.root)
        except sandbox.ManifestError as e:
            return e.problems
        return []

    def test_the_pinned_archive_validates(self):
        m = sandbox.validate(truth_manifest(self.root, self.digest), self.root)
        self.assertEqual(m.truth["lab"], LAB)
        self.assertEqual(m.doc()["truth"]["sha256"], self.digest)

    def test_another_archive_or_sha_is_refused(self):
        raw = truth_manifest(self.root, "0" * 64)
        self.assertTrue(any("pins" in p for p in self.problems(raw)))
        raw = truth_manifest(self.root, self.digest)
        raw["truth"] = dict(raw["truth"], archive="Hidden/labs/Q15/other.tar.age")
        self.assertTrue(any("[truth]" in p for p in self.problems(raw)))
        (self.root / "Hidden/labs/Q15/verdicts.tar.age").write_bytes(b"changed")
        self.assertTrue(any("does not match" in p for p in
                            self.problems(truth_manifest(self.root, self.digest))))

    def test_only_a_verification_container_unseals(self):
        raw = truth_manifest(self.root, self.digest, kind="agent",
                             agent={"cli": "none", "model": "m", "turns": 1})
        self.assertTrue(any("verification container" in p for p in self.problems(raw)))

    def test_a_truth_run_runs_the_grader_and_nothing_else(self):
        raw = truth_manifest(self.root, self.digest)
        raw["command"].append({"argv": ["scripts/vcheck", "--gate", "scripts/vcheck"]})
        self.assertTrue(any("grader" in p for p in self.problems(raw)))
        raw = truth_manifest(self.root, self.digest)
        raw["command"] = [{"argv": [sandbox.TRUTHCHECK, "manifest", "Q99"]}]
        self.assertTrue(any("truthcheck" in p for p in self.problems(raw)))

    def test_the_grader_never_runs_without_a_truth_table(self):
        raw = truth_manifest(self.root, self.digest)
        del raw["truth"]
        self.assertTrue(any("only in a truth run" in p for p in self.problems(raw)))

    def test_no_file_entry_may_name_the_sealed_tree(self):
        raw = truth_manifest(self.root, self.digest)
        raw["file"].append({"src": f"Hidden/labs/{LAB}/verdicts.tar.age", "dst": "x.age",
                            "role": "task", "sha256": self.digest})
        self.assertTrue(any("refused source class" in p for p in self.problems(raw)))


class TruthStaging(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dvl0-truth-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root, self.digest = make_root(self.tmp)
        self.home = self.tmp / "home"
        (self.home / ".keys").mkdir(parents=True)
        (self.home / ".keys" / "invented.agekey").write_text("AGE-SECRET-KEY-INVENTED\n")

    def test_materialize_copies_the_archive_and_key_unread_and_binds_them_read_only(self):
        m = sandbox.validate(truth_manifest(self.root, self.digest), self.root)
        started = []
        real_run, real_popen = subprocess.run, subprocess.Popen

        def spy_run(argv, *a, **k):
            started.append(list(argv) if isinstance(argv, (list, tuple)) else [argv])
            return real_run(argv, *a, **k)

        def spy_popen(argv, *a, **k):
            started.append(list(argv) if isinstance(argv, (list, tuple)) else [argv])
            return real_popen(argv, *a, **k)
        with mock.patch.dict(os.environ, {"HOME": str(self.home)}), \
                mock.patch.object(subprocess, "run", spy_run), \
                mock.patch.object(subprocess, "Popen", spy_popen):
            run = sandbox.materialize(m, self.root, base=self.tmp / "runs")
            try:
                rep = sandbox.selftest(m, run, self.root)
                lines = sandbox.docker_argv(m, run.path)
                d = run.path / "truth"
                self.assertEqual(oct(d.stat().st_mode & 0o777), "0o500")
                self.assertEqual(sorted(x.name for x in d.iterdir()), ["archive.tar.age", "identity"])
                for f in d.iterdir():
                    self.assertEqual(oct(f.stat().st_mode & 0o777), "0o400")
                self.assertEqual(hashlib.sha256((d / "archive.tar.age").read_bytes()).hexdigest(),
                                 self.digest)
                self.assertFalse(any((run.inp / n).exists() for n in ("archive.tar.age", "identity")))
                self.assertTrue(rep["ok"], rep)
            finally:
                sandbox.remove_run(run)
        self.assertFalse(run.path.exists())
        for argv in started:
            self.assertFalse(any("age" == Path(str(a)).name or "--decrypt" in str(a) for a in argv),
                             argv)
        binds = [x for x in lines[0] if x.startswith("type=bind") and "dvl-truth" in x]
        self.assertEqual(binds, [f"type=bind,source={run.path}/truth,destination="
                                 f"{sandbox.TRUTH_DIR},readonly"])
        grader = [ln for ln in lines if sandbox.TRUTHCHECK in ln]
        self.assertEqual(len(grader), 1)
        self.assertEqual(grader[0][-3:], [sandbox.TRUTHCHECK, "manifest", LAB])

    def test_no_key_on_this_machine_refuses_the_run(self):
        m = sandbox.validate(truth_manifest(self.root, self.digest), self.root)
        with mock.patch.dict(os.environ, {"HOME": str(self.tmp / "nohome")}):
            with self.assertRaises(sandbox.SandboxError) as e:
                sandbox.materialize(m, self.root, base=self.tmp / "runs")
        self.assertIn("not on this machine", str(e.exception))
        self.assertEqual(list((self.tmp / "runs").iterdir()), [])

    def test_no_kept_run_directory_holds_the_key(self):
        """DV5c fix round: --materialize and --selftest-only never stage the truth."""
        for flag in ("--materialize", "--selftest-only"):
            p = subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "mksandbox-run"),
                                "--truth", "Hidden/labs/Q15/verdicts.tar.age", "--truth-check",
                                "manifest", flag], capture_output=True, text=True, timeout=60)
            self.assertEqual(p.returncode, 2, p.stderr)
            self.assertIn("refused with --truth", p.stderr)

    def test_the_real_pin_names_an_archive_in_the_checkout(self):
        pins = sandbox.truth_pins(ROOT)
        self.assertIn(LAB, pins)
        p = pins[LAB]
        self.assertTrue(p["archive"].startswith("Hidden/labs/"))
        self.assertTrue(p["identity"].startswith("~/.cache/dafny-verus-learn-0/"))
        f = ROOT / p["archive"]
        self.assertTrue(f.is_file())
        self.assertEqual(hashlib.sha256(f.read_bytes()).hexdigest(), p["sha256"])
        self.assertTrue(f.read_bytes().startswith(b"age-encryption.org/v1\n"))


class StudySessionGuard(unittest.TestCase):
    """A study session's tools cannot reach the truth (the guard replayed in study mode)."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="dvl0-truthguard-"))
        cls.root = cls.tmp / "study"
        cls.root.mkdir()
        gen = ROOT / "scripts" / "gen_hook_fixtures.py"
        cls.sid = "11111111-2222-4333-8444-555555555555"
        cls.slug = "".join(c if c.isascii() and c.isalnum() else "-" for c in str(cls.root))
        cls.home = cls.tmp / "home"
        subprocess.run([sys.executable, str(gen), "--fake-root", str(cls.root)], check=True,
                       capture_output=True)
        subprocess.run([sys.executable, str(gen), "--fake-home", str(cls.home),
                        f"--slug={cls.slug}", f"--sid={cls.sid}"], check=True,
                       capture_output=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def hook(self, tool, tool_input):
        inp = {"session_id": self.sid,
               "transcript_path": f"{self.home}/.claude/projects/{self.slug}/{self.sid}.jsonl",
               "tool_name": tool, "tool_input": tool_input, "cwd": str(self.root)}
        env = {k: v for k, v in os.environ.items()
               if k not in ("CLAUDE_CODE_SESSION_ID", "CLAUDE_CONFIG_DIR", "TMPDIR",
                            "SPOILER_GUARD_NO_JQ")}
        env.update(HOME=str(self.home), CLAUDE_PROJECT_DIR=str(self.root))
        p = subprocess.run(["bash", str(ROOT / ".claude" / "hooks" / "spoiler-guard.sh")],
                           input=json.dumps(inp), capture_output=True, text=True, env=env,
                           timeout=60)
        return p.returncode, p.stderr

    def test_the_truth_runs_command_line_is_refused(self):
        code, err = self.hook("Bash", {"command": "scripts/mksandbox-run --truth "
                                                  "Hidden/labs/Q15/verdicts.tar.age --truth-check "
                                                  "validate"})
        self.assertEqual(code, 2, err)
        self.assertIn("rule 1c", err)

    def test_reading_the_archive_or_the_key_is_refused(self):
        code, err = self.hook("Read", {"file_path": f"{self.root}/Hidden/labs/Q15/verdicts.tar.age"})
        self.assertEqual(code, 2, err)
        code, err = self.hook("Read", {"file_path": f"{self.home}/.cache/dafny-verus-learn-0/keys/"
                                                    "hidden-labs.agekey"})
        self.assertEqual(code, 2, err)

    def test_a_decryption_is_refused(self):
        code, err = self.hook("Bash", {"command": "age --decrypt --identity "
                                                  "~/.cache/dafny-verus-learn-0/keys/hidden-labs.agekey "
                                                  "Hidden/labs/Q15/verdicts.tar.age"})
        self.assertEqual(code, 2, err)

    def test_the_plain_access_check_still_passes(self):
        code, err = self.hook("Bash", {"command": "scripts/mksandbox-run --check-access"})
        self.assertEqual(code, 0, err)


if __name__ == "__main__":
    unittest.main()
