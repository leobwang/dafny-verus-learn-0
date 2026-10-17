"""Q15 — Practice II-C: the language-server client (Reference Solution)

Hole-free reference for `harness/q/fvh_q/lsp_client.py` (author-only; never
learner-visible). Same names, signatures, docstrings, item markers and order
as the exercise file. Every hole is filled. Each H item declares, on a
`# triv:` line after its function, the trivial body that the Python TRIV
mode of `scripts/firsttry.sh Q15 --empty-body` lays over this reference: the
acceptance tests must reject each one (QPLAN §19.0, §11.8).

The tools run this file only by overlay: `scripts/dvl/python.py` copies
harness/ to scratch, lays this twin over its learner path and runs the
module's acceptance tests there (harness/tests/q/test_lsp_client.py; they
replay the server transcript recorded under harness/tests/q/fixtures/q15/lsp/
by Solutions/plans/Q15-record-transcript.py, so no server runs).
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
    if not isinstance(msg, dict):
        raise TypeError(f"a message is a dict, not {type(msg).__name__}")
    body = json.dumps(msg, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return b"Content-Length: " + str(len(body)).encode("ascii") + b"\r\n\r\n" + body
# triv: return json.dumps(msg).encode()


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
    lines = []
    buf = b""
    while True:
        c = stream.read(1)
        if not c:
            if not buf and not lines:
                return None
            raise ProtocolError("the stream ended inside a header")
        buf += c
        if buf.endswith(b"\r\n"):
            line = buf[:-2]
            buf = b""
            if line == b"":
                break
            lines.append(line)
    length = None
    for raw in lines:
        try:
            text = raw.decode("ascii")
        except UnicodeDecodeError:
            raise ProtocolError("a header line is not ASCII") from None
        name, colon, value = text.partition(":")
        if not colon:
            raise ProtocolError(f"a header line without a colon: {text!r}")
        if name.strip().lower() == "content-length":
            if length is not None:
                raise ProtocolError("a repeated Content-Length")
            v = value.strip()
            if not v.isdigit() or not v.isascii():
                raise ProtocolError(f"a malformed Content-Length: {v!r}")
            length = int(v)
    if length is None:
        raise ProtocolError("no Content-Length")
    body = b""
    while len(body) < length:
        chunk = stream.read(length - len(body))
        if not chunk:
            raise ProtocolError("the stream ended inside a body")
        body += chunk
    try:
        msg = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise ProtocolError("a body that is not UTF-8 JSON") from None
    if not isinstance(msg, dict):
        raise ProtocolError("a body that is not a JSON object")
    return msg
# triv: return json.loads(stream.read().split(b"\r\n\r\n", 1)[1] or b"null")


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
    proc = (start if start is not None else lsp.start_server)()
    uri = uri_of(path)

    def send(msg):  # reference-only: a helper of the reference
        proc.stdin.write(frame(msg))
        proc.stdin.flush()

    def recv():  # reference-only: a helper of the reference
        m = read_message(proc.stdout)
        if m is None:
            raise ProtocolError("the server's output ended")
        if "id" in m and "method" in m:
            send({"jsonrpc": "2.0", "id": m["id"], "result": None})
        return m

    def await_response(rid):  # reference-only: a helper of the reference
        while True:
            m = recv()
            if m.get("id") == rid and "method" not in m:
                if "error" in m:
                    raise ProtocolError(f"request {rid} failed: {m['error']!r}")
                return m

    try:
        send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
              "params": {"processId": os.getpid(), "rootUri": None, "capabilities": {}}})
        await_response(1)
        send({"jsonrpc": "2.0", "method": "initialized", "params": {}})
        send({"jsonrpc": "2.0", "method": "textDocument/didOpen",
              "params": {"textDocument": {"uri": uri, "languageId": "dafny", "version": 1,
                                          "text": text}}})
        statuses, diagnostics, ended = (), (), None
        while ended is None:
            m = recv()
            meth = m.get("method")
            params = m.get("params") if isinstance(m.get("params"), dict) else {}
            if params.get("uri") != uri or "id" in m:
                continue
            if meth == "textDocument/publishDiagnostics":
                diagnostics = tuple(
                    Diagnostic(d["range"]["start"]["line"] + 1, d.get("severity"), d.get("message"))
                    for d in params.get("diagnostics", []))
            elif meth == "dafny/textDocument/symbolStatus":
                vs = params.get("namedVerifiables", [])
                statuses = tuple(sorted(
                    (SymbolStatus(v["nameRange"]["start"]["line"] + 1,
                                  v["nameRange"]["start"]["character"] + 1,
                                  status_name(v["status"])) for v in vs),
                    key=lambda s: (s.line, s.character)))
                if statuses and all(s.status in FINAL for s in statuses):
                    ended = "verified"
            elif meth == "dafny/compilation/status":
                st = params.get("status")
                if st == "ParsingFailed":
                    ended = "parse-failed"
                elif st == "ResolutionFailed":
                    ended = "resolution-failed"
        send({"jsonrpc": "2.0", "id": 2, "method": "shutdown", "params": None})
        try:
            await_response(2)
        except ProtocolError:
            pass
        send({"jsonrpc": "2.0", "method": "exit", "params": None})
        return ServerReport(uri, statuses, diagnostics, ended)
    finally:
        lsp.stop_server(proc)
# triv: return ServerReport(uri_of(path), (), (), "verified")


if __name__ == "__main__":
    sys.exit(main())
