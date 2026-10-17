#!/usr/bin/env python3
"""Read R12's own captured JSON-RPC frames; never connect to a language server."""
from __future__ import annotations
import argparse
import base64
from collections import Counter
import json
from pathlib import Path


def decode_record(row):
    if not isinstance(row,dict) or row.get('direction') not in ('client','server'):
        raise ValueError('record direction')
    wire=base64.b64decode(row['wire_base64'],validate=True)
    header,sep,body=wire.partition(b'\r\n\r\n')
    if not sep:raise ValueError('missing framed header separator')
    lengths=[line.split(b':',1)[1].strip() for line in header.split(b'\r\n') if line.lower().startswith(b'content-length:')]
    if len(lengths)!=1 or not lengths[0].isdigit() or int(lengths[0])!=len(body):
        raise ValueError('Content-Length must equal UTF-8 body bytes')
    document=json.loads(body.decode('utf-8'))
    if not isinstance(document,dict) or document.get('jsonrpc')!='2.0' or document!=row['document']:
        raise ValueError('decoded JSON-RPC document differs from recording')
    return document


def observe(trace,source):
    records=[json.loads(line) for line in Path(trace).read_text().splitlines()]
    directions=Counter();methods=Counter();diagnostics=[];opened=[]
    for row in records:
        message=decode_record(row);directions[row['direction']]+=1
        method=message.get('method')
        if method:methods[method]+=1
        params=message.get('params')
        if method=='textDocument/didOpen':opened.append(params['textDocument']['text'])
        if method=='textDocument/publishDiagnostics':
            for d in params['diagnostics']:
                diagnostics.append({'uri':params['uri'],'version':params.get('version'),'line':d['range']['start']['line']+1,'severity':d.get('severity'),'message':d['message']})
    if opened!=[Path(source).read_text()]:raise ValueError('didOpen buffer is not the recorded source')
    return {'scope':'captured protocol observation, not a full gate','messages':len(records),'directions':dict(directions),'methods':dict(methods),'diagnostics':diagnostics}


def main():
    root=Path(__file__).resolve().parents[2]
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--trace',type=Path,default=root/'specimens/R12/lsp/messages.jsonl')
    ap.add_argument('--source',type=Path,default=root/'specimens/R12/lsp/source.dfy.trace')
    args=ap.parse_args();result=observe(args.trace,args.source)
    print('Captured frames: '+str(result['messages'])+'; each Content-Length matches body bytes')
    print('didOpen source matches the committed observation fixture')
    for d in result['diagnostics']:print(f"Diagnostic line {d['line']}, severity {d['severity']}: {d['message']}")
    print(result['scope'])
    return 0


if __name__=='__main__':raise SystemExit(main())
