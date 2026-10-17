"""dvl.lab2pub: Lab 2's public strata (QPLAN §25.6): five HumanEval-Verus tasks and five
vericoding `humaneval` Dafny tasks in Lab 2's form (the specification removed, the prose and
the code kept, an empty witness; dvl.benchstrip's verus-lab2-form and dafny-lab2-form), drawn
from the validated pools of bench/public/POOLS.toml by a pre-registered seeded rule.

    python3 scripts/dvl/lab2pub.py order verus|dafny --seed S
        the stratum's pool members in the seeded draw order (one per line)
    python3 scripts/dvl/lab2pub.py check verus|dafny TASK...
        the static eligibility checks (C0-C3 below) of each named pool member
    python3 scripts/dvl/lab2pub.py build [--check] [--author]
        write (or, with --check, compare) every card's task form of
        bench/local/q/lab2pub/STRATUM.toml from the installed sets, and the NOTICE
        (the sets' pins and licences, the change statement; D29); a form whose
        source or result differs from the sha256 the stratum records is refused, and
        so is one whose kept definitions (D37) differ from the card's
        kept_definitions_sha256; --author (the author's context only) also compares
        them by name with the author-side list, Solutions/bench/local/q/lab2pub/KEPT.toml
    python3 scripts/dvl/lab2pub.py record DRAW.json
        author-only (Δ103's three-condition test): write the finished draw's
        [[draw]] records into bench/public/POOLS.toml, the stratum file, the
        cards' task forms and the author-side list of their kept definitions

The kept definitions (the user's decision D37): a form keeps a non-recursive definition
that only the specification uses when the reference applies it under a quantifier. The form
names no such definition as kept (a marker would hint the hidden specification): the card
records the sha256 of their sorted names, one per line (kept_definitions_sha256; absent when
there are none), which dvl.benchstrip.definition_residue's check over a shipped form compares,
and the names themselves are author-side (KEPT.toml under Solutions/, the reference set).

The draw (pre-registered before it ran; the record names the rule's text and its sha256): a
stratum's members are its pool's tasks (Dafny: those of vericoding's `dafny/humaneval`
stratum), sorted, then shuffled by `random.Random(<seed>)`; the draw walks that order and
takes a member when every check passes, in order:

  C0 licence   its provenance has a recorded MIT or Apache-2.0 licence (vericoding's
               rows whose source-notes say "translated directly from HumanEval Python
               source": the set's MIT and the HumanEval prompts' MIT; HumanEval-Verus: MIT)
  C1 form      dvl.benchstrip poses it as one task (one target declaration with at least
               one ensures; Verus: one named result), the form keeps no specification and
               no proof (spec_residue), and the answer (Verus: its spec fns made `pub open`
               as the form's are, base_answer) is a delivery of the form (dvl.judge.lab_ok:
               its definitions and levers unchanged)
  C2 prose     its HumanEval prompt exists (Verus: the file's PROMPT block; Dafny: the
               PROMPT block of the HumanEval-Verus file of the same problem)
  C3 distinct  its HumanEval problem is not an earlier accepted task's (either stratum)
  C4 resolves  the form, as built, reaches the verify stage (`vcheck --json`)
  C5 stable    the answer (base_answer) passes `vcheck --gate` and verifies under each
               pinned seed
               (`vcheck --brittleness --json`: every seed verified, `stable`)
  C6 witness   the reference program (the answer with the author's witness call) passes
               `vcheck --gate` (since the user's decision D27, the lab gate as a delivery
               of its form: `vcheck --gate --lab-task <form>`, whose code check allows a
               public card's proof annotations and nothing else)
  C7 judged    the grader judges the reference program faithful against its sealed reference

A member that fails a check is skipped with its reason and the next one is taken (the redraw
rule). The forms were rebuilt once on the same draw under the user's decisions D27 and D28
(2026-10-14: the header names what a delivery may add; the non-recursive definitions only the
specification used leave the form and are sealed with the reference, `reference_toml`), and
C1, C4, C6 and C7 were re-run on the drawn tasks. A solver job killed by memory (137/143) or stopped by the net (124) is no verdict: it is
re-run once, and a second such stop skips the member as `retry`. C4-C7 run outside this module
(the solver and the grader container); `record` takes their results.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import sys
import tomllib
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dvl import bench  # noqa: E402
from dvl import benchstrip as B  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
STRATUM_DIR = ("bench", "local", "q", "lab2pub")
LAB = "Q15"
STRATA = {
    "verus": {"set": "humaneval-verus", "stratum": "verus", "lang": "verus", "prefix": "vp",
              "ext": ".rs", "licence": "MIT"},
    "dafny": {"set": "vericoding", "stratum": "dafny/humaneval", "lang": "dafny", "prefix": "dp",
              "ext": ".dfy", "licence": "MIT"},
}
VERICODING_OWN = "translated directly from HumanEval Python source"
PROMPT = re.compile(r"/\*\s*\n### PROMPT\s*\n(.*?)\n\*/", re.S)
HE_ID = re.compile(r"### ID\s*\nHumanEval/(\d+)")


class Ineligible(Exception):
    """A pool member the draw skips (its reason is the message)."""


def stratum_dir(root):
    return Path(root).joinpath(*STRATUM_DIR)


def sha(b):
    return hashlib.sha256(b if isinstance(b, bytes) else b.encode("utf-8")).hexdigest()


def _sets(root):
    _, sets = bench.load_manifest(root)
    return sets


def members(root, key):
    """The stratum's pool members (sorted task paths) and the pool's sha256."""
    st = STRATA[key]
    pool = bench.load_pools(root).get(st["set"])
    if not pool:
        raise bench.Refused(f"bench/public/POOLS.toml has no pool of {st['set']}")
    tasks = sorted(pool["tasks"])
    if bench.pool_digest(tasks) != pool["pool_sha256"]:
        raise bench.Refused(f"{st['set']}: the pool's members do not match its pool_sha256")
    if st["set"] == "vericoding":
        strata = bench.strata_of(root, _sets(root)[st["set"]], tasks)
        if not any(v != "dafny" and v != "verus" for v in strata.values()):
            raise bench.Refused("vericoding's subset index is not installed (get_bench.sh "
                                "vericoding)")
        tasks = [t for t in tasks if strata[t] == st["stratum"]]
    return tasks, pool["pool_sha256"]


def draw_order(tasks, seed):
    """The seeded draw order of a stratum's members."""
    order = sorted(tasks)
    random.Random(seed).shuffle(order)
    return order


