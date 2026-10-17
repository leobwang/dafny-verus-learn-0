"""R12 recorded framing only; no client/server process or native assertion claim."""
import base64
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('r12_trace',ROOT/'tools/R12/read_trace.py')
trace=importlib.util.module_from_spec(spec);spec.loader.exec_module(trace)

# Static decoder fixtures; no reusable client encoder is published here.
UNICODE_RECORD = {'direction': 'server', 'wire_base64': 'Q29udGVudC1MZW5ndGg6IDY1DQoNCnsianNvbnJwYyI6ICIyLjAiLCAibWV0aG9kIjogImV4YW1wbGUiLCAicGFyYW1zIjogWyLOuyIsICLwn6eqIl19', 'document': {'jsonrpc': '2.0', 'method': 'example', 'params': ['λ', '🧪']}}
EMPTY_RECORD = {'direction': 'server', 'wire_base64': 'Q29udGVudC1MZW5ndGg6IDMyDQoNCnsianNvbnJwYyI6ICIyLjAiLCAicGFyYW1zIjogW119', 'document': {'jsonrpc': '2.0', 'params': []}}
RESPONSE_RECORD = {'direction': 'server', 'wire_base64': 'Q29udGVudC1MZW5ndGg6IDQzDQoNCnsianNvbnJwYyI6ICIyLjAiLCAicmVzdWx0IjogbnVsbCwgImlkIjogMX0=', 'document': {'jsonrpc': '2.0', 'result': None, 'id': 1}}

class RecordedTrace(unittest.TestCase):
 def test_real_trace_binds_own_source_and_preserves_diagnostics(self):
  result=trace.observe(ROOT/'specimens/R12/lsp/messages.jsonl',ROOT/'specimens/R12/lsp/source.dfy.trace')
  self.assertEqual(result['messages'],24)
  self.assertTrue(any('assertion might not hold' in d['message'] for d in result['diagnostics']))
 def test_unicode_counts_bytes_and_array_params_are_not_lost(self):
  document=dict(jsonrpc='2.0',method='example',params=['λ','🧪'])
  self.assertEqual(trace.decode_record(UNICODE_RECORD),document)
 def test_wrong_length_and_duplicate_length_rejected(self):
  r=EMPTY_RECORD
  for header in [b'Content-Length: 1',b'Content-Length: 1\r\nContent-Length: 2']:
   wire=base64.b64decode(r['wire_base64']);r2={**r,'wire_base64':base64.b64encode(header+b'\r\n\r\n'+wire.split(b'\r\n\r\n',1)[1]).decode()}
   with self.assertRaises(ValueError):trace.decode_record(r2)
 def test_document_mismatch_rejected(self):
  r={**RESPONSE_RECORD,'document':{**RESPONSE_RECORD['document'],'id':2}}
  with self.assertRaises(ValueError):trace.decode_record(r)

if __name__=='__main__':unittest.main()
