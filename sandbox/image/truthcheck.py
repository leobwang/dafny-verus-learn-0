#!/usr/bin/python3
"""The grader container's truth mode (/opt/dvl/bin/truthcheck; DV4-PLAN §5.9,
QPLAN §30 Q49, design §10.3).

    truthcheck manifest <LAB>
    truthcheck validate <LAB> [<card> ...]
    truthcheck judge <LAB>
    truthcheck gate-agree <LAB> dafny|verus
    truthcheck bench-agree <LAB>

Run only by scripts/mksandbox-run, as a [[command]] of a verify manifest that
carries a [truth] table, inside a network-less verification container. The
host binds the sealed archive and the grader's key read-only at
/run/dvl-truth/ (archive.tar.age, identity); this program is the only reader
of either, and the plaintext exists only here:

  1. it unseals the archive with the image's pinned age binary into memory,
     parses the tar stream (regular files only, every name under
     labs/<LAB>/, no link, no absolute or parent path) and checks every file
     against the archive's own MANIFEST.sha256 (every listed file present
     with its sha256, no unlisted file);
  2. `manifest` prints the check's summary;
  3. `validate` checks that each local task's reference program (the task
     form with the hidden specification and a witness) passes the course's
     gate on the pins: for each card of tasks/<card>/ (or the named ones) it
     writes the reference program over the card's staged task form under
     /work, runs `scripts/vcheck --gate --json <task form>` there, restores
     the form, and prints the card's verdict;
  4. `judge` judges every candidate of /work/judge/candidates.json (written
     by the host, scripts/dvl/judge.py: a prose item's delivered statement or
     a Lab 2 arm's returned task file, each as its clauses and its file's
     definitions) against the sealed reference of its item
     (prose/<item>.toml) or card (tasks/<card>/reference.toml), with the
     frozen reference oracles the archive carries (judge/oracles.py, never a
     learner's). Per candidate: the host's refusal, if it sent one (the file
     does not hold the declaration readably, changes a frozen statement, or
     changes its task form's definitions or levers), is `mismatch`; so is a
     signature other than the reference's; the candidate's definitions alone
     must verify (a base lemma; else `context`); then
       - a Lab 2 card gets the oracles' own verdict (QPLAN §25.5-§25.6: their
         two implication lemmas, the vacuity lemma and their
         classification), the verdict the learner's oracles are measured
         against;
       - a prose item (QPLAN §19.0's hidden equivalence check) is judged as
         a refinement both ways, by four lemmas over the item's parameters
         and results: the reference's requires give the candidate's
         (`req_from_ref`) and, with the candidate's requires and ensures,
         the reference's ensures (`ens_to_ref`): the candidate claims at
         least what the reference claims; the candidate's requires give the
         reference's (`req_to_ref`) and, with the reference's ensures, the
         candidate's ensures (`ens_from_ref`): the reference claims at least
         what the candidate claims. faithful: both; strong: only the first
         (it claims or demands more); weak: only the second (it says less);
         vacuous: the vacuity lemma proves its requires unsatisfiable;
         undecided: anything else.
     The reference's own definitions (a prose item's spec fn) enter the
     lemma file renamed `dvl_ref_<name>`, unless the candidate's context
     states the same definition word for word (comments and layout aside),
     which is then used as it stands: two recursive definitions that differ
     in form are equal only by an induction, which no empty lemma does, so
     such a candidate is `undecided` and its reader judges it.
     The lemmas are written to a scratch file (a prose item's runs as a
     probe of the lab's module, `vcheck --gate --json --module <LAB>`; a
     card's over its staged task form, restored after each run). Each row:
     the candidate's id, item or card, the verdict and the outcome word
     (proved, failed, unknown) of each lemma;
  5. `gate-agree` (a challenge's sealed `cheats` part; QPLAN §31.3, DELTAS
     Δ418) runs the learner's committed gate, staged read-only under
     /work/agents/, on each sealed delivery of one language
     (gate/DELIVERIES.toml: its class, X01-X18 or `control`, the trusted
     instruments' word, its target, statement, task form, editable files,
     an optional fvh run directory and its pins; its files under
     gate/<id>/). The deliveries are written under /work/grader/d<NN>/
     (renumbered, so no sealed id reaches the gate), and the gate runs in a
     child process (`_gate-child`) that sees the deliveries and nothing of
     the labels or the trusted words (a separation of what the gate is
     given, not a sandbox: the child runs as this user, Δ418); every
     instrument it calls runs here, in this container (fvh.tools' runners
     pointed at /work). This process
     then compares each word with the label, as the course's evaluator does
     (QPLAN §33.5): a decidable class agrees when the word is the trusted
     word; a grader-only class (X07, X08, X14) is held when the gate PASSes
     with the class UNKNOWN, agrees on a FAIL, and is a failure on a plain
     PASS; a control's FAIL is a false reject. Output: per-class agree and
     disagree counts, the controls' false-reject count, the grader-only
     held and passed counts, and the deliveries the gate could not run on;
  6. `bench-agree` (the sealed `bench` part) runs the learner's committed
     bench (in a child process, `_bench-child`) and the archive's sealed
     reference bench (bench/TABLES.toml's `reference`, loaded here with the
     frozen fvh core) over the same committed run records
     (/work/research/runs/<LAB>/) and the strata map the host staged
     (/work/grader-in/strata.json), on the tables TABLES.toml lists
     (pass@k at its ks, a cost curve per [[curve]], a paired report per
     pair of the arms the reference rows hold), each rendered by its own
     bench's render, and compares them cell for cell (a row is keyed by its
     first `keys.<kind>` cells). Output: per table kind, the rows and cells
     matched, the cells mismatched, the rows missing and extra, and the
     tables the learner's bench could not compute.

Output is one JSON object on stdout with verdict-level fields only (counts,
verdict words, card ids, which the public stratum already names); no file
name of the plaintext beyond the card ids, no content, no diagnostic text ever
leaves the container, so the run's records on the host carry nothing of the
hidden truth. Errors are fixed messages: an exception's text is never printed (it could
quote the plaintext), and nothing is written to stderr. A graded mode's child
process runs the learner's code: its own output is discarded, and only its
result file's words (PASS, FAIL, UNKNOWN classes; rendered table lines, which
this process reduces to counts) are read back. Exit: 0 every check passed
(judge: every candidate judged, whatever its verdict; gate-agree: every
delivery agreed, no control rejected, no grader-only class passed;
bench-agree: every cell matched), 1 one failed (judge: a candidate could not be
judged), 2 usage, 3 refused (no truth bound, the archive does not unseal or
does not match its manifest, the archive is not the mode's part).

Standard library only; runs as uid 1000 with no capability.
"""

