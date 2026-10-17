"""fvh.holes — the Python hole form, its counter and its lint (QPLAN §8.0, §11.8).

A Python hole is a function (or method) whose body, after an optional
docstring, is exactly the one statement

    raise NotImplementedError("<item id>")

where <item id> is the id of the `# item:` marker whose block holds the
function. A block runs from its marker to the next marker or to the end of the
file (scripts/course_items.py's rule for Python files); a marker is a comment
line of the exact grammar `# item: <ID>.<K><n><lang> [S<k>] [format] [min=<m>]`,
never text inside a string.

Holes are counted on the syntax tree (`ast`), never on text: the form inside a
comment or a string is no hole, and neither is another exception (a renamed
or qualified one), an id that is not the block's, a raise with a cause, or a
body with any other statement. The course tools count holes only through this
module (scripts/dvl/python.py), so "zero holes" means what it says.

  count_holes(source) -> list[Hole]   Hole(item, name, line): the item id, the
                                      function's qualified name and its def line
  lint(source) -> list[Finding]       Finding(line, kind, message): bodies that
                                      look like holes but are not (below)
  markers(source) -> list[Marker]     Marker(line, item): the item markers

Lint kinds: bare-raise (a NotImplementedError with no id), hole-form (an id
that is not one plain string, or a raise with a cause), hole-id-mismatch (an
id that is not the block's, or a raise outside every item block),
hole-not-alone (the block's raise beside other statements, or nested in
one), renamed-exception (an item id raised by another exception), empty-body
(a body of only `pass` or `...` in an H item's block), duplicate-hole (two
holes of one item), malformed-marker (a comment that looks like a marker but
does not parse), parse-error.

CLI: python -m fvh.holes [--json] FILE...
  one line per file, `<file>: <n> hole(s)`; --json prints one JSON list of
  {"file", "holes": [{"item", "name", "line"}], "findings": [...]}.
  Exit 0; 1 when a file cannot be read or does not parse; 2 usage.
"""

import argparse
import ast
import io
import json
import re
import sys
import tokenize
from dataclasses import asdict, dataclass

__all__ = ["Finding", "Hole", "Marker", "count_holes", "lint", "main", "markers"]

ITEM_ID_RE = r"([RQ]\d\d)\.([WCPHXTA])([1-9]\d*)(dv|py|d|v)"
_SLUG = r"[a-z0-9]+(?:-[a-z0-9]+)*(?:/[a-z0-9]+(?:-[a-z0-9]+)*)*"
# scripts/course_items.py's marker grammar with the `#` leader.
MARKER = re.compile(
    rf"# item: (?P<id>{ITEM_ID_RE})(?: S(?:1[0-3]|[1-9]))?"
    rf"(?: (?:value|obligation|error|verdict|(?:write|recognise):{_SLUG}"
    rf"|diverge:[a-z0-9]+(?:-[a-z0-9]+)*))?"
    rf"(?: min=[1-9]\d*)?")
MARKER_LIKE = re.compile(r"#\s*item\s*:")
ITEM_ID = re.compile(ITEM_ID_RE)
HOLE_EXCEPTION = "NotImplementedError"


@dataclass(frozen=True)
class Hole:
    item: str
    name: str
    line: int


@dataclass(frozen=True)
class Finding:
    line: int
    kind: str
    message: str


@dataclass(frozen=True)
class Marker:
    line: int
    item: str


# --- markers ---------------------------------------------------------------------------

def _comments(source):
    """[(line, text)] of every comment that starts its line (outside strings)."""
    lines = source.splitlines()
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            if tok.type != tokenize.COMMENT:
                continue
            ln, col = tok.start
            text = lines[ln - 1] if ln - 1 < len(lines) else ""
            if not text[:col].strip():
                out.append((ln, tok.string.rstrip()))
    except (tokenize.TokenError, SyntaxError):
        pass   # the caller parsed the source first; a tokenizer error leaves the comments so far
    return out


