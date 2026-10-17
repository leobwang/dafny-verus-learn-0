#!/usr/bin/env python3
"""check_course_map.py — validate MODULES.toml, the course's module registry,
and the course files it declares (design §14.3; spec §8.1–§8.2; DELTAS Δ20,
Δ22, Δ26, Δ27, Δ34, Δ47).

MODULES.toml is the one place module facts live: ids, tracks, files, banks,
rubrics, cards, build units, layers, engines, budgets, instructor settings,
per-language WRITE/RECOGNISE constructs, import tiers, the D4 concept matrix,
and the [[coverage]] rows. Skills resolve their argument through --resolve;
scripts/ci.sh runs every group. Six groups; `--only GROUP` runs one.

registry
  schema   `schema = 1`; every [[module]] table has every field, in order,
           well typed; enums in range; no unknown field and no field whose
           name mentions solutions (the registry is learner-visible)
  ids      unique; Q01–Q33 then R01–R16, all present, in order; legacy ids
           unique; track follows the id
  Q rules  tier, layer, build target and topic follow the id; each concept
           and practice tier partitions S1–S13 (from moderate on by family,
           A S1–S5, B S6–S8, C S9–S13, in that order) and ends in the one
           tier viva; Q19–Q33 are solo with a defense, topics algorithms,
           quant, numerics, pl, agentic, three each
  R rules  no tier, topic or strands; a module viva; never solo; no field
           names a Q module (design §8.1: no cross-track prerequisite)
  files    langs = the languages of the module's files; every path sits where
           its field says (Dafny dafny/<T>/<ID>_<Name>/{core,std,exit,agent},
           Verus verus/<t>/<id>_<name>/src, specimens/<ID>, tools/<ID>,
           harness/<t>/fvh_<t>, Challenges/<Topic>/<ID>_<Name>, agents/);
           units = the units derived from exercises; no file has two owners;
           plain repo-relative paths, none into reference or held-out
           material, no component starting with `solutions` (solutions_policy
           and solutions-first are reserved, see isolation I1); every path of
           a shipped module exists; paper ⇔ the problems/answers pair; a
           Q01–Q18 gate file sits under harness/q/<pkg>/gate/ (guard rule 2s);
           only R16 names a trust-report path (under dafny/R/, verus/r/ or
           harness/r/, named *trust_report* or *trust-report*), never in
           agentic, and past planned it lists one (rule 2s)
  paper    paper = true wherever card is non-empty (a card is graded only as
           a [paper-card] problem of the pair) and wherever engines holds
           policy or agent (the lab's pre-registration unlocks its runs)
  model    engines ⊆ contract/policy/agent, contract ⇔ agentic; budget
           non-zero iff policy or agent; gpu_hours ≤ 10 per module and ≤ 45
           over the registry (design §3, §11.3); statements on Q19–Q33 and R08's exact frozen provided matcher,
           each file named *Statement* / *statement* (guard rule 2f)
  slugs    write_/recognise_ lists are slugs, per language, disjoint; at most
           6 WRITE units and 10 slugs; Q01–Q09 list WRITE constructs in both
           languages; no Verus integer-ring (Δ47); Q10–Q33 RECOGNISE []
  imports  per-language tiers; Q01–Q03 and R01–R06 stay prelude/core (OD8);
           a given layer's files are declared by its first module; past
           planned every module file is declared
  D4       concept_items keys S<k>.<concept>[@lang], values this module's
           P/H/X/T/A ids, "R" or "prose" (S12, S13); unsuffixed keys cite a d
           and a v item; Q10–Q33 and R: {}
  ledger   every `- tag: <ID>/<vocab-tag>` line names a known module
units
  scripts/gen_units.py's output equals the tree (every generated
  dfyconfig.toml, module Cargo.toml and verus/Cargo.toml), the options files
  are valid, no stale or unknown project file, build.rs or .cargo/ in a
  learner tree (Δ20); exits and agent files stay outside every unit (Verus:
  never mod-declared); an existing given layer crate depends on vstd and
  exactly the layers below it (Δ22)
import-tiers
  each declared file's effective imports, transitively through its own
  module's files and the given layers it reaches, stay within its tier:
  Dafny core (no Std) / std (Std minus Std.Arithmetic.LittleEndianNat, Δ35) /
  std-all; Verus prelude / seq_lib / arithmetic / all (vstd modules used;
  the root-level `calc!` macro, `vstd::calc` / `vstd::calc_macro`, is in
  every tier: a macro, not a lemma; QPLAN §6 Q16); Python py-std / py-fvh.
  Every course file on disk is declared exactly once; the course globs are
  never empty while a Q01–Q18 or R module is armed
isolation
  I1  a module file imports only externals, its tier's given layers and its
      own module's files; a given layer only lower layers of its track; no
      Dafny `include`, Verus `#[path]`/`include!`, Python `sys.path`; no name
      starting with `solutions`. Reserved names, over the whole learner-visible
      tree (every directory except dot-directories other than .claude, build
      outputs, symlinked directories and reference or held-out material, which
      is never listed or entered): no crate, package, Python module or Dafny
      module (nor a Rust module) is named solutions_policy or solutions-first,
      any case, '-' read as '_' — as a directory or module file, a Dafny
      module/refines/import name, a Rust mod/extern crate/path segment, a
      Python import, a Cargo package, lib, target or dependency name, or a
      pyproject project name. Guard rule 1 lets those two words through on a
      shell line, so `python3 -c 'import solutions_policy'` passes it.
  I2  the tracks never import or name each other's files, layers or bench
  I4a every Dafny declaration sits in a module named with its prefix
      (<ID>…, QG_<layer>_…, RG_<layer>_…)
  I5  docs, banks, rubrics and course files: no single-digit `Q1` label or
      v1 `F07` id; an R file names a Q module only in a `Recap → Qnn` line, a
      Q file an R module only in a `Deep dive → Rnn` line; bank labels
      K<n>/PP<n>, rubric labels C/D/A/B<n>; mermaid ids are not module ids
coverage (per armed module; the rows always)
  items    the module's item blocks parse (scripts/course_items.py); ids of
           this module, unique; strands among its strands; C slugs from its
           lists; pairs exist and are mutual
  D4       (Q01–Q09) every cited item exists; every P/H/X/T item is cited;
           every strand has a key
  uses     every WRITE slug is tagged by ≥ 2 H/X/T items in its language;
           every `uses:` slug is WRITE or RECOGNISE in that language here or
           earlier in the track
  parity   ≥ 2 cross-language (dv) predicts per concept module (Q01–Q09, R);
           exit floors per language (Q02–Q03 3+3, Q04–Q09 and R06/R11 2+2)
  gated    admissible keys name items; Q10–Q18 H items all have an entry; an
           exception ("<kind>: <why>") only on an admitted item, of a known
           kind: "short-format band" (D2, D7: a line short by design) or
           "statement-item" (D6, D9: the learner writes the statements, a
           contractor the proof) or "hidden-check spec" (D21: a prose
           specification graded by its hidden check); a statement-item
           exception names an H item whose block is a prose item
           (`// prose: <name>`) naming its contractor, or that sits in one of
           the module's agentic files (firsttry --empty-body runs its
           statement route when it ships no hole); a hidden-check spec
           exception names an H prose item of one of the module's exercise
           files that names no contractor, whose hidden check is recorded as
           holding (HIDDEN_CHECKS_HELD) and whose module's sealed truth is
           pinned in sandbox/truth.toml; the band itself: an exception only on
           an item OUT_OF_BAND records outside its tier's proof-line band, of
           the kind it records and naming its decision, and every admitted
           OUT_OF_BAND item carries one (the figures are the code notes')
  rows     [[coverage]]: fields exactly payload_id, langs, q_homes, r_homes,
           deepening, gap; ids unique; every listed language homed in both
           tracks (challenge homes are errors); homes in armed modules
           resolve; a gated item home needs a gap
vocab
  .claude/skills/instructor/concepts.md: kebab-case tags and aliases, unique,
  disjoint; bank vocabularies ⊆ tags ∪ aliases; ledger tags known (and in the
  module's bank vocabulary); Q bank strands legal; a shipped module's bank
  holds its questions (Q ≥ 8, R ≥ 12, R01 ≥ 8); a shipped tier-viva module
  has its whole tier's banks

Reads learner-visible files only, never a reference tree, so every mode is
safe in study mode. Errors print locations, never file content.

Usage:
  python3 scripts/check_course_map.py [--only GROUP] [--root DIR]
      exit 0 consistent, 1 on any error
  python3 scripts/check_course_map.py --resolve ID [--root DIR]
      one JSON record (case-insensitive; a legacy id maps); exit 0, 3 unknown
      id, 1 unreadable registry or malformed record
  python3 scripts/check_course_map.py --items ID [--json] [--root DIR]
      the module's parsed items, any status; --json prints one array of
      {id, kind, n, lang, strand, format, min, uses[], need[], pair, did[],
       file, line_start, line_end, slots: [{format, file, line, state}]}
      exit 0, 3 unknown id, 1 malformed record or item block
  python3 scripts/check_course_map.py --list-nonplanned RANGE [--root DIR]
      the ids in RANGE (Q01-Q18, R01-R16, …) whose status is not planned,
      one per line; exit 2 on a malformed range
"""

import argparse
import hashlib
import json
import os
import re
import sys
import tomllib
from pathlib import Path, PurePosixPath

sys.dont_write_bytecode = True  # importing the shared modules leaves no scripts/__pycache__
sys.path.insert(0, str(Path(__file__).resolve().parent))
import course_items as ci  # noqa: E402  (the one item parser)
import gen_units as gu  # noqa: E402  (the unit generator and the spine facts)

DEFAULT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY = "MODULES.toml"
SCHEMA = 1
LEDGER = "instructor/ledger.md"
BANKS = ".claude/skills/instructor/banks/"
CONCEPTS = ".claude/skills/instructor/concepts.md"
SLOTS = "slots"
GROUPS = ("registry", "units", "import-tiers", "isolation", "coverage", "vocab")
RAW_PREFIXES = ("instructor/", "dafny/", "verus/", "harness/", "docs/", "paper/", ".claude/",
                "specimens/", "slots/", "tools/", "Challenges/", "agents/", "scripts/", "tests/",
                "research/", "bench/", "sandbox/", "./")

# Field name -> type, in the order every [[module]] table lists them.
FIELDS = {
    "id": str, "legacy_id": str, "track": str, "status": str, "title": str, "tier": str,
    "topic": str, "strands": list, "langs": list, "chapter": str, "exercises": list,
    "exits": list, "agentic": list, "harness": list, "bank": str, "paper": bool,
    "rubric": str, "card": list, "build_target": str, "units": list, "layer": str,
    "engines": list, "statements": list, "deep_dive": list, "review_bar": str,
    "persona": str, "viva_mode": str, "tutor_max_rung": int, "solo": bool,
    "solutions_policy": str, "write_d": list, "write_v": list, "recognise_d": list,
    "recognise_v": list, "budget": dict, "admissible": dict, "imports": dict,
    "concept_items": dict,
}
TYPE_NAMES = {str: "a string", list: "a list", bool: "true or false", int: "an integer",
              dict: "a table"}
ENUMS = {
    "track": ("Q", "R"),
    "status": ("shipped", "authoring", "planned"),
    "build_target": ("Q", "R", "Challenges"),
    "review_bar": ("it-reads", "proof-shape", "library-conventions", "design-lite",
                   "design-judgment", "library-pr", "production", "harness"),
    "persona": ("sharp-dev", "smt-skeptic", "ml-engineer", "journal-referee", "risk-engineer",
                "numerical-analyst", "compiler-engineer", "eval-skeptic"),
    "viva_mode": ("module", "tier", "defense", "none"),
    "solutions_policy": ("solutions-first", "verifier-graded", "harness-graded",
                         "reference-impl"),
}
TOPICS = ("algorithms", "quant", "numerics", "pl", "agentic")
TOPIC_DIRS = {"algorithms": "Algorithms", "quant": "Quant", "numerics": "Numerics", "pl": "PL",
              "agentic": "Agentic"}
STRANDS = tuple(f"S{k}" for k in range(1, 14))
FAMILIES = (("A", STRANDS[0:5]), ("B", STRANDS[5:8]), ("C", STRANDS[8:13]))
Q_TIERS = (("survey", 1, 1), ("intro", 2, 3), ("moderate", 4, 6), ("detailed", 7, 9),
           ("practice-intro", 10, 12), ("practice-intermediate", 13, 15),
           ("practice-hard", 16, 18), ("challenge", 19, 33))
EXPECTED_IDS = [f"Q{n:02d}" for n in range(1, 34)] + [f"R{n:02d}" for n in range(1, 17)]
LANG_ORDER = ("d", "v", "py")
LANG_NAMES = {"d": "Dafny", "v": "Verus", "py": "Python"}
ENGINE_ORDER = ("contract", "policy", "agent")
BUDGET_KEYS = ("claude_calls", "claude_runs", "qwen_calls", "qwen_runs", "gpu_hours")
ADMISSIBLE_KEYS = ("admitted", "minutes", "fallback")
# An admitted item outside its tier's line band carries a declared exception
# (the user's decisions D2, 2026-10-12, and D6, D7, D9, 2026-10-12; DELTAS): a
# fourth key `exception`, a string "<kind>: <why>" of a kind below, only on an
# admitted item. "short-format band": the item's minutes line is short by
# design (Q15's S11 pair, Q18's H1 pair). "statement-item": the learner writes
# the item's statements and a contractor writes their proof, so the band of a
# proof's lines does not apply (Q17.H3d, Q18.H2d/H2v); its item is an item of
# an agentic file, or a prose item whose block names its contractor
# (`// contractor: <A item>`; STATEMENT_ITEM_KIND, checked in the coverage
# group, where the items are parsed). "hidden-check spec" (the user's decision
# D21, 2026-10-13): a prose specification below its band whose grade is its
# hidden check in the grader container, not a proof's lines (Q15's Lab 2
# specifications); its item is an H prose item (`// prose: <name>`) of one of
# the module's exercise files that names no contractor (a prose item that does
# is a statement item), whose hidden check is recorded as holding
# (HIDDEN_CHECKS_HELD) and whose module's sealed truth is pinned in
# TRUTH_PINS (HIDDEN_CHECK_KIND, hidden_check_problem; the coverage group).
STATEMENT_ITEM_KIND = "statement-item"
HIDDEN_CHECK_KIND = "hidden-check spec"
ADMISSIBLE_EXCEPTION_KINDS = ("short-format band", STATEMENT_ITEM_KIND, HIDDEN_CHECK_KIND)
# The prose items whose hidden check is recorded as holding: DELTAS Δ220 (DV5d's
# judging lane, 2026-10-12; archive dv5d/judge/): in the grader container, on
# the final image, each item's sealed reference was judged faithful against
# itself, and each recorded or planted wrong statement of it was classified as
# expected (Q15.H3v's undecided case is unfaithful either way). A new entry
# cites the DELTAS entry that records its judging run, with the manifest_sha256
# (TRUTH_PINS) of the sealed truth the hold applies to: the judged archive's, or
# a later re-seal's once its references are confirmed unchanged against the
# judged one (the plaintext MANIFEST.sha256 files compared; DV5e's re-seal of
# Q15 changed only judge/oracles.py and SEALING.md besides the new public
# cards, checked by the DV5e review; DV6's re-seal of Q15 under the user's
# decisions D27 and D28, 2026-10-14, changed only the ten public cards' files and
# SEALING.md: the prose items' references, judge/oracles.py and DVLCANARY are
# byte-identical, so the hold is re-confirmed on the DV6 manifest, and the six
# references were judged faithful against themselves again in the grader
# container; DV6 lab2 notes §5). A re-seal changes the pinned manifest, so
# the kind is refused until the hold is re-judged or re-confirmed and its
# manifest recorded here.
_Q13_MAN = "1b5525a8267559dd6860e592d074a23ba28b16d76ae53bbbf1570e3de271fa51"
_Q15_MAN = "5d5a353ea5c231025b78654242765c818090da458c597697c5ce5428e1803278"
_Q17_MAN = "f83b64b22b5ec788580f85ce4a574ac7728ad0b8ad23f09b0f2a1d4745d978ef"
HIDDEN_CHECKS_HELD = {
    "Q13.H3v": ("Δ220", _Q13_MAN), "Q15.H3d": ("Δ220", _Q15_MAN),
    "Q15.H4d": ("Δ220", _Q15_MAN), "Q15.H5d": ("Δ220", _Q15_MAN),
    "Q15.H3v": ("Δ220", _Q15_MAN), "Q15.H4v": ("Δ220", _Q15_MAN),
    "Q15.H5v": ("Δ220", _Q15_MAN), "Q17.H3d": ("Δ220", _Q17_MAN),
}
# The proof-line bands of the practice tiers (design §7.5's admissibility gate,
# QPLAN §19.0's count; Dafny, Verus): an admitted Dafny or Verus item of Q10-Q18
# whose recorded proof lines fall outside its tier's band is admitted only by a
# declared exception of the kind OUT_OF_BAND records for it.
PRACTICE_BANDS = {"practice-intro": {"d": (0, 10), "v": (0, 15)},   # QPLAN §19.0: "at most 10/15" (DV6)
                  "practice-intermediate": {"d": (10, 30), "v": (15, 45)},
                  "practice-hard": {"d": (30, 80), "v": (45, 120)}}