def order_digest(order):
    return sha("".join(t + "\n" for t in order))


def _vericoding_rows(root):
    idx = bench.set_dir(root, "vericoding") / "tasks" / "vericoding_benchmark_v1.csv"
    with open(idx, newline="", encoding="utf-8") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


def answer_path(root, key, task):
    return bench.set_dir(root, STRATA[key]["set"]) / "answers" / task


def base_answer(root, key, task):
    """The answer as the reference program starts from it: Verus, its spec fns made `pub open`
    as the form makes its kept ones (benchstrip.lab2_publish_verus); Dafny, as installed."""
    text = answer_path(root, key, task).read_text(encoding="utf-8")
    return B.lab2_publish_verus(text) if key == "verus" else text


def humaneval_number(root, key, task, rows=None):
    if key == "verus":
        m = HE_ID.search(answer_path(root, key, task).read_text(encoding="utf-8"))
        if not m:
            raise Ineligible("C2: no `### ID HumanEval/<n>` block")
        return int(m.group(1))
    row = (rows or _vericoding_rows(root)).get(Path(task).stem)
    m = re.fullmatch(r"humaneval_(\d+)(?:_.*)?", (row or {}).get("source-id", ""))
    if not m:
        raise Ineligible("C2: the subset index names no HumanEval problem")
    return int(m.group(1))


def prompt(root, number):
    """The HumanEval prompt of problem `number` as the HumanEval-Verus set ships it (the
    PROMPT block of the first file of that problem in sorted order)."""
    d = bench.set_dir(root, "humaneval-verus") / "answers"
    for f in sorted(d.glob(f"human_eval_{number:03d}*.rs")):
        m = PROMPT.search(f.read_text(encoding="utf-8"))
        if m and m.group(1).strip():
            return m.group(1).rstrip()
    raise Ineligible(f"C2: no PROMPT block for HumanEval/{number}")


