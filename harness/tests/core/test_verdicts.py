"""The frozen core's own tests: fvh.verdicts, the gate words and the cheat
classes as plain data (DV4-PLAN §3.7; spec §5.6)."""

import re
from pathlib import Path

import pytest

from fvh import verdicts
from fvh.verdicts import FAIL, GATE_WORDS, GRADER_ONLY, PASS, UNKNOWN, XCLASSES

ROOT = Path(__file__).resolve().parents[3]
SPEC = ROOT / "docs" / "design" / "spec4dafny-verus.md"


def test_the_gate_words():
    assert (PASS, FAIL, UNKNOWN) == ("PASS", "FAIL", "UNKNOWN")
    assert GATE_WORDS == (PASS, FAIL, UNKNOWN)


def test_the_classes_are_x01_to_x18_in_order():
    assert list(XCLASSES) == [f"X{n:02d}" for n in range(1, 19)]
    assert all(isinstance(t, str) and t.strip() == t and t for t in XCLASSES.values())


def test_the_titles_are_spec_5_6s_table_verbatim():
    text = SPEC.read_text(encoding="utf-8")
    start = text.index("### 5.6 Agentic challenges")
    section = text[start:text.index("\n### ", start + 10)]
    rows = {}
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 4:
            for k, v in ((cells[0], cells[1]), (cells[2], cells[3])):
                if re.fullmatch(r"X\d\d", k):
                    rows[k] = v
    assert rows == dict(XCLASSES)


def test_the_grader_only_classes():
    assert GRADER_ONLY == ("X07", "X08", "X14")
    assert set(GRADER_ONLY) <= set(XCLASSES)


def test_the_data_is_read_only():
    with pytest.raises(TypeError):
        XCLASSES["X19"] = "invented"
    with pytest.raises(TypeError):
        XCLASSES["X01"] = "renamed"
    assert isinstance(GATE_WORDS, tuple) and isinstance(GRADER_ONLY, tuple)


def test_the_module_holds_data_only():
    public = {n for n in dir(verdicts) if not n.startswith("_")}
    assert set(verdicts.__all__) <= public
    assert not [n for n in verdicts.__all__ if callable(getattr(verdicts, n))]
