"""fvh.records — the course's run and calibration records (QPLAN §11.8).

  RunRecord(task_id, arm, attempt, lang, verdict, holes, errors, verified_count)
      one verifier run of one task in one arm (frozen). `success` is the
      course's definition of done: verdict "verified" and no hole.
  load_jsonl(path) / dump_jsonl(records, path)
      RunRecords as JSON Lines, one object per line with exactly the eight
      fields.
  first_attempts(records)
      each (task_id, arm)'s attempt-1 record: what a pass rate counts.
  CalibRow(item, kind, verdict, date, slot_hash) and load_calib(path)
      the rows of instructor/calib/<ID>.tsv exactly as scripts/firsttry.py
      writes them: five tab-separated columns `item kind verdict date
      slot-hash`, lines starting with `#` ignored, an item's first row wins.
  calib_records(rows, arm)
      the bridge EVAL.md v0 uses: one RunRecord per `predict` row, and the
      number of rows of any other kind (the report's exclusions).

The vocabularies are the course tools': VERDICTS are scripts/dvl's verdict
words (the `verdict` key of `scripts/vcheck --json`), CALIB_KINDS and
CALIB_VERDICTS the words scripts/firsttry.py writes into a calibration file.
"""

import dataclasses
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

__all__ = ["CALIB_KINDS", "CALIB_VERDICTS", "CalibRow", "ITEM_ID", "RunRecord", "VERDICTS",
           "calib_records", "dump_jsonl", "first_attempts", "load_calib", "load_jsonl"]

# scripts/dvl/common.py's VERDICTS: the verdict words of every course tool.
VERDICTS = ("verified", "failed", "inconclusive", "refused", "killed(memory)", "error")
# scripts/firsttry.py's calibration rows: the kinds it records and its two
# verdict words (the first is the pass word).
CALIB_KINDS = ("predict", "observed", "exit")
CALIB_VERDICTS = ("pass", "fail")
# An item id (scripts/course_items.py's grammar): module, kind, number, language.
ITEM_ID = re.compile(r"([RQ]\d\d)\.([WCPHXTA])([1-9]\d*)(dv|py|d|v)")

_STR_FIELDS = ("task_id", "arm", "lang", "verdict")
_COUNT_FIELDS = ("attempt", "holes", "errors", "verified_count")


@dataclass(frozen=True)
class RunRecord:
    """One verifier run of one task in one arm.

    task_id, arm   non-empty strings
    attempt        1 for the task's first attempt in the arm, then 2, 3, …
    lang           the run's language, as its source names it
    verdict        one of VERDICTS
    holes          tool-counted holes (>= 0)
    errors         error diagnostics (>= 0)
    verified_count the tool's own count (>= 0; 0 when the run printed none)
    """

    task_id: str
    arm: str
    attempt: int
    lang: str
    verdict: str
    holes: int
    errors: int
    verified_count: int

    def __post_init__(self):
        for name in _STR_FIELDS:
            value = getattr(self, name)
            if not isinstance(value, str):
                raise TypeError(f"RunRecord.{name} must be a str, not {type(value).__name__}")
        for name in ("task_id", "arm"):
            if not getattr(self, name):
                raise ValueError(f"RunRecord.{name} must not be empty")
        for name in _COUNT_FIELDS:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"RunRecord.{name} must be an int, not {type(value).__name__}")
            if value < (1 if name == "attempt" else 0):
                raise ValueError(f"RunRecord.{name} must be >= {1 if name == 'attempt' else 0}, "
                                 f"not {value}")
        if self.verdict not in VERDICTS:
            raise ValueError(f"RunRecord.verdict must be one of {', '.join(VERDICTS)}, "
                             f"not {self.verdict!r}")

    @property
    def success(self) -> bool:
        """Done, as the course defines it: verdict "verified" with no hole."""
        return self.verdict == "verified" and self.holes == 0


_FIELDS = tuple(f.name for f in dataclasses.fields(RunRecord))


