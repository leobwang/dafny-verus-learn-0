"""The harness project's layout (QPLAN §11.8; design §14.2 rule 5): one pytest
process imports the frozen core and both learner packages, from this project."""

import importlib
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[2]


def test_one_process_imports_fvh_fvh_q_and_fvh_r():
    mods = {name: importlib.import_module(name)
            for name in ("fvh", "fvh.stats", "fvh.records", "fvh.holes", "fvh_q", "fvh_r")}
    where = {name: Path(m.__file__).resolve() for name, m in mods.items()}
    assert where["fvh"] == HARNESS / "fvh" / "__init__.py"
    assert where["fvh_q"] == HARNESS / "q" / "fvh_q" / "__init__.py"
    assert where["fvh_r"] == HARNESS / "r" / "fvh_r" / "__init__.py"


def test_the_core_depends_on_the_standard_library_only():
    """Every module of the core, its subpackages included (DV4's fvh.tools),
    imports the standard library and the core itself only."""
    import ast
    import sys
    allowed = set(sys.stdlib_module_names) | {"fvh"}
    files = sorted((HARNESS / "fvh").rglob("*.py"))
    assert HARNESS / "fvh" / "tools" / "runners.py" in files
    for f in files:
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                heads = {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                heads = {(node.module or "").split(".")[0]}
            else:
                continue
            assert heads <= allowed, (f.relative_to(HARNESS).as_posix(), heads)