# Every admitted item outside its band (DV5e review fix, 2026-10-13): item ->
# (its proof lines, the exception kind that admits it, the user's decision).
# The figures are the module code notes' pcount counts (QPLAN §19.0; the Q15,
# Q17 and Q18 code notes' four-results tables); a statement item's figure is
# the learner's proof lines. The checker requires the recorded kind's
# exception, whose reason names the decision, on each entry, and refuses an
# exception on any item this table does not hold. It does not count the
# references itself (they are reference material, which this checker never
# reads): an item re-probed outside its band joins the table with its notes.
OUT_OF_BAND = {
    "Q15.H2d": (7, "short-format band", "D40"), "Q15.H2v": (13, "short-format band", "D40"),
    "Q15.H1d": (5, "short-format band", "D2"), "Q15.H1v": (4, "short-format band", "D2"),
    "Q15.H3d": (0, "hidden-check spec", "D21"), "Q15.H4d": (0, "hidden-check spec", "D21"),
    "Q15.H5d": (0, "hidden-check spec", "D21"), "Q15.H3v": (7, "hidden-check spec", "D21"),
    "Q15.H5v": (0, "hidden-check spec", "D21"),
    "Q17.H3d": (10, "statement-item", "D6"),
    "Q18.H1d": (12, "short-format band", "D7"), "Q18.H1v": (19, "short-format band", "D7"),
    "Q18.H2d": (0, "statement-item", "D9"), "Q18.H2v": (0, "statement-item", "D9"),
}
TRUTH_PINS = "sandbox/truth.toml"     # each lab's sealed hidden truth ([[lab]] id = module)
PROSE_LINE = re.compile(r"^\s*//\s*prose:\s*\S")
CONTRACTOR_LINE = re.compile(r"^\s*//\s*contractor:\s*([A-Z]\d+\.[A-Z]\d+(?:dv|py|d|v)?)\s*$")
WRITE_UNIT_CAP, WRITE_SLUG_CAP = 6, 10   # design §4 comparative mechanics
BANNED_SLUGS = {"v": {"integer-ring"}}   # Δ47: `by (integer_ring)` is rejected at the pin
# Path components (compared by stem, any case) that mark reference or held-out
# material; the registry never points there. <id>_solutions is the written
# track's form; *.age is sealed held-out material.
REFERENCE_STEMS = {"solutions", "hidden", "leak_patterns"}
REFERENCE_FILE = re.compile(r"[rq]\d\d_solutions")
# Reserved names. Guard rule 1 lets the registry's field solutions_policy and its
# value solutions-first through on a shell line (spoiler-guard.sh RX_VOCAB), so a
# skill can extract the field by shell; `python3 -c 'import solutions_policy'`
# passes with them. That is safe only while no crate, package or module carries
# either name, so none may (compared lower-case with '-' read as '_': Cargo and
# Python packaging treat the two as one name). Every other name starting with
# `solutions` is a reference identifier the guard refuses outright.
RESERVED_NAMES = ("solutions_policy", "solutions-first")
RESERVED_WHY = ("solutions_policy and solutions-first are the registry's field and value, "
                "which guard rule 1 lets through on a shell line, so no crate, package or "
                "module may carry either name")
# The learner-visible tree the reserved-name walk covers: everything under the
# root except dot-directories (.git, .toolchain, .venv, …; .claude is walked),
# reference and held-out material (never entered), and build outputs.
WALK_SKIP_DIRS = {"target", "build", "__pycache__", "TestResults", "node_modules", "venv"}
DAFNY_OUTPUT_DIR = re.compile(r".+-(py|go|java|cs|js|cpp)")
MODULE_SUFFIXES = (".py", ".pyi", ".pyc", ".pyd", ".so", ".rs", ".dfy", ".doo", ".specimen")
CARD_ID = re.compile(r"\d\d\.\d{1,2}")
GPU_HOURS_PER_MODULE = 10   # design §3: ≤ 10 GPU-h per lab [A]
GPU_HOURS_TOTAL = 45        # design §11.3: the six labs' Qwen work in ≤ 45 GPU-h [A]
# The spoiler-guard's solo (2s) and frozen (2f) path patterns this registry must
# feed (.claude/hooks/spoiler-guard.sh, class_of): R16's trust-report, Q's gate,
# and challenge statements. Matched from the start of a repo-relative path. The
# trust-report pattern names the R trees as they are spelled: dafny/R/ (upper
# case, like every Dafny track directory), verus/r/ and harness/r/. Only Q has a
# harness gate (design §10.3: "R's gate is Rust", R16's trust-report command), so an
# R harness file named gate is ordinary learner work (rule 2), not solo.
TRUST_REPORT = re.compile(r"(dafny/R|verus/r|harness/r)/(.*/)?[^/]*trust[-_]report")
Q_GATE = re.compile(r"harness/q/[^/]+/gate(/|\.py$|$)")
GATE_WORD = re.compile(r"(?<![a-z])gates?(?![a-z])")
STATEMENT_NAME = re.compile(r"[Ss]tatement")
# PLAN F6: the exact frozen A2 matcher interface introduced by R08.
PROVIDED_STATEMENTS = {"R08": "dafny/given/R/RG_A2_MatcherStatement.dfy"}
SHA256 = re.compile(r"[0-9a-f]{64}")
KEBAB = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
CONCEPT_KEY = re.compile(r"S(1[0-3]|[1-9])\.[a-z0-9]+(?:-[a-z0-9]+)*(?:@(d|v|py))?")
PAYLOAD_ID = re.compile(r"S(1[0-3]|[1-9])\.[a-z0-9]+(?:-[a-z0-9]+)*")
COV_FIELDS = ("payload_id", "langs", "q_homes", "r_homes", "deepening", "gap")
Q_HOME = re.compile(r"(Q(?:0[1-9]|1[0-8]))\.(?:S(1[0-3]|[1-9])|B([1-9]\d*)|"
                    r"([WCPHXTA])([1-9]\d*)(dv|py|d|v))")
R_HOME = re.compile(r"(R(?:0[1-9]|1[0-6]))(?:\.(?:B([1-9]\d*)|([WCPHXTA])([1-9]\d*)(dv|py|d|v)))?")
COV_DEEP = re.compile(r"Q(19|2\d|3[0-3])")
PAPER_ITEM = re.compile(r"^%\s*item:\s*([QR]\d\d\.B[1-9]\d*)\s*$", re.M)

# Import tiers per language. Dafny: which Std modules a file may reach.
# Verus: which top-level vstd modules a file may use (prelude always); core,
# std and alloc are always allowed. Python: which top-level packages.
DAFNY_TIERS = ("core", "std", "std-all")
VERUS_TIERS = ("prelude", "seq_lib", "arithmetic", "all")
PYTHON_TIERS = ("py-std", "py-fvh")
TIERS_BY_LANG = {"d": DAFNY_TIERS, "v": VERUS_TIERS, "py": PYTHON_TIERS}
# `calc!` is a root-level macro of vstd (`use vstd::calc;`, defined in
# vstd::calc_macro): proof syntax, not a library lemma, so the prelude tier
# admits it (the orchestrator's QPLAN §6 Q16 decision, DV3a).
VSTD_ALLOW = {
    "prelude": {"prelude", "calc", "calc_macro"},
}
# Every wider tier inherits the prelude tier, `calc!` included (Δ131).
VSTD_ALLOW["seq_lib"] = VSTD_ALLOW["prelude"] | {"seq", "seq_lib", "set", "set_lib", "map",
                                                 "map_lib", "multiset", "view"}
VSTD_ALLOW["arithmetic"] = VSTD_ALLOW["seq_lib"] | {"arithmetic", "bits"}
STD_NEAR_ANSWER = "Std.Arithmetic.LittleEndianNat"   # Δ35: excluded from the std tier


def q_tier(mid):
    n = int(mid[1:])
    return next((tier, lo, hi) for tier, lo, hi in Q_TIERS if lo <= n <= hi)


def num(mid):
    return int(mid[1:])


def is_core_module(mid):
    """Q01–Q18 and every R module: the comparative core (not a challenge)."""
    return mid[0] == "R" or num(mid) <= 18


def expected_target(mid):
    return "R" if mid[0] == "R" else "Q" if num(mid) <= 18 else "Challenges"


def snake(name):
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name).lower()


def is_reference(path):
    p = PurePosixPath(path)
    # by stem and by the name up to its first dot (solutions.dfy.specimen)
    stems = [s for x in p.parts for s in (PurePosixPath(x).stem.lower(), x.split(".")[0].lower())]
    return (any(x in REFERENCE_STEMS or REFERENCE_FILE.fullmatch(x) for x in stems)
            or p.name.lower().endswith(".age"))


def reserved(name):
    """True when name is solutions_policy or solutions-first (any case, '-' as '_')."""
    return name.lower().replace("-", "_") in {n.replace("-", "_") for n in RESERVED_NAMES}


def lang_of_path(p):
    return None if p.endswith("/") else ci.file_lang(p)


def module_paths(m):
    """Every learner path the record lists (exercises, exits, agentic, harness)."""
    return [p for key in ("exercises", "exits", "agentic", "harness") for p in m[key]]


def load_registry(root):
    """Return (data, error). error is a one-line string when the file is unusable."""
    path = root / REGISTRY
    try:
        with open(path, "rb") as f:
            return tomllib.load(f), None
    except FileNotFoundError:
        return None, f"{REGISTRY} not found under {root}"
    except tomllib.TOMLDecodeError as e:
        return None, f"{REGISTRY}: not valid TOML: {e}"


def read_text(root, rel):
    path = root / rel
    return path.read_text(encoding="utf-8") if path.is_file() else None


# --- registry: one record -------------------------------------------------------------

