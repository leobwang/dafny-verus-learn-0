"""Δ277: `scripts/get_toolchain.sh claude [--check]`, the course's own copy of the pinned
Claude Code version file, on a throwaway HOME with an invented version file.

The pin is the apparatus file's [backend.claude] (FVH_APPARATUS names a test one). The
copy goes from ~/.local/share/claude/versions/<version> (the updater's directory) to
~/.local/share/dafny-verus-learn-0/claude/versions/<version>, read-only, after its
sha256 and `--version` line are checked; once there it survives the updater deleting
the original, and --check verifies it alone. Every refusal installs nothing."""
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "get_toolchain.sh"
VERSION = "9.9.9"
UPSTREAM = ".local/share/claude/versions"
STORE = ".local/share/dafny-verus-learn-0/claude/versions"
FAKE = f'#!/bin/sh\nif [ "$1" = --version ]; then echo "{VERSION} (Claude Code)"; fi\n'.encode()


class ClaudeCopy(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory(prefix="dvl-claude-pin-")
        self.addCleanup(t.cleanup)
        self.addCleanup(self.unlock, Path(t.name))
        self.home = Path(t.name) / "home"
        self.src = self.home / UPSTREAM / VERSION
        self.src.parent.mkdir(parents=True)
        self.src.write_bytes(FAKE)
        self.src.chmod(0o755)
        self.final = self.home / STORE / VERSION
        self.app = Path(t.name) / "apparatus.toml"
        self.pin()

    @staticmethod
    def unlock(base):
        for dirpath, dirnames, _ in os.walk(base):
            os.chmod(dirpath, 0o755)

    def pin(self, version=VERSION, binary=None, sha=None):
        binary = binary or f"~/{STORE}/{version}"
        sha = sha or hashlib.sha256(FAKE).hexdigest()
        self.app.write_text(f'schema = 1\n[backend.claude]\nversion = "{version}"\n'
                            f'binary = "{binary}"\nsha256 = "{sha}"\n')

    def run_script(self, *args):
        env = dict(os.environ, HOME=str(self.home), FVH_APPARATUS=str(self.app))
        return subprocess.run(["bash", str(SCRIPT), "claude", *args], env=env,
                              capture_output=True, text=True, timeout=60)

    def assert_nothing_installed(self):
        store = self.home / STORE
        left = sorted(p.name for p in store.iterdir()) if store.is_dir() else []
        self.assertEqual([x for x in left if x != ".lock"], [])

    def test_install_copies_verifies_and_is_idempotent(self):
        p = self.run_script()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, f"{self.final}\n")
        self.assertEqual(self.final.read_bytes(), FAKE)
        self.assertEqual(self.final.stat().st_mode & 0o777, 0o555)
        again = self.run_script()
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn("already installed and verified", again.stderr)
        self.assertEqual(again.stdout, f"{self.final}\n")

    def test_the_copy_survives_the_updater_deleting_the_original(self):
        self.assertEqual(self.run_script().returncode, 0)
        self.src.unlink()
        for args in ((), ("--check",)):
            p = self.run_script(*args)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(p.stdout, f"{self.final}\n")

    def test_check_without_a_copy_refuses_and_copies_nothing(self):
        p = self.run_script("--check")
        self.assertEqual((p.returncode, p.stdout), (1, ""))
        self.assertIn("get_toolchain.sh claude", p.stderr)
        self.assertFalse(self.final.exists())

    def test_a_modified_copy_fails_check_and_is_left_untouched(self):
        self.assertEqual(self.run_script().returncode, 0)
        self.final.chmod(0o755)
        self.final.write_bytes(FAKE + b"# edited\n")
        for args in ((), ("--check",)):
            p = self.run_script(*args)
            self.assertEqual((p.returncode, p.stdout), (1, ""), p.stderr)
        self.assertEqual(self.final.read_bytes(), FAKE + b"# edited\n")

    def test_a_source_with_another_sha256_installs_nothing(self):
        self.pin(sha="0" * 64)
        p = self.run_script()
        self.assertEqual((p.returncode, p.stdout), (1, ""))
        self.assertIn("pinned " + "0" * 64, p.stderr)
        self.assert_nothing_installed()

    def test_a_source_with_another_version_line_installs_nothing(self):
        self.src.write_bytes(FAKE.replace(VERSION.encode(), b"9.9.8"))
        self.pin(sha=hashlib.sha256(self.src.read_bytes()).hexdigest())
        p = self.run_script()
        self.assertEqual((p.returncode, p.stdout), (1, ""))
        self.assertIn("--version", p.stderr)
        self.assert_nothing_installed()

    def test_a_missing_source_names_the_way_out(self):
        self.src.unlink()
        p = self.run_script()
        self.assertEqual((p.returncode, p.stdout), (1, ""))
        self.assertIn("re-pin", p.stderr)
        self.assert_nothing_installed()

    def test_a_pin_on_the_updaters_directory_is_refused(self):
        self.pin(binary=f"~/{UPSTREAM}/{VERSION}")
        p = self.run_script()
        self.assertEqual((p.returncode, p.stdout), (1, ""))
        self.assertIn("course's copy", p.stderr)
        self.assertFalse((self.home / STORE).exists())

    def test_a_binary_naming_another_version_is_refused(self):
        self.pin(binary=f"~/{STORE}/9.9.8")
        p = self.run_script()
        self.assertEqual((p.returncode, p.stdout), (1, ""))
        self.assertFalse((self.home / STORE).exists())

    def test_usage(self):
        env = dict(os.environ, HOME=str(self.home), FVH_APPARATUS=str(self.app))
        for args in (["claude", "dafny"], ["claude", "--force"], ["--check"]):
            p = subprocess.run(["bash", str(SCRIPT), *args], env=env, capture_output=True,
                               text=True, timeout=60)
            self.assertEqual((p.returncode, p.stdout), (2, ""), args)

    def test_the_shipped_pin_names_the_course_store(self):
        import tomllib
        t = tomllib.loads((ROOT / "sandbox" / "apparatus.toml").read_text())["backend"]["claude"]
        self.assertEqual(t["binary"], f"~/{STORE}/{t['version']}")


if __name__ == "__main__":
    unittest.main()
