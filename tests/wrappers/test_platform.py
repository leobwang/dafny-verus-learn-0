"""Tests for the toolchain contract of DELTAS Δ503: the learner's dafny and verus
on PATH (D78), the version check that warns and continues (D79), the UNTRUSTED
marking of everything whose meaning depends on the exact toolchain, and the
small platform helper (dvl.host).

The mismatch cases run fake `dafny` and `verus` executables on PATH that answer
another version; nothing here runs a solver except the optional fingerprint.

Run: python3 -m unittest discover -s tests/wrappers -p 'test_platform.py'
"""

import importlib.machinery
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("DVL_SCRATCH", f"/tmp/dvl-test-{os.getuid()}")

from dvl import common  # noqa: E402
from dvl import host as plat  # noqa: E402

PINS = common.load_pins()


def load_script(name, modname):
    loader = importlib.machinery.SourceFileLoader(modname, str(ROOT / "scripts" / name))
    spec = importlib.util.spec_from_loader(modname, loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod            # dataclasses look their module up while it runs
    loader.exec_module(mod)
    return mod


def fake_tools(d, dafny_version="4.10.0+0000000", verus_version="0.2026.01.01.0000000",
               verus_commit="0" * 40, z3_dafny="Z3 version 4.8.5 - 64 bit"):
    """A release-zip-shaped fake Dafny (<d>/dafny/dafny, <d>/dafny/z3/bin/z3-4.12.1
    and z3-4.14.1) and a fake Verus (<d>/verus/verus, <d>/verus/z3); returns the
    PATH dirs."""
    d = Path(d)

    def sh(p, body):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("#!/bin/sh\n" + body)
        p.chmod(0o755)
    sh(d / "dafny" / "dafny", f'[ "$1" = --version ] && echo "{dafny_version}"\nexit 0\n')
    sh(d / "dafny" / "z3" / "bin" / "z3-4.12.1", f'echo "{z3_dafny}"\n')
    sh(d / "dafny" / "z3" / "bin" / "z3-4.14.1", 'echo "Z3 version 4.14.1 - 64 bit"\n')
    verus_json = json.dumps({"verus": {"version": verus_version, "commit": verus_commit}})
    sh(d / "verus" / "verus", f"echo '{verus_json}'\n")
    sh(d / "verus" / "z3", f'echo "{PINS["verus"]["solver_version"]}"\n')
    return [str(d / "dafny"), str(d / "verus")]


def env_with(path_dirs):
    env = {k: v for k, v in os.environ.items() if k != "DVL_TOOLCHAIN_DIR"}
    env["PATH"] = ":".join(path_dirs + [os.path.dirname(sys.executable), "/usr/bin", "/bin"])
    return env


def pin_fake_solvers(d):
    """Code that makes this process's pins name the fake solvers' sha256 for this
    platform (the fakes are shell scripts, never the release binaries)."""
    return ("import copy, hashlib\n_real = common.load_pins\n"
            "def _fake():\n    p = copy.deepcopy(_real())\n"
            "    for e in p['dafny']['solvers'].values():\n"
            f"        f = Path({str(d)!r}) / e['path']\n"
            "        e['sha256'] = {plat.current(): hashlib.sha256(f.read_bytes()).hexdigest()}\n"
            "    return p\ncommon.load_pins = _fake\n")


def run_isolated(code, path_dirs):
    """`code` (after `from dvl import common`) in a fresh process whose PATH leads
    with path_dirs and that has no DVL_TOOLCHAIN_DIR."""
    prog = (f"import sys; sys.path.insert(0, {str(ROOT / 'scripts')!r})\n"
            "from pathlib import Path\nfrom dvl import common\nfrom dvl import host as plat\n")
    return subprocess.run([sys.executable, "-B", "-c", prog + code], capture_output=True,
                          text=True, env=env_with(path_dirs))


class Helper(unittest.TestCase):
    def test_platform_answers(self):
        self.assertEqual(plat.SUPPORTED, ("linux-x86_64", "macos-arm64"))
        if sys.platform.startswith("linux"):
            self.assertEqual(plat.detach_argv(), ["setsid", "-f"])
            self.assertEqual(plat.default_env("/h"), {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8",
                                                      "LC_ALL": "C.UTF-8", "HOME": "/h"})
            self.assertEqual(common.rust_toolchain(), PINS["verus"]["rust_toolchain"])
        self.assertTrue(common.rust_toolchain().startswith("1.98.1-"))

    def test_no_dvl_module_shadows_the_standard_library(self):
        """A dvl file run as a script puts scripts/dvl/ first on sys.path, so a
        module there named like a stdlib one (platform.py) breaks every import of it."""
        names = {p.stem for p in (ROOT / "scripts" / "dvl").glob("*.py")}
        self.assertEqual(names & set(sys.stdlib_module_names), set())

    def test_no_memory_mechanism_is_left(self):
        src = (ROOT / "scripts" / "dvl" / "common.py").read_text()
        for gone in ("systemd-run", "dvl0.slice", "MemoryMax", "_slice_ready", "cap_argv",
                     "watchdog"):
            self.assertNotIn(gone, src)
        self.assertFalse((ROOT / "scripts" / "dvl" / "platforms.toml").exists())


class VersionCheck(unittest.TestCase):
    def test_a_mismatch_warns_once_continues_and_marks_the_run(self):
        with tempfile.TemporaryDirectory() as d:
            p = run_isolated(
                "tc = common.toolchain()\ncommon.toolchain()\n"
                "print('dafny', tc['dafny'].name, tc['dafny_z3'].name)\n"
                "print('tools', sorted(common.untrusted()))\n"
                "print('note', common.trust_note().startswith('UNTRUSTED'))\n", fake_tools(d))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("dafny dafny z3-4.12.1", p.stdout)
        self.assertIn("tools ['dafny', 'verus']", p.stdout)
        self.assertIn("note True", p.stdout)
        self.assertIn("WARNING: dafny is not the pinned toolchain", p.stderr)
        self.assertIn("'4.10.0+0000000'", p.stderr)
        self.assertIn(PINS["dafny"]["version_output"], p.stderr)
        self.assertEqual(p.stderr.count("WARNING: dafny"), 1, "warned more than once")

    def test_the_pinned_versions_are_trusted(self):
        with tempfile.TemporaryDirectory() as d:
            p = run_isolated(
                pin_fake_solvers(d) + "common.toolchain()\nprint(repr(common.trust_note()))\n",
                fake_tools(d, PINS["dafny"]["version_output"], PINS["verus"]["version"],
                           PINS["verus"]["commit"], PINS["dafny"]["solver_version"]))
        self.assertEqual(p.stdout.strip(), "''", p.stderr)
        self.assertNotIn("WARNING", p.stderr)

    def test_vcheck_versions_reports_and_exits_1_on_a_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            p = subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "vcheck"),
                                "--versions"], capture_output=True, text=True,
                               env=env_with(fake_tools(d)))
        self.assertEqual(p.returncode, 1, p.stderr)
        self.assertIn("vcheck --versions: dafny: MISMATCH", p.stdout)
        self.assertIn("UNTRUSTED toolchain", p.stdout)

    def test_versions_and_runs_see_the_same_solver_hashes(self):
        """One check: `vcheck --versions` and a run that names a bundled solver
        report the same sha256 mismatches (the Mac's step-1 self-test found
        them disagreeing: --versions trusted, the run UNTRUSTED)."""
        good = (PINS["dafny"]["version_output"], PINS["verus"]["version"],
                PINS["verus"]["commit"], PINS["dafny"]["solver_version"])
        code = ("vc = __import__('importlib.machinery').machinery.SourceFileLoader("
                f"'vc', {str(ROOT / 'scripts' / 'vcheck')!r})\n"
                "import importlib.util as u\nspec = u.spec_from_loader('vc', vc)\n"
                "m = u.module_from_spec(spec); sys.modules['vc'] = m; vc.exec_module(m)\n"
                "rc = m.versions_mode()\nfrom dvl import dafny as D\n"
                "D.solver_path('4.14.1'); D.solver_path('4.12.1')\n"
                "print('rc', rc)\nprint('run', sorted(common.untrusted()))\n")
        with tempfile.TemporaryDirectory() as d:
            unpinned = run_isolated(code, fake_tools(d, *good))
            pinned = run_isolated(pin_fake_solvers(d) + code, fake_tools(d, *good))
        self.assertIn("rc 1", unpinned.stdout, unpinned.stderr)
        self.assertIn("run ['dafny']", unpinned.stdout)
        for name in ("4.12.1", "4.14.1"):
            self.assertIn(f"MISMATCH — the solver {name} at", unpinned.stdout)
        self.assertEqual(unpinned.stderr.count("WARNING: dafny"), 1, unpinned.stderr)
        self.assertIn("rc 0", pinned.stdout, pinned.stderr)
        self.assertIn("run []", pinned.stdout)
        self.assertIn("every tool is the pinned one", pinned.stdout)

    def test_a_tool_missing_from_path_is_a_toolchain_error(self):
        p = run_isolated("try:\n    common.toolchain('verus')\n"
                         "except common.ToolchainError as e:\n    print('missing', e)\n", [])
        self.assertIn("missing `verus` is not on PATH", p.stdout, p.stderr)