def check_fields(m):
    """Schema and per-record rules for one module table. Returns error strings."""
    errs = []
    mid = m.get("id") if isinstance(m.get("id"), str) else "?"

    def err(msg):
        errs.append(f"{mid}: {msg}")

    for key in m:
        if key in FIELDS:
            continue
        if "solution" in key.lower():
            err(f"field '{key}' is not allowed: the registry is learner-visible and never "
                "names reference material")
        else:
            err(f"unknown field '{key}'")
    missing = [k for k in FIELDS if k not in m]
    for key in missing:
        err(f"missing field '{key}'")
    present = [k for k in m if k in FIELDS]
    if not missing and present != list(FIELDS):
        err("fields out of order (expected: " + ", ".join(FIELDS) + ")")
    for key, want in FIELDS.items():
        if key not in m:
            continue
        v = m[key]
        # bool is an int subclass; tutor_max_rung = true must not pass as 1
        if not isinstance(v, want) or (want is int and isinstance(v, bool)):
            err(f"'{key}' must be {TYPE_NAMES[want]}, got {type(v).__name__}")
        elif want is list and key != "statements" and not all(isinstance(x, str) and x for x in v):
            err(f"'{key}' must be a list of non-empty strings")
        elif key in ENUMS and v not in ENUMS[key]:
            err(f"'{key}' = {v!r} is not one of: " + ", ".join(ENUMS[key]))
    if errs:
        return errs  # the rules below assume a well-typed record
    if mid not in EXPECTED_IDS:
        return [f"{mid}: id must be one of Q01–Q33, R01–R16"]
    if m["track"] != mid[0]:
        err(f"track {m['track']!r} does not match the id")
    if not m["title"].strip():
        err("empty title")
    if m["legacy_id"] and (not re.fullmatch(r"[A-Z]\d\d", m["legacy_id"])
                           or m["legacy_id"] in EXPECTED_IDS):
        err(f"legacy_id {m['legacy_id']!r} must be \"\" or a retired id like F07 (never a "
            "current id)")
    if not 1 <= m["tutor_max_rung"] <= 5:
        err("tutor_max_rung must be 1–5")
    if m["solo"] and m["tutor_max_rung"] > 2:
        err("solo modules cap the tutor at rung 2")
    if m["paper"] and not m["rubric"]:
        err("paper = true needs a rubric")
    if m["card"] and not m["paper"]:
        err("card lists paper cards, so paper = true: /grade-paper grades a card only as a "
            "[paper-card] problem of paper/<ID>_problems.tex")
    if any(e in ("policy", "agent") for e in m["engines"]) and not m["paper"]:
        err("engines runs a model (policy or agent), so paper = true: the lab's "
            "pre-registration is a problem of the pair, and fvh runs only after /grade-paper "
            "unlocks it (design §11.1)")
    if m["build_target"] != expected_target(mid):
        err(f"build_target must be {expected_target(mid)!r} for {mid}")
    if m["layer"] != gu.expected_layer(mid):
        err(f"layer must be {gu.expected_layer(mid)!r} for {mid} (design §10.1, §10.2)")
    core = is_core_module(mid)

    if m["track"] == "R":
        for key in ("tier", "topic"):
            if m[key]:
                err(f"'{key}' is Q-only; must be \"\" on an R module")
        if m["strands"]:
            err("strands are Q-only; must be [] on an R module")
        if m["viva_mode"] != "module":
            err("every R module has a module viva (viva_mode = \"module\")")
        if m["solo"]:
            err("R modules are never solo")
        if m["deep_dive"]:
            err("deep_dive is Q-only; an R record never names a Q module (design §8.1)")
        if m["concept_items"]:
            err("concept_items (the D4 matrix) is Q01–Q09 only; must be {}")
        err_cross = sorted({x for x in re.findall(r"(?<![A-Za-z0-9])Q\d\d(?!\d)",
                                                  json.dumps(m, ensure_ascii=False))})
        if err_cross:
            err("an R record names a Q module (" + ", ".join(err_cross) + "); R is standalone "
                "and has no cross-track prerequisite (design §8.1)")
    else:
        tier, _, last = q_tier(mid)
        if m["tier"] != tier:
            err(f"tier must be {tier!r} for {mid}")
        bad = [s for s in m["strands"] if s not in STRANDS]
        if bad or not m["strands"] or len(set(m["strands"])) != len(m["strands"]):
            err("strands must be a non-empty list of distinct S1..S13")
        elif m["strands"] != sorted(m["strands"], key=STRANDS.index):
            err("strands must be listed in order")
        if tier == "challenge":
            topic = TOPICS[(num(mid) - 19) // 3]
            if m["topic"] != topic:
                err(f"topic must be {topic!r} for {mid} (Q19–Q33: " + ", ".join(TOPICS)
                    + ", three modules each)")
            if not m["solo"]:
                err("challenge modules are solo")
            if m["viva_mode"] != "defense":
                err("challenge modules end in a defense viva (viva_mode = \"defense\")")
            if list(m["strands"]) != list(STRANDS):
                err("a challenge module draws on every strand (S1–S13)")
            if m["solutions_policy"] == "solutions-first":
                err("a challenge is graded by verifier, harness or reference implementation, "
                    "never solutions-first")
        else:
            if m["topic"]:
                err("topic is for Q19–Q33 only; must be \"\"")
            if m["solo"]:
                err("only challenge modules are solo")
            viva = "tier" if num(mid) == last and tier != "survey" else "none"
            if m["viva_mode"] != viva:
                err(f"viva_mode must be {viva!r} for {mid} (the tier viva sits on the last "
                    "module of each tier after the survey)")
        for r in m["deep_dive"]:
            if not re.fullmatch(r"R(0[1-9]|1[0-6])", r):
                err(f"deep_dive: {r!r} is not an R module id")
        if len(set(m["deep_dive"])) != len(m["deep_dive"]):
            err("deep_dive lists a module twice")
        q_cross = sorted({x for k, v in m.items() if k != "deep_dive"
                          for x in re.findall(r"(?<![A-Za-z0-9])R\d\d(?!\d)",
                                              json.dumps(v, ensure_ascii=False))})
        if q_cross:
            err("names an R module outside deep_dive (" + ", ".join(q_cross) + "); the tracks "
                "never import each other (I2)")
    if core and m["solutions_policy"] != "solutions-first":
        err("Q01–Q18 and R modules are solutions-first")
    if m["solo"] and m["agentic"]:
        err("solo modules have no contract run, so agentic must be []")

    errs += path_hygiene(m)
    errs += check_langs_and_paths(m)
    errs += check_model_fields(m)
    errs += check_constructs(m)
    errs += check_imports_table(m)
    errs += check_concept_items(m)
    return errs


def chapter_name(m):
    c = re.fullmatch(rf"docs/{m['id']}_([A-Za-z0-9]+)\.md", m["chapter"])
    return c.group(1) if c else None


def path_errors(m, key, p, name):
    """Where a path of field `key` may live, for module m with chapter Name `name`."""
    mid, track = m["id"], m["id"][0]
    t = track.lower()
    crate = f"{mid.lower()}_{snake(name)}" if name else None
    dafny_root = f"dafny/{track}/{mid}_{name}/" if name else None
    verus_src = f"verus/{t}/{crate}/src/" if name else None
    tools = f"tools/{mid}/"
    if not is_core_module(mid):
        topic_dir = TOPIC_DIRS.get(m["topic"], "?")
        ch = f"Challenges/{topic_dir}/{mid}_{name}/"
        if key == "exercises" and not p.startswith(ch):
            return f"exercises: '{p}' must sit under {ch}"
        if key == "harness" and not (p.startswith(f"agents/{mid.lower()}_") and p.endswith(".py")):
            return f"harness: '{p}' must be a .py file under agents/{mid.lower()}_<name>/"
        if key in ("exits", "agentic"):
            return f"{key}: challenge modules have no {key} files (solo, gate-graded)"
        return None
    if name is None:
        return None  # the chapter error is reported
    if key == "harness":
        pkg = f"harness/{t}/fvh_{t}/"
        if not (p.startswith(pkg) and p.endswith(".py")):
            return f"harness: '{p}' must be a .py file under {pkg}"
        return None
    if p.startswith("dafny/"):
        sub = {"exercises": ("core", "std"), "exits": ("exit",), "agentic": ("agent", "core", "std")}[key]
        if not any(p.startswith(dafny_root + s + "/") for s in sub) or not p.endswith((".dfy", "/")):
            if key == "exercises" and re.fullmatch(rf"dafny/checks/{mid}_checks\.dfy", p):
                return None
            return (f"{key}: '{p}' must sit under {dafny_root}{{{','.join(sub)}}}/ "
                    "(a Dafny unit, exit or agent directory of this module)")
        return None
    if p.startswith("verus/"):
        if not p.startswith(verus_src) or not p.endswith((".rs", "/")):
            return f"{key}: '{p}' must sit under {verus_src} (this module's crate)"
        if key in ("exits", "agentic") and p == verus_src + "lib.rs":
            return f"{key}: '{p}' is the crate root; exit and agent files are separate, never mod-declared"
        return None
    if p.startswith("specimens/") and key == "exercises":
        if not p.startswith(f"specimens/{mid}/"):
            return f"exercises: '{p}' must sit under specimens/{mid}/"
        return None
    if p.startswith("tools/") and key in ("exercises", "agentic"):
        if not p.startswith(tools):
            return f"{key}: '{p}' must sit under {tools}"
        return None
    return (f"{key}: '{p}' is not a {key} location of {mid} (dafny/{track}/{mid}_<Name>/, "
            f"verus/{t}/<crate>/src/, specimens/{mid}/, tools/{mid}/)")


def check_langs_and_paths(m):
    errs = []
    mid = m["id"]

    def err(msg):
        errs.append(f"{mid}: {msg}")

    name = chapter_name(m)
    if not m["chapter"]:
        err("chapter is required")
    elif name is None:
        err(f"chapter must be docs/{mid}_<Name>.md (Name: letters and digits)")
    bad = [x for x in m["langs"] if x not in LANG_ORDER]
    if bad or not m["langs"] or len(set(m["langs"])) != len(m["langs"]):
        err("langs must be a non-empty list of distinct d, v, py")
    elif m["langs"] != sorted(m["langs"], key=LANG_ORDER.index):
        err("langs must be listed in the order d, v, py")
    if is_core_module(mid):
        if "d" not in m["langs"] or "v" not in m["langs"]:
            err("Q01–Q18 and R modules teach both verifiers: langs holds d and v")
        first_py = 6 if mid[0] == "Q" else 5
        if "py" in m["langs"] and num(mid) < first_py:
            err(f"Python enters at {mid[0]}{first_py:02d}; langs must not hold py before it")
    have = [x for x in LANG_ORDER if any(lang_of_path(p) == x for p in module_paths(m))]
    if not bad and have != [x for x in LANG_ORDER if x in m["langs"]]:
        err(f"langs {m['langs']} do not match the module's files {have}")
    if not m["exercises"]:
        err("exercises must list at least one path")
    if mid in [f"Q{n:02d}" for n in range(1, 16)] + ["R06", "R11"] and m["status"] != "planned" \
            and not m["exits"]:
        err("exits must list the closed-book exit files once the module leaves planned")
    for key in ("exercises", "exits", "agentic", "harness"):
        if len(set(m[key])) != len(m[key]):
            err(f"'{key}' lists a path twice")
        for p in m[key]:
            if e := path_errors(m, key, p, name):
                err(e)
    for p in m["harness"]:
        if not p.endswith(".py"):
            err(f"harness: '{p}' is not a Python file")
        elif mid[0] == "Q" and is_core_module(mid) and p.startswith("harness/q/") \
                and GATE_WORD.search(p.lower().split("/", 3)[-1]) and not Q_GATE.match(p):
            err(f"harness: '{p}' is a gate file; Q's gate sits under harness/q/fvh_q/gate/, "
                "which guard rule 2s keeps solo")
    reports = [p for p in module_paths(m) if TRUST_REPORT.match(p)]
    if mid != "R16" and reports:
        err(f"'{reports[0]}' matches R16's trust-report pattern, which guard rule 2s treats as "
            "solo work; only R16 names such a path")
    elif any(TRUST_REPORT.match(p) for p in m["agentic"]):
        err("agentic: R16's trust-report is solo work (guard rule 2s); a /contract session "
            "never works in it")
    if mid == "R16" and m["status"] != "planned" and not any(
            TRUST_REPORT.match(p) for p in m["exercises"] + m["harness"]):
        err("R16 past planned lists its trust-report in exercises or harness, at a path under "
            "verus/r/, harness/r/ or dafny/R/ whose name holds trust_report or trust-report "
            "(guard rule 2s keeps it solo)")
    derived = gu.derive_units(m["exercises"])
    if m["units"] != derived:
        err(f"units must be {derived} (derived from exercises: one unit per language and "
            "library tier)")
    if is_core_module(mid):
        kinds = [gu.unit_kind(u)[0] for u in derived]
        if "d" not in kinds or kinds.count("v") != 1:
            err("a core module has at least one Dafny unit and exactly one Verus crate")
        if any(gu.unit_kind(u) == ("d", "std") for u in derived) and (
                (mid[0] == "Q" and num(mid) <= 3) or (mid[0] == "R" and num(mid) <= 6)):
            err("the standard library enters at Q04 / R07 (OD8): no std unit before it")
    if m["bank"]:
        want = (f"{BANKS}{mid}.md" if is_core_module(mid)
                else f"{BANKS}defense_{m['topic']}.md")
        if m["bank"] != want:
            err(f"bank must be {want}")
    if m["rubric"] and m["rubric"] != f"paper/rubrics/{mid}_rubric.md":
        err(f"rubric must be paper/rubrics/{mid}_rubric.md")
    for c in m["card"]:
        if not CARD_ID.fullmatch(c):
            err(f"card: {c!r} is not a cheatsheets.md id (NN.N)")
    if len(set(m["card"])) != len(m["card"]):
        err("card lists an id twice")
    if is_core_module(mid) and not m["card"]:
        err("card must list the module's paper card(s)")
    return errs


def check_model_fields(m):
    errs = []
    mid = m["id"]

    def err(msg):
        errs.append(f"{mid}: {msg}")

    eng = m["engines"]
    if any(e not in ENGINE_ORDER for e in eng) or len(set(eng)) != len(eng):
        err("engines must be distinct entries of: " + ", ".join(ENGINE_ORDER))
    elif eng != sorted(eng, key=ENGINE_ORDER.index):
        err("engines must be listed in the order contract, policy, agent")
    if ("contract" in eng) != bool(m["agentic"]):
        err("engines holds contract exactly when agentic lists files (a /contract session "
            "works in them)")
    if m["solo"] and "contract" in eng:
        err("a solo module never runs /contract")
    b = m["budget"]
    if list(b) != list(BUDGET_KEYS):
        err("budget must hold exactly, in order: " + ", ".join(BUDGET_KEYS))
    elif not all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in b.values()):
        err("budget values are non-negative integers")
    else:
        spends = any(v > 0 for v in b.values())
        runs_models = "policy" in eng or "agent" in eng
        if spends != runs_models:
            err("budget is non-zero exactly when engines holds policy or agent"
                + (" (it spends, but no engine runs a model)" if spends else
                   " (a model engine needs its budget)"))
        if b["gpu_hours"] > GPU_HOURS_PER_MODULE:
            err(f"budget.gpu_hours = {b['gpu_hours']} exceeds the per-lab cap of "
                f"{GPU_HOURS_PER_MODULE} (design §3)")
    st = m["statements"]
    if is_core_module(mid) and st and mid not in PROVIDED_STATEMENTS:
        err("statements are the frozen statement files of Q19–Q33; must be []")
    if mid in PROVIDED_STATEMENTS and len(st) > 1:
        err("R08 declares one frozen matcher statement, not additional statement files")
    for i, s in enumerate(st, 1):
        if not isinstance(s, dict) or list(s) != ["path", "sha256"] or not all(
                isinstance(x, str) for x in s.values()):
            err(f"statements[{i}] must be {{ path = \"…\", sha256 = \"…\" }}")
            continue
        topic_dir = TOPIC_DIRS.get(m["topic"], "?")
        if mid in PROVIDED_STATEMENTS:
            if s["path"] != PROVIDED_STATEMENTS[mid]:
                err(f"statements[{i}]: R08 uses the exact provided A2 matcher "
                    f"'{PROVIDED_STATEMENTS[mid]}'")
            if s["sha256"] == "PENDING":
                err(f"statements[{i}]: the provided matcher needs an actual SHA256 pin, "
                    "including while planned")
        elif not s["path"].startswith(f"Challenges/{topic_dir}/{mid}_"):
            err(f"statements[{i}]: '{s['path']}' must sit under Challenges/{topic_dir}/{mid}_<Name>/")
        if not STATEMENT_NAME.search(PurePosixPath(s["path"]).name):
            err(f"statements[{i}]: '{s['path']}': a statement file's name holds 'Statement' "
                "(or 'statement'), so guard rule 2f freezes it")
        if s["sha256"] != "PENDING" and not SHA256.fullmatch(s["sha256"]):
            err(f"statements[{i}]: sha256 must be 64 lower-case hex digits or \"PENDING\"")
        if s["sha256"] == "PENDING" and m["status"] == "shipped":
            err(f"statements[{i}]: a shipped module pins its statement (no PENDING)")
    if not is_core_module(mid) and m["status"] != "planned" and not st:
        err("a challenge past planned lists its frozen statement files")
    for k, v in m["admissible"].items():
        im = ci.ITEM_ID.fullmatch(k)
        if not im or im.group(1) != mid:
            err(f"admissible: key '{k}' must be an item id of {mid} (<ID>.<K><n><lang>)")
            continue
        if im.group(2) not in ci.CHECKED_KINDS:
            err(f"admissible: '{k}' is a {im.group(2)} item; only checked items carry minutes")
        if not isinstance(v, dict) or list(v) not in (list(ADMISSIBLE_KEYS),
                                                      list(ADMISSIBLE_KEYS) + ["exception"]):
            err(f"admissible: '{k}' must be {{ admitted = …, minutes = …, fallback = \"…\" }}"
                " (and, for an admitted item outside its band, exception = \"<kind>: <why>\")")
            continue
        a, mins, fb = v["admitted"], v["minutes"], v["fallback"]
        if "exception" in v:
            ex = v["exception"]
            kind = ex.split(":", 1)[0].strip() if isinstance(ex, str) and ":" in ex else None
            if a is not True:
                err(f"admissible: '{k}' carries an exception but is not admitted (an exception "
                    "admits an item outside its band; a gated item needs none)")
            elif kind not in ADMISSIBLE_EXCEPTION_KINDS or not ex.split(":", 1)[1].strip():
                err(f"admissible: '{k}': exception must be \"<kind>: <why>\" with kind one of "
                    + ", ".join(f"'{x}'" for x in ADMISSIBLE_EXCEPTION_KINDS))
        if not isinstance(a, bool) or not isinstance(mins, int) or isinstance(mins, bool) \
                or not isinstance(fb, str):
            err(f"admissible: '{k}': admitted is true/false, minutes an integer, fallback a string")
        elif a and mins <= 0:
            err(f"admissible: '{k}' is admitted, so it carries its minutes (> 0)")
        elif not a and (mins != 0 or not fb.strip()):
            err(f"admissible: '{k}' is gated: no minutes (0) and a named fallback "
                "(design §7.5, spec §2.8)")
    return errs


def band_problems(mid, admissible):
    """The band errors of module `mid`'s admissible entries (DV5e review fix):
    an exception only on an item OUT_OF_BAND records outside its band, of the
    kind it records and naming its decision; every admitted OUT_OF_BAND item
    carries one; and every OUT_OF_BAND entry holds (out_of_band_problems).
    Entries whose shape check_fields refuses are left to it."""
    out = []
    for k, v in admissible.items():
        if not isinstance(v, dict):
            continue
        ex, kind = v.get("exception"), exception_kind(v)
        if ex is not None:
            if v.get("admitted") is not True or kind not in ADMISSIBLE_EXCEPTION_KINDS:
                continue                       # check_fields reports it
            if k not in OUT_OF_BAND:
                out.append(f"admissible: '{k}' carries an exception, but OUT_OF_BAND records "
                           "it in its band (an exception admits an item outside its band; an "
                           "item re-probed outside it joins OUT_OF_BAND with its proof lines "
                           "and the decision)")
            elif kind != OUT_OF_BAND[k][1]:
                out.append(f"admissible: '{k}' carries a '{kind}' exception, but OUT_OF_BAND "
                           f"records it under '{OUT_OF_BAND[k][1]}' (the user's decision "
                           f"{OUT_OF_BAND[k][2]})")
            elif not re.search(rf"\b{OUT_OF_BAND[k][2]}\b", ex.split(":", 1)[1]):
                out.append(f"admissible: '{k}': its exception's reason names the decision that "
                           f"admits it ({OUT_OF_BAND[k][2]})")
        elif v.get("admitted") is True and k in OUT_OF_BAND:
            lines, kind, dec = OUT_OF_BAND[k]
            out.append(f"admissible: '{k}' is admitted outside its band ({lines} proof lines, "
                       f"OUT_OF_BAND) with no exception: it needs exception = \"{kind}: <why>\" "
                       f"(the user's decision {dec})")
    out += [f"OUT_OF_BAND: '{k}' {why}" for k, why in out_of_band_problems(mid, admissible)]
    return out