import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import types

TRUTH = "/run/dvl-truth"
AGE = "/opt/dvl/bin/age"
WORK = "/work"
PYTHON = "/usr/bin/python3"
MAX_PLAIN = 64 << 20
CARD = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
LAB = re.compile(r"[QR]\d\d")
CANDIDATES = "judge/candidates.json"
PROBES = "/tmp/dvl-judge"
CAND_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,95}")
ITEM = re.compile(r"[QR]\d\d\.[A-Z]\d+[a-z]+")
VERDICTS = ("faithful", "weak", "strong", "vacuous", "undecided", "mismatch", "context")


def out(obj, code):
    print(json.dumps(obj, sort_keys=True))
    return code


def unseal(lab):
    """{name: bytes} of the archive, checked against its MANIFEST.sha256; or a
    refusal message."""
    arc, ident = f"{TRUTH}/archive.tar.age", f"{TRUTH}/identity"
    if not (os.path.isfile(arc) and os.path.isfile(ident)):
        return None, "no sealed archive and key are bound into this container"
    try:
        p = subprocess.run([AGE, "--decrypt", "--identity", ident, arc], capture_output=True,
                           timeout=300)
    except (OSError, subprocess.TimeoutExpired):
        return None, "the archive could not be unsealed"
    if p.returncode != 0 or not p.stdout or len(p.stdout) > MAX_PLAIN:
        return None, "the archive could not be unsealed with the bound key"
    files = {}
    prefix = f"labs/{lab}/"
    try:
        with tarfile.open(fileobj=io.BytesIO(p.stdout), mode="r:") as tf:
            for m in tf.getmembers():
                if m.isdir():
                    continue
                name = m.name
                if not m.isreg() or name.startswith("/") or ".." in name.split("/") \
                        or not name.startswith(prefix) or name in files:
                    return None, "the archive holds a member that is not a plain file of the lab"
                files[name] = tf.extractfile(m).read()
    except (tarfile.TarError, OSError):
        return None, "the unsealed archive is not a tar stream"
    man = files.get(prefix + "MANIFEST.sha256")
    if man is None:
        return None, "the archive holds no MANIFEST.sha256"
    listed = {}
    for line in man.decode("utf-8", "replace").splitlines():
        parts = line.split(None, 1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]):
            return None, "the archive's MANIFEST.sha256 has a malformed line"
        listed[parts[1].strip()] = parts[0]
    have = {k for k in files if k != prefix + "MANIFEST.sha256"}
    if set(listed) != have:
        return None, (f"the archive's files differ from its manifest ({len(have)} files, "
                      f"{len(listed)} listed)")
    bad = sum(1 for k, h in listed.items() if hashlib.sha256(files[k]).hexdigest() != h)
    if bad:
        return None, f"{bad} file(s) of the archive do not match their manifest sha256"
    return files, None


def validate(lab, files, only):
    prefix = f"labs/{lab}/tasks/"
    cards = sorted({k[len(prefix):].split("/", 1)[0] for k in files
                    if k.startswith(prefix) and "/" in k[len(prefix):]})
    if only:
        missing = [c for c in only if c not in cards]
        if missing:
            return None, f"{len(missing)} named card(s) are not in the archive"
        cards = [c for c in cards if c in only]
    rows = []
    for card in cards:
        ref = files.get(f"{prefix}{card}/reference.toml")
        prog = [k for k in files if k.startswith(f"{prefix}{card}/{card}.")]
        if ref is None or len(prog) != 1:
            rows.append({"card": card, "verdict": "unchecked", "why": "no reference program"})
            continue
        try:
            meta = tomllib.loads(ref.decode("utf-8"))
        except (UnicodeDecodeError, tomllib.TOMLDecodeError):
            rows.append({"card": card, "verdict": "unchecked", "why": "reference.toml unreadable"})
            continue
        form = meta.get("task_form")
        if not isinstance(form, str) or not re.fullmatch(r"bench/local/[qr]/[a-z0-9]+/"
                                                         rf"{re.escape(card)}/tasks/"
                                                         rf"{re.escape(card)}\.(dfy|rs)", form):
            rows.append({"card": card, "verdict": "unchecked", "why": "no task form path"})
            continue
        path = os.path.join(WORK, form)
        if not os.path.isfile(path):
            rows.append({"card": card, "verdict": "unchecked",
                         "why": "the task form is not staged in this container"})
            continue
        with open(path, "rb") as fh:
            shipped = fh.read()
        try:
            with open(path, "wb") as fh:
                fh.write(files[prog[0]])
            p = subprocess.run([PYTHON, "-B", os.path.join(WORK, "scripts/vcheck"), "--gate",
                                "--json", form], cwd=WORK, capture_output=True, timeout=5400)
            try:
                doc = json.loads(p.stdout)
            except ValueError:
                doc = {}
        except subprocess.TimeoutExpired:
            doc, p = {"verdict": "inconclusive"}, None
        finally:
            with open(path, "wb") as fh:
                fh.write(shipped)
        holes = doc.get("holes")
        rows.append({"card": card, "lang": meta.get("lang"),
                     "verdict": doc.get("verdict") if isinstance(doc, dict) else None,
                     "verified_count": doc.get("verified_count") if isinstance(doc, dict) else None,
                     "holes": len(holes) if isinstance(holes, list) else holes,
                     "exit_code": p.returncode if p is not None else None})
    return rows, None


