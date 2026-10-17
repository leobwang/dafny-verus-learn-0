"""Plan structure/binding controls only; neutral files are not admitted lab data."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import tomllib
import unittest
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'harness'),str(ROOT/'harness/r')]
from fvh import batch,protocol as P
spec=importlib.util.spec_from_file_location('r12_plan',ROOT/'tools/R12/plan.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def cards(root):
 rows=[]
 for lang,ext in [('dafny','.dfy'),('verus','.rs')]:
  for i in range(20):
   name=('d' if lang=='dafny' else 'v')+str(i);p=root/(name+ext);p.write_text('// neutral structure-only fixture '+name+'\n')
   rows.append(dict(id=name,lang=lang,path=p.name,statement='Neutral fixture; no native admission claim.',source_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 return rows


class PlanContract(unittest.TestCase):
 def test_frozen_loader_matched_budgets_source_binding_and_inline_prompt_bytes(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);rows=cards(root);plans,subset=module.build_plans(rows,seed=1217,subset_seed=4217)
   self.assertEqual(len(subset),10);self.assertEqual(sum(x.startswith('d') for x in subset),5)
   for name,text in plans.items():
    path=root/(name+'.toml');path.write_text(text);plan=batch.load_plan(path,root)
    self.assertTrue(plan.lever_check);self.assertEqual(plan.attempts,1)
    self.assertEqual(plan.repeats,3 if name=='qwen' else 1)
    runs=len(plan.tasks)*len(plan.arms)*plan.repeats
    self.assertEqual((runs,runs*10),(480,4800) if name=='qwen' else (10,100))
    self.assertEqual(plan.system,(ROOT/'tools/R12/lab_system.md').read_text())
    self.assertEqual(plan.instructions,(ROOT/'tools/R12/lab_instructions.md').read_text())
    self.assertTrue(all(a.construct=='seeded' and a.caps['turns']==12 and a.rounds==10 and a.lab_code=='preserve' for a in plan.arms))
    for card in rows:
     if card['id'] in plan.tasks:self.assertTrue(plan.task_statements[card['id']].startswith('R12_TASK_SHA256: '+card['source_sha256']+'\n'))
    if name=='qwen':self.assertEqual([a.policy for a in plan.arms],['fvh_r.engine:'+p for _,p in module.POLICIES])
 def test_subset_reproducible_without_reordering_main_stratum(self):
  with tempfile.TemporaryDirectory() as temporary:
   rows=cards(Path(temporary));original=[x['id'] for x in rows]
   self.assertEqual(module.build_plans(rows,seed=4,subset_seed=5),module.build_plans(rows,seed=4,subset_seed=5))
   self.assertEqual([x['id'] for x in rows],original)
 def test_incomplete_unbalanced_and_bool_seeds_refused(self):
  with tempfile.TemporaryDirectory() as temporary:
   rows=cards(Path(temporary))
   for data,seed,subset in [(rows[:-1],1,2),([dict(r,lang='dafny') for r in rows],1,2),(rows,True,2),(rows,1,False)]:
    with self.assertRaises(ValueError):module.build_plans(data,seed=seed,subset_seed=subset)
 def test_stratum_missing_admissions_or_hashes_cannot_produce_a_plan(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);path=root/'STRATUM.toml';path.write_text('schema=1\nlab="R12"\n')
   with self.assertRaisesRegex(ValueError,'40'):module.load_stratum(root,path)
 def test_course_file_cannot_escape_or_discover_reference_material(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);(root/'Solutions').mkdir();(root/'Solutions/answer.rs').write_text('protected fixture')
   for path in ['../escape.rs','/tmp/absolute.rs','Solutions/answer.rs','missing.rs']:
    with self.assertRaises(ValueError):module.course_path(root,path)

if __name__=='__main__':unittest.main()