def out_of_band_problems(mid, admissible):
    """(item, why) for each OUT_OF_BAND entry of module `mid` that does not
    hold: an item of a practice module, in Dafny or Verus, admitted in the
    registry, whose recorded proof lines fall outside its tier's band."""
    out = []
    for k, (lines, kind, dec) in OUT_OF_BAND.items():
        im = ci.ITEM_ID.fullmatch(k)
        if not im or im.group(1) != mid:
            continue
        tier = q_tier(mid)[0] if mid[0] == "Q" else None
        band = PRACTICE_BANDS.get(tier, {}).get(im.group(4))
        entry = admissible.get(k)
        if band is None:
            out.append((k, "is no Dafny or Verus item of a practice module (Q10-Q18): only "
                           "those have a proof-line band"))
        elif lines < 0 or band[0] <= lines <= band[1]:
            out.append((k, f"records {lines} proof lines, inside its band {band[0]}-{band[1]}: "
                           "an item in band needs no exception (drop the entry)"))
        elif kind not in ADMISSIBLE_EXCEPTION_KINDS:
            out.append((k, f"records an unknown exception kind '{kind}'"))
        elif not isinstance(entry, dict) or entry.get("admitted") is not True:
            out.append((k, "records an item the registry does not admit (an exception admits "
                           "an item; drop the entry or admit the item)"))
    return out


def crate_bin_roots(m):
    """The root files of a module crate's binary targets (gen_units.CRATE_BINS;
    D16: the capstone's `src/main.rs`): a course file of its module, declared in
    its imports, though no registry list names it (it holds no item and no
    hole: trusted code outside `verus!`, built only by `vcheck --bin`)."""
    if m.get("id") not in gu.CRATE_BINS or not isinstance(m.get("exercises"), list):
        return []
    rel = gu.CRATE_BINS[m["id"]][1]
    return [f"{u}/{rel}" for u in gu.derive_units(m["exercises"])
            if gu.unit_kind(u)[0] == "v"]


def exception_kind(entry):
    """The kind of an admissible entry's declared exception, or None."""
    ex = entry.get("exception") if isinstance(entry, dict) else None
    return ex.split(":", 1)[0].strip() if isinstance(ex, str) and ":" in ex else None


def statement_item_problem(root, m, it, items=()):
    """None when an item may carry a statement-item exception (D6, D9: the
    learner writes the statements, a contractor their proof): an H item that
    sits in one of the module's agentic files (statements a contractor's run
    proves), or an H item whose block is a prose item (a `// prose: <name>`
    line) and names its contractor (a `// contractor: <ID>` line: an A item of
    `items`, the module's, in one of its agentic files); else why not. A prose
    item with no contractor (the learner writes the spec and any proof) is not
    a statement item (DV5d review fix)."""
    if it["kind"] != "H":
        return f"it is a {it['kind']} item (a statement item is an H item)"
    if it["file"] in m["agentic"]:
        return None
    block = (read_text(root, it["file"]) or "").split("\n")[it["line_start"] - 1:it["line_end"]]
    if not any(PROSE_LINE.match(x) for x in block):
        return ("its block is no prose item (no `// prose: <name>` line) and its file is not "
                "one of the module's agentic files")
    named = [mm.group(1) for x in block if (mm := CONTRACTOR_LINE.match(x))]
    if len(named) != 1:
        return ("its prose block names no contractor (one `// contractor: <A item>` line): "
                "D6's statement item is one whose proof a contractor writes")
    by_id = {x["id"]: x for x in items}
    c = by_id.get(named[0])
    if c is None or c["kind"] != "A" or c["file"] not in m["agentic"]:
        return (f"its contractor {named[0]} is no A item of the module in one of its agentic "
                "files")
    return None


def sealed_labs(root):
    """{module id: its pinned manifest_sha256 (or None)} for each [[lab]] of
    TRUTH_PINS with an id and an archive whose file exists under `root` and
    hashes to the pinned sha256; an empty dict when the file is missing or
    unusable. (The archive is age ciphertext: hashing it reads no truth.)"""
    import hashlib
    text = read_text(root, TRUTH_PINS)
    try:
        data = tomllib.loads(text) if text is not None else {}
    except tomllib.TOMLDecodeError:
        return {}
    labs = data.get("lab") if isinstance(data.get("lab"), list) else []
    out = {}
    for x in labs:
        if not (isinstance(x, dict) and isinstance(x.get("id"), str)
                and isinstance(x.get("archive"), str) and x["archive"].strip()
                and isinstance(x.get("sha256"), str)):
            continue
        f = Path(root) / x["archive"]
        try:
            digest = hashlib.sha256(f.read_bytes()).hexdigest() if f.is_file() else None
        except OSError:
            digest = None
        if digest == x["sha256"]:
            man = x.get("manifest_sha256")
            out[x["id"]] = man if isinstance(man, str) else None
    return out


def hidden_check_problem(root, m, it, sealed=None):
    """None when an item may carry a hidden-check spec exception (the user's
    decision D21: a prose specification graded by its hidden check): an H item
    of one of the module's exercise files whose block is a prose item (a
    `// prose: <name>` line) naming no contractor, whose hidden check is
    recorded as holding (HIDDEN_CHECKS_HELD) and whose module's sealed truth is
    pinned (TRUTH_PINS: its archive on disk with the pinned sha256; `sealed`,
    when given, is sealed_labs(root)) at the manifest the hold was recorded on;
    else why not."""
    if it["kind"] != "H":
        return f"it is a {it['kind']} item (a hidden-check spec is an H item)"
    if it["file"] in m["agentic"]:
        return ("it sits in one of the module's agentic files (a contractor's statements: "
                "the statement-item kind)")
    if not any(it["file"] == e or (e.endswith("/") and it["file"].startswith(e))
               for e in m["exercises"]):
        return "it is no item of one of the module's exercise files"
    block = (read_text(root, it["file"]) or "").split("\n")[it["line_start"] - 1:it["line_end"]]
    if not any(PROSE_LINE.match(x) for x in block):
        return "its block is no prose item (no `// prose: <name>` line)"
    if any(CONTRACTOR_LINE.match(x) for x in block):
        return ("its prose block names a contractor (a statement item: the statement-item "
                "kind)")
    if it["id"] not in HIDDEN_CHECKS_HELD:
        return ("its hidden check is not recorded as holding (HIDDEN_CHECKS_HELD names the "
                "items whose judging run in the grader container held, Δ220)")
    sealed = sealed_labs(root) if sealed is None else sealed
    if m["id"] not in sealed:
        return (f"{TRUTH_PINS} pins no sealed hidden truth for {m['id']} (a [[lab]] whose "
                "archive is on disk with its pinned sha256)")
    held = HIDDEN_CHECKS_HELD[it["id"]]
    want = held[1] if isinstance(held, tuple) else None
    have = sealed.get(m["id"]) if isinstance(sealed, dict) else None
    if want is not None and have != want:
        return (f"its hidden check held on the sealed truth with manifest {want[:12]}…, but "
                f"{TRUTH_PINS} pins {str(have)[:12]}… for {m['id']} (a re-seal: re-judge it, "
                "or confirm its references unchanged and record the new manifest in "
                "HIDDEN_CHECKS_HELD)")
    return None


def check_constructs(m):
    errs = []
    mid = m["id"]

    def err(msg):
        errs.append(f"{mid}: {msg}")

    for lang in ("d", "v"):
        w, r = m[f"write_{lang}"], m[f"recognise_{lang}"]
        for key, lst in ((f"write_{lang}", w), (f"recognise_{lang}", r)):
            for x in lst:
                if not ci.SLUG.fullmatch(x):
                    err(f"'{key}': {x!r} is not a construct slug (kebab-case, '/' between "
                        "alternatives)")
                for a in x.split("/"):
                    if a in BANNED_SLUGS.get(lang, ()):
                        err(f"'{key}': '{a}' is not available at the pin (Δ47)")
            if len(set(lst)) != len(lst):
                err(f"'{key}' lists a construct twice")
            if lst and lang not in m["langs"]:
                err(f"'{key}' is non-empty but langs has no {lang}")
        written = {a: x for x in w for a in x.split("/")}
        for x in r:
            for a in x.split("/"):
                if a in written:
                    err(f"'{a}' is both WRITE ({written[a]}) and RECOGNISE ({x}) in "
                        f"{LANG_NAMES[lang]}; a construct is one or the other in a module")
    units = set(m["write_d"]) | set(m["write_v"])
    slugs = len(m["write_d"]) + len(m["write_v"])
    if len(units) > WRITE_UNIT_CAP or slugs > WRITE_SLUG_CAP:
        err(f"WRITE lists {len(units)} unit(s) and {slugs} slug(s); at most {WRITE_UNIT_CAP} "
            f"units and {WRITE_SLUG_CAP} slugs per module (a slug in both lists is one paired unit)")
    if mid[0] == "Q" and num(mid) <= 9:
        for lang in ("d", "v"):
            if not m[f"write_{lang}"]:
                err(f"write_{lang} is empty: a concept module lists its {LANG_NAMES[lang]} "
                    "WRITE constructs")
    if mid[0] == "Q" and num(mid) >= 10 and (m["recognise_d"] or m["recognise_v"]):
        err("recognise_d / recognise_v are for the concept tiers (Q01–Q09) and R; must be []")
    return errs


def given_file_layer(p):
    """(track, layer) when p is a given-layer file, else None."""
    if m := re.fullmatch(r"dafny/given/([QR])/(QG_(L[1-7])|RG_(A1b|A[1-5]))_[A-Za-z0-9_]+\.dfy", p):
        return m.group(1), m.group(3) or m.group(4)
    if m := re.fullmatch(r"verus/given/(qg_bignat_l[1-7]|rg_re_a(?:1b|[1-5]))/src/.+\.rs", p):
        layer = gu.crate_layer(m.group(1))
        return gu.layer_track(layer), layer
    return None


def in_listed(p, listed):
    return p in listed or any(x.endswith("/") and p.startswith(x) for x in listed)


def check_imports_table(m):
    errs = []
    mid = m["id"]

    def err(msg):
        errs.append(f"{mid}: {msg}")

    listed = module_paths(m)
    early = (mid[0] == "Q" and num(mid) <= 3) or (mid[0] == "R" and num(mid) <= 6)
    for p, tier in m["imports"].items():
        lang = ci.file_lang(p) if not p.endswith(".specimen") else None
        if lang is None:
            err(f"imports: '{p}' is not a .dfy, .rs or .py file")
            continue
        if not isinstance(tier, str) or tier not in TIERS_BY_LANG[lang]:
            err(f"imports: '{p}' has tier {tier!r}, not one of: " + ", ".join(TIERS_BY_LANG[lang]))
            continue
        g = given_file_layer(p)
        if g:
            first = gu.layer_first_module(g[1])
            if first != mid:
                err(f"imports: '{p}' is a given {g[1]} file, declared by {first}, the first "
                    "module of its layer")
        elif not in_listed(p, listed) and p not in crate_bin_roots(m):
            err(f"imports: '{p}' is not one of {mid}'s files (exercises, exits, agentic, harness, "
                "or its crate's binary root)")
        if lang == "d":
            d = re.search(r"/(core|std)/", p)
            if d and d.group(1) == "core" and tier != "core":
                err(f"imports: '{p}' sits in a core unit; its tier is core")
            if d and d.group(1) == "std" and tier == "core":
                err(f"imports: '{p}' sits in a std unit; its tier is std or std-all")
        if early and not g and tier not in ("core", "prelude", "py-std", "py-fvh"):
            err(f"imports: '{p}' has tier {tier}; the library enters at Q04 / R07 (OD8), so "
                f"{mid}'s files stay core (Dafny) and prelude (Verus)")
    if m["status"] != "planned":
        for key in ("exercises", "exits", "agentic", "harness"):
            for p in m[key]:
                if ci.file_lang(p) and not p.endswith(".specimen") and p not in m["imports"]:
                    errs.append(f"{mid}: imports: {key} file '{p}' has no import tier "
                                "(declare it under [module.imports])")
    return errs


def check_concept_items(m):
    errs = []
    mid = m["id"]

    def err(msg):
        errs.append(f"{mid}: {msg}")

    ci_ = m["concept_items"]
    if ci_ and not (mid[0] == "Q" and num(mid) <= 9):
        err("concept_items (the D4 matrix) is Q01–Q09 only; must be {}")
        return errs
    for k, cited in ci_.items():
        km = CONCEPT_KEY.fullmatch(k)
        if not km:
            err(f"concept_items: key '{k}' must be S<k>.<concept>[@d|@v|@py], the concept in "
                "kebab-case")
            continue
        strand, suffix = f"S{km.group(1)}", km.group(2)
        if strand not in m["strands"]:
            err(f"concept_items: '{k}': {strand} is not one of {mid}'s strands")
        if suffix and suffix not in m["langs"]:
            err(f"concept_items: '{k}' is @{suffix}, but langs has no {suffix}")
        if cited in ("R", "prose"):
            if cited == "prose" and strand not in ("S12", "S13"):
                err(f"concept_items: '{k}' = \"prose\": only S12 and S13 keys may rest on a "
                    "learner-written artifact")
            continue
        if not isinstance(cited, list) or not cited or not all(
                isinstance(x, str) and ci.ITEM_ID.fullmatch(x) for x in cited):
            err(f"concept_items: '{k}' must be \"R\", \"prose\" or a non-empty list of item "
                "ids (<ID>.<K><n><lang>)")
            continue
        ids = [ci.ITEM_ID.fullmatch(x) for x in cited]
        other = [x for x, im in zip(cited, ids) if im.group(1) != mid]
        if other:
            err(f"concept_items: '{k}' cites {', '.join(other)}, items of another module")
        bad = [x for x, im in zip(cited, ids) if im.group(2) not in ci.CITABLE_KINDS]
        if bad:
            err(f"concept_items: '{k}' cites {', '.join(bad)}; only P, H, X, T and A items "
                "are checked (D4)")
        covered = {c for im in ids for c in ci.covered_langs(im.group(4))}
        if suffix:
            off = [x for x, im in zip(cited, ids) if suffix not in ci.covered_langs(im.group(4))]
            if off:
                err(f"concept_items: '{k}' is @{suffix} but cites {', '.join(off)}")
        elif not {"d", "v"} <= covered:
            err(f"concept_items: '{k}' has no language suffix, so it cites a Dafny and a Verus "
                "item (or one dv item); add @d / @v for a one-language concept")
    return errs


# --- registry: the whole table -----------------------------------------------------------

