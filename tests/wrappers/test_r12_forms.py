"""Independent R12 form frames: static native parsers, no solver/model calls."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_tools_common as C
ROOT=Path(__file__).resolve().parents[2]
core=C.load_script('vcheck')
spec=importlib.util.spec_from_file_location('r12_admit_forms',ROOT/'tools/R12/admit_forms.py')
admit=importlib.util.module_from_spec(spec);spec.loader.exec_module(admit)
sys.path.insert(0,str(ROOT/'harness'));sys.path.insert(0,str(ROOT/'harness/r'))
from fvh_r.engine import source_task

class FormFrames(unittest.TestCase):
 def analyze(self,text,extension):
  with tempfile.TemporaryDirectory() as directory:
   p=Path(directory)/('form'+extension);p.write_text(text)
   return admit.analyze_form(p,core,source_task)
 def header(self,kind='expr',callees=()):
  import json
  return '// R12_HINT_SITES: '+json.dumps([dict(name='site',identifiers=['n','i'],kind=kind,callees=list(callees))])+'\n'
 def test_dafny_invariant_is_not_executable_code(self):
  text=self.header()+'''module FrameD {method Run(n:nat) returns(i:nat) {i:=0;while i<n
 invariant /*R12_HINT:site*/ true
 {i:=i+1;}}}'''
  self.assertEqual(self.analyze(text,'.dfy')['sites'][0]['kind'],'expr')
 def test_verus_invariant_is_not_executable_code(self):
  text=self.header()+'''use vstd::prelude::*;verus! {fn run(n:usize)->(i:usize){let mut i=0;while i<n
 invariant /*R12_HINT:site*/ true
 decreases n-i,
 {i=i+1;}i}}'''
  self.assertEqual(self.analyze(text,'.rs')['sites'][0]['kind'],'expr')
 def test_dafny_code_header_and_model_sites_are_rejected(self):
  bodies=['module FrameD {method Run() returns(v:bool) {v:=/*R12_HINT:site*/ true;}}','module FrameD {method Run() requires /*R12_HINT:site*/ true {}}','module FrameD {ghost predicate Meaning() {/*R12_HINT:site*/ true}}']
  for body in bodies:
   with self.subTest(body=body),self.assertRaises(ValueError):self.analyze(self.header()+body,'.dfy')
 def test_verus_code_header_and_model_sites_are_rejected(self):
  bodies=['use vstd::prelude::*;verus! {fn run()->bool {/*R12_HINT:site*/ true}}','use vstd::prelude::*;verus! {fn run() requires /*R12_HINT:site*/ true, {}}','use vstd::prelude::*;verus! {pub open spec fn meaning()->bool {/*R12_HINT:site*/ true}}']
  for body in bodies:
   with self.subTest(body=body),self.assertRaises(ValueError):self.analyze(self.header()+body,'.rs')
 def test_only_local_proof_callees_are_eligible(self):
  for lang,good,bad in [('.dfy','module CallsD {lemma Step(n:int) {} lemma Goal(n:int) {/*R12_CALLS:site*/}}','module CallsD {method Step(n:int) {} lemma Goal(n:int) {/*R12_CALLS:site*/}}'),('.rs','use vstd::prelude::*;verus! {proof fn Step(n:int) {} proof fn goal(n:int) {/*R12_CALLS:site*/}}','use vstd::prelude::*;verus! {fn Step(n:int) {} proof fn goal(n:int) {/*R12_CALLS:site*/}}')]:
   with self.subTest(lang=lang):
    self.assertEqual(self.analyze(self.header('calls',['Step'])+good,lang)['sites'][0]['callee_bindings'],['Step'])
    with self.assertRaises(ValueError):self.analyze(self.header('calls',['Step'])+bad,lang)
 def test_duplicate_proof_names_cannot_hide_ambiguous_callee_bindings(self):
  examples=[('.dfy','module A {lemma Step(n:int) {}} module B {lemma Step(n:int) {}} module Goal {lemma Run(n:int) {/*R12_CALLS:site*/}}'),('.rs','use vstd::prelude::*;verus! {mod a {proof fn Step(n:int) {}} mod b {proof fn Step(n:int) {}} proof fn goal(n:int) {/*R12_CALLS:site*/}}')]
  for language,text in examples:
   with self.subTest(language=language),self.assertRaisesRegex(ValueError,'unambiguous'):
    self.analyze(self.header('calls',['Step'])+text,language)

 def test_foreign_scope_and_local_shadowing_are_not_proof_callee_bindings(self):
  examples=[('.dfy','module A {lemma Step() {}} module B {lemma Goal() {/*R12_CALLS:site*/}}'),('.dfy','module A {lemma Step() {} lemma Goal(Step:int) {/*R12_CALLS:site*/}}'),('.rs','use vstd::prelude::*;verus! {mod a {proof fn Step(){}} proof fn goal(){/*R12_CALLS:site*/}}'),('.rs','use vstd::prelude::*;verus! {proof fn Step(){} proof fn goal(Step:int){/*R12_CALLS:site*/}}')]
  for language,text in examples:
   with self.subTest(language=language),self.assertRaisesRegex(ValueError,'unambiguous'):
    self.analyze(self.header('calls',['Step'])+text,language)
 def test_executable_call_sites_are_not_admitted_as_ghost_calls(self):
  for language,text in [('.dfy','module A {lemma Step(){} method Run(){/*R12_CALLS:site*/}}'),('.rs','use vstd::prelude::*;verus! {proof fn Step(){} fn run(){/*R12_CALLS:site*/}}')]:
   with self.subTest(language=language),self.assertRaisesRegex(ValueError,'proof-declaration'):
    self.analyze(self.header('calls',['Step'])+text,language)

if __name__=='__main__':unittest.main()