def card_id(key, k, number):
    return f"{STRATA[key]['prefix']}{k}-he{number:03d}"


def header(key, card, task, form, commit, number):
    st = STRATA[key]
    if key == "verus":
        src = (f"HumanEval-Verus `{task}` at {commit[:7]} ({st['licence']}; "
               f"bench/local/q/lab2pub/NOTICE)")
        where = "from its prose (the PROMPT comment below)"
        tr = "verus-lab2-form"
    else:
        src = (f"vericoding `{task}` at {commit[:7]} ({st['licence']}; "
               f"bench/local/q/lab2pub/NOTICE)")
        where = (f"from its prose (HumanEval/{number}'s prompt, as the HumanEval-Verus set "
                 f"ships it, above the method)")
        tr = "dafny-lab2-form"
    need = ("with any definition they need (a spec fn they name must be `pub open`)"
            if key == "verus" else "with any definition they need")
    lines = [f"Lab 2 public task {card} (Q15; QPLAN §25.6): {src}, its specification, its "
             f"proofs and the definitions only its specification used removed by "
             f"scripts/dvl/benchstrip.py ({tr}).",
             f"Write `{form.name}`'s `requires` and `ensures` {where}, {need}, and one call "
             f"whose `requires` hold in `{form.witness}`. You may add proof annotations (loop "
             f"invariants, assertions, proof blocks, lemmas); never change its executable "
             f"code, and keep every other line of the file."]
    out = []
    for para in lines:
        words, cur = para.split(), "//"
        for w in words:
            if len(cur) + 1 + len(w) > 96:
                out.append(cur)
                cur = "// " + w
            else:
                cur += " " + w
        out.append(cur)
    return "\n".join(out) + "\n"


def make_form(root, key, task, card, rows=None):
    """(form text, Lab2Form, HumanEval number) of a pool member as card `card`."""
    st = STRATA[key]
    text = answer_path(root, key, task).read_text(encoding="utf-8")
    number = humaneval_number(root, key, task, rows)
    prose = prompt(root, number)
    try:
        f = B.lab2_form(text, st["lang"], None if key == "verus" else prose)
    except B.StripError as e:
        raise Ineligible(f"C1: {e}") from None
    commit = _sets(root)[st["set"]]["commit"]
    if key == "verus" and not PROMPT.search(f.text):
        raise Ineligible("C2: the form keeps no PROMPT block")
    return header(key, card, task, f, commit, number) + f.text, f, number


def reference(root, key, task, name):
    """The reference statement of a pool member: its answer's target declaration as the
    grader's host half reads it (dvl.judge.candidate), and the definitions the form removed
    because only the specification used them and they are not recursive (the user's decision
    D28): `definitions` (their declarations' text, Verus made `pub open`, in file order) and
    `definition_names`. They are sealed with the reference (reference_toml), and the grader
    renders them, renamed, beside a delivery's own definitions (truthcheck's `_renamed`)."""
    from dvl import judge as J
    text = answer_path(root, key, task).read_text(encoding="utf-8")
    c = J.candidate(text, STRATA[key]["lang"], name)
    try:
        f = B.lab2_form(text, STRATA[key]["lang"], None if key == "verus" else "")
    except B.StripError as e:
        raise Ineligible(f"C1: {e}") from None
    if f.name != name:
        raise Ineligible(f"C1: the form's target is {f.name}, not {name}")
    return {"name": name, "lang": STRATA[key]["lang"], "params": c["params"],
            "results": c["results"], "requires": c["requires"], "ensures": c["ensures"],
            "definitions": list(f.definitions or []),
            "definition_names": list(f.definition_names or [])}