def _scan_markers(source):
    """(markers, malformed marker lines)."""
    found, bad = [], []
    for ln, text in _comments(source):
        m = MARKER.fullmatch(text)
        if m:
            found.append(Marker(ln, m.group("id")))
        elif MARKER_LIKE.match(text):
            bad.append(ln)
    return found, bad


def markers(source: str) -> list[Marker]:
    """The `# item:` markers of a source, in line order."""
    return _scan_markers(source)[0]


def _block_of(marks, line):
    """The item id of the block that holds `line`, or None."""
    item = None
    for m in marks:
        if m.line < line:
            item = m.item
        else:
            break
    return item


# --- the syntax tree -------------------------------------------------------------------

def _functions(tree):
    """[(qualified name, node)] of every function and method, in source order."""
    out = []

    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = f"{prefix}{child.name}"
                out.append((name, child))
                walk(child, f"{name}.<locals>.")
            elif isinstance(child, ast.ClassDef):
                walk(child, f"{prefix}{child.name}.")
            else:
                walk(child, prefix)
    walk(tree, "")
    return sorted(out, key=lambda x: (x[1].lineno, x[1].col_offset))


def _start(fn):
    """The first line of a function: its first decorator, else its def."""
    return min([d.lineno for d in fn.decorator_list] + [fn.lineno])