def check_registry(root, data, modules, good):
    errs = []
    ids = [m.get("id") for m in modules]
    for dup in sorted({i for i in ids if isinstance(i, str) and ids.count(i) > 1}):
        errs.append(f"{dup}: id listed more than once")
    for absent in [i for i in EXPECTED_IDS if i not in ids]:
        errs.append(f"{absent}: missing from the registry")
    listed = [i for i in ids if i in EXPECTED_IDS]
    if len(listed) == len(set(listed)) and listed != sorted(listed, key=EXPECTED_IDS.index):
        errs.append("modules must be listed in order: Q01–Q33, then R01–R16")
    legacy = [m.get("legacy_id") for m in modules if m.get("legacy_id")]
    for dup in sorted({i for i in legacy if legacy.count(i) > 1}):
        errs.append(f"legacy_id {dup} used more than once")
    for key in ("chapter", "card"):
        owners = {}
        for m in good:
            for v in (m[key] if isinstance(m[key], list) else [m[key]]):
                owners.setdefault(v, []).append(m["id"])
        for v, who in sorted(owners.items()):
            if v and len(who) > 1:
                errs.append(f"{key} {v!r} is shared by " + ", ".join(who)
                            + (" (paper cards are never shared, design §9.2)" if key == "card" else ""))
    owners = {}
    for m in good:
        for p in set(module_paths(m)) | set(m["imports"]):
            owners.setdefault(p, []).append(m["id"])
    for p, who in sorted(owners.items()):
        if len(who) > 1:
            errs.append(f"'{p}' is listed by " + ", ".join(who) + "; every file has one owner")

    # a concept or practice tier is one sweep: its modules partition S1–S13
    for tier, lo, hi in Q_TIERS[:-1]:
        members = [m for m in good if m["track"] == "Q" and lo <= num(m["id"]) <= hi]
        if len(members) != hi - lo + 1:
            continue  # a missing or malformed module is already reported
        swept = [s for m in members for s in m["strands"]]
        if sorted(swept, key=STRANDS.index) != list(STRANDS):
            errs.append(f"tier {tier} (Q{lo:02d}–Q{hi:02d}): strands must partition S1–S13")
        elif lo >= 4 and [m["strands"] for m in members] != [list(f) for _, f in FAMILIES]:
            errs.append(f"tier {tier} (Q{lo:02d}–Q{hi:02d}): from the moderate tier on the "
                        "modules take the families in order: A (S1–S5), B (S6–S8), C (S9–S13)")

    gpu = sum(m["budget"]["gpu_hours"] for m in good)
    if gpu > GPU_HOURS_TOTAL:
        errs.append(f"budget: gpu_hours sum to {gpu} over the registry, above the course cap of "
                    f"{GPU_HOURS_TOTAL} (design §11.3: the six labs' Qwen work in ≤ "
                    f"{GPU_HOURS_TOTAL} GPU-h)")

    for m in good:
        errs += check_paths(m, root)
    legacy_map = {m["legacy_id"]: m["id"] for m in good if m["legacy_id"]}
    n_tags, ledger_errs = check_ledger(root, {i for i in ids if isinstance(i, str)}, legacy_map)
    return errs + ledger_errs, n_tags


def record_paths(m):
    """(field, path) for every path a well-typed record names."""
    paths = [(k, m[k]) for k in ("chapter", "bank", "rubric") if isinstance(m.get(k), str) and m[k]]
    paths += [(k, p) for k in ("exercises", "exits", "agentic", "harness", "units")
              for p in (m.get(k) or []) if isinstance(p, str)]
    paths += [("imports", p) for p in (m.get("imports") or {})]
    paths += [("statements", s["path"]) for s in (m.get("statements") or [])
              if isinstance(s, dict) and isinstance(s.get("path"), str)]
    return paths


def bad_path(p):
    parts = PurePosixPath(p).parts
    return p.startswith("/") or "\\" in p or "//" in p or any(x in (".", "..") for x in parts)


def path_hygiene(m):
    """Plain repo-relative paths, none into reference or held-out material, no
    component named for the reference. Runs on every record, whatever else is
    wrong with it (the registry is learner-visible)."""
    errs = []
    for key, p in record_paths(m):
        parts = PurePosixPath(p).parts
        if bad_path(p):
            errs.append(f"{m['id']}: {key}: '{p}' must be a plain repo-relative path")
        elif is_reference(p):
            errs.append(f"{m['id']}: {key}: '{p}' points into reference or held-out material; "
                        "the registry is learner-visible")
        elif r := next((x for x in parts if reserved(x.split(".")[0])), None):
            errs.append(f"{m['id']}: {key}: '{p}' is named {r.split('.')[0]!r}; {RESERVED_WHY}")
        elif r := next((x for x in parts if x.lower().startswith("solutions")), None):
            errs.append(f"{m['id']}: {key}: '{p}': '{r}' starts with 'solutions', the reference "
                        "identifiers' prefix, which guard rule 1 refuses in every path field")
    return errs


def check_paths(m, root):
    """Existence for shipped modules; the paper pair in both directions."""
    errs = []
    mid, status = m["id"], m["status"]
    shipped, planned = status == "shipped", status == "planned"
    for key, p in record_paths(m):
        if not shipped or bad_path(p) or is_reference(p):
            continue
        target = root / p
        if key == "units" or p.endswith("/"):
            if not target.is_dir():
                errs.append(f"{mid}: {key}: directory '{p}' does not exist")
        elif not target.is_file():
            errs.append(f"{mid}: {key}: file '{p}' does not exist")
    if mid in PROVIDED_STATEMENTS:
        rel = PROVIDED_STATEMENTS[mid]
        statement = root / rel
        entries = m.get("statements") or []
        if (statement.exists() or not planned) and not entries:
            errs.append(f"{mid}: provided matcher must be declared and pinned in statements")
        for entry in entries:
            if not isinstance(entry, dict) or entry.get("path") != rel:
                continue  # the schema reports malformed or non-exact entries
            if not statement.is_file():
                errs.append(f"{mid}: provided matcher statement does not exist: '{rel}'")
            elif entry.get("sha256") != hashlib.sha256(statement.read_bytes()).hexdigest():
                errs.append(f"{mid}: provided matcher statement hash mismatch: '{rel}'")
    pair = [f"paper/{mid}_problems.tex", f"paper/{mid}_answers.tex"]
    have = [p for p in pair if (root / p).is_file()]
    if m["paper"] and shipped and len(have) < 2:
        errs += [f"{mid}: paper = true but '{p}' does not exist" for p in pair if p not in have]
    elif not m["paper"] and have:
        errs.append(f"{mid}: paper = false but '{have[0]}' exists")
    elif m["paper"] and not planned and not shipped and len(have) == 1:
        pass  # an authoring module may hold half the pair
    elif m["paper"] and planned and len(have) == 1:
        errs.append(f"{mid}: only half of the paper pair exists ('{have[0]}')")
    return errs


def read_ledger(root):
    """[(line number, tag)] for every `- tag:` entry of instructor/ledger.md."""
    text = read_text(root, LEDGER)
    if text is None:
        return []
    # the schema line inside a header comment is a template, not an entry
    text = re.sub(r"<!--.*?-->", lambda c: "\n" * c.group(0).count("\n"), text, flags=re.S)
    out = []
    for lineno, line in enumerate(text.splitlines(), 1):
        t = re.match(r"\s*[-*]\s*tag:\s*([^|\s]*)", line)
        if t:
            out.append((lineno, t.group(1)))
    return out


def check_ledger(root, ids, legacy):
    entries = read_ledger(root)
    errs = []
    for lineno, tag in entries:
        prefix, slash, vocab = tag.partition("/")
        where = f"{LEDGER}:{lineno}"
        if not slash or not prefix or not vocab:
            errs.append(f"{where}: tag '{tag}' is not <module id>/<vocab-tag>")
        elif prefix in legacy:
            errs.append(f"{where}: tag '{tag}' uses the legacy id {prefix}; write "
                        f"{legacy[prefix]}/{vocab}")
        elif prefix not in ids:
            errs.append(f"{where}: tag '{tag}' names no known module")
    return len(entries), errs


# --- units ---------------------------------------------------------------------------------

MOD_DECL = re.compile(r"(?m)^\s*(?:pub(?:\([^)]*\))?\s+)?mod\s+([A-Za-z_]\w*)\s*;")


def check_units(root, data, good):
    errs, units = gu.check(root, data)
    for m in good:
        if m["status"] == "planned":
            continue
        for key in ("exits", "agentic"):
            for p in m[key]:
                if not p.startswith("verus/") or not p.endswith(".rs"):
                    continue
                lib = PurePosixPath(p).parent / "lib.rs"
                text = read_text(root, lib.as_posix())
                if text is None:
                    continue
                code = "\n".join(ci.scan_c(text)[0])
                if PurePosixPath(p).stem in MOD_DECL.findall(code):
                    errs.append(f"{lib}: declares `mod {PurePosixPath(p).stem};` — {key} files "
                                "stay outside the crate's build (spec §3.1 rule 2)")
    given = root / "verus" / "given"
    if given.is_dir():
        for d in sorted(x for x in given.iterdir() if x.is_dir()):
            layer = gu.crate_layer(d.name)
            rel = f"verus/given/{d.name}/Cargo.toml"
            if layer is None:
                errs.append(f"verus/given/{d.name}: not a layer crate (qg_bignat_l1..l7, "
                            "rg_re_a1, rg_re_a1b, rg_re_a2..a5)")
                continue
            try:
                with open(d / "Cargo.toml", "rb") as f:
                    cargo = tomllib.load(f)
            except FileNotFoundError:
                errs.append(f"{rel}: missing")
                continue
            except tomllib.TOMLDecodeError:
                errs.append(f"{rel}: not valid TOML")
                continue
            deps = sorted(cargo.get("dependencies", {}))
            want = sorted(["vstd"] + [gu.verus_layer_crate(x) for x in gu.layer_chain(layer)[:-1]])
            if deps != want:
                errs.append(f"{rel}: dependencies {deps} must be exactly {want} (vstd and every "
                            "lower layer of the chain, Δ22)")
            if cargo.get("package", {}).get("name") != d.name:
                errs.append(f"{rel}: package name must be {d.name!r}")
            if "patch" in cargo or cargo.get("package", {}).get("build", False) is not False:
                errs.append(f"{rel}: no [patch] section and no build script (Δ20)")
    n = len(units)
    return errs, f"units: {n} unit(s) generated for the armed modules; {gu.WORKSPACE} consistent"


# --- source scanning per language -------------------------------------------------------------

DAFNY_IMPORT = re.compile(r"\bimport\s+(?:opened\s+)?(?:[A-Za-z_][\w']*\s*[=:]\s*)?"
                          r"([A-Za-z_][\w'.]*)")
DAFNY_MODULE = re.compile(r"^\s*(?:(?:abstract|replaceable)\s+)?module\s+(?:\{[^}]*\}\s*)*"
                          r"([A-Za-z_][\w'.]*)")
DAFNY_TOP_DECL = re.compile(
    r"^\s*(?:(?:ghost|static|opaque|twostate|least|greatest|abstract)\s+)*"
    r"(lemma|function|method|predicate|datatype|codatatype|type|class|trait|const|iterator|"
    r"newtype|import|export|constructor)\b")


def dafny_facts(text):
    """(imports [(line, name)], top modules [(line, name)], top declarations
    outside a module [(line, kw)], include lines [line], every module name
    declared at any depth)."""
    code, starts = ci.scan_c(text)
    imports, mods, loose, incl, local = [], [], [], [], set()
    depth = 0
    for ln, line in enumerate(code, 1):
        if mm := DAFNY_MODULE.match(line):
            local.add(mm.group(1).split(".")[-1])
            if depth == 0:
                mods.append((ln, mm.group(1)))
        elif depth == 0 and (dm := DAFNY_TOP_DECL.match(line)):
            loose.append((ln, dm.group(1)))
        if depth == 0 and re.match(r"\s*include\b", line):
            incl.append(ln)
        for im in DAFNY_IMPORT.finditer(line):
            imports.append((ln, im.group(1)))
        depth = max(0, depth + line.count("{") - line.count("}"))
    return imports, mods, loose, incl, local


RUST_ROOT = re.compile(r"(?<![\w:])([A-Za-z_]\w*)\s*::")
RUST_USE = re.compile(r"\b(?:use|extern\s+crate)\s+(?:::)?([A-Za-z_]\w*)")
VSTD_PATH = re.compile(r"(?<![\w:])vstd\s*::\s*(\{[^}]*\}|[A-Za-z_]\w*)")


def rust_facts(text):
    """(crate roots [(line, name)], vstd modules [(line, name)], reach lines [(line, what)])."""
    code, _ = ci.scan_c(text)
    roots, vstd, reach = [], [], []
    for ln, line in enumerate(code, 1):
        for r in RUST_ROOT.finditer(line):
            roots.append((ln, r.group(1)))
        for r in RUST_USE.finditer(line):
            roots.append((ln, r.group(1)))
        for v in VSTD_PATH.finditer(line):
            seg = v.group(1)
            if seg.startswith("{"):
                for part in seg[1:-1].split(","):
                    first = part.strip().split("::")[0].strip()
                    if first:
                        vstd.append((ln, first))
            else:
                vstd.append((ln, seg))
        if re.search(r"#\s*\[\s*path\s*=", line) or "#[path" in line:
            reach.append((ln, "#[path = …]"))
        if re.search(r"\binclude(?:_str|_bytes)?\s*!", line):
            reach.append((ln, "include!"))
    # `#[path = "…"]`: the attribute's string is blanked, the attribute name is not
    return roots, vstd, reach


def python_facts(text):
    """(imports [(line, top-level name or '.' for relative)], sys.path lines)."""
    code, _ = ci.scan_py(text)
    imports, syspath = [], []
    for ln, line in enumerate(code, 1):
        if m := re.match(r"\s*import\s+(.+)", line):
            for part in m.group(1).split(","):
                name = part.strip().split()[0] if part.strip() else ""
                if name:
                    imports.append((ln, name.split(".")[0]))
        elif m := re.match(r"\s*from\s+(\.*)([\w.]*)\s+import\b", line):
            imports.append((ln, "." if m.group(1) else m.group(2).split(".")[0]))
        if re.search(r"\bsys\s*\.\s*path\b", line):
            syspath.append(ln)
    return imports, syspath


def course_files(root):
    """Every course source file on disk the import-tier and isolation groups
    check: module files and given layers of both tracks, both verifiers, and
    the learner Python packages."""
    out = []
    for pattern in ("dafny/Q/**/*.dfy", "dafny/R/**/*.dfy", "dafny/checks/*.dfy",
                    "dafny/given/Q/*.dfy",
                    "dafny/given/R/*.dfy", "verus/q/*/src/**/*.rs", "verus/r/*/src/**/*.rs",
                    "verus/given/*/src/**/*.rs", "harness/q/fvh_q/**/*.py",
                    "harness/r/fvh_r/**/*.py"):
        out += [p.relative_to(root).as_posix() for p in root.glob(pattern) if p.is_file()]
    return sorted(set(out))


class Sources:
    """Course source facts, read once."""

    def __init__(self, root):
        self.root, self.cache = root, {}

    def text(self, rel):
        if rel not in self.cache:
            self.cache[rel] = read_text(self.root, rel) or ""
        return self.cache[rel]

    def dafny(self, rel):
        return dafny_facts(self.text(rel))

    def rust(self, rel):
        return rust_facts(self.text(rel))

    def python(self, rel):
        return python_facts(self.text(rel))


def dafny_module_index(root, src):
    """{top-level Dafny module name: file} over every Dafny course file."""
    index = {}
    for rel in course_files(root):
        if rel.endswith(".dfy"):
            for _, name in src.dafny(rel)[1]:
                index.setdefault(name.split(".")[0], rel)
    return index


def given_crate_files(root, crate):
    d = root / "verus" / "given" / crate / "src"
    return sorted(p.relative_to(root).as_posix() for p in d.rglob("*.rs")) if d.is_dir() else []


# --- import-tiers ------------------------------------------------------------------------------