def reference_toml(root, key, card, task, name, *, notes=(), extra=()):
    """The text of a public card's sealed `tasks/<card>/reference.toml` (author-only: it is
    written into the hidden truth's plaintext tree, never into the course tree): the
    reference statement as fvh_q.oracles.Spec fields over the form's declaration, and the
    sealed definitions it names (D28). `notes` are comment lines, `extra` TOML lines (the
    kill rate, D27)."""
    st = STRATA[key]
    ref = reference(root, key, task, name)
    form_rel = f"bench/local/q/lab2pub/{card}/tasks/{card}{st['ext']}"
    q = _q
    lines = [f"# Hidden truth, Lab 2 public task {card}: the reference statement of {st['set']}'s",
             f"# {task} (its answer's declaration, as dvl.judge.candidate reads it), as fvh_q.oracles.Spec",
             "# fields over the task form's declaration, with the definitions the form removed because",
             "# only the specification used them and they are not recursive (the user's decision D28;",
             "# the grader renders them renamed beside a delivery's own); the reference program beside",
             "# it (the answer, the form's header and the author's witness call) passes the lab gate.",
             *[f"# {n}" for n in notes],
             f"id = {q(card)}", f"lang = {q(st['lang'])}", f"name = {q(name)}",
             f"task_form = {q(form_rel)}", f"source_set = {q(st['set'])}",
             f"source_task = {q(task)}",
             f"answer_sha256 = {q(sha(answer_path(root, key, task).read_bytes()))}",
             f"requires = {q(ref['requires'])}", f"ensures = {q(ref['ensures'])}",
             f"definitions = {q(ref['definitions'])}",
             f"definition_names = {q(ref['definition_names'])}", *extra]
    return "\n".join(lines) + "\n"


def static_check(root, key, task, *, taken=(), rows=None, card="xx0-he000"):
    """Checks C0-C3 of one pool member; returns (form text, Lab2Form, number, reference)
    or raises Ineligible."""
    from dvl import judge as J
    import tempfile
    st = STRATA[key]
    rows = rows if rows is not None or key == "verus" else _vericoding_rows(root)
    if key == "dafny":
        notes = (rows.get(Path(task).stem) or {}).get("source-notes", "")
        if notes != VERICODING_OWN:
            raise Ineligible(f"C0: provenance {notes or 'unrecorded'!r} has no recorded MIT or "
                             f"Apache-2.0 licence")
    form_text, f, number = make_form(root, key, task, card, rows)
    res = B.spec_residue(form_text, st["lang"], f.name)
    if res:
        raise Ineligible(f"C1: the form keeps {res[0][1]} (line {res[0][0]})")
    try:
        ref = reference(root, key, task, f.name)
    except J.JudgeInputError as e:
        raise Ineligible(f"C1: the grader cannot read the answer's declaration: {e}") from None
    if not ref["ensures"]:
        raise Ineligible("C1: the reference states no ensures")
    if st["lang"] == "verus" and len(ref["results"]) != 1:
        raise Ineligible("C1: the result is not one named value")
    with tempfile.TemporaryDirectory(prefix="dvl0-lab2pub-") as tmp:
        p = Path(tmp) / f"form{st['ext']}"
        p.write_text(form_text, encoding="utf-8")
        if not J.lab_ok(root, str(p), base_answer(root, key, task), st["lang"], f.name):
            raise Ineligible("C1: the answer is not a delivery of the form (a definition or a "
                             "lever differs)")
    if number in taken:
        raise Ineligible(f"C3: HumanEval/{number} is an earlier accepted task's")
    return form_text, f, number, ref


# --- the stratum file and the records ----------------------------------------------------------

def load_stratum(root):
    p = stratum_dir(root) / "STRATUM.toml"
    if not p.is_file():
        return {}
    return tomllib.loads(p.read_text(encoding="utf-8"))


KEPT_FILE = ("Solutions", "bench", "local", "q", "lab2pub", "KEPT.toml")


def kept_digest(names):
    """The sha256 a card records for its kept definitions (D37), or None for none."""
    names = sorted(set(names))
    return sha("".join(n + "\n" for n in names)) if names else None


def kept_path(root):
    return Path(root).joinpath(*KEPT_FILE)


