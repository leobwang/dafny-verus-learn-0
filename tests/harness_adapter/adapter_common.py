"""Shared helpers for the Python adapter's suites (test_python_static.py,
test_python_tool.py): scripts/dvl/python.py over a throwaway course root.

build_root() makes the root: a minimal MODULES.toml whose one record (the
invented module Q98) lists the invented learner file in `harness`, this
checkout's harness project and frozen core (pyproject.toml, uv.lock, fvh/),
the empty package files, the invented learner file with two holes, its
invented acceptance tests, and an invented reference twin under
Solutions/harness/ with `# triv:` bodies. Nothing here is course content or an
answer of a course item.

This module holds no TestCase: unittest discovery imports it and finds nothing.
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
os.environ.setdefault("DVL_SCRATCH", f"/tmp/dvl-test-{os.getuid()}")
TMP_BASE = os.environ.get("DVL_TEST_TMP") or None

from dvl import python as P  # noqa: E402

# The vcheck whose Python branch the tool suite exercises (this checkout's, unless
# DVL_ADAPTER_SCRIPTS names another scripts/ directory, e.g. a patched copy).
TOOL_SCRIPTS = Path(os.environ.get("DVL_ADAPTER_SCRIPTS") or SCRIPTS)

LEARNER_REL = "harness/q/fvh_q/q98_demo.py"
TESTS_REL = "harness/tests/q/test_q98_demo.py"
TWIN_REL = "Solutions/" + LEARNER_REL

REGISTRY = """schema = 1

[[module]]
id = "Q98"
status = "authoring"
harness = ["harness/q/fvh_q/q98_demo.py"]

[[module]]
id = "Q97"
status = "planned"
harness = ["harness/q/fvh_q/q97_later.py"]
"""

LEARNER = '''"""Q98 — an invented module for the adapter's tests (not course content)."""

from fvh import stats

# item: Q98.P1py S13 verdict
# An invented prediction (no code).
# SLOT: CHECK P1py

# item: Q98.H1py S9
def double(x: int) -> int:
    """Twice x."""
    raise NotImplementedError("Q98.H1py")


# item: Q98.H2py S13
def significant(pvalues: list) -> list:
    """Holm's rejections at level 0.05, by composing fvh.stats."""
    raise NotImplementedError("Q98.H2py")
'''

TWIN = '''"""Q98 — an invented module for the adapter's tests (Reference Solution)."""

from fvh import stats

# item: Q98.P1py S13 verdict
# An invented prediction (no code).
# CHECK P1py

# item: Q98.H1py S9
def double(x: int) -> int:
    """Twice x."""
    y = x
    return x + y
# triv: return 0


# item: Q98.H2py S13
def significant(pvalues: list) -> list:
    """Holm's rejections at level 0.05, by composing fvh.stats."""
    return stats.holm(pvalues)
# triv: flags = [False] * len(pvalues)
# triv: return flags
'''

TESTS = '''"""Invented acceptance tests for the adapter's suites."""

from fvh import stats
from fvh_q import q98_demo as d


def test_double():
    assert d.double(21) == 42


def test_double_zero():
    assert d.double(0) == 0


def test_significant():
    assert d.significant([0.01, 0.2]) == stats.holm([0.01, 0.2]) == [True, False]
'''


def tmpdir(prefix):
    if TMP_BASE:
        Path(TMP_BASE).mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=prefix, dir=TMP_BASE))


def build_root(base, learner=LEARNER, twin=TWIN, tests=TESTS):
    """A throwaway course root under `base` (see the module doc)."""
    root = Path(base) / "root"
    h = root / "harness"
    (h / "q" / "fvh_q").mkdir(parents=True)
    (h / "r" / "fvh_r").mkdir(parents=True)
    (h / "tests" / "q").mkdir(parents=True)
    for f in ("pyproject.toml", "uv.lock"):
        shutil.copyfile(ROOT / "harness" / f, h / f)
    shutil.copytree(ROOT / "harness" / "fvh", h / "fvh",
                    ignore=shutil.ignore_patterns("__pycache__"))
    (h / "q" / "fvh_q" / "__init__.py").write_text("", encoding="utf-8")
    (h / "r" / "fvh_r" / "__init__.py").write_text("", encoding="utf-8")
    (root / "MODULES.toml").write_text(REGISTRY, encoding="utf-8")
    (root / LEARNER_REL).write_text(learner, encoding="utf-8")
    (root / TESTS_REL).write_text(tests, encoding="utf-8")
    t = root / TWIN_REL
    t.parent.mkdir(parents=True)
    t.write_text(twin, encoding="utf-8")
    return root


def remove(path):
    shutil.rmtree(path, ignore_errors=True)


def vcheck_has_python(scripts=None):
    """True when scripts/vcheck carries the Python branch (DV4 wiring)."""
    try:
        text = (Path(scripts or TOOL_SCRIPTS) / "vcheck").read_text(encoding="utf-8")
    except OSError:
        return False
    return "MODULE_LANGS" in text and "dvl import python" in text


def has_uv():
    try:
        P.uv_binary()
        return True
    except P.Refused:
        return False
