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


# --- the freeze and the plan roles (DVR4 plan sections 3.6, 3.8) ------------------------

import json
from types import SimpleNamespace

STRATUM_REL = "bench/local/r/labx/STRATUM.toml"


def stratum(tmp_path, roles):
    """A schema-2 stratum: cluster id -> (role, descriptive); one task per cluster."""
    lines = ["schema = 2", 'lab = "Q98"']
    for cid, (role, desc) in roles.items():
        lines += ["[[cluster]]", f'id = "{cid}"', f'role = "{role}"', f"descriptive = {str(desc).lower()}",
                  f'tasks = ["{cid}-d"]']
        p = tmp_path / f"bench/local/r/labx/{cid}-d/tasks/{cid}-d.dfy"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"// {cid}\n")
    p = tmp_path / STRATUM_REL
    p.write_text("\n".join(lines) + "\n")
    return hashlib.sha256(p.read_bytes()).hexdigest()


ROLES = {"c1": ("confirmatory", True), "c2": ("confirmatory", False), "p1": ("pilot", False),
         "u1": ("unassigned", False)}


def freeze(tmp_path, **over):
    fields = dict(estimand="mean over clusters of AUC_obl - AUC_raw", primary_contrast="best vs best-raw",
                  test="paired sign-flip", budget_axis="node calls, B = 10", aggregation="run > cluster-arm",
                  missing_rule="policy failures fail; apparatus failures re-run once",
                  resource_accounting="equal cap", cluster_rule="one per lemma family",
                  confirmatory_clusters=["c1", "c2"], pilot_clusters=["p1"],
                  descriptive_clusters=["c1"], power_sim_sha256="a" * 64, K=2,
                  stratum=STRATUM_REL, stratum_sha256=stratum(tmp_path, ROLES))
    fields.update(over)
    fields = {k: v for k, v in fields.items() if v is not None}
    text = "schema = 1\n" + "".join(f"{k} = {json.dumps(v)}\n" for k, v in fields.items())
    (tmp_path / "FREEZE.toml").write_text(text)
    return "FREEZE.toml"


def test_a_complete_freeze_loads(tmp_path):
    f = G.load_freeze(tmp_path, freeze(tmp_path))
    assert f["confirmatory_clusters"] == ["c1", "c2"] and len(f["sha256"]) == 64


@pytest.mark.parametrize("over, match", [
    (dict(estimand=None), "incomplete: missing estimand"),
    (dict(power_sim_sha256=None), "missing power_sim_sha256"),
    (dict(test="  "), "test is empty"),
    (dict(pilot_clusters=["p1", "c2"]), "overlap"),
    (dict(confirmatory_clusters=[]), "non-empty list"),
    (dict(descriptive_clusters=["p1"]), "outside the confirmatory"),
    (dict(descriptive_clusters=["c2"]), "descriptive flags"),
    (dict(power_sim_sha256="xyz"), "power_sim_sha256"),
    (dict(K=80), "K = 80"),
    (dict(stratum_sha256="0" * 64), "changed after the freeze"),
    (dict(stratum_sha256=None), "incomplete: stratum"),
    (dict(confirmatory_clusters=["c1", "u1"], K=None), "frozen confirmatory but the stratum says unassigned"),
])
def test_an_incomplete_or_inconsistent_freeze_is_refused(tmp_path, over, match):
    rel = freeze(tmp_path, **over)
    with pytest.raises(G.FreezeRefused, match=match):
        G.load_freeze(tmp_path, rel)


def test_no_freeze_file_is_refused(tmp_path):
    with pytest.raises(G.FreezeRefused, match="no freeze is committed"):
        G.load_freeze(tmp_path, "FREEZE.toml")


def plan(tasks, role="", frz="", lab=""):
    return SimpleNamespace(tasks={t: (f"bench/local/r/labx/{t}/tasks/{t}.dfy", "dafny") for t in tasks},
                           role=role, freeze=frz, lab=lab, path="plan.toml")


