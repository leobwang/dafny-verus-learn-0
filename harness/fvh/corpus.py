"""fvh.corpus — a read-only view of the cheat corpus (DV4-PLAN §3.7;
tests/corpus/README.md).

Each fixture of tests/corpus/<lang>/<ID>/manifest.toml is loaded as two parts
kept apart:

  Delivery(id, lang, half, target, files)
      what a gate may see: the fixture's id, its language ("dafny" |
      "verus"), its half ("Q" | "R"), the target the tools run and every file
      of the fixture (the task and its companions), all as repo-relative
      POSIX paths. A delivery carries no label.
  Label(xclass, kind, title, expects)
      what only an evaluator reads: the X class ("" for a control), the kind
      ("construct" | "control" | "covered-elsewhere"), the one-line title,
      and one Expect(tool, outcome, kinds) per [[expect]] table of the
      manifest, in manifest order.
  Fixture(delivery, label)
      one of each; `fixture.id` is the delivery's id.

  load_half(lang, half, *, root=None, covered=False) -> tuple[Fixture, ...]
      the fixtures of one language and one half, in the corpus runner's
      order (catalog rows, then DELTAS additions, then controls). Only
      fixtures that hold a program are deliveries, so a covered-elsewhere row
      (a row the wrapper suites cover, with no program) is left out unless
      `covered=True`, which adds it with target "" and no files.

`root` is the course root (default: the checkout this package lives in). The
loader reads the manifests the way scripts/test_corpus.py reads them (the same
ids, classes, kinds, targets and files); a CI test checks the two on every
fixture. It raises CorpusError on a missing corpus or a manifest it cannot
read; scripts/test_corpus.py remains the corpus's validator.

Frozen (guard rule 2f), standard library only.
"""

import posixpath
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

__all__ = ["CORPUS", "CorpusError", "Delivery", "Expect", "Fixture", "HALVES", "KINDS", "LANGS",
           "Label", "load_half"]

ROOT = Path(__file__).resolve().parents[2]
CORPUS = "tests/corpus"                      # relative to the course root
LANGS = ("dafny", "verus")
HALVES = ("Q", "R")
KINDS = ("construct", "control", "covered-elsewhere")
DEFAULT_TARGET = {"dafny": "main.dfy", "verus": "."}


class CorpusError(ValueError):
    """The corpus is missing, or a manifest cannot be read as a fixture."""


@dataclass(frozen=True)
class Delivery:
    """What a gate may see of one fixture: no class, kind, title or expectation."""

    id: str
    lang: str
    half: str
    target: str
    files: tuple[str, ...]


@dataclass(frozen=True)
class Expect:
    """One [[expect]] table: the instrument, its recorded outcome and kinds."""

    tool: str
    outcome: str
    kinds: tuple[str, ...]


@dataclass(frozen=True)
class Label:
    """What only an evaluator reads of one fixture."""

    xclass: str
    kind: str
    title: str
    expects: tuple[Expect, ...]


@dataclass(frozen=True)
class Fixture:
    delivery: Delivery
    label: Label

    @property
    def id(self) -> str:
        return self.delivery.id


_ORDER = re.compile(r"([A-Z])(-?)(\d+)([a-z]?)")


def _order(lang_index, fid):
    """scripts/test_corpus.py's sort_key: catalog rows, DELTAS additions, controls."""
    m = _ORDER.fullmatch(fid)
    if not m:
        return (lang_index, 9, 0, fid)
    cat = 2 if m[1] == "C" else (1 if m[2] else 0)
    return (lang_index, cat, int(m[3]), m[4])


def _str(data, key, where):
    v = data.get(key)
    if not isinstance(v, str):
        raise CorpusError(f"{where}: {key} must be a string")
    return v


def _strs(value, what, where):
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        raise CorpusError(f"{where}: {what} must be a list of strings")
    return tuple(value)


def _fixture(lang, d, rel_dir, data, where, covered):
    fid = _str(data, "id", where)
    if d.name != fid and not d.name.startswith(fid + "_"):
        raise CorpusError(f"{where}: id {fid!r} does not name the directory")
    if _str(data, "lang", where) != lang:
        raise CorpusError(f"{where}: lang differs from the parent directory")
    half = _str(data, "half", where)
    if half not in HALVES:
        raise CorpusError(f"{where}: half must be one of {', '.join(HALVES)}")
    kind = _str(data, "kind", where)
    if kind not in KINDS:
        raise CorpusError(f"{where}: kind must be one of {', '.join(KINDS)}")
    xclass, title = _str(data, "xclass", where), _str(data, "title", where)
    files = _strs(data.get("files"), "files", where)
    raw = data.get("expect")
    if not isinstance(raw, list) or not all(isinstance(e, dict) for e in raw):
        raise CorpusError(f"{where}: no [[expect]] table")
    expects = []
    for e in raw:
        tool, outcome = e.get("tool"), e.get("outcome")
        if not isinstance(tool, str) or not isinstance(outcome, str):
            raise CorpusError(f"{where}: an [[expect]] table needs tool and outcome strings")
        expects.append(Expect(tool, outcome, _strs(e.get("kinds"), "kinds", where)))
    label = Label(xclass, kind, title, tuple(expects))
    if kind == "covered-elsewhere":
        if not covered:
            return None
        return Fixture(Delivery(fid, lang, half, "", ()), label)
    t = data.get("target", DEFAULT_TARGET[lang])
    if not isinstance(t, str) or not t:
        raise CorpusError(f"{where}: target must be a non-empty relative path")
    target = posixpath.normpath(f"{rel_dir}/{t}")
    paths = tuple(posixpath.normpath(f"{rel_dir}/{f}") for f in files)
    for p in (target, *paths):
        if p != rel_dir and not p.startswith(rel_dir + "/"):
            raise CorpusError(f"{where}: {p} leaves the fixture")
    return Fixture(Delivery(fid, lang, half, target, paths), label)


def load_half(lang: str, half: str, *, root=None, covered: bool = False) -> tuple[Fixture, ...]:
    """The fixtures of one language and one half (module docstring)."""
    if lang not in LANGS:
        raise ValueError(f"lang must be one of {', '.join(LANGS)}, not {lang!r}")
    if half not in HALVES:
        raise ValueError(f"half must be one of {', '.join(HALVES)}, not {half!r}")
    base = Path(root).resolve() if root is not None else ROOT
    corpus = base / CORPUS
    if not corpus.is_dir():
        raise CorpusError(f"{CORPUS}/ does not exist under {base} (an absent corpus fails)")
    ld = corpus / lang
    if not ld.is_dir():
        raise CorpusError(f"{CORPUS}/{lang}/ does not exist (an absent corpus fails)")
    out = []
    for d in sorted(p for p in ld.iterdir() if p.is_dir()):
        rel_dir = f"{CORPUS}/{lang}/{d.name}"
        where = f"{rel_dir}/manifest.toml"
        try:
            data = tomllib.loads((d / "manifest.toml").read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise CorpusError(f"{where}: missing") from None
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
            raise CorpusError(f"{where}: unreadable ({type(e).__name__})") from None
        if data.get("half") != half:
            if data.get("half") not in HALVES:
                raise CorpusError(f"{where}: half must be one of {', '.join(HALVES)}")
            continue
        fx = _fixture(lang, d, rel_dir, data, where, covered)
        if fx is not None:
            out.append(fx)
    out.sort(key=lambda f: _order(LANGS.index(lang), f.id))
    return tuple(out)