def load_kept(root):
    """{card id: [kept definition names]} from the author-side list (author context only)."""
    why = bench.author_gate(root)
    if why:
        raise bench.Refused(f"the kept-definition list is author-side and is not read here ({why})")
    p = kept_path(root)
    if not p.is_file():
        return {}
    data = tomllib.loads(p.read_text(encoding="utf-8"))
    return {k: sorted(v.get("quantified_definitions", [])) for k, v in data.get("card", {}).items()}


KEPT_HEAD = """\
# Solutions/bench/local/q/lab2pub/KEPT.toml — author-only (the reference set). The definitions
# each Lab 2 public form keeps although only its reference specification uses them, because
# the reference applies them under a quantifier (the user's decision D37). Written by
# `scripts/dvl/lab2pub.py record`; checked by `scripts/dvl/lab2pub.py build --check --author`.
# The form itself names none of them (a marker would hint the hidden specification); its card
# in bench/local/q/lab2pub/STRATUM.toml records only the sha256 of the sorted names, one per
# line (kept_definitions_sha256).
"""


def kept_text(kept):
    out = [KEPT_HEAD, "schema = 1"]
    for cid in sorted(kept):
        if kept[cid]:
            out += ["", f'[card."{cid}"]', f"quantified_definitions = {_q(sorted(kept[cid]))}"]
    return "\n".join(out) + "\n"


def form_path(root, card, lang):
    ext = ".rs" if lang == "verus" else ".dfy"
    return stratum_dir(root) / card / "tasks" / f"{card}{ext}"


def build(root, check=False, author=False):
    """Write (or compare) every card's form from the installed sets. Returns problems.
    author: also compare each card's kept definitions with the author-side list."""
    data = load_stratum(root)
    out = []
    kept = load_kept(root) if author else None
    keys = {v["set"]: k for k, v in STRATA.items()}
    rows = None
    for c in data.get("card", []):
        key = keys.get(c.get("set"))
        if key is None:
            out.append(f"{c.get('id')}: unknown set {c.get('set')!r}")
            continue
        a = answer_path(root, key, c["task"])
        if not a.is_file():
            out.append(f"{c['id']}: {c['set']} is not installed (get_bench.sh {c['set']})")
            continue
        if sha(a.read_bytes()) != c.get("answer_sha256"):
            out.append(f"{c['id']}: the installed {c['task']} is not the one the draw used")
            continue
        if key == "dafny" and rows is None:
            rows = _vericoding_rows(root)
        text, f, _ = make_form(root, key, c["task"], c["id"], rows)
        if sha(text) != c.get("form_sha256"):
            out.append(f"{c['id']}: the transform no longer gives the recorded form")
            continue
        if kept_digest(f.quantified or []) != c.get("kept_definitions_sha256"):
            out.append(f"{c['id']}: the transform's kept definitions (D37) are not the ones "
                       "the card records")
            continue
        if kept is not None and kept.get(c["id"], []) != sorted(f.quantified or []):
            out.append(f"{c['id']}: the author-side list of kept definitions differs from the "
                       "transform's")
            continue
        p = form_path(root, c["id"], c["lang"])
        if check:
            if not p.is_file() or sha(p.read_bytes()) != c["form_sha256"]:
                out.append(f"{c['id']}: {p.relative_to(root)} is missing or differs")
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
    if not out and data.get("card"):
        try:
            want = notice_text(root)
        except bench.Refused as e:
            return out + [f"NOTICE: {e}"]
        n = stratum_dir(root) / "NOTICE"
        if check:
            if not n.is_file() or n.read_text(encoding="utf-8") != want:
                out.append(f"{n.relative_to(root)} is missing or differs from the sets' pins "
                           "and licences")
        else:
            n.write_text(want, encoding="utf-8")
    return out


NOTICE_SETS = (
    ("verus", "vp1..vp5", "HumanEval-Verus",
     ["the HumanEval prompts its files carry: OpenAI's HumanEval,",
      "https://github.com/openai/human-eval, MIT (the copyright line",
      "of the LICENSE below)"]),
    ("dafny", "dp1..dp5", "vericoding",
     ["those whose source-notes say \"translated directly from",
      "HumanEval Python source\" (vericoding's own translations, under",
      "its MIT licence); the prose above each method is the HumanEval",
      "prompt of the same problem, as HumanEval-Verus ships it"]),
)