def check_import_tiers(root, good):
    errs, declared = [], {}
    for m in good:
        for p, tier in m["imports"].items():
            if p in declared:
                errs.append(f"{m['id']}: imports: '{p}' is also declared by {declared[p][0]}; "
                            "every course file has exactly one owner")
            else:
                declared[p] = (m["id"], tier)
    on_disk = course_files(root)
    for p in on_disk:
        if p in declared:
            continue
        if PurePosixPath(p).name == "__init__.py":
            declared[p] = ("package", "py-fvh")  # package scaffolding: no module owns it
            continue
        errs.append(f"{p}: undeclared course file escapes the tier check — declare it in "
                    "its module's [module.imports] (a given layer: its first module's)")
    armed = [m["id"] for m in good if is_core_module(m["id"]) and m["status"] != "planned"]
    if armed and not any(not given_file_layer(p) for p in on_disk):
        errs.append("course globs match no module file (dafny/{Q,R}, verus/{q,r}, "
                    "harness/{q,r}) while " + ", ".join(armed) + " "
                    + ("is" if len(armed) == 1 else "are") + " past planned — a broken glob, "
                    "not a pass")
    src = Sources(root)
    index = dafny_module_index(root, src)
    checked, tiers = 0, set()
    for p, (mid, tier) in sorted(declared.items()):
        if not (root / p).is_file():
            continue
        checked += 1
        tiers.add(tier)
        lang = ci.file_lang(p)
        if lang == "d":
            # None-safe order: a name can be reached both directly (via None) and through
            # a layer file that imports its own first module (L4's QG_L4_Limbs), same line
            for line, mod, via in sorted(dafny_reach(src, index, p), key=_reach_key):
                if not mod.startswith("Std"):
                    continue
                how = f" (via {via})" if via else ""
                if tier == "core":
                    errs.append(f"{p}:{line}: reaches {mod}{how} but its tier is core (no "
                                "standard library)")
                elif tier == "std" and (mod == STD_NEAR_ANSWER or mod.startswith(STD_NEAR_ANSWER + ".")):
                    errs.append(f"{p}:{line}: reaches {mod}{how}: the std tier excludes it "
                                "(a near-answer for the spine, Δ35); only a std-all file may")
        elif lang == "v":
            for line, seg, via in sorted(verus_reach(root, src, p), key=_reach_key):
                if tier != "all" and seg not in VSTD_ALLOW[tier]:
                    how = f" (via {via})" if via else ""
                    errs.append(f"{p}:{line}: uses vstd::{seg}{how} but its tier is {tier}")
        elif lang == "py":
            track = file_track(p) or mid[0]
            for line, name in src.python(p)[0]:
                if name == "." or name == "__future__" or name in sys.stdlib_module_names:
                    continue
                if name in ("fvh_q", "fvh_r", "solutions", "Solutions"):
                    continue  # course-internal: the isolation group judges these
                if tier == "py-fvh" and name == "fvh":
                    continue
                errs.append(f"{p}:{line}: imports {name} but its tier is {tier} "
                            f"({'stdlib only' if tier == 'py-std' else 'stdlib, fvh and fvh_' + track.lower()})")
    summary = (f"import-tiers: {checked} file{'s' if checked != 1 else ''} in {len(tiers)} "
               f"tier{'s' if len(tiers) != 1 else ''}, all within their allowlists")
    return errs, summary, len(declared)


def _reach_key(t):
    """Sort key of a (line, name, via) reach tuple: via may be None."""
    return (t[0], t[1], t[2] or "")


def dafny_reach(src, index, rel, seen=None, via=None, line0=None):
    """{(line in rel, module name, via)}: rel's imports, plus (transitively) the
    imports of every course module it imports. Std names are what tiers judge."""
    seen = set() if seen is None else seen
    if rel in seen:
        return set()
    seen.add(rel)
    out = set()
    for line, name in src.dafny(rel)[0]:
        at = line0 if line0 is not None else line
        out.add((at, name, via))
        target = index.get(name.split(".")[0])
        if target and target != rel:
            out |= dafny_reach(src, index, target, seen, via or name.split(".")[0], at)
    return out


def verus_reach(root, src, rel, seen=None, via=None, line0=None):
    """{(line in rel, vstd module, via)}: the vstd modules rel uses, plus those of
    every given layer crate it reaches (transitively)."""
    seen = set() if seen is None else seen
    if rel in seen:
        return set()
    seen.add(rel)
    roots, vstd, _ = src.rust(rel)
    out = {(line0 if line0 is not None else line, seg, via) for line, seg in vstd}
    for line, name in roots:
        if gu.crate_layer(name):
            for f in given_crate_files(root, name):
                out |= verus_reach(root, src, f, seen, via or name,
                                   line0 if line0 is not None else line)
    return out


# --- isolation ----------------------------------------------------------------------------------

def check_isolation(root, good):
    errs = []
    by_id = {m["id"]: m for m in good}
    owner = {p: m["id"] for m in good for p in m["imports"]}
    src = Sources(root)
    files = course_files(root)
    n_q = n_r = 0
    for rel in files:
        g = given_file_layer(rel)
        if g:
            track, layer, mid = g[0], g[1], None
        else:
            mm = re.match(r"(?:dafny/([QR])/([QR]\d\d)_|verus/([qr])/([qr]\d\d)_|harness/([qr])/"
                          r"|dafny/checks/(([QR])\d\d)_)", rel)
            track = (mm.group(1) or mm.group(3) or mm.group(5) or mm.group(7)).upper() if mm else None
            mid = (mm.group(2) or (mm.group(4) or "").upper() or mm.group(6) or owner.get(rel)) \
                if mm else None
            layer = gu.expected_layer(mid) if mid else ""
        if track == "Q":
            n_q += 1
        else:
            n_r += 1
        lang = ci.file_lang(rel)
        if lang == "d":
            errs += isolation_dafny(rel, src, track, layer, mid, g)
        elif lang == "v":
            errs += isolation_rust(rel, src, track, layer, mid, g)
        else:
            errs += isolation_python(rel, src, track)
        other = "bench/local/r" if track == "Q" else "bench/local/q"
        for ln, line in enumerate(src.text(rel).split("\n"), 1):
            if other in line:
                errs.append(f"{rel}:{ln}: names {other}: the tracks never reach each other's "
                            "bench (I2)")

    residue = residue_files(root, good)
    for rel in residue:
        errs += check_residue(rel, read_text(root, rel) or "")
    e, n_walked = check_reserved_names(root)
    errs += e
    summary = (f"isolation: {n_q} Q file(s), {n_r} R file(s); no cross-track or reference "
               f"reach, every declaration prefixed, {len(residue)} file(s) free of label residue, "
               f"no reserved name in {n_walked} learner-tree entries")
    return errs, summary


# --- isolation: reserved names (RESERVED_NAMES) ------------------------------------------------

DAFNY_MODULE_NAMES = re.compile(r"\b(?:module\s+(?:\{[^}]*\}\s*)*|refines\s+|import\s+(?:opened\s+)?)"
                                r"([A-Za-z_][\w'.]*)(?:\s*[=:]\s*([A-Za-z_][\w'.]*))?")
RUST_MODULE_NAMES = re.compile(r"\b(?:mod|extern\s+crate)\s+([A-Za-z_]\w*)(?:\s+as\s+([A-Za-z_]\w*))?")
RUST_PATH_SEGMENT = re.compile(r"(?<![\w])([A-Za-z_]\w*)\s*::")


def walk_learner_tree(root):
    """Yield (rel, is_dir) for every entry of the learner-visible tree, sorted.
    Never lists or enters reference or held-out material; never enters a
    dot-directory other than .claude, a build output or a symlinked directory."""
    for dirpath, dirnames, filenames in os.walk(root):
        here = Path(dirpath).relative_to(root).as_posix()
        here = "" if here == "." else here + "/"
        keep = []
        for d in sorted(dirnames):
            if is_reference(d):
                continue
            yield here + d, True
            if (d.startswith(".") and here + d != ".claude") or d in WALK_SKIP_DIRS \
                    or DAFNY_OUTPUT_DIR.fullmatch(d) or os.path.islink(os.path.join(dirpath, d)):
                continue
            keep.append(d)
        dirnames[:] = keep
        for f in sorted(filenames):
            if not is_reference(f):
                yield here + f, False


