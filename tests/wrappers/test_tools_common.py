"""Shared helpers for the tools suites (test_tools_static.py, test_tools_tool.py).

build_root() makes a throwaway course root: the committed MODULES.toml with every
real module set back to planned and Q04's table replaced by the synthetic armed Q04
(tests/course_map/armed/Q04.toml), the
armed tree (tests/course_map/armed/tree/), the tools overlay
(tests/wrappers/fixtures/tools/overlay/: invented specimens, a check unit, a Verus
test module and an exit file; nothing here is course content or an answer), the
real dafny/options/, instructor/gradebook.md and the contract skill's list of
hand-written agentic exercises (chapter_lint.py reads it), and the units
scripts/gen_units.py generates for it. tool() runs one of the scripts against such a root.

This module holds no TestCase: unittest discovery imports it and finds nothing.
"""

import contextlib
import importlib.machinery
import io
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
ARMED = ROOT / "tests" / "course_map" / "armed"
OVERLAY = ROOT / "tests" / "wrappers" / "fixtures" / "tools" / "overlay"
os.environ.setdefault("DVL_SCRATCH", f"/tmp/dvl-test-{os.getuid()}")
TMP_BASE = os.environ.get("DVL_TEST_TMP") or None

# Files the overlay adds to Q04's record: (field, path, import tier or None).
EXTRA = (("exercises", "dafny/checks/Q04_checks.dfy", "core"),
         ("exercises", "verus/q/q04_proof_craft/src/tests.rs", "prelude"))


def load_script(name):
    """A script of scripts/ as a module (vcheck, vaudit and specfreeze have no .py)."""
    if name in sys.modules:
        return sys.modules[name]
    path = SCRIPTS / name if (SCRIPTS / name).exists() else SCRIPTS / f"{name}.py"
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    loader.exec_module(mod)
    return mod


def _table_span(text, mid):
    s = text.index(f'[[module]]\nid = "{mid}"')
    e = text.find("\n[[", s + 1)
    return s, (len(text) if e < 0 else e + 1)


def _setf(text, mid, key, value):
    s, e = _table_span(text, mid)
    seg, n = re.subn(rf"(?m)^{re.escape(key)} = .*$", lambda _: f"{key} = {value}",
                     text[s:e], count=1)
    assert n == 1, (mid, key)
    return text[:s] + seg + text[e:]


def plan_real_modules(text):
    """The registry text with every real module set back to `planned`. DV2
    armed Q01-Q03, but a throwaway root holds none of their files: only the
    synthetic Q04 is armed there, as every case of these suites assumes."""
    return re.sub(r'(?m)^status = "(authoring|shipped)"$', 'status = "planned"', text)


def _declare_given(text, mid, files):
    """text with mid declaring the given files of its layer, unless its record
    already does (DV2 declares L1 in Q01 and L2 in Q02, as sub-tables)."""
    s, e = _table_span(text, mid)
    if all(f'"{f}"' in text[s:e] for f in files):
        return text
    return _setf(text, mid, "imports", "{ " + ", ".join(
        f'"{f}" = "{"core" if f.endswith(".dfy") else "prelude"}"' for f in files) + " }")


def armed_registry(overlay=True):
    base = plan_real_modules((ROOT / "MODULES.toml").read_text(encoding="utf-8"))
    table = (ARMED / "Q04.toml").read_text(encoding="utf-8")
    if overlay:
        for field, path, tier in EXTRA:
            table = re.sub(rf'(?m)^({field} = \[)', rf'\1"{path}", ', table, count=1)
            if tier:
                table = table.replace("[module.imports]\n",
                                      f'[module.imports]\n"{path}" = "{tier}"\n', 1)
    s, e = _table_span(base, "Q04")
    text = base[:s] + table + base[e:]
    text = _declare_given(text, "Q01", ("dafny/given/Q/QG_L1_BigNat.dfy",
                                        "verus/given/qg_bignat_l1/src/lib.rs"))
    text = _declare_given(text, "Q02", ("dafny/given/Q/QG_L2_BigNat.dfy",
                                        "verus/given/qg_bignat_l2/src/lib.rs"))
    tomllib.loads(text)
    return text


def build_root(overlay=True, git=False):
    """A throwaway course root (see the module docstring). git=True commits it
    on `main` and leaves HEAD on a new branch `work` (the shipped baseline)."""
    root = Path(tempfile.mkdtemp(prefix="dvl-tools-root-", dir=TMP_BASE))
    (root / "MODULES.toml").write_text(armed_registry(overlay), encoding="utf-8")
    shutil.copytree(ROOT / "dafny" / "options", root / "dafny" / "options")
    shutil.copytree(ARMED / "tree", root, dirs_exist_ok=True)
    if overlay:
        shutil.copytree(OVERLAY, root, dirs_exist_ok=True)
    (root / "instructor").mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "instructor" / "gradebook.md", root / "instructor" / "gradebook.md")
    hand = Path(".claude/skills/contract/hand_written.toml")
    (root / hand.parent).mkdir(parents=True)
    shutil.copyfile(ROOT / hand, root / hand)
    import gen_units
    data = tomllib.loads((root / "MODULES.toml").read_text(encoding="utf-8"))
    with contextlib.redirect_stdout(io.StringIO()):
        errs, _, _ = gen_units.write(root, data)
    assert not errs, errs
    if git:
        g = lambda *a: subprocess.run(["git", "-C", str(root), *a], check=True,  # noqa: E731
                                      capture_output=True, text=True)
        g("init", "-q", "-b", "main")
        g("-c", "user.email=t@example.invalid", "-c", "user.name=t", "add", "-A")
        g("-c", "user.email=t@example.invalid", "-c", "user.name=t", "commit", "-q", "-m",
          "shipped")
        g("switch", "-q", "-c", "work")
    return root


def tool(script, *args, root=None, env=None, timeout=1800):
    """Run scripts/<script> with --root; returns (exit code, stdout, stderr).

    The author self-gate's outcome depends only on the root and on `env`: CI
    is dropped unless `env` sets it, and git discovery stops at the root's
    parent (GIT_CEILING_DIRECTORIES), so a throwaway root is "not inside a git
    checkout" (or its own checkout, git=True) wherever DVL_TEST_TMP, TMPDIR,
    DVL_SCRATCH or the cwd lie."""
    path = SCRIPTS / script
    argv = [sys.executable, "-B", str(path), *[str(a) for a in args]]
    if root is not None and script != "update_rubric_pins.sh":
        argv.append(f"--root={root}")
    if script.endswith(".sh"):
        argv = ["bash", str(path), *[str(a) for a in args]]
        if root is not None:
            argv += ["--root", str(root)]
    e = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    e.pop("CI", None)
    if root is not None:
        e["GIT_CEILING_DIRECTORIES"] = str(Path(root).resolve().parent)
    e.update(env or {})
    p = subprocess.run(argv, capture_output=True, text=True, env=e, timeout=timeout,
                       cwd=str(root or ROOT))
    return p.returncode, p.stdout, p.stderr


def replace_in(path, old, new, count=1):
    p = Path(path)
    t = p.read_text(encoding="utf-8")
    assert old in t, (path, old)
    p.write_text(t.replace(old, new, count), encoding="utf-8")


def remove_root(root):
    shutil.rmtree(root, ignore_errors=True)