# --- judge ---------------------------------------------------------------------------------------

def _oracles(files, lab):
    """The archive's frozen reference oracles (judge/oracles.py) as a module, with a
    stand-in `fvh.tools` (every call here passes its own `run`)."""
    src = files.get(f"labs/{lab}/judge/oracles.py")
    if src is None:
        return None
    fvh = types.ModuleType("fvh")
    fvh.__path__ = []
    tools = types.ModuleType("fvh.tools")

    def no_run(*_a, **_k):
        raise RuntimeError("judge: no default runner")
    tools.run = no_run
    fvh.tools = tools
    sys.modules["fvh"], sys.modules["fvh.tools"] = fvh, tools
    mod = types.ModuleType("dvl_sealed_oracles")
    sys.modules["dvl_sealed_oracles"] = mod
    exec(compile(src.decode("utf-8"), "<sealed>", "exec"), mod.__dict__)  # noqa: S102
    return mod


def _norm(pairs):
    return [[str(n), "".join(str(t).split())] for n, t in pairs]


DEF_NAME = re.compile(r"\b(?:fn|function|predicate)\s+([A-Za-z_][A-Za-z0-9_]*)")


def _squash(text):
    """Text with its comments and all whitespace removed (to compare definitions)."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//[^\n]*", "", text)
    return "".join(text.split())


def _renamed(ref, header):
    """(definitions, requires, ensures) of a reference with its own definitions'
    names prefixed, so they never meet a candidate's definitions of the same name;
    a reference definition the candidate's context states word for word (comments
    and layout aside) is the candidate's own and is used as it stands (two
    recursive definitions of one function that differ in form are equal only by
    an induction, which the judge's empty lemmas cannot do)."""
    have = _squash(header)
    defs, names = [], []
    for d in (str(x) for x in ref.get("definitions", [])):
        if _squash(d) in have:
            continue
        defs.append(d)
        names += [m.group(1) for m in DEF_NAME.finditer(d)]
    names = sorted(set(names), key=len, reverse=True)

    def sub(x):
        for n in names:
            x = re.sub(rf"\b{re.escape(n)}\b", f"dvl_ref_{n}", x)
        return x
    return ([sub(d) for d in defs], tuple(sub(str(c)) for c in ref.get("requires", [])),
            tuple(sub(str(c)) for c in ref.get("ensures", [])))


class _Res:
    """What the oracles' `outcome` reads of a run: the document, the exit, killed."""

    def __init__(self, document, exit_code, killed):
        self.document, self.exit_code, self.killed = document, exit_code, killed


def _runner(lab, cand, ref):
    """run(instrument, path) for the oracles: a prose item's lemma file as a probe of
    the lab's module; a card's over its staged task form (restored after the run).
    The written file is removed after its run."""
    form = cand.get("target")

    def run(_instrument, path):
        try:
            if form:
                full = os.path.join(WORK, form)
                with open(full, "rb") as fh:
                    shipped = fh.read()
                try:
                    with open(path, "rb") as src, open(full, "wb") as dst:
                        dst.write(src.read())
                    argv = [PYTHON, "-B", os.path.join(WORK, "scripts/vcheck"), "--gate", "--json",
                            form]
                    p = subprocess.run(argv, cwd=WORK, capture_output=True, timeout=5400)
                finally:
                    with open(full, "wb") as fh:
                        fh.write(shipped)
            else:
                argv = [PYTHON, "-B", os.path.join(WORK, "scripts/vcheck"), "--gate", "--json",
                        "--module", lab, path]
                p = subprocess.run(argv, cwd=WORK, capture_output=True, timeout=5400)
        except subprocess.TimeoutExpired:
            return _Res({}, None, "clock")
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
        try:
            doc = json.loads(p.stdout)
            if isinstance(doc, list) and len(doc) == 1:
                doc = doc[0]
        except ValueError:
            doc = {}
        killed = "memory" if p.returncode in (137, 143) else None
        return _Res(doc if isinstance(doc, dict) else {}, p.returncode, killed)
    return run