def notice_text(root):
    """bench/local/q/lab2pub/NOTICE (the user's decision D29, 2026-10-14: the ten forms stay
    tracked with this notice): each upstream set's name, repository URL, commit and licence as
    fetched (bench/manifest.toml's pins and licence check, and the installed LICENSE file
    itself with its sha256), then the change statement and the two LICENSE files verbatim.
    Refused when a set is not installed (its LICENSE is read from bench/public/<set>/)."""
    sets = _sets(root)
    head = ["Lab 2's public strata (bench/local/q/lab2pub/): the upstream sets, their licences "
            "and the",
            "change statement. The forms are tracked in the course tree with this notice (the "
            "user's",
            "decision D29, 2026-10-14). Each card's task form is derived from one file of a "
            "public",
            "benchmark set that scripts/get_bench.sh fetches on the pins (bench/manifest.toml).",
            ""]
    blocks = []
    for key, cards, label, extra in NOTICE_SETS:
        st = STRATA[key]
        meta = sets[st["set"]]
        lic = bench.set_dir(root, st["set"]) / "LICENSE"
        if not lic.is_file():
            raise bench.Refused(f"{st['set']} is not installed (get_bench.sh {st['set']}): its "
                                f"LICENSE is read from {lic.relative_to(root)}")
        data = lic.read_bytes()
        ld = meta.get("licence") or {}
        head += [f"  {cards}  {label}" + (f" ({st['set']})" if label != st["set"] else ""),
                 f"            repository  {meta.get('repo')}",
                 f"            commit      {meta.get('commit')}",
                 f"            licence     {ld.get('spdx')}, as fetched: the set's LICENSE at that "
                 f"commit (below),",
                 f"                        sha256 {sha(data)}",
                 f"            checked     {ld.get('checked')}: {ld.get('method')}"]
        head += [f"            {'upstream' if key == 'verus' else 'rows    '}    {extra[0]}"]
        head += [f"                        {x}" for x in extra[1:]]
        blocks += ["=" * 80, f"{label} LICENSE (bench/public/{st['set']}/LICENSE)", "=" * 80,
                   data.decode("utf-8").rstrip("\n"), ""]
    change = (
        "Changes (the change statement): each form is the upstream answer file with its target "
        "declaration's `requires` and `ensures` removed, its proofs removed (Verus: proof fns, "
        "proof statements and the comment lines above them, ghost lets, reveals, loop "
        "invariants and the spec fns only proofs use; Dafny: lemmas, assertions, calc, reveal, "
        "ghost variables, proof forall statements, lemma calls, loop invariants and the helper "
        "definitions only proofs use), the definitions only its specification used removed "
        "when they are not recursive or used under quantifiers (the user’s decision D28, amended by D37; they are sealed with the "
        "grader's hidden reference, not shipped), (Verus) each kept spec fn made `pub open` "
        "(one marked `closed` upstream stays closed, made `pub`), an empty witness declaration "
        "and a header comment added, and (Dafny) the HumanEval prompt added as a comment "
        "(scripts/dvl/benchstrip.py: verus-lab2-form, dafny-lab2-form; scripts/dvl/lab2pub.py).")
    words, cur, wrapped = change.split(), "", []
    for w in words:
        if cur and len(cur) + 1 + len(w) > 92:
            wrapped.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    wrapped.append(cur)
    return "\n".join(head + [""] + wrapped + [""] + blocks).rstrip("\n") + "\n"


