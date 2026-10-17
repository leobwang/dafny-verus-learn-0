#!/usr/bin/env python3
"""Build locked R12 batch plans from an explicitly admitted 40-task stratum.

This performs no model/provider/container execution, creates no grade row and
never discovers reference completions. Separate plans need separate exact plan
bindings and genuine matching pre-registration grades before frozen Batch.open.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import re
import sys
import tomllib

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'harness'))
from fvh.budget import CLAUDE,QWEN
POLICIES=(('independent','R12Independent'),('repair','R12Repair'),('best','R12BestFirst'),('best-raw','R12BestFirstRaw'))


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def course_path(root,value):
    if not isinstance(value,str) or not value or Path(value).is_absolute() or '..' in Path(value).parts:
        raise ValueError('one course-relative path required')
    path=root/value
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):raise ValueError('missing or escaping course file')
    if any(p.lower() in ('solutions','hidden','leak_patterns') for p in path.relative_to(root).parts):raise ValueError('reference material cannot enter a plan')
    return path


def load_stratum(root,path):
    data=tomllib.loads(path.read_text())
    if data.get('schema')!=1 or data.get('lab')!='R12':raise ValueError('R12 stratum schema1 required')
    cards=data.get('card',[])
    if len(cards)!=40 or Counter(c.get('lang') for c in cards)!=Counter({'dafny':20,'verus':20}):raise ValueError('exactly40admitted cards,20per language required')
    clusters={c.get('cluster') for c in cards}
    if data.get('cluster_rule')!='paired-language-original-algorithm' or data.get('analysis_clusters')!=20 or len(clusters)!=20 or any(Counter(c['lang'] for c in cards if c.get('cluster')==cluster)!=Counter({'dafny':1,'verus':1}) for cluster in clusters):raise ValueError('twenty explicit paired-language algorithm clusters required')
    ids=set();hashes=set()
    for card in cards:
        name=card.get('id')
        if not isinstance(name,str) or not re.fullmatch(r'[a-z][a-z0-9-]*',name) or name in ids:raise ValueError('unique lowercase card id required')
        ids.add(name);source=course_path(root,card.get('path'))
        if source.suffix!=('.dfy' if card['lang']=='dafny' else '.rs'):raise ValueError('task language/suffix mismatch')
        if not card['path'].startswith('bench/local/r/'):raise ValueError('R local task forms only')
        if digest(source)!=card.get('source_sha256') or card['source_sha256'] in hashes:raise ValueError('stale or duplicate task source')
        hashes.add(card['source_sha256'])
        for key in ('origin','exposure','cluster','statement'):
            if not isinstance(card.get(key),str) or not card[key].strip():raise ValueError('task provenance, exposure, cluster and statement required')
        report=course_path(root,card.get('admission'))
        if digest(report)!=card.get('admission_sha256'):raise ValueError('stale task admission report')
        evidence=json.loads(report.read_text())
        if evidence.get('source_sha256')!=card['source_sha256'] or evidence.get('status')!='admitted':raise ValueError('admission not bound to original source')
        checks=evidence.get('checks')
        expected={'baseline-proof-fails','max-auto-empty-fails','reference-gate','reference-three-seeds','wrong-hints-fail','audit-clean','original-model-code-frame'}
        if not isinstance(checks,dict) or set(checks)!=expected or any(type(x) is not bool or x is not True for x in checks.values()):
            raise ValueError('all native admission controls must precede plan construction')
    unused=data.get('unused_public',[])
    if len(unused)!=10 or Counter(Path(row.get('task','')).suffix for row in unused)!=Counter({'.dfy':5,'.rs':5}):raise ValueError('unused pinned public slice must contain5tasks per language')
    pools_path=course_path(root,data.get('pools'))
    if digest(pools_path)!=data.get('pools_sha256'):raise ValueError('public pool metadata changed; recheck unused slice')
    pools=tomllib.loads(pools_path.read_text())
    sys.path.insert(0,str(ROOT/'scripts'))
    from dvl import bench
    seen_problems={int(m[1]) for d in pools.get('draw',[]) for card in d.get('cards',[]) if (m:=re.fullmatch(r'[dv]p\d+-he(\d+)',card))}
    selected=set()
    for row in unused:
        key=(row.get('set'),row.get('task'))
        pool=next((p for p in pools.get('pool',[]) if p.get('set')==key[0]),None)
        if pool is None or row.get('pool_sha256')!=pool.get('pool_sha256') or key[1] not in pool.get('tasks',[]) or key[1] not in bench.lab_members(root,key[0],'R12') or key in selected:raise ValueError('public slice must be unique, pinned and unused by prior draws')
        problem=re.match(r'human_eval_(\d+)(?:_|\.)',Path(key[1]).name)
        if problem and int(problem[1]) in seen_problems:raise ValueError('public task duplicates a previously drawn HumanEval problem in another language/set')
        selected.add(key)
    return cards


def render_plan(cards,*,family,seed,repeats,arms):
    q=lambda value:json.dumps(value,ensure_ascii=False)
    s='# Generated R12 plan; creating this file does not unlock execution.\n'
    s+='lab = "R12"\nseed = '+str(seed)+'\nrepeats = '+str(repeats)+'\nattempts = 1\nmax_reissue = 3\nlever_check = true\n'
    s+='tasks = '+q([c['id'] for c in cards])+'\n'
    s+='system = '+q((ROOT/'tools/R12/lab_system.md').read_text())+'\ninstructions = '+q((ROOT/'tools/R12/lab_instructions.md').read_text())+'\n'
    for card in cards:s+='\n[task.'+q(card['id'])+']\npath = '+q(card['path'])+'\nstatement = '+q('R12_TASK_SHA256: '+card['source_sha256']+'\nR12_CLUSTER: '+card['cluster']+'\nR12_EXPOSURE: '+card['exposure']+'\n'+card['statement'])+'\n'
    for name,policy in arms:
        s+='\n[[arm]]\nname = '+q(name)+'\nfamily = '+q(family)+'\nrounds = 10\nturns = 12\npolicy = '+q('fvh_r.engine:'+policy)+'\nconstruct = "seeded"\nlab_code = "preserve"\nacceptance = "verify"\n'
    return s


def build_plans(cards,*,seed,subset_seed):
    if type(seed) is not int or seed<0 or type(subset_seed) is not int or subset_seed<0:raise ValueError('nonnegative explicit integer seeds required')
    if len(cards)!=40 or Counter(c['lang'] for c in cards)!=Counter({'dafny':20,'verus':20}):raise ValueError('main stratum must contain40tasks,20per language')
    rng=random.Random(subset_seed);subset=[]
    for lang in ('dafny','verus'):
        population=sorted([c for c in cards if c['lang']==lang],key=lambda c:c['id'])
        subset.extend(rng.sample(population,5))
    return {QWEN:render_plan(cards,family=QWEN,seed=seed,repeats=3,arms=POLICIES),CLAUDE:render_plan(subset,family=CLAUDE,seed=seed+1,repeats=1,arms=(('best','R12BestFirst'),))},[c['id'] for c in subset]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stratum',type=Path,default=ROOT/'bench/local/r/labalpha/STRATUM.toml')
    ap.add_argument('--seed',type=int,required=True)
    ap.add_argument('--subset-seed',type=int,required=True)
    ap.add_argument('--write-dir',type=Path,required=True)
    args=ap.parse_args()
    try:
        cards=load_stratum(ROOT,args.stratum);plans,subset=build_plans(cards,seed=args.seed,subset_seed=args.subset_seed)
        # Validate frozen syntax before creating reviewable plan files. No Batch.open.
        sys.path[:0]=[str(ROOT/'harness'),str(ROOT/'harness/r')]
        from fvh import batch
        import tempfile
        with tempfile.TemporaryDirectory(prefix='dvl0-r12-plan-check-') as temporary:
            for name,text in plans.items():
                p=Path(temporary)/(name+'.toml');p.write_text(text);plan=batch.load_plan(p,ROOT)
                if plan.lever_check is not True or any(a.caps.get('turns')!=12 or a.rounds!=10 for a in plan.arms):raise ValueError('unexpected frozen plan scope')
        args.write_dir.mkdir(parents=True,exist_ok=True)
        targets=[args.write_dir/(name+'.toml') for name in plans]+[args.write_dir/'bindings.json']
        if any(p.exists() for p in targets):raise ValueError('refuse to overwrite existing plan/binding; choose a fresh directory')
        binding={'scope':'reviewable locked plans; no run, grade or budget event','stratum_sha256':digest(args.stratum),'subset_seed':args.subset_seed,'claude_subset':subset,'qwen':{'runs':480,'generation_calls':4800},'claude':{'runs':10,'generation_calls':100,'sentinel_ceiling':10},'inputs':{}}
        for path in ['harness/r/fvh_r/engine.py','tools/R12/lab_system.md','tools/R12/lab_instructions.md','tools/R12/plan.py']:
            binding['inputs'][path]=digest(ROOT/path)
        for name,text in plans.items():
            p=args.write_dir/(name+'.toml');p.write_text(text);binding[name]['plan_sha256']=digest(p);print(name+': '+str(p)+' sha256 '+digest(p))
        (args.write_dir/'bindings.json').write_text(json.dumps(binding,indent=2,sort_keys=True)+'\n')
        print('Plans remain locked until each exact digest has a genuine matching pre-registration grade.')
        return 0
    except (OSError,ValueError,KeyError,TypeError) as error:
        print('R12 plan refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