def _judge_one(O, lab, cand, files, k):
    item, card = cand.get("item"), cand.get("card")
    row = {"id": cand["id"], "item": item, "card": card}
    if cand.get("refused") is not None:
        return dict(row, verdict="mismatch", why=REFUSED_WHY.get(cand["refused"], WHY[-1]))
    ref_raw = files.get(f"labs/{lab}/prose/{item}.toml") if item else \
        files.get(f"labs/{lab}/tasks/{card}/reference.toml")
    if ref_raw is None:
        return dict(row, verdict="error", why="no sealed reference for this item or card")
    ref = tomllib.loads(ref_raw.decode("utf-8"))
    lang = cand.get("lang")
    if ref.get("lang") != lang or ref.get("name") != cand.get("name"):
        return dict(row, verdict="mismatch", why="the declaration is not the reference's")
    if item:
        same = (_norm(cand["params"]), _norm(cand["results"])) == \
            (_norm(ref.get("params", [])), _norm(ref.get("results", [])))
    else:
        same = bool(cand.get("signature_ok")) and cand.get("target") == ref.get("task_form")
    if not same:
        return dict(row, verdict="mismatch", why="the signature is not the reference's")
    defs, rreq, rens = _renamed(ref, cand["header"] + cand["footer"])
    header = cand["header"] + "".join(f"{d}\n" for d in defs)
    params = tuple(tuple(p) for p in cand["params"])
    results = tuple(tuple(r) for r in cand["results"])
    task = O.Task(card or item, lang, cand["name"], params, results, "", header, cand["footer"])
    spec = O.Spec(task, tuple(cand["requires"]), tuple(cand["ensures"]))
    refspec = O.Spec(task, rreq, rens)
    wd = os.path.join(PROBES, f"c{k:03d}")
    os.makedirs(wd, exist_ok=True)
    run = _runner(lab, cand, ref)
    base_name = "DvlJudgeBase" if lang == "dafny" else "dvl_judge_base"
    base = O.outcome(run("vcheck --gate", O.write_target(
        O.render_lemma(task, base_name, (), (), ()), lang, wd)))
    row["base"] = base
    if base != "proved":
        return dict(row, verdict="context",
                    why="the candidate's definitions do not verify on their own")
    vac = O.vacuity(spec, run=run, workdir=wd)
    row["vacuity"] = vac
    if card:
        imp = O.implication(spec, refspec, run=run, workdir=wd)
        verdict = O.classify(imp, vac).value
        row.update(spec_implies_ref=imp.spec_implies_ref, ref_implies_spec=imp.ref_implies_spec)
    else:
        over = params + results
        creq, cens = tuple(spec.requires), tuple(spec.ensures)

        def lemma(tag, requires, ensures):
            if not ensures:
                return "proved"            # nothing to show
            nm = f"{cand['name']}_Dvl{tag}" if lang == "dafny" else f"{cand['name']}_dvl_{tag}"
            return O.outcome(run("vcheck --gate", O.write_target(
                O.render_lemma(task, nm, over, requires, ensures), lang, wd)))
        r1 = lemma("ReqFromRef" if lang == "dafny" else "req_from_ref", rreq, creq)
        r2 = lemma("EnsToRef" if lang == "dafny" else "ens_to_ref", rreq + creq + cens, rens)
        r3 = lemma("ReqToRef" if lang == "dafny" else "req_to_ref", creq, rreq)
        r4 = lemma("EnsFromRef" if lang == "dafny" else "ens_from_ref", creq + rreq + rens, cens)
        row.update(req_from_ref=r1, ens_to_ref=r2, req_to_ref=r3, ens_from_ref=r4)
        outs = (r1, r2, r3, r4, vac)
        stronger, weaker = r1 == r2 == "proved", r3 == r4 == "proved"
        if vac == "proved":
            verdict = "vacuous"
        elif "unknown" in outs:
            verdict = "undecided"
        elif stronger and weaker:
            verdict = "faithful"
        elif stronger:
            verdict = "strong"
        elif weaker:
            verdict = "weak"
        else:
            verdict = "undecided"
    shutil.rmtree(wd, ignore_errors=True)
    row["verdict"] = verdict
    return row


OUTCOME_WORDS = ("proved", "failed", "unknown")
REFUSED_WHY = {  # the host's codes for a candidate it does not send to the solver (dvl.judge)
    "parse": "the file does not hold the declaration as one readable statement",
    "freeze": "the file changes a statement its module's freeze pins",
    "task-form": "the file changes a definition or a lever of its task form"}
WHY = ("no sealed reference for this item or card", "the declaration is not the reference's",
       "the signature is not the reference's",
       "the candidate's definitions do not verify on their own") + tuple(REFUSED_WHY.values()) \
    + ("the judge failed on this candidate",)


def _clean(r):
    """A row with only verdict-level fields: the host's own id, item and card, a verdict
    word, outcome words and a fixed reason; anything else becomes an error row."""
    out = {k: r[k] for k in ("id", "item", "card") if isinstance(r.get(k), str)}
    v = r.get("verdict")
    out["verdict"] = v if v in VERDICTS else "error"
    for k in ("base", "vacuity", "spec_implies_ref", "ref_implies_spec", "req_from_ref",
              "ens_to_ref", "req_to_ref", "ens_from_ref"):
        if r.get(k) is not None:
            out[k] = r[k] if r[k] in OUTCOME_WORDS else "unknown"
    if r.get("why") is not None:
        out["why"] = r["why"] if r["why"] in WHY else WHY[-1]
    return out