class Marking(unittest.TestCase):
    """D79: the gate verdict, pins, first tries and brittleness say UNTRUSTED."""

    def setUp(self):
        self.saved = {k: list(v) for k, v in common._MISMATCH.items()}
        self.vc = load_script("vcheck", "vcheck_t")
        self.res = common.Result(lang="dafny", target="t.dfy", exit_code=0, verdict="verified",
                                 stage="verify", verified_count=1)

    def tearDown(self):
        common._MISMATCH.clear()
        common._MISMATCH.update(self.saved)

    def test_trusted_output_is_unchanged(self):
        common._MISMATCH.clear()
        self.assertNotIn("untrusted", self.vc.result_json(self.res))
        self.assertEqual(common.trust_note(), "")

    def test_untrusted_json_and_text(self):
        common._MISMATCH["dafny"] = ["dafny --version: found 'x', pinned 'y'"]
        d = self.vc.result_json(self.res)
        self.assertTrue(d["untrusted"].startswith("UNTRUSTED (toolchain version mismatch:"))
        out = io.StringIO()
        with redirect_stdout(out):
            self.vc.print_result(self.res, ROOT, "gate")
        self.assertIn("vcheck: UNTRUSTED", out.getvalue())
        self.assertEqual(self.vc.untrusted_note("v"), "")   # only the mismatched tool

    def test_first_tries_on_an_untrusted_toolchain_are_marked(self):
        common._MISMATCH["verus"] = ["verus --version: found 'x', pinned 'y'"]
        with tempfile.TemporaryDirectory() as root:
            out = io.StringIO()
            with redirect_stdout(out):
                self.vc.append_calib(Path(root), "Q01", [["Q01.P1d", "predict", "pass",
                                                           "2026-10-21", "ab" * 32]])
            rec = self.vc.read_calib(Path(root), "Q01")["Q01.P1d"]
            self.assertTrue(rec["untrusted"])
            self.assertIn("marked untrusted", out.getvalue())
            line = self.vc.calib_path(Path(root), "Q01").read_text().strip()
            self.assertTrue(line.endswith("\tuntrusted"))

    def test_pins_and_firsttry_close_with_the_note(self):
        common._MISMATCH["dafny"] = ["dafny --version: found 'x', pinned 'y'"]
        for name in ("pins.py", "firsttry.py"):
            mod = load_script(name, f"t_{name[:-3]}")
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                mod.main(["--definitely-not-an-option"])
            self.assertIn("UNTRUSTED", out.getvalue(), name)