def learner_text(root, rel):
    """rel's text when it resolves inside this checkout and outside every
    reference tree, else None (a symlink is never followed out of the tree)."""
    try:
        real = (root / rel).resolve()
        inside = real.relative_to(root.resolve())
        if any(is_reference(x) for x in inside.parts) or real.stat().st_size > (1 << 21):
            return None
        return real.read_text(encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        return None


def code_names(rel, text):
    """[(line, what, name)]: the module, crate and package names a source file
    declares or reaches, comments and strings blanked."""
    name = PurePosixPath(rel).name
    out = []
    if name.endswith((".dfy", ".dfy.specimen")):
        for ln, line in enumerate(ci.scan_c(text)[0], 1):
            for mm in DAFNY_MODULE_NAMES.finditer(line):
                out += [(ln, "Dafny module", x) for g in mm.groups() if g for x in g.split(".")]
    elif name.endswith((".rs", ".rs.specimen")):
        for ln, line in enumerate(ci.scan_c(text)[0], 1):
            for mm in RUST_MODULE_NAMES.finditer(line):
                out += [(ln, "Rust crate or module", g) for g in mm.groups() if g]
            out += [(ln, "Rust crate or module", g) for g in RUST_PATH_SEGMENT.findall(line)]
    elif name.endswith((".py", ".pyi")):
        for ln, line in enumerate(ci.scan_py(text)[0], 1):
            if mm := re.match(r"\s*import\s+(.+)", line):
                heads = [p.split()[0] for p in mm.group(1).split(",") if p.split()]
            elif mm := re.match(r"\s*from\s+\.*([\w.]+)\s+import\b", line):
                heads = [mm.group(1)]
            else:
                continue
            out += [(ln, "Python module", x) for h in heads for x in h.split(".")]
    return out


def toml_names(rel, text):
    """[(where, name)]: the crate and package names a Cargo.toml or
    pyproject.toml declares or depends on."""
    try:
        doc = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return []  # the units group reports a broken generated file
    out = []

    def get(tbl, key):
        v = tbl.get(key) if isinstance(tbl, dict) else None
        return v if isinstance(v, dict) else {}

    if PurePosixPath(rel).name == "pyproject.toml":
        out.append(("project.name", get(doc, "project").get("name")))
        st = get(get(doc, "tool"), "setuptools")
        for key in ("packages", "py-modules"):
            if isinstance(st.get(key), list):
                out += [(f"tool.setuptools.{key}", x) for x in st[key]]
        return [(w, n) for w, n in out if isinstance(n, str)]
    out.append(("package.name", get(doc, "package").get("name")))
    out.append(("lib.name", get(doc, "lib").get("name")))
    for kind in ("bin", "test", "example", "bench"):
        targets = doc.get(kind) if isinstance(doc.get(kind), list) else []
        out += [(f"[[{kind}]] name", t.get("name")) for t in targets if isinstance(t, dict)]
    tables = [("", doc), ("workspace.", get(doc, "workspace"))]
    tables += [(f"target.{cfg}.", t) for cfg, t in get(doc, "target").items() if isinstance(t, dict)]
    for where, tbl in tables:
        for key in ("dependencies", "dev-dependencies", "build-dependencies"):
            for dep, spec in get(tbl, key).items():
                out.append((f"{where}{key}", dep))
                if isinstance(spec, dict):
                    out.append((f"{where}{key}.{dep}.package", spec.get("package")))
    return [(w, n) for w, n in out if isinstance(n, str)]


def check_reserved_names(root):
    """No crate, package, Python module or Dafny module (nor a Rust module) in the
    learner-visible tree is named solutions_policy or solutions-first: not as a
    file or directory, not declared, not imported, not a Cargo or pyproject name.
    A reference twin keeps its exercise file's stem, so the learner side covers
    the twins; a reference-only name is the reference lint's (author-only)."""
    errs, n = [], 0
    for rel, is_dir in walk_learner_tree(root):
        n += 1
        shown = rel if "/" in rel else f"./{rel}"
        name = PurePosixPath(rel).name
        if (is_dir or name.endswith(MODULE_SUFFIXES)) and reserved(name.split(".")[0]):
            errs.append(f"{shown}: a {'directory' if is_dir else 'module file'} named "
                        f"{name.split('.')[0]!r}; {RESERVED_WHY}")
        if is_dir:
            continue
        if name in ("Cargo.toml", "pyproject.toml"):
            for where, x in toml_names(rel, learner_text(root, rel) or ""):
                if reserved(x):
                    errs.append(f"{shown}: {where} names {x!r}; {RESERVED_WHY}")
        elif ci.file_lang(rel) or name.endswith(".pyi"):
            text = learner_text(root, rel)
            for ln, what, x in code_names(rel, text or ""):
                if reserved(x):
                    errs.append(f"{shown}:{ln}: {what} {x!r}; {RESERVED_WHY}")
    return errs, n


def classify_layer_ref(track, layer_of_file, ref_layer, is_given):
    """None when a file at layer_of_file may reach ref_layer, else a reason."""
    if gu.layer_track(ref_layer) != track:
        return "a layer of the other track (I2: the tracks never import each other)"
    if is_given:
        if gu.layer_rank(ref_layer) >= gu.layer_rank(layer_of_file):
            return "a layer imports only lower layers of its track"
        return None
    if not layer_of_file or gu.layer_rank(ref_layer) > gu.layer_rank(layer_of_file):
        return (f"a layer above the module's tier (it may reach "
                + ("no layer" if not layer_of_file else
                   f"{gu.layer_chain(layer_of_file)[0]}–{layer_of_file}") + ")")
    return None


def isolation_dafny(rel, src, track, layer, mid, given):
    errs = []
    imports, mods, loose, incl, local = src.dafny(rel)
    if given:
        prefix = gu.dafny_layer_prefix(given[1])
        own = lambda name: name.startswith(prefix)
    else:
        prefix = mid or "?"
        own = lambda name: re.match(rf"{re.escape(prefix)}(?![0-9])", name) is not None
    for ln, name in mods:
        if not own(name):
            errs.append(f"{rel}:{ln}: module {name} must be named {prefix}… (I4a: every "
                        "declaration sits under its module's prefix)")
    for ln, kw in loose:
        errs.append(f"{rel}:{ln}: `{kw}` outside any module (I4a: wrap the file's "
                    "declarations in `module {prefix}… {{ }}`)")
    for ln in incl:
        errs.append(f"{rel}:{ln}: `include` in a course file (I1: projects include the "
                    "given layers; a file never includes, design §6.3)")
    for ln, name in imports:
        head = name.split(".")[0]
        if head == "Std" or own(head) or head in local:
            continue
        if head.lower().startswith("solutions"):
            errs.append(f"{rel}:{ln}: imports {name}: reference identifiers start with "
                        "`solutions`; course files never reach them (I1)")
            continue
        lm = re.match(r"(QG_(L[1-7])|RG_(A1b|A[1-5]))_", head)
        if lm:
            ref = lm.group(2) or lm.group(3)
            why = classify_layer_ref(track, layer if not given else given[1], ref, bool(given))
            if why:
                errs.append(f"{rel}:{ln}: imports {name}, {why} (I1)")
            continue
        if re.match(r"[QR]\d\d", head):
            same = head[0] == track
            errs.append(f"{rel}:{ln}: imports {name}, " + (
                "another module's file — a later module reaches earlier work only through a "
                "given layer (I1, re-supply)" if same else
                "a module of the other track (I2: the tracks never import each other)"))
            continue
        errs.append(f"{rel}:{ln}: imports {name}, which is neither Std, a given layer of its "
                    f"tier nor one of {prefix}'s own modules (I1)")
    return errs


def isolation_rust(rel, src, track, layer, mid, given):
    errs = []
    roots, _, reach = src.rust(rel)
    seen = set()
    for ln, name in roots:
        if (ln, name) in seen:
            continue
        seen.add((ln, name))
        if name.lower().startswith("solutions"):
            errs.append(f"{rel}:{ln}: names {name}: reference identifiers start with "
                        "`solutions`; course files never reach them (I1)")
        elif gu.crate_layer(name):
            why = classify_layer_ref(track, layer if not given else given[1],
                                     gu.crate_layer(name), bool(given))
            if why:
                errs.append(f"{rel}:{ln}: uses {name}, {why} (I1)")
        elif re.fullmatch(r"[qr]\d\d_\w+", name):
            own = mid is not None and name.startswith(mid.lower() + "_")
            if not own:
                same = name[0].upper() == track
                errs.append(f"{rel}:{ln}: uses {name}, " + (
                    "another module's crate (I1, re-supply)" if same else
                    "a crate of the other track (I2)"))
    for ln, what in reach:
        errs.append(f"{rel}:{ln}: {what} reaches files outside the crate's module tree (I1)")
    return errs


def isolation_python(rel, src, track):
    errs = []
    imports, syspath = src.python(rel)
    other = "fvh_r" if track == "Q" else "fvh_q"
    for ln, name in imports:
        if name == other:
            errs.append(f"{rel}:{ln}: imports {other}, the other track's package (I2)")
        elif name.lower().startswith("solutions"):
            errs.append(f"{rel}:{ln}: imports {name}: never the reference harness (I1)")
    for ln in syspath:
        errs.append(f"{rel}:{ln}: sys.path manipulation reaches files outside the package (I1)")
    return errs


def residue_files(root, good):
    out = set(course_files(root))
    for folder, pattern in (("docs", "[QR][0-9][0-9]_*.md"), (BANKS.rstrip("/"), "*.md"),
                            ("paper/rubrics", "*_rubric.md")):
        d = root / folder
        if d.is_dir():
            out |= {f"{folder}/{p.name}" for p in d.glob(pattern) if p.is_file()}
    return sorted(out)


RESIDUE_Q = re.compile(r"(?<![A-Za-z0-9_])Q[1-9](?!\d)")
RESIDUE_V1 = re.compile(r"(?<![A-Za-z0-9_])F(?:0\d|1[0-7])(?!\d)")
MODULE_ID = re.compile(r"(?<![A-Za-z0-9_])([QR])(\d\d)(?!\d)")
MERMAID_ID = re.compile(r"(?<![\w-])[QR]\d\w*")
BANK_LABEL = re.compile(r"#{2,4}\s+([A-Z]{1,3})(\d+)\b")
RUBRIC_LABEL = re.compile(r"\s*(?:[-*]\s+)?\*\*([A-Z]{1,3})(\d+)\s+—")


def file_track(rel):
    """'Q' or 'R' for a track-owned file (by its name), else None."""
    if PurePosixPath(rel).name.startswith("defense_"):
        return "Q"  # the challenge defense banks
    for part in PurePosixPath(rel).parts:
        if m := re.match(r"([QR])\d\d(?:_|\.|$)", part):
            return m.group(1)
        if m := re.match(r"([qr])\d\d_", part):
            return m.group(1).upper()
        if part in ("fvh_q", "Q"):
            return "Q"
        if part in ("fvh_r", "R"):
            return "R"
        if m := re.match(r"(QG|RG)_", part):
            return part[0]
        if m := re.match(r"(qg|rg)_", part):
            return part[0].upper()
    return None


def check_residue(rel, text):
    """I5: label hygiene and cross-track mentions in one course-authored file."""
    errs = []
    fence = None
    track = file_track(rel)
    for ln, line in enumerate(text.split("\n"), 1):
        for m in RESIDUE_Q.finditer(line):
            errs.append(f"{rel}:{ln}: '{m.group(0)}' is a single-digit Q label; module ids are "
                        "Q01–Q33 (I5)")
        for m in RESIDUE_V1.finditer(line):
            errs.append(f"{rel}:{ln}: '{m.group(0)}' is a design-v1 module id (F00–F17); the "
                        "course uses Q01–Q33 and R01–R16 (I5)")
        if track:
            for m in MODULE_ID.finditer(line):
                if m.group(1) == track:
                    continue
                allowed = (r"Recap\s*(?:→|->)\s*Q\d\d" if track == "R"
                           else r"Deep dive\s*(?:→|->)\s*R\d\d")
                if not re.search(allowed, line):
                    form = "Recap → Qnn" if track == "R" else "Deep dive → Rnn"
                    errs.append(f"{rel}:{ln}: names {m.group(0)}, a module of the other track; "
                                f"a cross-track mention is only a `{form}` link (I5)")
        if not rel.endswith(".md"):
            continue
        s = line.strip()
        if s.startswith("```"):
            fence = None if fence else (s[3:].strip() or "text")
            continue
        if fence == "mermaid" and not s.startswith("%%"):
            t = re.sub(r'"[^"]*"', " ", line)
            t = re.sub(r"\[[^\]]*\]|\([^)]*\)|\{[^}]*\}|\|[^|]*\|", " ", t)
            for m in MERMAID_ID.finditer(t):
                errs.append(f"{rel}:{ln}: mermaid node id '{m.group(0)}' looks like a module id; "
                            "use a lower-case id and put the module in a quoted label")
        if fence:
            continue
        if rel.startswith(BANKS) and (m := BANK_LABEL.match(line)) \
                and m.group(1) not in ("K", "PP"):
            errs.append(f"{rel}:{ln}: bank question label '{m.group(1)}{m.group(2)}' — bank "
                        "questions are K<n>, parallel problems PP<n>")
        if rel.startswith("paper/rubrics/") and (m := RUBRIC_LABEL.match(line)) \
                and m.group(1) not in ("C", "D", "A", "B"):
            errs.append(f"{rel}:{ln}: rubric line label '{m.group(1)}{m.group(2)}' — rubric "
                        "lines are C<n>, D<n>, A<n> or B<n>")
    return errs


# --- items and coverage ----------------------------------------------------------------------------

ITEM_EXTS = (".dfy", ".rs", ".py", ".dfy.specimen", ".rs.specimen")


def item_files(root, m):
    """The module's item-bearing files that exist: listed files, files under
    listed directories, and declared imports (given layers excluded)."""
    out = []
    for p in list(module_paths(m)) + [p for p in m["imports"] if not given_file_layer(p)]:
        if p.endswith("/"):
            d = root / p
            if d.is_dir():
                out += sorted(x.relative_to(root).as_posix() for x in d.rglob("*")
                              if x.is_file() and x.name.endswith(ITEM_EXTS))
        elif p.endswith(ITEM_EXTS) and (root / p).is_file():
            out.append(p)
    return list(dict.fromkeys(out))


def module_items(root, m):
    """Items of one module plus per-item errors. Returns (items, errors)."""
    mid = m["id"]
    slot_rel = f"{SLOTS}/{mid}.slots"
    slot_text = read_text(root, slot_rel)
    errs, slot_file = [], None
    if slot_text is not None:
        table, e = ci.parse_slot_file(slot_rel, slot_text)
        errs += e
        slot_file = (slot_rel, table)
    items = []
    for rel in item_files(root, m):
        got, e = ci.parse_items(rel, read_text(root, rel) or "", slot_file)
        items += got
        errs += e
    seen = {}
    lists = {("write", "d"): m["write_d"], ("write", "v"): m["write_v"],
             ("recognise", "d"): m["recognise_d"], ("recognise", "v"): m["recognise_v"]}
    by_id = {it["id"]: it for it in items}
    for it in items:
        at = f"{it['file']}:{it['line_start']}"
        if not it["id"].startswith(mid + "."):
            errs.append(f"{at}: item {it['id']} in a {mid} file (ids carry their module)")
        if it["id"] in seen:
            errs.append(f"{at}: duplicate item id {it['id']} (first at {seen[it['id']]})")
        else:
            seen[it["id"]] = at
        if it["strand"] and it["strand"] not in m["strands"]:
            errs.append(f"{at}: {it['id']} is in {it['strand']}, not one of {mid}'s strands")
        for lang in ci.covered_langs(it["lang"]):
            if lang not in m["langs"]:
                errs.append(f"{at}: {it['id']} is a {it['lang']} item but langs has no {lang}")
        fmt = it["format"] or ""
        if it["kind"] == "C" and fmt.partition(":")[0] in ("write", "recognise"):
            card, _, slug = fmt.partition(":")
            for lang in ci.covered_langs(it["lang"]):
                if lang in ("d", "v") and not any(slug == w or slug in w.split("/")
                                                  for w in lists[(card, lang)]):
                    errs.append(f"{at}: card {it['id']} is {fmt}, but '{slug}' is not in "
                                f"{mid}'s {card}_{lang}")
        if it["pair"]:
            other = by_id.get(it["pair"])
            if other is None:
                errs.append(f"{at}: {it['id']} pairs with {it['pair']}, which no marker declares")
            elif other["pair"] != it["id"]:
                errs.append(f"{at}: {it['id']} pairs with {it['pair']}, but {it['pair']} does not "
                            f"pair back")
    if slot_file:
        verdicts = {it["id"].split(".", 1)[1] for it in items if it["format"] == "verdict"}
        for local, (line, _) in sorted(slot_file[1].items()):
            if local not in verdicts:
                errs.append(f"{slot_rel}:{line}: slot {local} names no verdict item of {mid}")
    return items, errs


def checked_langs(items, kinds=ci.CHECKED_KINDS):
    return {c for it in items if it["kind"] in kinds for c in ci.covered_langs(it["lang"])}


def check_coverage(root, good, data):
    errs = []
    by_id = {m["id"]: m for m in good}
    items_of = {}
    seen = {"Q": {"d": set(), "v": set()}, "R": {"d": set(), "v": set()}}
    for m in sorted(good, key=lambda x: EXPECTED_IDS.index(x["id"])):
        mid, track = m["id"], m["id"][0]
        for lang in ("d", "v"):
            seen[track][lang] |= {a for key in (f"write_{lang}", f"recognise_{lang}")
                                  for w in m[key] for a in [w, *w.split("/")]}
        if m["status"] == "planned":
            continue
        items, ierrs = module_items(root, m)
        errs += ierrs
        items_of[mid] = items
        ids = {it["id"] for it in items}
        for it in items:
            for tok in it["uses"]:
                for lang in ci.covered_langs(it["lang"]):
                    if lang in seen[track] and tok not in seen[track][lang] and not (
                            set(tok.split("/")) <= seen[track][lang]):
                        errs.append(f"{it['file']}:{it['line_start']}: {it['id']} uses '{tok}', "
                                    f"which no {track} module up to {mid} lists as {LANG_NAMES[lang]} "
                                    "WRITE or RECOGNISE (no unseen construct)")
        concept = (track == "Q" and num(mid) <= 9) or track == "R"
        if track == "Q" and num(mid) <= 9:
            cited = set()
            for key, value in m["concept_items"].items():
                for iid in value if isinstance(value, list) else []:
                    cited.add(iid)
                    if iid not in ids:
                        errs.append(f"{mid}: concept_items: '{key}' cites {iid}, but no item "
                                    "marker in the module's files declares it")
            for it in items:
                if it["kind"] in ci.CHECKED_KINDS and it["id"] not in cited:
                    errs.append(f"{it['file']}:{it['line_start']}: {it['id']} is cited by no "
                                "concept_items key — an orphan checked item (D4)")
            for s in m["strands"]:
                if not any(k.split(".")[0] == s for k in m["concept_items"]):
                    errs.append(f"{mid}: strand {s} has no concept_items key (D4: every "
                                "strand's concepts cite checked items)")
        for lang in ("d", "v"):
            for w in m[f"write_{lang}"]:
                alts = {w, *w.split("/")}
                tagged = [it["id"] for it in items if it["kind"] in ci.USES_KINDS
                          and lang in ci.covered_langs(it["lang"]) and alts & set(it["uses"])]
                if len(tagged) < 2:
                    errs.append(f"{mid}: {LANG_NAMES[lang]} WRITE '{w}' has {len(tagged)} tagged "
                                f"item{'' if len(tagged) == 1 else 's'} (need ≥ 2 `uses:` in "
                                f"{LANG_NAMES[lang]})" + (": " + ", ".join(tagged) if tagged else ""))
        if concept:
            dv = [it["id"] for it in items if it["kind"] == "P" and it["lang"] == "dv"]
            if len(dv) < 2:
                errs.append(f"{mid}: {len(dv)} cross-language (dv) predict(s); a concept module "
                            "has ≥ 2 (design §6.2 C4)")
        floor = (3 if track == "Q" and num(mid) in (2, 3) else
                 2 if (track == "Q" and 4 <= num(mid) <= 9) or mid in ("R06", "R11") else 0)
        for lang in ("d", "v"):
            n = sum(1 for it in items if it["kind"] == "X" and lang in ci.covered_langs(it["lang"]))
            if n < floor:
                errs.append(f"{mid}: {n} {LANG_NAMES[lang]} exit item(s); the tier's exit needs "
                            f"≥ {floor} per language")
        errs += [f"{mid}: {e}" for e in band_problems(mid, m["admissible"])]
        for key in m["admissible"]:
            if key not in ids:
                errs.append(f"{mid}: admissible: '{key}' names no item marker of {mid}")
            elif exception_kind(m["admissible"][key]) == STATEMENT_ITEM_KIND:
                why = statement_item_problem(root, m, next(it for it in items if it["id"] == key),
                                             items)
                if why:
                    errs.append(f"{mid}: admissible: '{key}' carries a {STATEMENT_ITEM_KIND} "
                                f"exception, but {why}")
            elif exception_kind(m["admissible"][key]) == HIDDEN_CHECK_KIND:
                why = hidden_check_problem(root, m, next(it for it in items if it["id"] == key))
                if why:
                    errs.append(f"{mid}: admissible: '{key}' carries a {HIDDEN_CHECK_KIND} "
                                f"exception, but {why}")
        if track == "Q" and 10 <= num(mid) <= 18:
            for it in items:
                if it["kind"] == "H" and it["id"] not in m["admissible"]:
                    errs.append(f"{it['file']}:{it['line_start']}: {it['id']} has no admissible "
                                "entry: a practice item carries minutes only once admitted "
                                "(design §7.5)")

    pending, rows = 0, data.get("coverage")
    if not isinstance(rows, list) or not rows or not all(isinstance(r, dict) for r in rows):
        errs.append("coverage: no [[coverage]] tables (one per goal payload, design §5)")
        rows = []
    seen_ids = {}
    for i, row in enumerate(rows, 1):
        pid = row["payload_id"] if isinstance(row.get("payload_id"), str) else f"row {i}"
        if list(row) != list(COV_FIELDS):
            errs.append(f"coverage: {pid}: fields must be exactly, in order: " + ", ".join(COV_FIELDS))
            continue
        if not all(isinstance(row[k], str) for k in ("payload_id", "gap")) or not all(
                isinstance(row[k], list) and all(isinstance(x, str) for x in row[k])
                for k in ("langs", "q_homes", "r_homes", "deepening")):
            errs.append(f"coverage: {pid}: payload_id and gap are strings; langs, q_homes, "
                        "r_homes and deepening lists of strings")
            continue
        if not PAYLOAD_ID.fullmatch(pid):
            errs.append(f"coverage: '{pid}' is not a payload id (S<k>.<kebab-name>)")
        if pid in seen_ids:
            errs.append(f"coverage: {pid} has more than one row (rows {seen_ids[pid]} and {i})")
        seen_ids.setdefault(pid, i)
        langs = row["langs"]
        if any(x not in LANG_ORDER for x in langs) or len(set(langs)) != len(langs) \
                or langs != sorted(langs, key=LANG_ORDER.index):
            errs.append(f"coverage: {pid}: langs must be distinct d, v, py in that order")
            continue
        for d in row["deepening"]:
            if not COV_DEEP.fullmatch(d):
                errs.append(f"coverage: {pid}: deepening '{d}' must be a bare Q19–Q33 id")
        for side, key, rx in (("Q", "q_homes", Q_HOME), ("R", "r_homes", R_HOME)):
            homes = row[key]
            if not homes:
                errs.append(f"coverage: {pid}: no {side} home — every payload has a core home "
                            f"in both tracks")
                continue
            covered = set()
            for h in homes:
                hm = rx.fullmatch(h)
                if not hm:
                    errs.append(f"coverage: {pid}: {key}: '{h}' is not a"
                                + (" Q01–Q18 strand anchor (Qxx.S<k>), item id or paper item (a "
                                   "challenge is deepening, never a home)" if side == "Q" else
                                   "n R module anchor (Rxx), item id or paper item"))
                    continue
                res, why = resolve_home(root, side, hm, h, by_id, items_of)
                if res is None:
                    if why:
                        errs.append(f"coverage: {pid}: {key}: '{h}' {why}")
                    continue
                langs_covered, is_pending, gated = res
                covered |= langs_covered
                pending += is_pending
                if gated and not row["gap"].strip():
                    errs.append(f"coverage: {pid}: {key}: '{h}' is a gated item (admitted = "
                                "false); name the asymmetry in gap or home it elsewhere")
            for lang in langs:
                if lang not in covered:
                    errs.append(f"coverage: {pid}: no {side} home covers {LANG_NAMES[lang]} "
                                f"(langs {langs})")
    n = len(rows)
    armed = sorted(items_of)
    summary = (f"coverage: {len(armed)} module(s) past planned"
               + (f" ({', '.join(armed)})" if armed else "")
               + f"; {n} rows ({pending} pending)")
    return errs, summary, f"coverage: {n} rows ({pending} pending)"


def resolve_home(root, side, hm, h, by_id, items_of):
    """((langs covered, pending?, gated?), None) or (None, reason)."""
    mid = hm.group(1)
    m = by_id.get(mid)
    if m is None:
        return None, None  # a malformed module is already reported
    if side == "Q":
        strand = hm.group(2) and f"S{hm.group(2)}"
        paper, kind, n, lang = hm.group(3), hm.group(4), hm.group(5), hm.group(6)
    else:
        strand = None
        paper, kind, n, lang = hm.group(2), hm.group(3), hm.group(4), hm.group(5)
    if paper:
        if not m["paper"]:
            return None, f"is a paper item, but {mid} has paper = false"
        if m["status"] == "planned":
            return (set(), 1, False), None
        tex = f"paper/{mid}_problems.tex"
        if h not in PAPER_ITEM.findall(read_text(root, tex) or ""):
            return None, f"does not resolve — no `% item: {h}` line in {tex}"
        return (set(), 0, False), None
    if strand:
        if strand not in m["strands"]:
            return None, f"names {strand}, which {mid} does not sweep"
        if m["status"] == "planned":
            return (set(m["langs"]), 1, False), None
        items = items_of.get(mid, [])
        if num(mid) <= 9:
            ok = any(k.split(".")[0] == strand and isinstance(v, list)
                     for k, v in m["concept_items"].items())
        else:
            ok = any(it["strand"] == strand and it["kind"] in ci.CHECKED_KINDS for it in items)
        if not ok:
            return None, (f"does not resolve — {mid} has no checked item in {strand}"
                          + (" (no concept_items key of the strand cites items)"
                             if num(mid) <= 9 else ""))
        if num(mid) <= 9:
            cited = {x for k, v in m["concept_items"].items()
                     if k.split(".")[0] == strand and isinstance(v, list) for x in v}
            covered = {c for x in cited if (im := ci.ITEM_ID.fullmatch(x))
                       for c in ci.covered_langs(im.group(4))}
        else:
            covered = {c for it in items if it["strand"] == strand
                       and it["kind"] in ci.CHECKED_KINDS for c in ci.covered_langs(it["lang"])}
        return (covered, 0, False), None
    if kind:
        iid = f"{mid}.{kind}{n}{lang}"
        gated = isinstance(m["admissible"].get(iid), dict) and m["admissible"][iid].get("admitted") is False
        if m["status"] == "planned":
            return (set(ci.covered_langs(lang)), 1, gated), None
        if iid not in {it["id"] for it in items_of.get(mid, [])}:
            return None, f"does not resolve — no item marker {iid} in {mid}'s files"
        return (set(ci.covered_langs(lang)), 0, gated), None
    # a bare R module anchor
    if m["status"] == "planned":
        return (set(m["langs"]), 1, False), None
    covered = checked_langs(items_of.get(mid, []))
    return (covered, 0, False), None


# --- the shared vocabulary -----------------------------------------------------------------------

def bank_vocab(text):
    """[(line, tag)] declared under a bank's `## Controlled tag vocabulary`
    heading (table rows, bullets or a `·` list), or None without one."""
    lines = text.split("\n")
    start = next((i for i, l in enumerate(lines) if re.match(r"##\s+Controlled tag vocabulary", l)),
                 None)
    if start is None:
        return None
    out = []
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if re.match(r"##\s", line) or line.strip() == "---":
            break
        if m := re.match(r"\s*\|\s*`([^`]+)`\s*\|", line):
            out.append((i + 1, m.group(1)))
        elif m := re.match(r"\s*[-*]\s+`([^`]+)`", line):
            out.append((i + 1, m.group(1)))
        elif "·" in line:
            out += [(i + 1, t) for t in re.findall(r"`([^`]+)`", line)]
    return out


def parse_concepts(text):
    """Rows of concepts.md's `| tag | aliases | … |` table as
    [(line, tag, [aliases])], plus format errors."""
    lines = text.split("\n")
    head = next((i for i, l in enumerate(lines)
                 if re.match(r"\|\s*tag\s*\|\s*aliases\s*\|", l, re.I)), None)
    if head is None:
        return [], [f"{CONCEPTS}: no `| tag | aliases | covers | declared by |` table"]
    rows, errs = [], []
    for i in range(head + 1, len(lines)):
        line = lines[i].strip()
        if not line.startswith("|"):
            break
        if re.fullmatch(r"\|[\s:|-]+", line):
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip("|"))]
        tags = re.findall(r"`([^`]+)`", cells[0])
        if len(tags) != 1 or cells[0] != f"`{tags[0]}`" or len(cells) < 2:
            errs.append(f"{CONCEPTS}:{i + 1}: a row's first cell is one `tag`, its second the "
                        "aliases")
            continue
        rows.append((i + 1, tags[0], re.findall(r"`([^`]+)`", cells[1])))
    return rows, errs


