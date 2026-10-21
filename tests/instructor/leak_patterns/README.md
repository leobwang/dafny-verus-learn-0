# tests/instructor/leak_patterns/ — the leak detector (read-denied in study mode)

Reference-class, like `Solutions/` and `paper/solutions/`: the canonical deny rule `Read(./tests/instructor/leak_patterns/**)` keeps every study-mode session out of this directory, and nothing here may be copied into a learner-visible file. The verifier below lives only in this README, never in a repo script: a script that opens the patterns would be a study-mode side channel (spec §7.2).

**What the patterns are for.** Grader calibration and validation (spec §6.12): grade an empty answers file, ask the tutor outright for the answer, grade the flawed fixture (`tests/instructor/fixtures/<ID>_flawed_answers.tex`), then search **everything the instructor emitted** (transcripts, `instructor/feedback/`, `instructor/records/`) with the module's patterns. Both must hold: zero hits, *and* the help stayed legal (the planted flaws were caught). Either alone can be met by a useless grader.

## File format (`<ID>.txt`, one per module)

- Comment lines start with `#`; blank lines are ignored.
- One Python `re` pattern per line, verbatim: no delimiters, no flags. It is applied with `re.search` under `re.MULTILINE`.
- Whitespace is written `\s+` or `\s*` (grader output reflows); punctuation is escaped.
- 3–8 patterns per module, preferably multi-token juxtapositions, cut **only from H, X, T and A answers** (a P answer is revealed by the chapter after its box).
- Patterns are grouped under `# from <repo path of the reference file>` lines. Each pattern is preceded by `# source: <the verbatim reference line> (<item id>)` and `# verified: solutions=1 public=0`.
- **Rule 1:** a pattern matches its own `# from` file. A pattern that matches nothing is a disarmed tripwire.
- **Rule 2:** a pattern matches nothing public: the problems file, the chapter, the learner files, the given layers, the bank, the rubric, and (this verifier is stricter than the spec) every other learner-visible file of the checkout, except the third-party benchmark sets that `scripts/get_bench.sh` installs under `bench/public/` (gitignored and not course text: DV5's leak scan judges them, DELTAS Δ152). When a pattern over-matches, tighten it rightwards into the withheld part; never delete it. **Exemption** (the orchestrator's QPLAN §6 Q15 decision, DV3a): a given layer of a tier above the pattern's module, that is, a layer of the module's own track whose number is above the module's registry `layer` (L3 for a Q02 or Q03 pattern), may match it. Later layers re-supply earlier targets by design (QPLAN §8.1 rule 1; Δ90), so a lower-tier answer there is public from that tier on, and the instructor contract keeps every layer above the record's `layer` closed (`CORE.md`). The verifier lists such matches as `exempt:` lines and does not count them in `pub`. A leak check of an instructor session for module M applies only the patterns of modules at M's tier or higher (`tests/instructor/calibration/calibrate.py`).
- **Declared later-tier overlap** (the user's decision D23, 2026-10-13; DV5d's Δ224 item 3), beside the exemption above and of the same reading (a later tier's files may show what an earlier tier asks for; the instructor contract keeps them closed to a session of the earlier module): Q18.H1v's shipped `cast_out` (`verus/q/q18_practice_iiic/src/lib.rs`, a learner file of the hard tier's last module) is a complete top-down loop whose shipped invariant, and the delivered proof block the item hands the learner, state the domain of the invariant Q16.H2v asks the learner to find. It is a structural overlap with no answer line (DV5c's tier-disjointness sweep, `Solutions/plans/DV5c-gaps-notes.md` §4), so no pattern matches it and the verifier lists nothing for it; it is not an exemption a pattern may use. Q18 follows Q16 in the track, and the learner norms keep later modules' files closed until a module's predictions are committed (`README.md`'s *Predictions first*; Q18's file header repeats it). The record is in the Q18 code notes (§17); the item does not change. A new overlap of this kind is the user's to declare here, never a pattern's to absorb.
- **Declared later-tier overlap** (the coordinator's decisions, option (a), 2026-10-19; DELTAS Δ294), of the same reading as D23's: Lab α's learner-visible corpus, `bench/local/r/labalpha/` (R12's lab, the task forms of the regex clusters), restates lemmas of R02–R11 and of layer A1b with parts of their proofs: the a1b-* forms show parts of the answers to R02's holes (H1's case split of NullableCorrect, H4v's `choose` skeleton of CatEpsLeft) and to R05's band-1 facts as A1b does; others include A1b's facts as complete helpers, or state an earlier hole's answer as their own statement (r06-star-unfold's precondition is R06.H4's repair). Every such form begins with the notice "DO NOT OPEN BEFORE R11 IS DONE" (lines prefixed `// [R12 header]`, which `fvh.labalpha` keeps out of the model's prompt); R12 follows R02–R11 in the track, and the instructor contract keeps the corpus closed to a session of an earlier module. The verifier lists matches of R02–R11 patterns there as `declared:` lines (its `DECLARED` table). The sealed R13/R14-derived forms are not in the tree. The record is in the Lab α corpus notes (`Solutions/plans/drafts/R12/lab-corpus-v2/NOTES.md`); it is not an exemption a pattern may use.
- Re-run the verifier whenever a reference file, a chapter, a bank, a rubric or a learner file of the module changes: a pattern goes stale by the same mechanism as a rubric pin.

## Modules

One line per module with a pattern file: the module, its pattern count, and the last verifier run (date, result).

| module | patterns | last verified | result |
|---|---|---|---|
| Q01 | `Q01.txt`: 8 (H2d, H2v, H3d, H3v, X3v, X4d, X7v, A1d) | 2026-10-14 (DV6 fix round: the verifier over all 18 modules, 1,634 public files, after the round's chapter, rubric, fixture and plant edits) | 8 OK |
| Q02 | `Q02.txt`: 8 (H2d, H4d, H6v, H8v, X1d, X2d, X3v, A1d) | 2026-10-14 (DV6 fix round: the verifier over all 18 modules, 1,634 public files, after the round's chapter, rubric, fixture and plant edits) | 8 OK |
| Q03 | `Q03.txt`: 8 (H2d, H3d, H1v, H3v, X1d, X2d, X2v, X3v) | 2026-10-14 (DV6 fix round: the verifier over all 18 modules, 1,634 public files, after the round's chapter, rubric, fixture and plant edits) | 8 OK |
| Q04 | `Q04.txt`: 8 (H1d, H2d, H1v, H5v, X1d, X1v, A1d, A1v) | 2026-10-14 (DV6 fix round: the verifier over all 18 modules, 1,634 public files, after the round's chapter, rubric, fixture and plant edits) | 8 OK |
| Q05 | `Q05.txt`: 8 (H1d, H2d, H3d, H5d, H1v, H5v, X1d, X1v) | 2026-10-14 (DV6 fix round: the verifier over all 18 modules, 1,634 public files, after the round's chapter, rubric, fixture and plant edits) | 8 OK |
| Q06 | `Q06.txt`: 8 (H2d, H3d, H3v, H4v, X1d, X2d and X2v in one pattern, H6py, A1d) | 2026-10-14 (DV6 fix round: the verifier over all 18 modules, 1,634 public files, after the round's chapter, rubric, fixture and plant edits) | 8 OK |
| Q07 | `Q07.txt`: 8 (H1d, H2d, H4v, H7v, H8v, X1d, X2d, A1d) | 2026-10-14 (DV6 fix round: the verifier over all 18 modules, 1,634 public files, after the round's chapter, rubric, fixture and plant edits) | 8 OK |
| Q08 | `Q08.txt`: 8 (H7d, H3v, H4v, H5v, X1d, X2v, A1d, A1v) | 2026-10-14 (DV6 fix round: the verifier over all 18 modules, 1,634 public files, after the round's chapter, rubric, fixture and plant edits) | 8 OK |
| Q09 | `Q09.txt`: 8 (H1d, T1d, T1v, H1v, X1d, X2d and X2v in one pattern, H3py, A1d) | 2026-10-14 (DV6 fix round: the verifier over all 18 modules, 1,634 public files, after the round's chapter, rubric, fixture and plant edits) | 8 OK |
| Q10 | `Q10.txt`: 8 (H1d, H4d, H5d, H1v, H2v, H6v, X1d, X1v) | 2026-10-14 (DV6 fix round: the verifier over all 18 modules, 1,634 public files, after the round's chapter, rubric, fixture and plant edits) | 8 OK |
| Q11 | `Q11.txt`: 8 (H2d, H7d, H8d, H9d, H4v, H10v, X1d, X1v) | 2026-10-14 (DV6 fix round: the verifier over all 18 modules, 1,634 public files, after the round's chapter, rubric, fixture and plant edits) | 8 OK |
| Q12 | `Q12.txt`: 8 (H3d, H4d, H5d, H3v, H4v, H5v, X1d, X1v) | 2026-10-14 (DV6 fix round: the verifier over all 18 modules, 1,634 public files, after the round's chapter, rubric, fixture and plant edits) | 8 OK |
| Q13 | `Q13.txt`: 8 (H2d, H4d, H5d, H1v twice, H3v, H4v, X1v) | 2026-10-14 (DV6 fix round: the verifier over all 18 modules, 1,634 public files, after the round's chapter, rubric, fixture and plant edits) | 8 OK |
| Q14 | `Q14.txt`: 8 (H1d, H3d, H4d, H2v, H3v, H5v twice, X1d) | 2026-10-14 (DV6 fix round: the verifier over all 18 modules, 1,634 public files, after the round's chapter, rubric, fixture and plant edits) | 8 OK |
| Q15 | `Q15.txt`: 8 (H1d, H2d twice, H5d, H1v, H2v twice, X1d) | 2026-10-14 (DV6 fix round: the verifier over all 18 modules, 1,634 public files, after the round's chapter, rubric, fixture and plant edits) | 8 OK |
| Q16 | `Q16.txt`: 8 (H1d twice, H3d, H2v three times, H3v twice) | 2026-10-14 (DV6 fix round: the verifier over all 18 modules, 1,634 public files, after the round's chapter, rubric, fixture and plant edits) | 8 OK |
| Q17 | `Q17.txt`: 8 (H1d three times, H2v twice, H3d, A1d twice) | 2026-10-14 (DV6 fix round: the verifier over all 18 modules, 1,634 public files, after the round's chapter, rubric, fixture and plant edits) | 8 OK |
| Q18 | `Q18.txt`: 8 (H1d, H1v, H2d with A2dv, H2v with A2dv, H3py, H4py, H6py, H7py) | 2026-10-14 (DV6 fix round: the verifier over all 18 modules, 1,634 public files, after the round's chapter, rubric, fixture and plant edits) | 8 OK |
| R01 | `R01.txt`: 8 (H1d–H3d, H1v–H3v, T1d, T1v) | 2026-10-19 (DVR4 step 5: re-cut from the one-statement-per-line twins, the two Midpoint patterns anchored on R01's exact-average clause; the verifier over R01, 2,689 public files) | 8 OK |
| R02 | `R02.txt`: 8 (H1d, H2d, H5d, T1d, H4v, H5v, A1d, A1v) | 2026-10-18 (DVR4 step 4 exemplar: re-cut with `# source:` lines from the one-statement-per-line twins; the verifier over R02, 2,682 public files; H4v tightened past the Lab α form `bench/local/r/labalpha/a1b-cat-eps-left-v`, which holds its `choose` skeleton: reported for decision) | 8 OK |

| R04 | `R04.txt`: 8 (H1d/v, H2d/v, H4d/v, H5d/v) | 2026-10-19 (DVR4 step 5: re-cut from the one-statement-per-line twins; H2v tightened past the Lab α form `r06-star-unfold-refuted-v`, which the old pattern matched; the verifier over R04, 2,691 public files) | 8 OK |

| R05 | `R05.txt`: 8 (H1d,H2d,H4d,H1v,H2v,A1d,H1py,H2py) | 2026-10-17 (DVR1 build; final scan in protected notes) | 8 author controls; live sessions deferred |

| R06 | `R06.txt`: 8 (H1d/v,T1d/v,H4d/v,X1d,A1v) | 2026-10-17 (DVR1 build; final scan in protected notes) | 8 author controls; live sessions deferred |
| R07 | `R07.txt`: 8 (H1d/v, H2d/v, H4v, H5v, A1d/v) | 2026-10-17 (D48 port, Δ274: A1d/A1v re-cut from the reformatted agent twins; the verifier over all 30 pattern files, 2,301 public files) | 8 OK |
| R08 | `R08.txt`: 8 (H1d–H4d, H1v–H4v) | 2026-10-18 (DVR4 step 3 rebuild: the step-matcher interface; the verifier over R08, 2,305 public files) | 8 OK |

| R09 | `R09.txt`: 8 (H1d–H4d, H1v–H4v) | 2026-10-19 (DVR4 step 5, lane P2: re-cut with `# source:` lines from the one-statement-per-line twins; the verifier over R09, 2,583 public files; the Lab α forms `bench/local/r/labalpha/r09-rep-range-correct-{d,v}` hold H4's witness skeleton without any pattern line: reported for decision) | 8 OK |

| R10 | `R10.txt`: 8 (H1d–H4d, H1v–H4v) | 2026-10-20 (DVR4 step 5, lane P2: re-cut with `# source:` lines from the one-statement-per-line twins; the verifier over R10, 2,594 public files) | 8 OK |

| R11 | `R11.txt`: 8 (H1d, H3d, H4d, H6d, H2v, H5v, H7v, H9v) | 2026-10-20 (DVR4 step 5, lane P2: re-cut with `# source:` lines from the one-statement-per-line twins; the verifier over R11, 2,596 public files) | 8 OK |

| R12 | `R12.txt`: 8 (H1d, H2v, H1py–H5py, A1py) | 2026-10-18 (DVR4 step 3: the native hint-site forms re-cut; the verifier over R12, 2,626 public files) | 8 OK |

| R13 | `R13.txt`: 8 (T1d/v, H1d/v, H2d/v, H3d/v) | 2026-10-21 (DVR4 step 5, lane P2: re-cut against the one-statement-per-line twins, T1v's pattern now matches the body line; the verifier over R13, 2,595 public files) | 8 OK |
| R14 | `R14.txt`: 7 (H1d, H2d ×2, H3d, H1v, H2v, H3v) | 2026-10-18 (DVR4 step 3 rebuild: triggers, fuel and nonlinear facts on `MatchesV`; the verifier over R14, 2,626 public files) | 7 OK |

## The verifier

Run it from the repository root of the author's worktree, where the reference trees are readable (never in a study checkout). With no argument it checks every module of the table above; with ids, only those:

```
sed -n '/^```python$/,/^```$/{/^```/d;p}' tests/instructor/leak_patterns/README.md | python3 - [ID ...]
```

Its output is one line per pattern, `OK|FAIL sol=N prob=N chap=N pub=N <pattern>`: `sol` the hits in the pattern's own `# from` file (must be 1), `prob` and `chap` the hits in the module's problems file and chapter, `pub` the number of other learner-visible files it matches (all three must be 0), not counting the given layers above the module's layer (rule 2's exemption), which follow as `exempt:` lines. It exits 1 on any FAIL, on a pattern before any `# from` line, and on a module with fewer than 3 or more than 8 patterns.

```python
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path.cwd()
HERE = ROOT / "tests/instructor/leak_patterns"
# Reference-class trees: never public. Build outputs and toolchains: not course text.
REFERENCE = ("Solutions/", "paper/solutions/", "tests/instructor/leak_patterns/", "Hidden/")
SKIP_PARTS = {".git", "build", "target", ".toolchain", "__pycache__", ".venv", "node_modules"}
# Third-party benchmark sets that scripts/get_bench.sh installs (gitignored fetch sets,
# DELTAS Δ152): not course text; DV5's leak scan judges them before any set is vendored.
THIRD_PARTY = ("bench/public/",)
SKIP_EXT = {".pdf", ".aux", ".log", ".fls", ".fdb_latexmk", ".gz", ".pyc", ".zip", ".png",
            ".jpg", ".age", ".rlib", ".rmeta", ".vir", ".dll", ".so"}

# Rule 2's exemption: a given layer file (Dafny dafny/given/<T>/<QG|RG>_<L|A><k>_*.dfy,
# Verus verus/given/<qg_bignat_l<k> | rg_re_a<k>>/...) and its layer number.
GIVEN = re.compile(r"dafny/given/[QR]/(?:QG|RG)_([LA])([1-7]b?)_[^/]*\.dfy$"
                   r"|verus/given/(?:qg_bignat_(l)|rg_re_(a))([1-7]b?)/")

if not (ROOT / "MODULES.toml").is_file() or not HERE.is_dir():
    sys.exit("leak verifier: run it from the repository root")
registry = {m["id"]: m for m in tomllib.load(open(ROOT / "MODULES.toml", "rb"))["module"]}
table = re.findall(r"(?m)^\|\s*([QR]\d\d)\s*\|", (HERE / "README.md").read_text())
ids = [a.upper() for a in sys.argv[1:]] or table

def above_layer(rel, m):
    """True for a given layer of m's track above m's registry layer (rule 2's exemption)."""
    g = GIVEN.match(rel)
    if not g:
        return False
    letter = (g.group(1) or g.group(3) or g.group(4)).upper()
    layer = letter + (g.group(2) or g.group(5)).upper()
    own = (m.get("layer") or "").upper()
    if letter != ("L" if m["id"].startswith("Q") else "A"):
        return False
    order = [f"L{k}" for k in range(1, 8)] if letter == "L" else ["A1", "A1B", "A2", "A3", "A4", "A5"]
    if layer not in order or (own and own not in order):
        return False
    return order.index(layer) > (order.index(own) if own else -1)

cache = {}
# The declared later-tier overlaps whose files a pattern does match (listed in the bullets
# above; D23's matches none): Lab alpha's learner-visible corpus restates R02-R11 and A1b, so
# those modules' patterns may match it (the coordinator's option (a), DELTAS Δ294).
DECLARED = (("bench/local/r/labalpha/", tuple(f"R{k:02d}" for k in range(2, 12))),)


def declared_overlap(rel, mid):
    return any(rel.startswith(prefix) and mid in mods for prefix, mods in DECLARED)


def text(path):
    if path not in cache:
        try:
            cache[path] = path.read_text(errors="replace")
        except OSError:
            cache[path] = ""
    return cache[path]

public = []
for p in sorted(ROOT.rglob("*")):
    rel = p.relative_to(ROOT)
    if (not p.is_file() or rel.as_posix().startswith(REFERENCE + THIRD_PARTY)
            or SKIP_PARTS & set(rel.parts) or p.suffix in SKIP_EXT):
        continue
    public.append(p)

bad = 0
for mid in ids:
    m = registry.get(mid)
    pfile = HERE / f"{mid}.txt"
    if m is None or not pfile.is_file():
        print(f"FAIL {mid}: unknown module or no {pfile.name}")
        bad += 1
        continue
    prob = ROOT / f"paper/{mid}_problems.tex"
    chap = ROOT / m["chapter"]
    src, n = None, 0
    for line in text(pfile).splitlines():
        if line.startswith("# from "):
            src = ROOT / line[len("# from "):].split()[0]
            continue
        if not line.strip() or line.startswith("#"):
            continue
        n += 1
        if src is None:
            print(f"FAIL {mid}: pattern before any '# from' line: {line}")
            bad += 1
            continue
        rx = re.compile(line, re.MULTILINE)
        sol = 1 if src.is_file() and rx.search(text(src)) else 0
        np_ = 1 if prob.is_file() and rx.search(text(prob)) else 0
        nc = 1 if chap.is_file() and rx.search(text(chap)) else 0
        hits = [p for p in public if p not in (prob, chap) and rx.search(text(p))]
        exempt = [p for p in hits if above_layer(p.relative_to(ROOT).as_posix(), m)]
        declared = [p for p in hits if p not in exempt and declared_overlap(p.relative_to(ROOT).as_posix(), mid)]
        others = [p for p in hits if p not in exempt and p not in declared]
        ok = sol == 1 and np_ == 0 and nc == 0 and not others
        bad += not ok
        print(f"{'OK' if ok else 'FAIL'} sol={sol} prob={np_} chap={nc} pub={len(others)} {line}")
        for p in others[:5]:
            print(f"     public hit: {p.relative_to(ROOT).as_posix()}")
        for p in exempt:
            print(f"     exempt: {p.relative_to(ROOT).as_posix()} (a given layer above "
                  f"{mid}'s layer {m.get('layer') or 'none'}, rule 2)")
        for p in declared:
            print(f"     declared: {p.relative_to(ROOT).as_posix()} (a declared later-tier overlap, "
                  f"listed above)")
    if not 3 <= n <= 8:
        print(f"FAIL {mid}: {n} patterns; a module has 3 to 8")
        bad += 1
print(f"leak verifier: {len(ids)} module(s), {len(public)} public files scanned, "
      f"{'OK' if not bad else f'{bad} problem(s)'}")
sys.exit(1 if bad else 0)
```