def load_jsonl(path) -> list[RunRecord]:
    """The RunRecords of a JSON Lines file, in file order; blank lines skipped.

    Each line is one JSON object with exactly RunRecord's eight fields.
    ValueError (naming the line) for any other line."""
    p = Path(path)
    out = []
    for ln, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f"{p}:{ln}: not JSON ({e.msg})") from None
        if not isinstance(obj, dict) or set(obj) != set(_FIELDS):
            raise ValueError(f"{p}:{ln}: a run record is one object with exactly the fields "
                             + ", ".join(_FIELDS))
        try:
            out.append(RunRecord(**obj))
        except (TypeError, ValueError) as e:
            raise ValueError(f"{p}:{ln}: {e}") from None
    return out


def dump_jsonl(records: Iterable[RunRecord], path) -> None:
    """Write records to path as JSON Lines (one sorted-key object per line),
    replacing the file; load_jsonl reads it back to equal records."""
    lines = []
    for r in records:
        if not isinstance(r, RunRecord):
            raise TypeError(f"dump_jsonl writes RunRecords, not {type(r).__name__}")
        lines.append(json.dumps(dataclasses.asdict(r), sort_keys=True, ensure_ascii=False))
    Path(path).write_text("".join(x + "\n" for x in lines), encoding="utf-8")


def first_attempts(records: Iterable[RunRecord]) -> list[RunRecord]:
    """Each (task_id, arm)'s attempt-1 record, in input order (the first one
    if a pair has several). A pair with no attempt-1 record has none."""
    seen, out = set(), []
    for r in records:
        key = (r.task_id, r.arm)
        if r.attempt == 1 and key not in seen:
            seen.add(key)
            out.append(r)
    return out


@dataclass(frozen=True)
class CalibRow:
    """One row of instructor/calib/<ID>.tsv: an item's first-try record."""

    item: str
    kind: str
    verdict: str
    date: str
    slot_hash: str


def load_calib(path) -> list[CalibRow]:
    """The rows of a calibration file, in file order, one per item.

    The format is scripts/firsttry.py's: five tab-separated columns (item,
    kind, verdict, date, slot hash), blank lines and lines starting with `#`
    skipped, the file append-only and an item's FIRST row the record (a later
    row of the same item is ignored, as the course tools read it). ValueError
    (naming the line) for a row with another number of columns, an item that
    is no item id, or a kind or verdict outside CALIB_KINDS / CALIB_VERDICTS."""
    p = Path(path)
    out, seen = [], set()
    for ln, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) != 5:
            raise ValueError(f"{p}:{ln}: a calibration row has 5 tab-separated columns (item, "
                             f"kind, verdict, date, slot hash), not {len(cols)}")
        item, kind, verdict, date, slot_hash = cols
        if not ITEM_ID.fullmatch(item):
            raise ValueError(f"{p}:{ln}: {item!r} is no item id")
        if kind not in CALIB_KINDS:
            raise ValueError(f"{p}:{ln}: kind {kind!r} is not one of {', '.join(CALIB_KINDS)}")
        if verdict not in CALIB_VERDICTS:
            raise ValueError(f"{p}:{ln}: verdict {verdict!r} is not one of "
                             + ", ".join(CALIB_VERDICTS))
        if item in seen:
            continue
        seen.add(item)
        out.append(CalibRow(item, kind, verdict, date, slot_hash))
    return out


def calib_records(rows: Iterable[CalibRow], arm: str) -> tuple[list[RunRecord], int]:
    """(records, excluded): one RunRecord per row of kind `predict`, in order,
    and the number of rows of any other kind (`observed` and `exit` rows are
    no first-try predictions; EVAL.md reports them as exclusions).

    Each record: task_id the item id, the given arm, attempt 1, lang the item
    id's language suffix (d, v, dv or py), verdict "verified" for the pass word
    and "failed" otherwise, holes 0, errors 0 for a pass and 1 for a fail,
    verified_count 0."""
    if not isinstance(arm, str) or not arm:
        raise ValueError("arm must be a non-empty str")
    records, excluded = [], 0
    for row in rows:
        if row.kind != "predict":
            excluded += 1
            continue
        m = ITEM_ID.fullmatch(row.item)
        if not m:
            raise ValueError(f"{row.item!r} is no item id")
        passed = row.verdict == CALIB_VERDICTS[0]
        records.append(RunRecord(task_id=row.item, arm=arm, attempt=1, lang=m.group(4),
                                 verdict="verified" if passed else "failed", holes=0,
                                 errors=0 if passed else 1, verified_count=0))
    return records, excluded