def _body(fn):
    """The body without a leading docstring."""
    body = list(fn.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
            and isinstance(body[0].value.value, str):
        body = body[1:]
    return body


def _exc_name(exc):
    """The raised exception's name: `X` for `raise X` / `raise X(…)`, the last
    part of a dotted name, else None."""
    target = exc.func if isinstance(exc, ast.Call) else exc
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return None


def _is_plain_name(exc):
    target = exc.func if isinstance(exc, ast.Call) else exc
    return isinstance(target, ast.Name) and target.id == HOLE_EXCEPTION


def _single_str_arg(exc):
    """The one positional string literal of a raise call, else None."""
    if isinstance(exc, ast.Call) and len(exc.args) == 1 and not exc.keywords and \
            isinstance(exc.args[0], ast.Constant) and isinstance(exc.args[0].value, str):
        return exc.args[0].value
    return None


def _hole_item(fn, block):
    """The item id if fn is a hole of `block`, else None."""
    body = _body(fn)
    if block is None or len(body) != 1 or not isinstance(body[0], ast.Raise):
        return None
    r = body[0]
    if r.cause is not None or r.exc is None or not _is_plain_name(r.exc):
        return None
    return block if _single_str_arg(r.exc) == block else None


def _analyse(source):
    tree = ast.parse(source)
    marks, bad = _scan_markers(source)
    holes, hole_raises = [], set()
    fns = _functions(tree)
    for name, fn in fns:
        block = _block_of(marks, _start(fn))
        item = _hole_item(fn, block)
        if item is not None:
            holes.append(Hole(item, name, fn.lineno))
            hole_raises.add(id(_body(fn)[0]))
    return tree, marks, bad, fns, holes, hole_raises


def count_holes(source: str) -> list[Hole]:
    """The holes of a Python source, in line order. Raises SyntaxError when the
    source does not parse (a count of a broken file is not a count)."""
    return _analyse(source)[4]


# --- the lint --------------------------------------------------------------------------

def _enclosing(fns, node):
    """The innermost function whose span holds node, else None."""
    best = None
    for _, fn in fns:
        end = getattr(fn, "end_lineno", fn.lineno)
        if fn.lineno <= node.lineno <= end and (best is None or fn.lineno >= best.lineno):
            best = fn
    return best


def lint(source: str) -> list[Finding]:
    """Hole-like code that is not a hole, sorted by line (see the module doc).
    A source that does not parse gives one parse-error finding."""
    try:
        tree, marks, bad, fns, holes, hole_raises = _analyse(source)
    except SyntaxError as e:
        return [Finding(e.lineno or 0, "parse-error", f"the file does not parse: {e.msg}")]
    out = [Finding(ln, "malformed-marker", "a comment that looks like an item marker does not "
                   "parse as one (`# item: <ID>.<K><n><lang> [S<k>] [format] [min=<m>]`)")
           for ln in bad]
    counts = {}
    for h in holes:
        counts[h.item] = counts.get(h.item, 0) + 1
    for h in holes:
        if counts[h.item] > 1:
            out.append(Finding(h.line, "duplicate-hole", f"{h.item} has {counts[h.item]} holes; "
                               "an item has one"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Raise) or node.exc is None or id(node) in hole_raises:
            continue
        exc = node.exc
        name = _exc_name(exc)
        arg = _single_str_arg(exc)
        fn = _enclosing(fns, node)
        block = _block_of(marks, _start(fn) if fn is not None else node.lineno)
        if name == HOLE_EXCEPTION:
            if not isinstance(exc, ast.Call) or (not exc.args and not exc.keywords):
                out.append(Finding(node.lineno, "bare-raise", "NotImplementedError without its "
                                   "item id is no hole: the counter does not count it"))
            elif arg is None or node.cause is not None or not _is_plain_name(exc):
                out.append(Finding(node.lineno, "hole-form", "a hole raises NotImplementedError "
                                   "with its item id as the one string argument, and no cause"))
            elif block is None or arg != block:
                out.append(Finding(node.lineno, "hole-id-mismatch",
                                   f"the raise names {arg!r} but its block is "
                                   + (f"{block}'s" if block else "no item's")
                                   + ": the counter does not count it"))
            else:
                out.append(Finding(node.lineno, "hole-not-alone", f"{arg}'s raise is not the "
                                   "function's only statement (after its docstring): no hole, "
                                   "and not finished either"))
        elif arg is not None and ITEM_ID.fullmatch(arg):
            out.append(Finding(node.lineno, "renamed-exception", f"{name or 'an exception'} "
                               f"raised with the item id {arg!r}: a hole raises "
                               "NotImplementedError, so the counter does not count it"))
    for _, fn in fns:
        block = _block_of(marks, _start(fn))
        if block is None or ITEM_ID.fullmatch(block).group(2) != "H":
            continue
        body = _body(fn)
        if body and all(isinstance(s, ast.Pass) or (isinstance(s, ast.Expr) and
                        isinstance(s.value, ast.Constant) and s.value.value is Ellipsis)
                        for s in body):
            out.append(Finding(fn.lineno, "empty-body", f"{block}: a body of only `pass` or "
                               "`...` is no hole and no answer"))
        elif not body:
            out.append(Finding(fn.lineno, "empty-body", f"{block}: a body of only a docstring "
                               "is no hole and no answer"))
    return sorted(set(out), key=lambda f: (f.line, f.kind, f.message))


# --- CLI -------------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m fvh.holes",
                                 description="Count the Python holes of each file (AST).")
    ap.add_argument("files", nargs="+", metavar="FILE")
    ap.add_argument("--json", action="store_true", help="one JSON list instead of lines")
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    code, report = 0, []
    for f in a.files:
        try:
            with open(f, encoding="utf-8") as fh:
                src = fh.read()
            found = count_holes(src)
        except OSError as e:
            code = 1
            report.append({"file": f, "error": f"cannot read: {e.strerror}"})
            continue
        except (SyntaxError, ValueError) as e:
            code = 1
            line = getattr(e, "lineno", None) or 0
            report.append({"file": f, "error": f"does not parse (line {line})"})
            continue
        report.append({"file": f, "holes": [asdict(h) for h in found],
                       "findings": [asdict(x) for x in lint(src)]})
    if a.json:
        print(json.dumps(report, ensure_ascii=False))
    else:
        for r in report:
            if "error" in r:
                print(f"{r['file']}: {r['error']}")
            else:
                print(f"{r['file']}: {len(r['holes'])} hole(s)")
    return code


if __name__ == "__main__":
    sys.exit(main())
