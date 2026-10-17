#!/usr/bin/env python3
"""Author-only: record the Dafny language server's side of one session for Q15's
frozen client tests (harness/tests/q/fixtures/q15/lsp/), and capture P1d.

    cd harness && PYTHONPATH=q:../Solutions/harness/q uv run python \
        ../Solutions/plans/Q15-record-transcript.py record OUT_DIR
    ... python ../Solutions/plans/Q15-record-transcript.py p1d

`record` runs the reference client (Solutions/harness/q/fvh_q/lsp_client.py)
on TRANSCRIPT_TEXT through fvh.lsp.start_server (the pinned server under the
Dafny cap), tees every byte the server writes, and writes OUT_DIR/server.jsonl
(one server message per line, in order) and OUT_DIR/source.dfy (the file's
text), with the scratch file's path replaced by FIXTURE_PATH and every other
absolute path in a telemetry payload replaced by "<redacted>". `p1d` runs the
client on the P1d scenario and prints the statuses of its two lemmas.
One server at a time; run with the lane's scratch (DVL_SCRATCH) set.
"""

import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

from fvh import lsp
import fvh_q.lsp_client as lc

FIXTURE_PATH = "/work/q15/transcript.dfy"

TRANSCRIPT_TEXT = """module TranscriptProbe {
  function Triple(x: nat): nat { 3 * x }

  lemma TripleGrows(x: nat)
    ensures x <= Triple(x)
  {
  }

  lemma TripleBelow(x: nat)
    ensures Triple(x) < 2 * x + 1
  {
  }
}
"""

P1D_TEXT = """module P1Scenario {
  lemma DoubleGrows(x: nat)
    ensures x <= 2 * x
  {
  }

  lemma DoubleMono(x: nat, y: nat)
    requires x <= y
    ensures 2 * x <= 2 * y
}
"""


class Tee(io.RawIOBase):
    def __init__(self, raw, sink):
        self.raw, self.sink = raw, sink

    def readable(self):
        return True

    def read(self, n=-1):
        b = self.raw.read(n)
        self.sink.extend(b)
        return b


class Proxy:
    def __init__(self, proc, sink):
        self.proc, self.stdin, self.pid = proc, proc.stdin, proc.pid
        self.stdout = Tee(proc.stdout, sink)

    def wait(self, timeout=None):
        return self.proc.wait(timeout=timeout)


def run(text):
    sink = bytearray()
    with tempfile.TemporaryDirectory(prefix="q15-lsp-") as d:
        p = Path(d) / "transcript.dfy"
        p.write_text(text, encoding="utf-8")
        rep = lc.verify_with_server(str(p), text, start=lambda: Proxy(lsp.start_server(), sink))
        return rep, bytes(sink), lc.uri_of(str(p))


def split(raw):
    out, s = [], io.BytesIO(raw)
    while True:
        m = lc.read_message(s)
        if m is None:
            return out
        out.append(m)


def redact(obj, uri):
    txt = json.dumps(obj, ensure_ascii=False)
    txt = txt.replace(uri, "file://" + FIXTURE_PATH)
    txt = re.sub(r'"/(?:tmp|home)/[^"]*"', '"<redacted>"', txt)
    return json.loads(txt)


def main(argv):
    if argv[:1] == ["p1d"]:
        rep, _, _ = run(P1D_TEXT)
        print(rep.ended, [(s.line, s.status) for s in rep.statuses])
        return 0
    out = Path(argv[1])
    rep, raw, uri = run(TRANSCRIPT_TEXT)
    msgs = [redact(m, uri) for m in split(raw)]
    out.mkdir(parents=True, exist_ok=True)
    (out / "server.jsonl").write_text("".join(json.dumps(m, ensure_ascii=False, sort_keys=True) + "\n"
                                             for m in msgs), encoding="utf-8")
    (out / "source.dfy").write_text(TRANSCRIPT_TEXT, encoding="utf-8")
    print(rep.ended, [(s.line, s.status) for s in rep.statuses],
          [(d.line, d.severity) for d in rep.diagnostics], len(msgs), "messages")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