class Fingerprint(unittest.TestCase):
    def test_reference_fingerprints_cover_the_pinned_solvers(self):
        exp = ROOT / "tests" / "fingerprint" / "z3" / "expected"
        for v in ("4.12.1", "4.14.1", "4.16.0"):
            self.assertEqual(len((exp / f"{v}.tsv").read_text().splitlines()), 29, v)

    @unittest.skipUnless(shutil.which("dafny") and shutil.which("verus"), "no tools on PATH")
    def test_vcheck_fingerprint_is_a_diagnostic(self):
        p = subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "vcheck"),
                            "--fingerprint"], capture_output=True, text=True, timeout=1800)
        self.assertIn("a diagnostic, never a gate", p.stdout, p.stderr)
        self.assertEqual(p.returncode, 0, p.stdout)


if __name__ == "__main__":
    unittest.main()


class PerPlatformPins(unittest.TestCase):
    """Δ503: the bundled solvers' and the age binary's sha256 per supported
    platform; a platform's value holds there and nowhere else."""

    MAC = {"4.12.1": "7d15df1e4ba8f60b0808dce02ec85e0dd6dac4b975231a2f7b35fe8789464208",
           "4.14.1": "2fb05b03121f522fdea1ee523c73b9341d327814c81f051a887e97e931af06bf"}

    def test_every_solver_names_one_sha256_per_supported_platform(self):
        for name, e in PINS["dafny"]["solvers"].items():
            with self.subTest(solver=name):
                self.assertEqual(sorted(e["sha256"]), sorted(plat.SUPPORTED))
                for v in e["sha256"].values():
                    self.assertRegex(v, r"^[0-9a-f]{64}$")
                self.assertEqual(e["sha256"]["macos-arm64"], self.MAC[name])

    def test_the_macos_values_hold_on_macos_arm64_only(self):
        for name, e in PINS["dafny"]["solvers"].items():
            self.assertEqual(common.pinned_solver_sha256(e, "macos-arm64"), self.MAC[name])
            self.assertNotEqual(common.pinned_solver_sha256(e, "linux-x86_64"), self.MAC[name])
            self.assertIsNone(common.pinned_solver_sha256(e, "unsupported-linux-aarch64"))
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "z3-4.14.1"
            f.write_bytes(b"a macOS build")
            digest = __import__("hashlib").sha256(f.read_bytes()).hexdigest()
            entry = {"sha256": {"macos-arm64": digest, "linux-x86_64": "0" * 64}}
            self.assertIsNone(common.solver_hash_mismatch("4.14.1", f, entry, "macos-arm64"))
            for other in ("linux-x86_64", "unsupported-linux-aarch64"):
                with self.subTest(platform=other):
                    m = common.solver_hash_mismatch("4.14.1", f, entry, other)
                    self.assertIn(f"has sha256 {digest}", m)
                    self.assertIn(other, m)

    def test_a_plain_pin_holds_on_linux_x86_64_only(self):
        self.assertEqual(plat.pinned("x", "linux-x86_64"), "x")
        self.assertIsNone(plat.pinned("x", "macos-arm64"))
        self.assertEqual(plat.pinned({"macos-arm64": "m"}, "macos-arm64"), "m")
        self.assertIsNone(plat.pinned({"macos-arm64": "m"}, "linux-x86_64"))

    def test_the_age_pins_name_both_platforms_and_every_reader_agrees(self):
        from dvl import sandbox
        sys.path.insert(0, str(ROOT / "harness"))
        from fvh import statements
        mac = "4012dfc2725883beafb710894af4f599b7a94f8c8e0f51f02cc96ab8df33915e"
        linux = "eb7dd1b518f0a307c99cd97782623c5321da049154b04acd2d98d21aa7bc9b2c"
        pins = sandbox.truth_pins(ROOT)
        self.assertTrue(pins)
        for lab, pin in pins.items():
            with self.subTest(lab=lab):
                self.assertEqual(pin["age_sha256"], {"linux-x86_64": linux, "macos-arm64": mac})
                for platform, want in (("linux-x86_64", linux), ("macos-arm64", mac),
                                       ("unsupported-linux-aarch64", None)):
                    self.assertEqual(sandbox.age_sha256(pin, platform), want)
                    self.assertEqual(statements._pinned(pin["age_sha256"], platform), want)
        self.assertEqual(statements._platform(), plat.current())