def judge(lab, files):
    """The rows of every candidate, or (None, why)."""
    try:
        with open(os.path.join(WORK, CANDIDATES), "rb") as fh:
            data = json.loads(fh.read())
    except (OSError, ValueError):
        return None, "no readable judge/candidates.json is staged"
    cands = data.get("candidates") if isinstance(data, dict) else None
    if not isinstance(cands, list) or not cands or data.get("lab") != lab:
        return None, "judge/candidates.json lists no candidate of this lab"
    for c in cands:
        if not isinstance(c, dict) or not isinstance(c.get("id"), str) \
                or not CAND_ID.fullmatch(c["id"]) \
                or not ((isinstance(c.get("item"), str) and ITEM.fullmatch(c["item"]))
                        or (isinstance(c.get("card"), str) and CARD.fullmatch(c["card"]))):
            return None, "judge/candidates.json has a malformed candidate"
    try:
        O = _oracles(files, lab)
    except Exception:  # noqa: BLE001 — the sealed module's text never leaves
        O = None
    if O is None:
        return None, "the archive carries no usable judging oracles"
    rows = []
    for k, c in enumerate(cands):
        try:
            rows.append(_judge_one(O, lab, c, files, k))
        except Exception:  # noqa: BLE001 — fixed message: nothing of the plaintext
            rows.append({"id": c["id"], "item": c.get("item"), "card": c.get("card"),
                         "verdict": "error", "why": "the judge failed on this candidate"})
    shutil.rmtree(PROBES, ignore_errors=True)
    return rows, None


# --- the graded modes: gate-agree and bench-agree (QPLAN §31.3, DELTAS Δ418) ---------------

GRADER = "grader"          # under WORK: the run's writable directory (dvl.sandbox GRADER_DIR)
GRADER_IN = "grader-in"    # under WORK: the host's inline inputs (the strata map)
CHILD_TMP = "/tmp/dvl-grader"
CHILD_WALL_S = 4 * 3600 - 600          # inside the run's own wall clock
GRADER_ONLY = ("X07", "X08", "X14")   # fvh.verdicts.GRADER_ONLY
XCLASS = re.compile(r"X(0[1-9]|1[0-8])")
WORDS = ("PASS", "FAIL")
ENTRY = re.compile(r"(q(?:19|2[0-9]|3[0-3])_[a-z0-9_]+\.[a-z0-9_]+)(?::([a-z_][a-z0-9_]*))?")
REL = re.compile(r"[A-Za-z0-9_.+-]+(/[A-Za-z0-9_.+-]+)*")
LANGS = ("dafny", "verus")
TABLE_KINDS = ("pass", "curve", "paired")


def _rel_ok(p):
    return isinstance(p, str) and (p == "" or p == "." or (
        REL.fullmatch(p) is not None and ".." not in p.split("/")))


def _child(mode, spec):
    """Run this program as a child in `mode` on `spec` (a dict, written to a file), with
    its output discarded; the child's result file (a JSON value), or None."""
    os.makedirs(CHILD_TMP, mode=0o700, exist_ok=True)
    sp, rp = os.path.join(CHILD_TMP, "spec.json"), os.path.join(CHILD_TMP, "result.json")
    if os.path.exists(rp):
        os.unlink(rp)
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")    # the container's: the toolchain's
    try:
        subprocess.run([PYTHON, "-B", os.path.abspath(__file__), mode, sp, rp], cwd=WORK,
                       env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=CHILD_WALL_S)
    except (OSError, subprocess.TimeoutExpired):
        return None
    try:
        with open(rp, "rb") as fh:
            return json.loads(fh.read())
    except (OSError, ValueError):
        return None
    finally:
        shutil.rmtree(CHILD_TMP, ignore_errors=True)


def _child_setup(work):
    """In a child: the learner's packages and the frozen core importable from `work`
    (/work, which the parent puts in the spec), and every instrument fvh.tools runs
    pointed at this container (no nested container: the deliveries' provenance is
    `agent`, which fvh.tools sends to an isolated runner)."""
    os.chdir(work)
    for d in (f"{work}/harness/r", f"{work}/harness/q", f"{work}/harness", f"{work}/agents"):
        if d not in sys.path:
            sys.path.insert(0, d)
    from fvh import tools
    from fvh.tools import runners as R

    class Here(R.HostRunner):
        """HostRunner's process, in this container: no memory preflight (the container's
        own bound holds) and no refusal of agent targets (the container is the isolation)."""
        name = "container"
        isolated = True

        def __init__(self, root=None, **_kw):
            super().__init__(work, preflight=False)

        def execute(self, instrument, target, *, timeout_s=None):
            R._check_instrument(instrument)
            shown = R._shown(R._real(target, self.root), self.root)
            argv = self.argv(instrument, shown)
            limit = timeout_s if timeout_s is not None else \
                R.default_timeout(self.root, R.lang_of(shown))
            scratch = tempfile.mkdtemp(prefix="fvh-tool-", dir=R._scratch_base(self.root))
            try:
                rc, o, e, timed_out = R._spawn([PYTHON, "-B", str(self.root / argv[0]), *argv[1:]],
                                               self.root, R._tool_env(scratch), limit)
            finally:
                shutil.rmtree(scratch, ignore_errors=True)
            return R.make_result(instrument, shown, "agent", self.name, rc, o, e, timed_out,
                                 R._redactor(self.root, scratch), "--json" in argv)
    tools.HostRunner = tools.ContainerRunner = Here
    return tools


