"""Q15 — Practice II-C: the language-server client (Exercises, Python)

Imports: the Python standard library and the frozen core `fvh` (harness/fvh/:
fvh.lsp), nothing else. The core is frozen and complete; read it, never edit
it. The server starts only through `fvh.lsp.start_server`: the pinned
`dafny server`, from a scratch copy of the install, under the Dafny memory
cap (QPLAN §30 Q56). Never start a server process of your own.

How to work this file (the S9 block of Q15, after the module's predictions;
P1 is about this client's report: record its first try with
`scripts/firsttry.sh Q15 --check` first):
1. Replace each hole, in order: H6, H7, then H8. A Python hole is a function
   whose body, after its docstring, is the one statement
   `raise NotImplementedError("<item id>")`; the tools count holes on the
   syntax tree, never by searching the text.
2. Run the acceptance tests (harness/tests/q/test_lsp_client.py, frozen):
   `scripts/vcheck harness/q/fvh_q/lsp_client.py`. No server runs in them:
   they replay a recorded server transcript
   (harness/tests/q/fixtures/q15/lsp/) and hand-made streams.
3. Done = `scripts/vcheck --gate harness/q/fvh_q/lsp_client.py` exits 0
   (zero holes and every acceptance test passing), AND
   `scripts/firsttry.sh Q15 --report --strict` exits 0.
4. Then your own live check, outside the tests: one file through the pinned
   server, on the host (well under a minute for a small file):
   `cd harness && PYTHONPATH=q uv run python -m fvh_q.lsp_client FILE.dfy`.
5. Stuck for 20 minutes? /tutor Q15.

This file ships with exactly 3 holes: H6, H7 and H8, each counted from the
syntax tree. Item kinds and the slot protocol are in the Dafny file's header
(dafny/Q/Q15_PracticeIIC/std/Q15_PracticeIIC.dfy).

The protocol, in brief: every message is a JSON object framed by a header
(`Content-Length: <n>`, a blank line) and n bytes of UTF-8 JSON. The client
sends requests (with an `id`, answered by a response with the same id) and
notifications (no id); the server answers and publishes notifications of its
own, among them `textDocument/publishDiagnostics` and Dafny's
`dafny/textDocument/symbolStatus` (one entry per verifiable symbol of the
file, each with its status) and `dafny/compilation/status`.
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import BinaryIO

from fvh import lsp

# =============================================================================
# Given (frozen statements: expected/Q15.freeze pins them). Read them, never
# change them.
# =============================================================================

# The per-symbol verification statuses of Dafny's `dafny/textDocument/symbolStatus`
# notification, by the integer the server sends (3 is not used by the pinned server).
STATUS_NAMES = {0: "stale", 1: "queued", 2: "running", 4: "error", 5: "correct"}
FINAL = frozenset({"error", "correct"})       # a symbol whose verification has ended
ENDED = ("verified", "parse-failed", "resolution-failed")


class ProtocolError(Exception):
    """A malformed message, or a server that broke the protocol."""


@dataclass(frozen=True)
class SymbolStatus:
    """One verifiable symbol of the file: the 1-based line and column of its
    name (the server's nameRange start, plus one each) and its status name."""

    line: int
    character: int
    status: str


@dataclass(frozen=True)
class Diagnostic:
    """One diagnostic the server published for the file: its 1-based start
    line, its LSP severity (1 error, 2 warning, 3 information, 4 hint) and its
    message."""

    line: int
    severity: int
    message: str


@dataclass(frozen=True)
class ServerReport:
    """What one verification of one file came to.

    uri          the file's URI, as the client sent it
    statuses     the symbol statuses of the LAST symbolStatus notification for
                 the file, sorted by (line, character); () when none came
    diagnostics  the diagnostics of the LAST publishDiagnostics notification
                 for the file, in the server's order; () when none came
    ended        "verified" (every status of a symbolStatus notification was
                 final), "parse-failed" or "resolution-failed" (the server's
                 compilation status said so, and nothing was verified)
    """

    uri: str
    statuses: tuple
    diagnostics: tuple
    ended: str


def status_name(code) -> str:
    """The status name of a symbolStatus integer: STATUS_NAMES, else
    "status-<code>"."""
    return STATUS_NAMES.get(code, f"status-{code}")


def uri_of(path: str) -> str:
    """The file URI of a path, as the client sends it: `file://` and the
    absolute path."""
    return "file://" + os.path.abspath(path)


def main(argv=None) -> int:
    """Your own live check, outside the tests: one file through the pinned
    server, on the host (the server starts under the Dafny memory cap; well
    under a minute for a small file).
        cd harness && PYTHONPATH=q uv run python -m fvh_q.lsp_client FILE.dfy
    Prints the ended state, then one line per symbol status and one per
    diagnostic. Exit 0 once a report came back."""
    ap = argparse.ArgumentParser(prog="python -m fvh_q.lsp_client", allow_abbrev=False)
    ap.add_argument("file")
    a = ap.parse_args(argv)
    with open(a.file, encoding="utf-8") as f:
        text = f.read()
    rep = verify_with_server(a.file, text)
    print(f"ended: {rep.ended}")
    for s in rep.statuses:
        print(f"  {s.line}:{s.character} {s.status}")
    for d in rep.diagnostics:
        print(f"  {d.line}: severity {d.severity}: {d.message}")
    return 0


# =============================================================================
# Holes
# =============================================================================

# item: Q15.H6py S9
def frame(msg: dict) -> bytes:
    """**H6.** One JSON-RPC message, framed for the Language Server Protocol:
    the header `Content-Length: <n>` and a blank line (each line ended by
    `\\r\\n`), then the message as UTF-8 JSON, where <n> is the length of that
    body in bytes. No other header. Raises TypeError when `msg` is not a dict.
    """
    raise NotImplementedError("Q15.H6py")
# Hint: `json.dumps` gives a str; the header counts the bytes of its UTF-8
#    encoding, which can be more than its characters.


# item: Q15.H7py S9
def read_message(stream: BinaryIO):
    """**H7.** Read one framed message from `stream` (a binary stream with
    `read`), leaving the rest of the stream for the next call.

    The header is lines ended by `\\r\\n`, each `Name: value` (names compared
    without regard to case), ended by an empty line; it must hold exactly one
    `Content-Length` whose value is a non-negative decimal integer, and may
    hold other headers (`Content-Type`), which are ignored. The body is then
    exactly that many bytes of UTF-8 JSON, a JSON object.

    Returns the message as a dict, or None when the stream ends before the
    first byte of a message. Raises ProtocolError for anything else: a header
    line without a colon, a missing, repeated or malformed Content-Length,
    the stream ending inside the header or the body, or a body that is not a
    JSON object.
    """
    raise NotImplementedError("Q15.H7py")
# Hint: read the header one byte at a time up to the blank line; read the
#    body by its length, and a short read is an ended stream, not a body.


# item: Q15.H8py S9
def verify_with_server(path: str, text: str, *, start=None) -> ServerReport:
    """**H8.** Verify one file with the Dafny language server and report.

    Start the server with `start()` when it is given, else with
    `fvh.lsp.start_server()` looked up at the time of the call (the course's
    only way to start it: the pinned server under the Dafny memory cap).
    Either returns a process with binary `stdin` and `stdout`. Then, on the
    process's pipes, framed with `frame` and read with `read_message`:

      1. the request `initialize` (id 1; params `processId`, `rootUri` null,
         `capabilities` {}), and wait for its response (a response is a
         message with an `id` and no `method`): an `error` in it is a
         ProtocolError;
      2. the notification `initialized` (params {});
      3. the notification `textDocument/didOpen` for the file: `uri` its
         `uri_of(path)`, `languageId` "dafny", `version` 1, `text` the text;
      4. read messages until the file's verification ends: a
         `dafny/textDocument/symbolStatus` notification for the file whose
         `namedVerifiables` are not empty and all final (FINAL, by
         status_name), or a `dafny/compilation/status` notification for the
         file whose `status` is "ParsingFailed" or "ResolutionFailed". Keep
         the last symbolStatus and the last `textDocument/publishDiagnostics`
         seen for the file; ignore notifications for other files and every
         other method. A request from the server (a message with both an
         `id` and a `method`) gets the response `result` null, with its id;
      5. the request `shutdown` (id 2) and its response, then the
         notification `exit`; stop the server with `fvh.lsp.stop_server` in
         every case, an exception included.

    Every message the client sends carries `"jsonrpc": "2.0"`; a
    notification has no id. Returns the ServerReport (above). Raises
    ProtocolError when the server's output ends before the verification
    ends.
    """
    raise NotImplementedError("Q15.H8py")
# Hint: `try` / `finally` around everything after the start; a response is
#    told from a request by its `method`.


if __name__ == "__main__":
    sys.exit(main())