def test_check_roles_pilot_and_confirmatory(tmp_path):
    rel = freeze(tmp_path)
    assert G.check_roles(tmp_path, "Q98", plan(["p1-d"], role="pilot")) is None
    with pytest.raises(G.FreezeRefused, match="outside the pilot clusters: c1-d"):
        G.check_roles(tmp_path, "Q98", plan(["p1-d", "c1-d"], role="pilot"))
    with pytest.raises(G.FreezeRefused, match="only under the committed freeze"):
        G.check_roles(tmp_path, "Q98", plan(["c1-d"], role="confirmatory"))
    assert G.check_roles(tmp_path, "Q98", plan(["c1-d", "c2-d"], role="confirmatory", frz=rel))
    with pytest.raises(G.FreezeRefused, match="outside the confirmatory clusters: p1-d"):
        G.check_roles(tmp_path, "Q98", plan(["c1-d", "p1-d"], role="confirmatory", frz=rel))
    with pytest.raises(G.FreezeRefused, match="outside the descriptive clusters: c2-d"):
        G.check_roles(tmp_path, "Q98", plan(["c2-d"], role="descriptive", frz=rel))
    with pytest.raises(G.FreezeRefused, match="names its role"):
        G.check_roles(tmp_path, "Q98", plan(["c1-d"]))
    with pytest.raises(G.FreezeRefused, match="before and outside the freeze"):
        G.check_roles(tmp_path, "Q98", plan(["p1-d"], role="pilot", frz=rel))


def test_a_lab_plan_registers_the_freeze_it_runs_under(tmp_path):
    rel = freeze(tmp_path)
    sha = G.load_freeze(tmp_path, rel)["sha256"]
    (tmp_path / "paper").mkdir()
    ans = tmp_path / "paper" / "Q98_answers.tex"
    ans.write_text("% PREREG-BEGIN\nplan\n% PREREG-END\n")
    p = plan(["c1-d"], role="confirmatory", frz=rel, lab="Q98")
    with pytest.raises(G.FreezeRefused, match="must name the freeze"):
        G.check_roles(tmp_path, "Q98", p)
    ans.write_text(f"% PREREG-BEGIN\n\\texttt{{freeze-sha256: {sha}}}\n% PREREG-END\n")
    assert G.freeze_fields(ans) == [sha]
    assert G.check_roles(tmp_path, "Q98", p)["sha256"] == sha


def test_plans_over_other_strata_carry_no_role(tmp_path):
    p = SimpleNamespace(tasks={"t": ("bench/local/q/lab9/t/tasks/t.dfy", "dafny")}, role="", freeze="",
                        lab="", path="p")
    assert G.check_roles(tmp_path, "Q98", p) is None
    with pytest.raises(G.FreezeRefused, match="serve a plan over a schema-2 stratum"):
        G.check_roles(tmp_path, "Q98", SimpleNamespace(**dict(vars(p), role="pilot")))


def test_a_sealed_cluster_never_enters_a_plan(tmp_path):
    rel = freeze(tmp_path)
    st = tmp_path / STRATUM_REL
    st.write_text(st.read_text() + '[[task]]\nid = "c2-d"\nsealed = true\n')
    import hashlib as h
    text = (tmp_path / rel).read_text()
    old = [l for l in text.splitlines() if l.startswith("stratum_sha256")][0]
    (tmp_path / rel).write_text(text.replace(old, f'stratum_sha256 = "{h.sha256(st.read_bytes()).hexdigest()}"'))
    assert G.check_roles(tmp_path, "Q98", plan(["c1-d"], role="confirmatory", frz=rel))
    with pytest.raises(G.FreezeRefused, match="outside the confirmatory clusters: c2-d"):
        G.check_roles(tmp_path, "Q98", plan(["c2-d"], role="confirmatory", frz=rel))
