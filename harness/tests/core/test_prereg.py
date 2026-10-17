"""The frozen core's own tests: fvh.prereg, the pre-registration gate (DV4-PLAN
§4.5; Δ91, Δ192), on synthetic answers files and gradebooks. Only rows whose
track is `prereg` unlock; a `prereg-fixture` row never does, and never hides an
older `prereg` row."""

import hashlib
import shutil
import subprocess

import pytest

from fvh import prereg as G

ANSWERS = """\\documentclass{article}
% preamble
% PREREG-BEGIN
\\section*{Problem B1}
Claim: the arms differ.
% PREREG-END
\\section*{Problem B2}
"""


def root(tmp_path, answers=ANSWERS, rows=()):
    (tmp_path / "paper").mkdir(parents=True, exist_ok=True)
    (tmp_path / "instructor").mkdir(exist_ok=True)
    (tmp_path / "paper" / "Q98_answers.tex").write_text(answers)
    book = "# Gradebook\n\n| date | module | track | grade | open findings |\n|---|---|---|---|---|\n"
    book += "".join(r + "\n" for r in rows)
    (tmp_path / "instructor" / "gradebook.md").write_text(book)
    return tmp_path


def full():
    block = "% PREREG-BEGIN\n\\section*{Problem B1}\nClaim: the arms differ.\n% PREREG-END\n"
    return hashlib.sha256(block.encode()).hexdigest()


def row(grade, prefix, track="prereg", module="Q98", date="2026-10-11"):
    g = f"{grade} sha256 {prefix}" if prefix else str(grade)
    return f"| {date} | {module} | {track} | {g} | 0 |"


@pytest.mark.skipif(shutil.which("sed") is None or shutil.which("sha256sum") is None,
                    reason="no sed or sha256sum")
def test_the_hash_is_the_skills_sed_pipeline(tmp_path):
    r = root(tmp_path)
    p = r / "paper" / "Q98_answers.tex"
    out = subprocess.run(f"sed -n '/^% PREREG-BEGIN/,/^% PREREG-END/p' '{p}' | sha256sum",
                         shell=True, capture_output=True, text=True, check=True).stdout.split()[0]
    assert G.section_hash(p) == out == full()
    p.write_text(ANSWERS.rstrip("\n").replace("% PREREG-END\n\\section*{Problem B2}",
                                              "% PREREG-END"))
    out = subprocess.run(f"sed -n '/^% PREREG-BEGIN/,/^% PREREG-END/p' '{p}' | sha256sum",
                         shell=True, capture_output=True, text=True, check=True).stdout.split()[0]
    assert G.section_hash(p) == out                    # no newline after the last marker


def test_an_unlocked_matching_row_passes(tmp_path):
    r = root(tmp_path, rows=[row(2, "0" * 16), row(3, full()[:16])])
    assert G.check(r, "Q98") == full()


@pytest.mark.parametrize("rows, match", [
    ([], "no prereg row"),
    ([row(3, "0" * 16)], "differs"),
    ([row(2, None)], "grade field"),
    ([row(3, full()[:16]), row(2, full()[:16])], "held at 2"),
    ([row(3, full()[:16]), row(4, "1" * 16)], "differs"),       # the newest row decides
    ([row(3, full()[:16], module="Q97")], "no prereg row"),
])
def test_refusals_name_the_row_and_the_hashes(tmp_path, rows, match):
    with pytest.raises(G.PreregRefused, match=match):
        G.check(root(tmp_path, rows=rows), "Q98")


def test_a_fixture_row_never_unlocks(tmp_path):
    with pytest.raises(G.PreregRefused, match="no prereg row"):
        G.check(root(tmp_path, rows=[row(4, full()[:16], track="prereg-fixture")]), "Q98")


def test_a_newer_fixture_row_does_not_hide_the_prereg_row(tmp_path):
    r = root(tmp_path, rows=[row(3, full()[:16]), row(1, "0" * 16, track="prereg-fixture")])
    assert G.check(r, "Q98") == full()
    assert [x.line for x in G.prereg_rows(r / "instructor" / "gradebook.md", "Q98")] == [5]