def check_vocab(root, good):
    text = read_text(root, CONCEPTS)
    if text is None:
        return [f"{CONCEPTS}: not found — the shared ledger vocabulary (both tracks) is "
                "required"], ""
    rows, errs = parse_concepts(text)
    if not rows and not errs:
        errs.append(f"{CONCEPTS}: the tag table is empty")
    banks = {}  # bank path -> (records using it, [(line, tag)] | None)
    for m in good:
        if m["bank"] and (bt := read_text(root, m["bank"])) is not None:
            users, _ = banks.setdefault(m["bank"], ([], bank_vocab(bt)))
            users.append(m)
    canon, tags = {}, set()
    for ln, tag, aliases in rows:
        if not KEBAB.fullmatch(tag):
            errs.append(f"{CONCEPTS}:{ln}: tag '{tag}' is not kebab-case")
        if tag in canon:
            errs.append(f"{CONCEPTS}:{ln}: tag '{tag}' is listed twice")
        canon[tag] = tag
        tags.add(tag)
    for ln, tag, aliases in rows:
        for a in aliases:
            if not KEBAB.fullmatch(a):
                errs.append(f"{CONCEPTS}:{ln}: alias '{a}' is not kebab-case")
            if a in tags:
                errs.append(f"{CONCEPTS}:{ln}: alias '{a}' is also a tag; aliases and tags are "
                            "disjoint")
            elif a in canon:
                errs.append(f"{CONCEPTS}:{ln}: alias '{a}' is listed twice")
            else:
                canon[a] = tag
    n_aliases = len(canon) - len(tags)
    n_banks = 0
    for path, (users, vocab) in sorted(banks.items()):
        if vocab is None:
            if any(is_core_module(u["id"]) for u in users):
                errs.append(f"{path}: no `## Controlled tag vocabulary` section")
            continue
        n_banks += 1
        for ln, t in vocab:
            if t not in canon:
                errs.append(f"{path}:{ln}: tag '{t}' is not in {CONCEPTS} (add a row, or use an "
                            "existing tag or alias)")
        if users[0]["track"] == "Q":
            strands = {s for u in users for s in u["strands"]}
            for ln, line in enumerate(read_text(root, path).split("\n"), 1):
                if f := re.search(r"\*\*strand:\*\*\s*([^·*]*)", line):
                    for s in re.findall(r"S\d+", f.group(1)):
                        if s not in strands:
                            errs.append(f"{path}:{ln}: strand {s} is not one of "
                                        f"{'/'.join(u['id'] for u in users)}'s strands")
    by_id = {m["id"]: m for m in good}
    entries = read_ledger(root)
    for ln, tag in entries:
        prefix, _, vocab = tag.partition("/")
        if prefix not in by_id or not vocab:
            continue  # the registry group reports malformed and unknown prefixes
        if vocab not in canon:
            errs.append(f"{LEDGER}:{ln}: tag '{tag}': '{vocab}' is not in {CONCEPTS}")
            continue
        bank = by_id[prefix]["bank"]
        if bank in banks and banks[bank][1] is not None:
            declared = {canon.get(t, t) for _, t in banks[bank][1]}
            if canon[vocab] not in declared:
                errs.append(f"{LEDGER}:{ln}: tag '{tag}': '{vocab}' is not in {prefix}'s bank "
                            f"vocabulary ({bank})")
    for m in good:
        if m["status"] != "shipped" or not is_core_module(m["id"]):
            continue
        need = 12 if m["track"] == "R" and m["id"] != "R01" else 8
        text = read_text(root, m["bank"]) if m["bank"] else None
        if text is None:
            errs.append(f"{m['id']}: a shipped module needs its bank ('{m['bank'] or 'unset'}')")
            continue
        n = len({x for x in re.findall(r"(?m)^#{2,4}\s+K(\d+)\b", text)})
        if n < need:
            errs.append(f"{m['bank']}: {n} bank question(s) (K<n>); a shipped {m['id']} needs "
                        f"≥ {need} (design §8.1, §13.1)")
    for m in good:
        if m["track"] != "Q" or m["viva_mode"] != "tier" or m["status"] != "shipped":
            continue
        tier, lo, hi = q_tier(m["id"])
        members = [f"Q{n:02d}" for n in range(lo, hi + 1)]
        for x in members:
            bank = by_id[x]["bank"] if x in by_id else ""
            if not bank or bank not in banks:
                errs.append(f"{m['id']}: the tier viva draws from {members[0]}–{members[-1]}, but "
                            f"{x}'s bank " + (f"'{bank}' does not exist" if bank else "is unset"))
    summary = (f"vocab: {len(tags)} tags + {n_aliases} aliases; {n_banks} bank vocabularies "
               f"within {CONCEPTS}; ledger: {len(entries)} tag(s), all known")
    return errs, summary


# --- driver --------------------------------------------------------------------------------------

def validate(root, only=None):
    data, load_err = load_registry(root)
    if load_err:
        print(load_err)
        return 1
    run = GROUPS if only is None else (only,)
    errs = []
    unknown = sorted(set(data) - {"schema", "module", "coverage"})
    if data.get("schema") != SCHEMA:
        errs.append(f"top level: 'schema = {SCHEMA}' is required")
    errs += [f"top level: unknown key '{k}'" for k in unknown]
    modules = data.get("module")
    if not isinstance(modules, list) or not modules:
        errs.append("top level: no [[module]] tables")
        modules = []
    if not all(isinstance(m, dict) for m in modules):
        errs.append("top level: every 'module' entry must be a [[module]] table")
        modules = [m for m in modules if isinstance(m, dict)]
    good = []
    for m in modules:
        e = check_fields(m)
        errs += e
        if not e:
            good.append(m)
    summaries, tags = {}, 0
    if "registry" in run:
        e, tags = check_registry(root, data, modules, good)
        errs += e
    n_imports = sum(len(m["imports"]) for m in good)
    cov_line = ""
    if "units" in run:
        e, summaries["units"] = check_units(root, data, good)
        errs += e
    if "import-tiers" in run:
        e, summaries["import-tiers"], n_imports = check_import_tiers(root, good)
        errs += e
    if "isolation" in run:
        e, summaries["isolation"] = check_isolation(root, good)
        errs += e
    if "coverage" in run:
        e, summaries["coverage"], cov_line = check_coverage(root, good, data)
        errs += e
    if "vocab" in run:
        e, summaries["vocab"] = check_vocab(root, good)
        errs += e
    errs = list(dict.fromkeys(errs))  # one report per distinct error
    if errs:
        for e in errs:
            print(e if e.startswith(RAW_PREFIXES) else f"{REGISTRY}: {e}")
        print(f"\n{len(errs)} error(s) — the course map is inconsistent")
        return 1
    if only is not None and only != "registry":
        print(summaries[only])
        return 0
    count = {s: sum(m["status"] == s for m in good) for s in ENUMS["status"]}
    tracks = {t: sum(m["track"] == t for m in good) for t in ENUMS["track"]}
    extra = "" if only else f"; imports: {n_imports} files; {cov_line}"
    print(f"course map OK: {len(good)} modules ({tracks['Q']} Q, {tracks['R']} R; "
          f"{count['shipped']} shipped, {count['authoring']} authoring, "
          f"{count['planned']} planned){extra}; ledger: {tags} tag(s), all known")
    return 0


def find_record(root, arg):
    """(record, exit code): the module table whose id or legacy id is arg."""
    data, load_err = load_registry(root)
    if load_err:
        print(load_err, file=sys.stderr)
        return None, 1
    key = arg.strip().upper()
    modules = data.get("module") if isinstance(data.get("module"), list) else []
    for m in modules:
        if isinstance(m, dict) and key and key in (m.get("id"), m.get("legacy_id")):
            errs = check_fields(m)
            if errs:
                for e in errs:
                    print(f"{REGISTRY}: {e}", file=sys.stderr)
                return None, 1
            return m, 0
    print(f"check_course_map: unknown module id {arg!r} (expected Q01–Q33 or R01–R16)",
          file=sys.stderr)
    return None, 3


def resolve(root, arg):
    m, code = find_record(root, arg)
    if m is not None:
        print(json.dumps(m, ensure_ascii=False))
    return code


def items_cmd(root, arg, as_json):
    m, code = find_record(root, arg)
    if m is None:
        return code
    items, errs = module_items(root, m)
    if errs:
        for e in errs:
            print(e, file=sys.stderr)
        return 1
    if as_json:
        print(json.dumps(ci.public(items), ensure_ascii=False))
        return 0
    for it in items:
        slots = " ".join(f"{s['state']}@{s['line']}" for s in it["slots"])
        print(f"{it['id']}\t{it['strand'] or '-'}\t{it['format'] or '-'}\t"
              f"{it['file']}:{it['line_start']}-{it['line_end']}"
              + (f"\tuses: {', '.join(it['uses'])}" if it["uses"] else "")
              + (f"\tpair: {it['pair']}" if it["pair"] else "")
              + (f"\tslots: {slots}" if slots else ""))
    return 0


def list_nonplanned(root, rng):
    r = re.fullmatch(r"([RQ])(\d\d)-([RQ])?(\d\d)", rng.strip().upper())
    if not r or (r.group(3) and r.group(3) != r.group(1)) or int(r.group(2)) > int(r.group(4)):
        print(f"check_course_map: --list-nonplanned wants a range like Q01-Q18, got {rng!r}",
              file=sys.stderr)
        return 2
    data, load_err = load_registry(root)
    if load_err:
        print(load_err, file=sys.stderr)
        return 1
    lo, hi = int(r.group(2)), int(r.group(4))
    for m in data.get("module", []):
        mid = m.get("id") if isinstance(m, dict) else None
        if isinstance(mid, str) and re.fullmatch(r"[RQ]\d\d", mid) and mid[0] == r.group(1) \
                and lo <= int(mid[1:]) <= hi and m.get("status") != "planned":
            print(mid)
    return 0


def main():
    ap = argparse.ArgumentParser(description="Validate MODULES.toml, or resolve one module id.")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--resolve", metavar="ID", help="print one module record as JSON")
    mode.add_argument("--items", metavar="ID", help="print a module's parsed item blocks")
    mode.add_argument("--list-nonplanned", metavar="RANGE",
                      help="print the non-planned ids in a range like Q01-Q18")
    mode.add_argument("--only", choices=GROUPS, help="run one group of checks")
    ap.add_argument("--json", action="store_true", help="with --items: one JSON array")
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT,
                    help="repo root (default: this script's repo)")
    args = ap.parse_args()
    if args.json and args.items is None:
        ap.error("--json goes with --items")
    if args.resolve is not None:
        return resolve(args.root, args.resolve)
    if args.items is not None:
        return items_cmd(args.root, args.items, args.json)
    if args.list_nonplanned is not None:
        return list_nonplanned(args.root, args.list_nonplanned)
    return validate(args.root, args.only)


if __name__ == "__main__":
    sys.exit(main())
