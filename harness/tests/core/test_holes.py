"""The frozen core's own tests: fvh.holes, the Python hole form (QPLAN §8.0, §11.8).

Every source below is invented for the test (module id Q98 is no course
module); none is course content.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from fvh import holes
from fvh.holes import Hole

HARNESS = Path(__file__).resolve().parents[2]


def src(*lines):
    return "\n".join(lines) + "\n"


HOLLOW = src(
    '"""A module."""',
    "import math",
    "",
    "# item: Q98.P1py S13 verdict",
    "# A prediction; no code.",
    "# SLOT: CHECK P1py",
    "",
    "# item: Q98.H1py S9",
    "def first(xs: list) -> int:",
    '    """The first element."""',
    '    raise NotImplementedError("Q98.H1py")',
    "",
    "",
    "# item: Q98.H2py S13",
    "def second(xs):",
    '    raise NotImplementedError("Q98.H2py")',
    "",
    "",
    "# item: Q98.H3py S13",
    "class Box:",
    "    @staticmethod",
    "    def area(w, h):",
    '        """w * h"""',
    '        raise NotImplementedError("Q98.H3py")',
)


def test_counts_each_hole_with_its_item_name_and_def_line():
    assert holes.count_holes(HOLLOW) == [
        Hole("Q98.H1py", "first", 9),
        Hole("Q98.H2py", "second", 15),
        Hole("Q98.H3py", "Box.area", 22),
    ]
    assert holes.lint(HOLLOW) == []


def test_markers_are_comments_only():
    text = src('"""', "# item: Q98.H9py S1", '"""', "# item: Q98.H1py S2", "x = 1")
    assert holes.markers(text) == [holes.Marker(4, "Q98.H1py")]


def test_a_filled_function_is_no_hole():
    text = src("# item: Q98.H1py S9", "def first(xs):", '    """Doc."""', "    return xs[0]")
    assert holes.count_holes(text) == []
    assert holes.lint(text) == []


@pytest.mark.parametrize("body,kind", [
    ('    x = "raise NotImplementedError(\'Q98.H1py\')"\n    return x', None),
    ("    # raise NotImplementedError('Q98.H1py')\n    return 0", None),
    ("    raise NotImplementedError", "bare-raise"),
    ("    raise NotImplementedError()", "bare-raise"),
    ('    raise NotImplementedError("Q98.H2py")', "hole-id-mismatch"),
    ('    raise NotImplementedError(f"Q98.H1py")', "hole-form"),
    ('    raise NotImplementedError("Q98.H1py", 1)', "hole-form"),
    ('    raise NotImplementedError("Q98.H1py") from None', "hole-form"),
    ('    raise builtins.NotImplementedError("Q98.H1py")', "hole-form"),
    ('    raise RuntimeError("Q98.H1py")', "renamed-exception"),
    ('    raise NotImplemented("Q98.H1py")', "renamed-exception"),
    ('    x = 1\n    raise NotImplementedError("Q98.H1py")', "hole-not-alone"),
    ('    if xs:\n        raise NotImplementedError("Q98.H1py")\n    return 0', "hole-not-alone"),
    ("    pass", "empty-body"),
    ("    ...", "empty-body"),
])
def test_hole_like_bodies_are_not_counted_and_the_lint_names_them(body, kind):
    text = "# item: Q98.H1py S9\ndef first(xs):\n" + body + "\n"
    assert holes.count_holes(text) == []
    kinds = [f.kind for f in holes.lint(text)]
    assert kinds == ([] if kind is None else [kind])


def test_a_raise_outside_every_item_block_is_no_hole():
    text = src("def helper():", '    raise NotImplementedError("Q98.H1py")')
    assert holes.count_holes(text) == []
    assert [f.kind for f in holes.lint(text)] == ["hole-id-mismatch"]


def test_a_docstring_only_body_under_an_h_marker_is_flagged():
    text = src("# item: Q98.H1py S9", "def first(xs):", '    """Only a docstring."""')
    assert [f.kind for f in holes.lint(text)] == ["empty-body"]


def test_pass_outside_an_h_block_is_fine():
    text = src("# item: Q98.W1py S9", "def given():", "    pass")
    assert holes.lint(text) == []


def test_two_holes_of_one_item_are_counted_and_flagged():
    text = src("# item: Q98.H1py S9",
               "def a():", '    raise NotImplementedError("Q98.H1py")',
               "def b():", '    raise NotImplementedError("Q98.H1py")')
    assert len(holes.count_holes(text)) == 2
    assert [f.kind for f in holes.lint(text)] == ["duplicate-hole", "duplicate-hole"]


def test_decorated_and_async_functions_and_nested_ones():
    text = src("# item: Q98.H1py S9",
               "@functools.cache",
               "async def a():", '    raise NotImplementedError("Q98.H1py")',
               "",
               "# item: Q98.H2py S9",
               "def outer():",
               "    def inner():", '        raise NotImplementedError("Q98.H2py")',
               "    return inner")
    assert holes.count_holes(text) == [Hole("Q98.H1py", "a", 3),
                                       Hole("Q98.H2py", "outer.<locals>.inner", 8)]


def test_malformed_markers_are_flagged_and_open_no_block():
    text = src("#item: Q98.H1py S9", "def first():", '    raise NotImplementedError("Q98.H1py")')
    assert holes.count_holes(text) == []
    assert sorted(f.kind for f in holes.lint(text)) == ["hole-id-mismatch", "malformed-marker"]


def test_a_source_that_does_not_parse():
    with pytest.raises(SyntaxError):
        holes.count_holes("def broken(:\n")
    assert [f.kind for f in holes.lint("def broken(:\n")] == ["parse-error"]


# --- the command line ------------------------------------------------------------------

def run_cli(*args):
    return subprocess.run([sys.executable, "-B", "-m", "fvh.holes", *args], cwd=HARNESS,
                          capture_output=True, text=True, timeout=60)


def test_cli_prints_one_line_per_file(tmp_path):
    a, b = tmp_path / "a.py", tmp_path / "b.py"
    a.write_text(HOLLOW, encoding="utf-8")
    b.write_text("x = 1\n", encoding="utf-8")
    p = run_cli(str(a), str(b))
    assert p.returncode == 0, p.stderr
    assert p.stdout.splitlines() == [f"{a}: 3 hole(s)", f"{b}: 0 hole(s)"]


def test_cli_json_and_a_broken_file(tmp_path):
    a, bad = tmp_path / "a.py", tmp_path / "bad.py"
    a.write_text(HOLLOW, encoding="utf-8")
    bad.write_text("def broken(:\n", encoding="utf-8")
    p = run_cli("--json", str(a), str(bad))
    assert p.returncode == 1
    report = json.loads(p.stdout)
    assert [h["item"] for h in report[0]["holes"]] == ["Q98.H1py", "Q98.H2py", "Q98.H3py"]
    assert report[1]["file"] == str(bad) and "does not parse" in report[1]["error"]


def test_cli_usage_error():
    assert run_cli().returncode == 2
