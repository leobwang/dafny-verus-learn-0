"""Q15's acceptance tests for harness/q/fvh_q/lsp_client.py (frozen; QPLAN §25.1, §25.3).

They fail while H6py, H7py or H8py is a hole and pass on a correct file. No
server runs here: `verify_with_server` is fed a recorded transcript of the
pinned `dafny server` (harness/tests/q/fixtures/q15/lsp/server.jsonl: every
message the server wrote in one session over source.dfy, its paths
replaced) and hand-made streams, through a fake process. The tests frame and
parse bytes with their own helpers below, never with the functions under
test, and the transcript's expected report is written out (TRANSCRIPT_REPORT).

What they hold the client to:
  - `frame`: the one header `Content-Length: <bytes>`, CRLF lines, UTF-8 JSON;
  - `read_message`: one message per call, header names without case, other
    headers ignored, None only at a clean end, ProtocolError otherwise;
  - `verify_with_server`: initialize, its response, initialized, didOpen, then
    reading until the file's verification ends, the last symbolStatus and
    diagnostics for the file only, a response to every server request,
    shutdown and exit, and the server stopped through `fvh.lsp.stop_server`
    in every case; `fvh.lsp.start_server` looked up at call time.

Run: scripts/vcheck harness/q/fvh_q/lsp_client.py
     (or, from harness/: uv run pytest tests/q/test_lsp_client.py)
"""

import io
import json
from pathlib import Path

import pytest

from fvh import lsp
from fvh_q import lsp_client as lc

HARNESS = Path(__file__).resolve().parents[2]
FIX = HARNESS / "tests" / "q" / "fixtures" / "q15" / "lsp"
FIXTURE_PATH = "/work/q15/transcript.dfy"
URI = "file://" + FIXTURE_PATH

# The recorded session's report, written out (1-based lines of the symbols' names).
TRANSCRIPT_REPORT = {
    "statuses": [(2, 12, "correct"), (4, 9, "correct"), (9, 9, "error")],
    "diagnostics": [(11, 1, "a postcondition could not be proved on this return path")],
    "ended": "verified",
}


# --- the tests' own framing (independent of the code under test) -------------------------

def enc(msg):
    body = json.dumps(msg).encode("utf-8")
    return b"Content-Length: %d\r\n\r\n" % len(body) + body


def parse_all(raw):
    out, i = [], 0
    while i < len(raw):
        j = raw.index(b"\r\n\r\n", i)
        head = raw[i:j].decode("ascii")
        n = int(head.split(":", 1)[1])
        out.append(json.loads(raw[j + 4:j + 4 + n].decode("utf-8")))
        i = j + 4 + n
    return out


def transcript():
    return [json.loads(line) for line in (FIX / "server.jsonl").read_text(encoding="utf-8")
            .splitlines() if line.strip()]


class Sink(io.BytesIO):
    """The fake server's stdin: keeps what the client wrote, even once closed."""

    def close(self):
        self.kept = self.getvalue()
        super().close()

    def written(self):
        return self.kept if self.closed else self.getvalue()


class FakeProcess:
    pid = 2 ** 22 + 7      # never a real process group: wait() returns first

    def __init__(self, server_msgs=(), raw=None):
        self.stdin = Sink()
        self.stdout = io.BytesIO(raw if raw is not None else b"".join(enc(m) for m in server_msgs))
        self.waited = False

    def wait(self, timeout=None):
        self.waited = True
        return 0


def run_on(msgs=None, raw=None, text="module M {}\n", path=FIXTURE_PATH):
    proc = FakeProcess(msgs or (), raw)
    calls = []

    def start():
        calls.append(1)
        return proc
    rep = lc.verify_with_server(path, text, start=start)
    return rep, proc, calls


def note(method, params):
    return {"jsonrpc": "2.0", "method": method, "params": params}


def status(uri, *pairs):
    return note("dafny/textDocument/symbolStatus", {
        "uri": uri, "version": 1,
        "namedVerifiables": [{"nameRange": {"start": {"line": ln, "character": ch},
                                            "end": {"line": ln, "character": ch + 3}},
                              "status": st} for ln, ch, st in pairs]})


INIT_OK = {"jsonrpc": "2.0", "id": 1, "result": {"capabilities": {}}}
SHUT_OK = {"jsonrpc": "2.0", "id": 2, "result": None}


# --- H6: frame ---------------------------------------------------------------------------