STRATUM_HEAD = """\
# bench/local/q/lab2pub/STRATUM.toml — Lab 2's public strata (QPLAN §25.6). Learner-owned tree
# (guard rule 2); written by the author-only `scripts/dvl/lab2pub.py record` from the draw that
# bench/public/POOLS.toml's [[draw]] records (seed, rule, order and every skipped member).
#
# Each card is one public task in Lab 2's form: its specification, its proofs and the
# definitions only its specification used (when they are not recursive; the user's decision
# D28) removed by scripts/dvl/benchstrip.py (verus-lab2-form, dafny-lab2-form), the prose (the
# HumanEval prompt), the executable code and the other definitions kept, an empty witness. A
# delivery adds the `requires` and `ensures` with any definition they need (Verus: `pub open`),
# one witness call and, on these cards only, proof annotations (loop invariants, assertions,
# proof blocks, lemmas; the user's decision D27), and changes no executable code: the lab gate
# checks it (`scripts/vcheck --gate --lab-task`, dvl.labcode). The reference statements are in
# no course file, and the removed definitions in no course file of this tree (the forms before
# D28 held them, so this repository's history before DV6 does): both are sealed with Lab 2's
# hidden truth for the grader (Hidden/labs/Q15/, QPLAN §30 Q49), and the upstream sets that
# scripts/get_bench.sh installs under bench/public/ (fetched on the pins) hold them either way,
# which is why this stratum is no contamination control: the local stratum is (lab2/).
#
# A card whose form keeps a definition that no line of its code uses records the sha256 of
# those definitions' sorted names, one per line (kept_definitions_sha256), which the shipped-
# form check compares; the list itself is author-side.
#
# `python3 scripts/dvl/lab2pub.py build --check` re-derives every form from the installed sets
# and compares it with form_sha256; the licences and the change statement are in NOTICE.
"""


def _q(v):
    return bench._toml_value(v)


def stratum_text(cards, date, forms_date=None):
    out = [STRATUM_HEAD, "schema = 1", f'lab = "{LAB}"', f'date = "{date}"',
           'stratum = "public"']
    if forms_date:
        out.append(f'forms_date = "{forms_date}"   # the forms rebuilt on the same draw (D27, D28)')
    for c in cards:
        out += ["", "[[card]]"]
        for k in ("id", "lang", "name", "set", "task", "humaneval", "answer_sha256",
                  "form_sha256", "kept_definitions_sha256"):
            if k in c:
                out.append(f"{k} = {_q(c[k])}")
    return "\n".join(out) + "\n"


def record(root, draw):
    """Write the finished draw (a dict: date, prereg_sha256, rule, strata: [{key, seed,
    order_sha256, drawn: [{task, card, name, humaneval}], skipped: {task: reason}}], and
    optionally amendment_sha256 and forms_date) into POOLS.toml's [[draw]] tables, the stratum
    file and the cards' forms. `draw_of_records` gives the recorded draw back, for a rebuild
    of the forms on the same draw."""
    why = bench.author_gate(root)
    if why:
        raise bench.Refused(f"record is author-only and refuses to run here ({why})")
    cards, draws, kept = [], [], {}
    rows = _vericoding_rows(root)
    for s in draw["strata"]:
        key = s["key"]
        st = STRATA[key]
        tasks, pool_sha = members(root, key)
        order = draw_order(tasks, s["seed"])
        if order_digest(order) != s["order_sha256"]:
            raise bench.Refused(f"{key}: the seeded order is not the one the draw walked")
        pool = bench.load_pools(root)[st["set"]]
        for d in s["drawn"]:
            text, f, number = make_form(root, key, d["task"], d["card"], rows)
            cards.append({"id": d["card"], "lang": st["lang"], "name": f.name, "set": st["set"],
                          "task": d["task"], "humaneval": number,
                          "answer_sha256": sha(answer_path(root, key, d["task"]).read_bytes()),
                          "form_sha256": sha(text),
                          **({"kept_definitions_sha256": kept_digest(f.quantified)}
                             if f.quantified else {})})
            kept[d["card"]] = sorted(f.quantified or [])
            p = form_path(root, d["card"], st["lang"])
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        walked = order[:order.index(s["drawn"][-1]["task"]) + 1] if s["drawn"] else order
        draws.append({"lab": LAB, "stratum": key, "set": st["set"], "subset": st["stratum"],
                      "set_sha256": pool["set_sha256"], "pins_sha256": pool["pins_sha256"],
                      "pool_sha256": pool_sha, "members": len(tasks), "seed": s["seed"],
                      "order_sha256": s["order_sha256"], "walked": len(walked),
                      "rule": draw["rule"], "prereg_sha256": draw["prereg_sha256"],
                      **({"amendment_sha256": draw["amendment_sha256"]}
                         if draw.get("amendment_sha256") else {}),
                      "date": draw["date"], "drawn": [d["task"] for d in s["drawn"]],
                      "cards": [d["card"] for d in s["drawn"]],
                      "skipped": dict(sorted(s["skipped"].items()))})
    (stratum_dir(root) / "STRATUM.toml").write_text(
        stratum_text(cards, draw["date"], draw.get("forms_date")), encoding="utf-8")
    kept_path(root).parent.mkdir(parents=True, exist_ok=True)
    kept_path(root).write_text(kept_text(kept), encoding="utf-8")
    bench.write_draws(root, draws)
    return cards