@pytest.mark.parametrize("answers", [
    ANSWERS.replace("% PREREG-BEGIN\n", ""),
    ANSWERS + "% PREREG-BEGIN\n",
    "% PREREG-END\n" + ANSWERS.replace("% PREREG-END\n", "").replace("% PREREG-BEGIN\n", "")
    + "% PREREG-BEGIN\n",
])
def test_missing_repeated_or_reversed_markers_refuse(tmp_path, answers):
    with pytest.raises(G.PreregRefused, match="PREREG"):
        G.check(root(tmp_path, answers=answers, rows=[row(3, full()[:16])]), "Q98")


def test_a_missing_answers_file_refuses(tmp_path):
    r = root(tmp_path)
    (r / "paper" / "Q98_answers.tex").unlink()
    with pytest.raises(G.PreregRefused, match="missing"):
        G.check(r, "Q98")


# The plan field (DV5d): `plan-sha256: <64 hex>` inside the block binds the batch plan.

PLAN = hashlib.sha256(b"seed = 1\n").hexdigest()


def with_plan(field_lines, outside=""):
    return ANSWERS.replace("% PREREG-END\n", field_lines + "% PREREG-END\n").replace(
        "\\section*{Problem B2}\n", "\\section*{Problem B2}\n" + outside)


def test_the_plan_field_is_read_from_the_block_only(tmp_path):
    r = root(tmp_path, answers=with_plan(f"\\textbf{{Batch plan}} plans/lab.toml, "
                                         f"\\texttt{{plan-sha256: {PLAN.upper()}}}\n",
                                         outside=f"plan-sha256: {'1' * 64}\n"))
    assert G.plan_fields(r / "paper" / "Q98_answers.tex") == [PLAN]
    G.check_plan(r, "Q98", PLAN)
    # the template's wording, filled in: the brace closes before the digits (DV5d fix)
    for line in (f"\\texttt{{plan-sha256:}} {PLAN}\n", f"\\texttt{{plan-sha256:}}~{PLAN}\n",
                 f"plan-sha256:\\ {PLAN}\n", f"\\texttt{{plan-sha256:}} \\texttt{{{PLAN}}}\n",
                 f"\\texttt{{plan-sha256: {PLAN}}}\n", f"plan-sha256: {PLAN}\n"):
        assert G.plan_fields(root(tmp_path, answers=with_plan(line)) /
                             "paper" / "Q98_answers.tex") == [PLAN], line
    # the template's own description, a short value or a longer run is not a field
    for line in ("as \\texttt{plan-sha256:} followed by the 64 hex digits\n",
                 f"plan-sha256: {PLAN[:63]}\n", f"plan-sha256: {PLAN}0\n",
                 f"xplan-sha256: {PLAN}\n", f"plan-sha256:\n{PLAN}\n"):
        assert G.plan_fields(root(tmp_path, answers=with_plan(line)) /
                             "paper" / "Q98_answers.tex") == [], line


@pytest.mark.parametrize("lines,msg", [
    ("", "names no batch plan"),
    (f"plan-sha256: {PLAN}\nplan-sha256: {'2' * 64}\n", "names 2 different plans"),
    (f"plan-sha256: {'3' * 64}\n", "the plan changed after the pre-registration"),
])
def test_the_plan_check_refuses(tmp_path, lines, msg):
    r = root(tmp_path, answers=with_plan(lines))
    with pytest.raises(G.PreregRefused, match=msg):
        G.check_plan(r, "Q98", PLAN)


def test_the_plan_field_is_inside_the_hash(tmp_path):
    a = root(tmp_path, answers=with_plan(f"plan-sha256: {PLAN}\n"))
    h1 = G.section_hash(a / "paper" / "Q98_answers.tex")
    root(tmp_path, answers=with_plan(f"plan-sha256: {'4' * 64}\n"))
    assert G.section_hash(a / "paper" / "Q98_answers.tex") != h1
    G.check_plan(root(tmp_path, answers=with_plan(f"plan-sha256: {PLAN}\nplan-sha256: {PLAN}\n")),
                 "Q98", PLAN)                      # the same plan named twice is one plan
