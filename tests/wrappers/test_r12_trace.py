"""R12 recorded framing only; no client/server process or native assertion claim."""
import base64
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('r12_trace',ROOT/'tools/R12/read_trace.py')
trace=importlib.util.module_from_spec(spec);spec.loader.exec_module(trace)

def record(document):
 body=json.dumps(document,ensure_ascii=False).encode();wire=b'Content-Length: '+str(len(body)).encode()+b'\r\n\r\n'+body
 return dict(direction='server',wire_base64=base64.b64encode(wire).decode(),document=document)

class RecordedTrace(unittest.TestCase):
 def test_real_trace_binds_own_source_and_preserves_diagnostics(self):
  result=trace.observe(ROOT/'specimens/R12/lsp/messages.jsonl',ROOT/'specimens/R12/lsp/source.dfy.trace')
  self.assertEqual(result['messages'],24)
  self.assertTrue(any('assertion might not hold' in d['message'] for d in result['diagnostics']))
 def test_unicode_counts_bytes_and_array_params_are_not_lost(self):
  document=dict(jsonrpc='2.0',method='example',params=['λ','🧪'])
  self.assertEqual(trace.decode_record(record(document)),document)
 def test_wrong_length_and_duplicate_length_rejected(self):
  r=record(dict(jsonrpc='2.0',params=[]))
  for header in [b'Content-Length: 1',b'Content-Length: 1\r\nContent-Length: 2']:
   wire=base64.b64decode(r['wire_base64']);r2={**r,'wire_base64':base64.b64encode(header+b'\r\n\r\n'+wire.split(b'\r\n\r\n',1)[1]).decode()}
   with self.assertRaises(ValueError):trace.decode_record(r2)
 def test_document_mismatch_rejected(self):
  r=record(dict(jsonrpc='2.0',result=None,id=1));r['document']['id']=2
  with self.assertRaises(ValueError):trace.decode_record(r)

if __name__=='__main__':unittest.main()
