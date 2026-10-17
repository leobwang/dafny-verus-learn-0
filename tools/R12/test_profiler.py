"""Frozen toolwright acceptance. The actor edits profiler.py's A1 body only.

Only scripted normalized documents are used here; no verifier or model runs.
The CLI/signature/data-model frame is pinned independently of the A1 body.
"""
import ast
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('r12_profiler_under_test',HERE/'profiler.py')
profiler=importlib.util.module_from_spec(spec);sys.modules[spec.name]=profiler;spec.loader.exec_module(profiler)
FRAME_SHA256='be77d830840a0466f9046258bff42cb55e4906ea9a3283a17038551c15e9a1cf'

def document(**changes):
 d=dict(lang='dafny',target='sample.dfy',verdict='verified',stage='verify',exit_code=0,verified_count=1,holes=[],findings=[],diagnostics=[],per_symbol={'M.F':'verified'},wall_s=.25,resource_count=None)
 d.update(changes);return d

class ProfilerContract(unittest.TestCase):
 def test_fixed_signature_cli_and_models(self):
  tree=ast.parse((HERE/'profiler.py').read_text())
  target=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='profile_symbols_r12');target.body=[ast.Pass()]
  self.assertEqual(hashlib.sha256(ast.dump(tree,include_attributes=False).encode()).hexdigest(),FRAME_SHA256)
 def test_order_repeats_exact_native_commands_and_unavailable_resources(self):
  calls=[]
  def run(argv):calls.append(argv);return document(per_symbol={argv[4]:'verified'})
  rows=profiler.profile_symbols_r12('sample.dfy',['M.F','M.G'],repeats=2,run=run)
  self.assertEqual([(r.symbol,r.repeat,r.resource_count) for r in rows],[('M.F',0,None),('M.F',1,None),('M.G',0,None),('M.G',1,None)])
  self.assertEqual(calls,[['scripts/vcheck','--json','--measures','--symbol',r.symbol,'--isolate','sample.dfy'] for r in rows])
 def test_every_native_failure_and_unknown_scope_remains_visible(self):
  for verdict in ['failed','inconclusive','refused','killed(memory)','error']:
   with self.subTest(verdict=verdict):
    row=profiler.profile_symbols_r12('sample',['M.F'],repeats=1,run=lambda _:document(verdict=verdict,resource_count=0,per_symbol={'M.F':verdict}))[0]
    self.assertEqual((row.verdict,row.selected_status,row.resource_count),(verdict,verdict,0))
  for statuses in [{},{'Other.F':'verified'},{'A::F':'verified','B::F':'failed'}]:
   symbol='F' if 'A::F' in statuses else 'M.F'
   self.assertIsNone(profiler.profile_symbols_r12('sample',[symbol],repeats=1,run=lambda _:document(per_symbol=statuses))[0].selected_status)
 def test_invalid_requests_never_call_a_runner(self):
  for target,symbols,repeats in [('', ['F'],1),('x',[],1),('x',['F','F'],1),('x',[None],1),('x',['F'],True),('x',['F'],0)]:
   with self.subTest(target=target,symbols=symbols,repeats=repeats),self.assertRaises(ValueError):profiler.profile_symbols_r12(target,symbols,repeats=repeats,run=lambda _:self.fail('invalid request ran'))
 def test_missing_and_invalid_measurements_do_not_turn_into_zero(self):
  bad=[{'wall_s':True},{'wall_s':float('nan')},{'wall_s':-1},{'wall_s':None},{'resource_count':'0'},{'resource_count':float('inf')},{'stage':'unknown'},{'verdict':'ok'},{'holes':[True]},{'per_symbol':{'M.F':False}}]
  for changes in bad:
   with self.subTest(changes=changes),self.assertRaises(ValueError):profiler.profile_symbols_r12('sample',['M.F'],repeats=1,run=lambda _:document(**changes))
  def missing(_):d=document();del d['wall_s'];return d
  with self.assertRaises(ValueError):profiler.profile_symbols_r12('sample',['M.F'],repeats=1,run=missing)
 def test_documents_are_snapshots_not_a_mutable_runner_alias(self):
  shared=document();calls=[]
  def run(_):shared['wall_s']=len(calls)+1;calls.append(1);return shared
  rows=profiler.profile_symbols_r12('sample',['M.F'],repeats=2,run=run);shared['wall_s']=99
  self.assertEqual([r.document['wall_s'] for r in rows],[1,2])
 def test_cli_reports_isolated_scope_and_preserves_native_failure(self):
  with tempfile.TemporaryDirectory() as directory:
   source=Path(directory)/'sample.dfy';source.write_text('module Neutral {}\n');out=io.StringIO()
   code=profiler.main([str(source),'--symbol','M.F','--repeats','1'],run=lambda _:document(verdict='failed'),out=out)
   self.assertEqual(code,0);report=json.loads(out.getvalue());self.assertIn('not a full acceptance gate',report['scope']);self.assertEqual(report['results'][0]['verdict'],'failed')
 def test_source_change_during_measurement_is_rejected(self):
  with tempfile.TemporaryDirectory() as directory:
   source=Path(directory)/'sample.dfy';source.write_text('module Neutral {}\n');out=io.StringIO()
   def change(_):source.write_text('module Changed {}\n');return document()
   self.assertEqual(profiler.main([str(source),'--symbol','M.F','--repeats','1'],run=change,out=out),2)
   self.assertEqual(out.getvalue(),'')

if __name__=='__main__':unittest.main()