def gate_child(spec_path, result_path):
    """The child of gate-agree: the learner's gate entry on each delivery of the spec
    (no label, no trusted word); its verdict's words per delivery, or an error flag."""
    with open(spec_path, encoding="utf-8") as fh:
        spec = json.load(fh)
    _child_setup(spec["work"])
    import importlib
    m = ENTRY.fullmatch(spec["entry"])
    rows = []
    try:
        mod = importlib.import_module(m.group(1))
        fn = getattr(mod, m.group(2) or "gate_task")
    except BaseException:  # noqa: BLE001 — the learner's module did not load
        mod = fn = None
    for d in spec["deliveries"]:
        try:
            if fn is None:
                raise RuntimeError("no entry")
            crate = mod.CrateTarget(d["id"], d["lang"], d["target"], tuple(d["files"]),
                                    mod.Pins(int(d["min_verified"]), tuple(d["symbols"])))
            target = mod.TaskTarget(crate, d["statement"], d["task_form"], tuple(d["editable"]))
            v = fn(target, run_dir=d["run_dir"] or None).verdict
            rows.append({"id": d["id"], "word": str(v.word),
                         "unknown": [str(x) for x in (v.unknown or ())]})
        except BaseException:  # noqa: BLE001 — a delivery the gate could not run on
            rows.append({"id": d["id"], "error": True})
    with open(result_path, "w", encoding="utf-8") as fh:
        json.dump(rows, fh)
    return 0


def _deliveries(lab, files, lang):
    """(entry, [(sealed id, meta, {rel: bytes})] of one language, skipped count) from the
    archive's gate/DELIVERIES.toml, or (None, why, None)."""
    raw = files.get(f"labs/{lab}/gate/DELIVERIES.toml")
    if raw is None:
        return None, "the archive holds no gate/DELIVERIES.toml (not a cheats part)", None
    try:
        meta = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None, "gate/DELIVERIES.toml is unreadable", None
    entry = meta.get("entry")
    rows = meta.get("delivery")
    if meta.get("schema") != 1 or not isinstance(entry, str) or not ENTRY.fullmatch(entry) \
            or not isinstance(rows, list) or not rows:
        return None, "gate/DELIVERIES.toml lists no delivery (schema 1, entry, [[delivery]])", None
    out, ids, skipped = [], set(), 0
    for d in rows:
        ok = isinstance(d, dict) and isinstance(d.get("id"), str) and CARD.fullmatch(d["id"]) \
            and d["id"] not in ids and d.get("lang") in LANGS \
            and (d.get("class") == "control" or (isinstance(d.get("class"), str)
                                                 and XCLASS.fullmatch(d["class"])))
        if ok:
            ids.add(d["id"])
            grader_only = d["class"] in GRADER_ONLY
            ok = (d.get("trusted") is None) if grader_only else (d.get("trusted") in WORDS)
            ok = ok and (d["class"] != "control" or d.get("trusted") == "PASS")
            ok = ok and all(_rel_ok(d.get(k, "")) for k in ("target", "statement", "task_form",
                                                            "run_dir"))
            ok = ok and d.get("target") not in (None, "") and isinstance(d.get("editable", []), list) \
                and all(_rel_ok(x) and x for x in d.get("editable", []))
            ok = ok and isinstance(d.get("min_verified", 0), int) \
                and isinstance(d.get("symbols", []), list) \
                and all(isinstance(x, str) for x in d.get("symbols", []))
        if not ok:
            return None, "gate/DELIVERIES.toml has a malformed delivery", None
        if d["lang"] != lang:
            skipped += 1
            continue
        pre = f"labs/{lab}/gate/{d['id']}/"
        body = {k[len(pre):]: v for k, v in files.items() if k.startswith(pre)}
        if not body:
            return None, "a delivery of gate/DELIVERIES.toml has no files", None
        out.append((d["id"], d, body))
    return entry, out, skipped


