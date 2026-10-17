"""Frozen R14 toolsmith controls: native byte spans, scope and original frame.
Actual capture and synthetic boundary cases are distinguished explicitly.
"""
import ast
from dataclasses import FrozenInstanceError
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'MODULES.toml').is_file())
FIX=ROOT/'specimens/R14/native-triggers'
spec=importlib.util.spec_from_file_location('r14_tool_under_test',HERE/'trigscan.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
FRAME_SHA256='77df9096e67eb220ff17ca46cceef597ea297a013a50872f168150714fa593b0'

def capture(source=b'alpha[k]',records=(),identity='fixture://source',extra=b''):
 raw=b''.join((json.dumps(x,ensure_ascii=False)+'\n').encode() for x in records)+extra
 return m.CaptureR14(identity,source,raw,m.sha_r14(source),m.sha_r14(raw))
def note(message,spans=()):return {'$message_type':'diagnostic','message':message,'spans':list(spans)}
def span(a,z,*,identity='fixture://source',line=1):return {'file_name':identity,'byte_start':a,'byte_end':z,'line_start':line}
AUTO='automatically chose triggers for this expression:'
SELECT='selected triggers for this expression:'

class TriggerTests(unittest.TestCase):
 def test_actual_path_normalized_native_capture(self):
  b=json.loads((FIX/'binding.json').read_text())
  c=m.CaptureR14(b['source_id'],(FIX/'source.rs.trace').read_bytes(),(FIX/'stderr.jsonl').read_bytes(),b['source_sha256'],b['stderr_sha256'])
  result=m.scan_trigger_notes_r14(c)
  self.assertEqual(len(result.groups),7)
  self.assertEqual(sum(len(g.patterns) for g in result.groups),8)
  self.assertEqual([(t.text,t.line,t.start,t.end) for t in result.located_terms],[('values[i]',4,141,150)])
  self.assertEqual(result.availability,'reported')
  self.assertEqual(result.source_sha256,b['source_sha256'])
  self.assertEqual(result.stderr_sha256,b['stderr_sha256'])
  self.assertEqual(result.unparsed_lines,0)
  self.assertEqual(result.orphan_patterns,0)
  self.assertEqual(sum(t.status=='external' for g in result.groups for p in g.patterns for t in p.terms),6)
 def test_synthetic_utf8_uses_native_byte_offsets(self):
  blob='//λ\ntrace[k]'.encode();a=blob.index(b'trace')
  c=capture(blob,[note(AUTO),note('  trigger 1 of 1:',[span(a,len(blob),line=2)])])
  r=m.scan_trigger_notes_r14(c)
  self.assertEqual([(t.text,t.line) for t in r.located_terms],[('trace[k]',2)])
  self.assertEqual(c.source,blob)
 def test_alternatives_and_multiterm_groups_are_not_flattened(self):
  c=capture(b'left[k] right[k]',[note(SELECT),note('  trigger 1 of 2:',[span(0,7),span(8,16)]),note('  trigger 2 of 2:')])
  r=m.scan_trigger_notes_r14(c)
  self.assertEqual(len(r.groups),1);self.assertEqual(r.groups[0].selection,'selected')
  self.assertEqual([p.ordinal for p in r.groups[0].patterns],[1,2])
  self.assertEqual([t.text for t in r.groups[0].patterns[0].terms],['left[k]','right[k]'])
  self.assertEqual(r.groups[0].patterns[1].terms[0].status,'unlocated')
 def test_unreported_is_unavailable_and_unparsed_lines_are_retained(self):
  for c in [capture(),capture(records=[note('postcondition not satisfied')],extra=b'unrecognized native text\n')]:
   r=m.scan_trigger_notes_r14(c);self.assertEqual(r.availability,'unavailable');self.assertEqual(r.located_terms,())
  self.assertEqual(r.unparsed_lines,1)
 def test_orphan_and_invalid_ordinal_are_not_invented_headers(self):
  c=capture(records=[note('  trigger 1 of 1:',[span(0,8)]),note('  trigger 2 of 1:')])
  r=m.scan_trigger_notes_r14(c)
  self.assertEqual(r.orphan_patterns,1);self.assertEqual(r.unparsed_lines,1)
  self.assertEqual(r.groups[0].selection,'unattached')
 def test_external_identity_and_invalid_extent_do_not_guess_source_terms(self):
  c=capture(records=[note(AUTO),note('  trigger 1 of 1:',[span(0,8,identity='other://source'),span(0,99),span(True,8),span(0,8,line=9)])])
  r=m.scan_trigger_notes_r14(c)
  self.assertEqual(r.located_terms,())
  self.assertEqual([t.status for t in r.groups[0].patterns[0].terms],['external','invalid-span','invalid-span','invalid-span'])
 def test_capture_drift_is_rejected_before_analysis(self):
  c=capture(records=[note(AUTO)])
  with self.assertRaisesRegex(ValueError,'digest mismatch'):m.CaptureR14(c.source_id,c.source+b'x',c.stderr,c.source_sha256,c.stderr_sha256)
  with self.assertRaisesRegex(ValueError,'digest mismatch'):m.CaptureR14(c.source_id,c.source,c.stderr+b'x',c.source_sha256,c.stderr_sha256)
  with self.assertRaises(FrozenInstanceError):c.source=b'changed'
 def test_only_the_actor_body_may_change(self):
  tree=ast.parse((HERE/'trigscan.py').read_text());found=[]
  for n in ast.walk(tree):
   if isinstance(n,ast.FunctionDef) and n.name=='scan_trigger_notes_r14':n.body=n.body[:1]+[ast.Pass()];found.append(n.name)
  self.assertEqual(found,['scan_trigger_notes_r14'])
  self.assertEqual(hashlib.sha256(ast.dump(tree,include_attributes=False).encode()).hexdigest(),FRAME_SHA256)
if __name__=='__main__':unittest.main()