def draw_of_records(root):
    """The recorded draw (record's argument) from POOLS.toml's two Q15 [[draw]] records."""
    recs = {d["stratum"]: d for d in bench.load_draws(root) if d.get("lab") == LAB}
    if sorted(recs) != sorted(STRATA):
        raise bench.Refused("bench/public/POOLS.toml lacks a Q15 [[draw]] record per stratum")
    st = {c["id"]: c for c in load_stratum(root).get("card", [])}
    first = recs["verus"]
    draw = {"date": first["date"], "prereg_sha256": first["prereg_sha256"], "rule": first["rule"],
            "strata": []}
    if first.get("amendment_sha256"):
        draw["amendment_sha256"] = first["amendment_sha256"]
    for key in ("verus", "dafny"):
        r = recs[key]
        drawn = [{"task": t, "card": c, "name": st[c]["name"], "humaneval": st[c]["humaneval"]}
                 for t, c in zip(r["drawn"], r["cards"])]
        draw["strata"].append({"key": key, "seed": r["seed"], "order_sha256": r["order_sha256"],
                               "drawn": drawn, "skipped": dict(r["skipped"])})
    return draw


def main(argv=None):
    ap = argparse.ArgumentParser(prog="lab2pub.py", allow_abbrev=False)
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("order")
    o.add_argument("key", choices=sorted(STRATA))
    o.add_argument("--seed", required=True)
    c = sub.add_parser("check")
    c.add_argument("key", choices=sorted(STRATA))
    c.add_argument("tasks", nargs="+")
    b = sub.add_parser("build")
    b.add_argument("--check", action="store_true")
    b.add_argument("--author", action="store_true")
    r = sub.add_parser("record")
    r.add_argument("draw")
    ap.add_argument("--root", help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    root = Path(a.root).resolve() if a.root else REPO_ROOT
    try:
        if a.cmd == "order":
            tasks, pool_sha = members(root, a.key)
            order = draw_order(tasks, a.seed)
            for t in order:
                print(t)
            print(f"# {len(order)} members, pool_sha256 {pool_sha}, order_sha256 "
                  f"{order_digest(order)}", file=sys.stderr)
            return 0
        if a.cmd == "check":
            bad = 0
            for t in a.tasks:
                try:
                    _, f, number, _ = static_check(root, a.key, t)
                    print(f"{t}: eligible (C0-C3): {f.name}, HumanEval/{number}")
                except Ineligible as e:
                    print(f"{t}: skipped: {e}")
                    bad += 1
            return 1 if bad else 0
        if a.cmd == "build":
            probs = build(root, check=a.check, author=a.author)
            for p in probs:
                print(f"lab2pub: {p}", file=sys.stderr)
            if not probs:
                n = len(load_stratum(root).get("card", []))
                print(f"lab2pub: {n} card(s) {'current' if a.check else 'written'}")
            return 3 if probs else 0
        if a.cmd == "record":
            cards = record(root, json.loads(Path(a.draw).read_text(encoding="utf-8")))
            print(f"lab2pub: recorded {len(cards)} card(s)")
            return 0
    except bench.Refused as e:
        print(f"lab2pub: refused: {e}", file=sys.stderr)
        return 3
    return 2


if __name__ == "__main__":
    sys.exit(main())
