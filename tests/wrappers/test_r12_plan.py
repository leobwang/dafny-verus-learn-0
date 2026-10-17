"""Plan structure/binding controls only; neutral files are not admitted lab data."""
import hashlib
import json
import shutil
import re
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
   rows.append(dict(id=name,lang=lang,path=p.name,statement='Neutral fixture; no native admission claim.',cluster='algorithm-'+str(i),exposure='neutral fixture; no exposure claim',source_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
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



class CatalogBindings(unittest.TestCase):
 def setUp(self):
  self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
  self.root=Path(self.directory.name)
  paths=[ROOT/'bench/local/r/labalpha/STRATUM.toml',ROOT/'bench/public/POOLS.toml']
  data=tomllib.loads(paths[0].read_text())
  for card in data['card']:paths.extend([ROOT/card['path'],ROOT/card['admission']])
  for path in paths:
   dest=self.root/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
  self.stratum=self.root/'bench/local/r/labalpha/STRATUM.toml'
 def test_actual_catalog_has40_bound_tasks_and20_paired_clusters(self):
  rows=module.load_stratum(self.root,self.stratum)
  self.assertEqual(len(rows),40);self.assertEqual(len({r['cluster'] for r in rows}),20)
 def test_source_change_after_admission_refused(self):
  card=tomllib.loads(self.stratum.read_text())['card'][0];source=self.root/card['path'];source.write_text(source.read_text()+'// changed bytes\n')
  with self.assertRaisesRegex(ValueError,'stale'):module.load_stratum(self.root,self.stratum)
 def test_boolean_admission_checks_cannot_be_numeric_or_missing(self):
  card=tomllib.loads(self.stratum.read_text())['card'][0];path=self.root/card['admission'];original=json.loads(path.read_text());text=self.stratum.read_text()
  for bad in [1,False,None]:
   report=json.loads(json.dumps(original))
   if bad is None:del report['checks']['max-auto-empty-fails']
   else:report['checks']['max-auto-empty-fails']=bad
   path.write_text(json.dumps(report));new=hashlib.sha256(path.read_bytes()).hexdigest();self.stratum.write_text(text.replace(card['admission_sha256'],new))
   with self.subTest(value=bad),self.assertRaisesRegex(ValueError,'all native'):module.load_stratum(self.root,self.stratum)
 def test_cluster_pairing_cannot_silently_make40_independent_units(self):
  text=self.stratum.read_text().replace('cluster = "accepted-ledger"','cluster = "first-rejection"',1);self.stratum.write_text(text)
  with self.assertRaisesRegex(ValueError,'paired-language'):module.load_stratum(self.root,self.stratum)
 def test_cross_language_public_problem_already_drawn_is_not_unused(self):
  pools=tomllib.loads((self.root/'bench/public/POOLS.toml').read_text());used={int(m[1]) for d in pools.get('draw',[]) for c in d.get('cards',[]) if (m:=re.fullmatch(r'[dv]p\d+-he(\d+)',c))}
  sys.path.insert(0,str(ROOT/'scripts'));from dvl import bench
  eligible=bench.lab_members(self.root,'humaneval-verus','R12')
  candidate=next(t for t in eligible if int(re.search(r'human_eval_(\d+)',t)[1]) in used)
  current=next(r for r in tomllib.loads(self.stratum.read_text())['unused_public'] if r['set']=='humaneval-verus')
  self.stratum.write_text(self.stratum.read_text().replace('task = '+json.dumps(current['task']),'task = '+json.dumps(candidate),1))
  with self.assertRaisesRegex(ValueError,'another language'):module.load_stratum(self.root,self.stratum)

if __name__=='__main__':unittest.main()