def test_frame_header_and_body():
    out = lc.frame({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    head, sep, body = out.partition(b"\r\n\r\n")
    assert sep == b"\r\n\r\n"
    assert head == b"Content-Length: %d" % len(body)
    assert json.loads(body.decode("utf-8")) == {"jsonrpc": "2.0", "id": 1, "method": "initialize"}


def test_frame_counts_bytes_not_characters():
    msg = {"text": "lemma Größe() {} // ≤ π"}
    out = lc.frame(msg)
    head, _, body = out.partition(b"\r\n\r\n")
    assert int(head.split(b":")[1]) == len(body)
    assert len(body) > len(body.decode("utf-8"))
    assert json.loads(body.decode("utf-8")) == msg


def test_frame_round_trips_through_the_tests_parser():
    msgs = [{"a": [1, 2, {"b": None}]}, {"jsonrpc": "2.0", "method": "exit"}]
    assert parse_all(b"".join(lc.frame(m) for m in msgs)) == msgs


def test_frame_refuses_a_non_dict():
    for bad in ([1, 2], "x", None):
        with pytest.raises(TypeError):
            lc.frame(bad)


# --- H7: read_message --------------------------------------------------------------------

def test_read_message_one_at_a_time():
    s = io.BytesIO(enc({"id": 1}) + enc({"id": 2, "result": None}))
    assert lc.read_message(s) == {"id": 1}
    assert lc.read_message(s) == {"id": 2, "result": None}
    assert lc.read_message(s) is None


def test_read_message_other_headers_and_case():
    body = json.dumps({"ok": True}).encode()
    raw = (b"content-length: %d\r\nContent-Type: application/vscode-jsonrpc; charset=utf-8\r\n\r\n"
           % len(body) + body)
    assert lc.read_message(io.BytesIO(raw)) == {"ok": True}


def test_read_message_utf8_body():
    msg = {"message": "Größe ≤ π"}
    assert lc.read_message(io.BytesIO(enc(msg))) == msg


def test_read_message_clean_end_is_none():
    assert lc.read_message(io.BytesIO(b"")) is None


@pytest.mark.parametrize("raw", [
    b"Content-Type: x\r\n\r\n{}",                       # no Content-Length
    b"Content-Length: two\r\n\r\n{}",                    # not an integer
    b"Content-Length: -2\r\n\r\n{}",                     # negative
    b"Content-Length 2\r\n\r\n{}",                       # no colon
    b"Content-Length: 2\r\nContent-Length: 2\r\n\r\n{}",  # repeated
    b"Content-Length: 2\r\n",                            # ends inside the header
    b"Content-Len",                                      # ends inside a header line
    b"Content-Length: 10\r\n\r\n{}",                     # ends inside the body
    b"Content-Length: 2\r\n\r\n[]",                      # not a JSON object
    b"Content-Length: 3\r\n\r\n{x}",                     # not JSON
])
def test_read_message_refuses_malformed(raw):
    with pytest.raises(lc.ProtocolError):
        lc.read_message(io.BytesIO(raw))


# --- H8: verify_with_server over the recorded transcript ---------------------------------

def test_transcript_report():
    rep, proc, calls = run_on(transcript(), text=(FIX / "source.dfy").read_text(encoding="utf-8"))
    assert calls == [1]
    assert rep.uri == URI
    assert [(s.line, s.character, s.status) for s in rep.statuses] == TRANSCRIPT_REPORT["statuses"]
    assert [(d.line, d.severity, d.message) for d in rep.diagnostics] == \
        TRANSCRIPT_REPORT["diagnostics"]
    assert rep.ended == TRANSCRIPT_REPORT["ended"]


def test_transcript_client_messages():
    text = (FIX / "source.dfy").read_text(encoding="utf-8")
    _rep, proc, _ = run_on(transcript(), text=text)
    sent = parse_all(proc.stdin.written())
    assert all(m.get("jsonrpc") == "2.0" for m in sent)
    methods = [m.get("method") for m in sent]
    assert methods == ["initialize", "initialized", "textDocument/didOpen", "shutdown", "exit"]
    init, inited, opened, shut, ex = sent
    assert init["id"] == 1 and init["params"]["rootUri"] is None and init["params"]["capabilities"] == {}
    assert "processId" in init["params"]
    assert "id" not in inited and "id" not in opened and "id" not in ex
    doc = opened["params"]["textDocument"]
    assert doc == {"uri": URI, "languageId": "dafny", "version": 1, "text": text}
    assert shut["id"] == 2


def test_server_stopped_through_fvh_lsp(monkeypatch):
    stopped = []
    monkeypatch.setattr(lsp, "stop_server", lambda p, **kw: stopped.append(p) or 0)
    _rep, proc, _ = run_on(transcript())
    assert stopped == [proc]


def test_default_start_is_looked_up_at_call_time(monkeypatch):
    proc = FakeProcess(transcript())
    monkeypatch.setattr(lsp, "start_server", lambda *a, **kw: proc)
    rep = lc.verify_with_server(FIXTURE_PATH, "module M {}\n")
    assert rep.ended == "verified"
    assert proc.stdin.closed or proc.waited


# --- H8: hand-made sessions --------------------------------------------------------------

def test_waits_for_final_statuses_and_keeps_the_last():
    msgs = [INIT_OK,
            status(URI, (3, 2, 1), (7, 2, 1)),
            note("textDocument/publishDiagnostics", {"uri": URI, "diagnostics": []}),
            status(URI, (3, 2, 5), (7, 2, 2)),
            note("textDocument/publishDiagnostics", {"uri": URI, "diagnostics": [
                {"range": {"start": {"line": 8, "character": 0}, "end": {"line": 8, "character": 1}},
                 "severity": 2, "message": "w"}]}),
            status(URI, (7, 2, 4), (3, 2, 5)),
            SHUT_OK]
    rep, _, _ = run_on(msgs)
    assert [(s.line, s.character, s.status) for s in rep.statuses] == [(4, 3, "correct"),
                                                                     (8, 3, "error")]
    assert [(d.line, d.severity, d.message) for d in rep.diagnostics] == [(9, 2, "w")]
    assert rep.ended == "verified"


def test_other_files_are_ignored():
    other = "file:///work/q15/other.dfy"
    msgs = [INIT_OK, status(other, (1, 1, 5)),
            note("textDocument/publishDiagnostics", {"uri": other, "diagnostics": [
                {"range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 1}},
                 "severity": 1, "message": "elsewhere"}]}),
            status(URI, (2, 4, 5)), SHUT_OK]
    rep, _, _ = run_on(msgs)
    assert [(s.line, s.status) for s in rep.statuses] == [(3, "correct")]
    assert rep.diagnostics == ()


def test_unknown_status_code_is_named():
    rep, _, _ = run_on([INIT_OK, status(URI, (0, 0, 3)), status(URI, (0, 0, 5)), SHUT_OK])
    assert [s.status for s in rep.statuses] == ["correct"]
    assert lc.status_name(3) == "status-3" and lc.status_name(4) == "error"


@pytest.mark.parametrize("st,ended", [("ResolutionFailed", "resolution-failed"),
                                      ("ParsingFailed", "parse-failed")])
def test_front_end_failure_ends_the_session(st, ended):
    msgs = [INIT_OK,
            note("dafny/compilation/status", {"uri": URI, "version": 1, "status": "ResolutionStarted"}),
            note("dafny/compilation/status", {"uri": URI, "version": 1, "status": st}), SHUT_OK]
    rep, _, _ = run_on(msgs)
    assert rep.ended == ended and rep.statuses == ()


def test_server_requests_get_a_null_response():
    req = {"jsonrpc": "2.0", "id": "srv-7", "method": "window/workDoneProgress/create",
           "params": {"token": "t"}}
    rep, proc, _ = run_on([req, INIT_OK, status(URI, (1, 1, 5)), SHUT_OK])
    sent = parse_all(proc.stdin.written())
    answers = [m for m in sent if m.get("id") == "srv-7"]
    assert answers == [{"jsonrpc": "2.0", "id": "srv-7", "result": None}]
    assert rep.ended == "verified"


def test_initialize_error_is_a_protocol_error(monkeypatch):
    stopped = []
    monkeypatch.setattr(lsp, "stop_server", lambda p, **kw: stopped.append(p) or 0)
    err = {"jsonrpc": "2.0", "id": 1, "error": {"code": -32600, "message": "no"}}
    with pytest.raises(lc.ProtocolError):
        run_on([err])
    assert len(stopped) == 1


def test_end_of_output_before_verification_ends(monkeypatch):
    stopped = []
    monkeypatch.setattr(lsp, "stop_server", lambda p, **kw: stopped.append(p) or 0)
    with pytest.raises(lc.ProtocolError):
        run_on([INIT_OK, status(URI, (1, 1, 2))])
    assert len(stopped) == 1


def test_empty_status_list_is_not_an_end():
    rep, _, _ = run_on([INIT_OK, status(URI), status(URI, (5, 2, 5)), SHUT_OK])
    assert [(s.line, s.status) for s in rep.statuses] == [(6, "correct")]