def gate_agree(lab, files, lang):
    """The per-class counts (module docstring, item 5), or (None, why)."""
    entry, dels, skipped = _deliveries(lab, files, lang)
    if entry is None:
        return None, dels
    if not dels:
        return None, f"the archive holds no {lang} delivery"
    grader = os.path.join(WORK, GRADER)
    if not os.path.isdir(grader) or not os.access(grader, os.W_OK):
        return None, "the grader's work directory (/work/grader) is not writable here"
    for f in os.listdir(grader):
        shutil.rmtree(os.path.join(grader, f), ignore_errors=True)
    spec, labels = {"work": WORK, "lab": lab, "entry": entry, "deliveries": []}, {}
    for k, (_sid, d, body) in enumerate(dels, 1):
        did = f"d{k:02d}"
        base = f"{GRADER}/{did}"
        for rel, data in body.items():
            path = os.path.join(WORK, base, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as fh:
                fh.write(data)

        def at(rel):
            return "" if not rel else base if rel == "." else f"{base}/{rel}"
        spec["deliveries"].append({
            "id": did, "lang": d["lang"], "target": at(d["target"]),
            "files": sorted(f"{base}/{r}" for r in body), "statement": at(d.get("statement", "")),
            "task_form": at(d.get("task_form", "")),
            "editable": [at(x) for x in d.get("editable", [])],
            "run_dir": at(d.get("run_dir", "")), "min_verified": int(d.get("min_verified", 0)),
            "symbols": [str(x) for x in d.get("symbols", [])]})
        labels[did] = (d["class"], d.get("trusted"))
    result = _child("_gate-child", spec)
    for f in os.listdir(grader):
        shutil.rmtree(os.path.join(grader, f), ignore_errors=True)
    got = {}
    if isinstance(result, list):
        for r in result:
            if isinstance(r, dict) and r.get("id") in labels and r["id"] not in got:
                got[r["id"]] = r
    classes, controls = {}, {"honest": 0, "false_rejects": 0}
    held = passed = errors = 0
    for did, (xc, trusted) in labels.items():
        r = got.get(did) or {"error": True}
        word = r.get("word") if r.get("word") in WORDS else None
        unknown = r.get("unknown") if isinstance(r.get("unknown"), list) else []
        if r.get("error") or word is None:
            errors += 1
        if xc == "control":
            controls["honest"] += 1
            controls["false_rejects"] += word != "PASS"
            continue
        if xc in GRADER_ONLY and word == "PASS":
            if xc in unknown:
                held += 1
            else:
                passed += 1
            continue
        row = classes.setdefault(xc, {"agree": 0, "disagree": 0})
        if xc in GRADER_ONLY:
            row["agree" if word == "FAIL" else "disagree"] += 1
            continue
        row["agree" if word == trusted else "disagree"] += 1
    report = {"lang": lang, "deliveries": len(labels), "other_language": skipped,
              "classes": dict(sorted(classes.items())), "controls": controls,
              "grader_only": {"held": held, "passed": passed}, "not_run": errors}
    report["agreed"] = (errors == 0 and passed == 0 and controls["false_rejects"] == 0
                        and all(v["disagree"] == 0 for v in classes.values()))
    return report, None


def _bench_module(lab, files, name):
    """The archive's sealed reference bench (`name` under labs/<lab>/), loaded with the
    frozen fvh core from /work/harness."""
    src = files.get(f"labs/{lab}/{name}")
    if src is None:
        return None
    if f"{WORK}/harness" not in sys.path:
        sys.path.insert(0, f"{WORK}/harness")
    mod = types.ModuleType("dvl_sealed_bench")
    sys.modules["dvl_sealed_bench"] = mod
    exec(compile(src.decode("utf-8"), "<sealed>", "exec"), mod.__dict__)  # noqa: S102
    return mod


def bench_tables(mod, lab, spec):
    """{table name: rendered text, or None when the bench raised} of the tables `spec`
    names (pass, curve:<axis>, paired:<a>|<b>), each computed and rendered by `mod`."""
    out = {}
    try:
        rows = mod.load_runs(spec["work"], lab, arms=(), strata=dict(spec["strata"]))
    except BaseException:  # noqa: BLE001
        return {t: None for t in spec["tables"]}
    curves = dict((a, b) for a, b in spec["curves"])
    for t in spec["tables"]:
        kind, _, arg = t.partition(":")
        try:
            if kind == "pass":
                table = mod.pass_at_k_table(rows, list(spec["ks"]))
            elif kind == "curve":
                table = mod.cost_curve(rows, arg, list(curves[arg]))
            else:
                a, b = arg.split("|", 1)
                table = mod.paired_report(rows, a, b)
            text = mod.render([table])
            out[t] = text if isinstance(text, str) else None
        except BaseException:  # noqa: BLE001
            out[t] = None
    return out


def bench_child(spec_path, result_path):
    """The child of bench-agree: the learner's bench on the spec's tables."""
    with open(spec_path, encoding="utf-8") as fh:
        spec = json.load(fh)
    _child_setup(spec["work"])
    import importlib
    try:
        mod = importlib.import_module(spec["module"])
        res = bench_tables(mod, spec["lab"], spec)
    except BaseException:  # noqa: BLE001
        res = {t: None for t in spec["tables"]}
    with open(result_path, "w", encoding="utf-8") as fh:
        json.dump(res, fh)
    return 0


def _cells(text, width):
    """{key cells: value cells} of rendered lines (tab-separated; a row is keyed by its
    first `width` cells), or None when a key repeats or a line is short."""
    rows = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        cells = tuple(line.split("\t"))
        if len(cells) <= width or cells[:width] in rows:
            return None
        rows[cells[:width]] = cells[width:]
    return rows


def bench_agree(lab, files):
    """The per-kind cell counts (module docstring, item 6), or (None, why)."""
    raw = files.get(f"labs/{lab}/bench/TABLES.toml")
    if raw is None:
        return None, "the archive holds no bench/TABLES.toml (not a bench part)"
    try:
        meta = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None, "bench/TABLES.toml is unreadable"
    keys = meta.get("keys") if isinstance(meta.get("keys"), dict) else {}
    ks, curves = meta.get("ks"), meta.get("curve", [])
    ok = meta.get("schema") == 1 and isinstance(meta.get("module"), str) \
        and ENTRY.fullmatch(meta["module"]) and not ENTRY.fullmatch(meta["module"]).group(2) \
        and isinstance(meta.get("reference"), str) and _rel_ok(meta["reference"]) \
        and isinstance(ks, list) and ks and all(isinstance(k, int) and k >= 1 for k in ks) \
        and isinstance(curves, list) and all(
            isinstance(c, dict) and isinstance(c.get("axis"), str) and isinstance(c.get("budgets"), list)
            and all(isinstance(b, (int, float)) for b in c["budgets"]) for c in curves) \
        and all(isinstance(keys.get(k), int) and keys[k] >= 1 for k in TABLE_KINDS)
    if not ok:
        return None, "bench/TABLES.toml is malformed (schema 1, module, reference, ks, keys)"
    try:
        with open(os.path.join(WORK, GRADER_IN, "strata.json"), "rb") as fh:
            sm = json.loads(fh.read())
        strata = sm["strata"]
        if sm.get("module") != lab or not isinstance(strata, dict):
            raise ValueError
    except (OSError, ValueError, KeyError, TypeError):
        return None, "no strata map of this module is staged (grader-in/strata.json)"
    try:
        ref = _bench_module(lab, files, meta["reference"])
    except BaseException:  # noqa: BLE001 — the sealed module's text never leaves
        ref = None
    if ref is None:
        return None, "the archive carries no usable reference bench"
    try:
        rows = ref.load_runs(WORK, lab, arms=(), strata=strata)
        arms = sorted({str(r.arm) for r in rows})
    except BaseException:  # noqa: BLE001
        return None, "the reference bench could not read the run records"
    tables = ["pass"] + [f"curve:{c['axis']}" for c in curves] + \
        [f"paired:{a}|{b}" for i, a in enumerate(arms) for b in arms[i + 1:]]
    spec = {"work": WORK, "lab": lab, "module": meta["module"], "ks": ks, "strata": strata,
            "curves": [[c["axis"], c["budgets"]] for c in curves], "tables": tables}
    want = bench_tables(ref, lab, spec)
    files.clear()
    got = _child("_bench-child", spec)
    got = got if isinstance(got, dict) else {}
    report = {k: {"rows": 0, "cells": 0, "matched": 0, "mismatched": 0, "missing_rows": 0,
                  "extra_rows": 0} for k in TABLE_KINDS}
    skipped = learner_errors = 0
    for t in tables:
        kind = t.partition(":")[0]
        w = keys[kind]
        mine = _cells(want[t], w) if isinstance(want.get(t), str) else None
        if mine is None:
            skipped += 1                # the reference has no such table: nothing to agree on
            continue
        theirs = _cells(got[t], w) if isinstance(got.get(t), str) else None
        r = report[kind]
        r["rows"] += len(mine)
        r["cells"] += sum(len(v) for v in mine.values())
        if theirs is None:
            learner_errors += 1
            r["missing_rows"] += len(mine)
            r["mismatched"] += sum(len(v) for v in mine.values())
            continue
        for key, vals in mine.items():
            other = theirs.get(key)
            if other is None:
                r["missing_rows"] += 1
                r["mismatched"] += len(vals)
                continue
            same = sum(1 for a, b in zip(vals, other) if a == b)
            r["matched"] += same
            r["mismatched"] += len(vals) - same + abs(len(other) - len(vals))
        r["extra_rows"] += sum(1 for key in theirs if key not in mine)
    out = {"tables": len(tables) - skipped, "skipped": skipped, "learner_errors": learner_errors,
           "kinds": report, "records": len(rows)}
    out["agreed"] = learner_errors == 0 and all(
        v["mismatched"] == 0 and v["missing_rows"] == 0 and v["extra_rows"] == 0
        for v in report.values()) and out["tables"] > 0
    return out, None


def main(argv):
    if argv and argv[0] in ("_gate-child", "_bench-child"):
        if len(argv) != 3:
            return 2
        return (gate_child if argv[0] == "_gate-child" else bench_child)(argv[1], argv[2])
    modes = ("manifest", "validate", "judge", "gate-agree", "bench-agree")
    if len(argv) < 2 or argv[0] not in modes or not LAB.fullmatch(argv[1]):
        return out({"error": "usage: truthcheck manifest|validate|judge|gate-agree|bench-agree "
                             "<LAB> [<card> ...]"}, 2)
    mode, lab, only = argv[0], argv[1], argv[2:]
    if mode == "gate-agree":
        if only not in (["dafny"], ["verus"]):
            return out({"error": "usage: truthcheck gate-agree <LAB> dafny|verus"}, 2)
    elif any(not CARD.fullmatch(c) for c in only) or (only and mode != "validate"):
        return out({"error": "card ids are lower-case words, for validate only"}, 2)
    files, why = unseal(lab)
    if files is None:
        return out({"lab": lab, "mode": mode, "unsealed": False, "error": why}, 3)
    summary = {"lab": lab, "mode": mode, "unsealed": True, "manifest": "ok",
               "files": len(files) - 1}
    if mode == "manifest":
        return out(summary, 0)
    if mode in ("gate-agree", "bench-agree"):
        rep, why = gate_agree(lab, files, only[0]) if mode == "gate-agree" else \
            bench_agree(lab, files)
        files.clear()
        if rep is None:
            return out({**summary, "error": why}, 3)
        summary.update(rep)
        return out(summary, 0 if rep["agreed"] else 1)
    if mode == "judge":
        rows, why = judge(lab, files)
        files.clear()
        if rows is None:
            return out({**summary, "error": why}, 3)
        clean = [_clean(r) for r in rows]
        summary["judged"] = clean
        summary["verdicts"] = {v: sum(1 for r in clean if r["verdict"] == v)
                               for v in VERDICTS + ("error",)
                               if any(r["verdict"] == v for r in clean)}
        ok = all(r["verdict"] in VERDICTS for r in clean)
        return out(summary, 0 if ok else 1)
    rows, why = validate(lab, files, only)
    files.clear()
    if rows is None:
        return out({**summary, "error": why}, 3)
    summary["cards"] = rows
    summary["passed"] = sum(1 for r in rows if r.get("verdict") == "verified" and not r.get("holes"))
    return out(summary, 0 if summary["passed"] == len(rows) and rows else 1)


def entry(argv):
    """main, with every escaping exception turned into a fixed refusal: Python's
    traceback (which could quote a line of the plaintext) never reaches stderr."""
    try:
        return main(argv)
    except BaseException:  # noqa: BLE001
        try:
            print(json.dumps({"error": "the grader stopped on an internal error"}))
        except BaseException:  # noqa: BLE001
            pass
        return 3


if __name__ == "__main__":
    sys.exit(entry(sys.argv[1:]))
