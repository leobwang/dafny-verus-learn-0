#!/usr/bin/env python3
"""Provided bounded R14 battery executor. Analyzer output is advisory data.

Complete the native hand targets and the toolsmith first. Every assertion keeps
its original model, contract and executable frame. Fixed candidate options only;
all closure comes from actual full gates, source frames and native audits.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[2]
SITE='// R14_PROOF_SITE'

def digest(data):return hashlib.sha256(data).hexdigest()

def command(args,where):
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True)
    where.parent.mkdir(parents=True,exist_ok=True)
    where.write_text(p.stdout+p.stderr)
    return p

def gate(path,where,*,feedback=False):
    argv=[str(ROOT/'scripts/vcheck'),'--json','--module','R14']
    if not feedback:argv.append('--gate')
    argv.append(str(path))
    if feedback:argv+=['--','--triggers-mode','verbose']
    p=command(argv,where)
    try:doc=json.loads(p.stdout)
    except json.JSONDecodeError:raise RuntimeError('native wrapper did not supply a Result; see '+str(where))
    return p.returncode,doc

def clean(code,doc):
    return code==0 and doc.get('verdict')=='verified' and doc.get('stage')=='verify' and doc.get('exit_code')==0 and type(doc.get('verified_count')) is int and doc['verified_count']>0 and not doc.get('holes') and not doc.get('findings') and not any(d.get('severity')=='error' for d in doc.get('diagnostics',[]))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--core-d',type=Path,default=ROOT/'dafny/R/R14_Smt/std/R14_Smt.dfy')
    ap.add_argument('--core-v',type=Path,default=ROOT/'verus/r/r14_smt/src/lib.rs')
    ap.add_argument('--analyzer',type=Path,default=ROOT/'tools/R14/trigscan.py')
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    pinned=json.loads((ROOT/'expected/R14.battery.json').read_text());catalogue=(ROOT/'tools/R14/battery.json').read_bytes()
    if digest(catalogue)!=pinned['catalog_sha256']:raise ValueError('original battery catalogue changed')
    cards=json.loads(catalogue)['cards']
    if len(cards)!=12 or len({c['id'] for c in cards})!=12:raise ValueError('battery must retain12unique assertions')
    if any(c['template'].count(SITE)!=1 or digest(c['template'].encode())!=pinned['templates'].get(c['id']) for c in cards):raise ValueError('original assertion/frame changed')
    p=command([str(ROOT/'scripts/specfreeze'),'--check','R14'],out/'course-frame.log')
    if p.returncode:raise ValueError('the course statement/model freeze does not match')
    # Separate processes keep the analyzer out of the executor's Python state.
    p=command([sys.executable,str(ROOT/'tools/R14/test_trigscan.py'),'--implementation',str(a.analyzer.resolve())],out/'actor-contract.log')
    if p.returncode:raise RuntimeError('toolsmith contract incomplete; see actor-contract.log')
    frozen=[ROOT/'scripts/vcheck',ROOT/'scripts/vaudit',ROOT/'scripts/specfreeze',ROOT/'MODULES.toml',ROOT/'tools/R14/battery.json',ROOT/'scripts/dvl/pins.toml']+list((ROOT/'scripts').rglob('*.py'))+list((ROOT/'expected').glob('R14.*'))+list((ROOT/'dafny/options').glob('*.toml'))+list((ROOT/'dafny/given/R').glob('RG_A[1-4]*.dfy'))
    for layer in ['rg_re_a1','rg_re_a1b','rg_re_a2','rg_re_a3','rg_re_a4']:
        frozen+=list((ROOT/'verus/given'/layer).rglob('*.rs'))+[ROOT/'verus/given'/layer/'Cargo.toml']
    original_frozen={str(p):digest(p.read_bytes()) for p in frozen}
    cores={};origins={}
    for lang,path,shipped in [('dafny',a.core_d,ROOT/'dafny/R/R14_Smt/std/R14_Smt.dfy'),('verus',a.core_v,ROOT/'verus/r/r14_smt/src/lib.rs')]:
        path=path.resolve();origins[path]=path.read_bytes();cores[lang]=origins[path].decode()
        if SITE in cores[lang]:raise ValueError('core contains a reserved battery proof-site marker')
        p=command([str(ROOT/'scripts/specfreeze'),'--against',str(shipped),str(path)],out/('core-frame-'+lang+'.log'))
        if p.returncode:raise ValueError('core does not preserve the original statement/model frame')
        code,doc=gate(path,out/('core-gate-'+lang+'.log'))
        if not clean(code,doc):raise RuntimeError('complete the zero-hole native core before the battery')
        p=command([str(ROOT/'scripts/vaudit'),str(path)],out/('core-audit-'+lang+'.log'))
        if p.returncode:raise RuntimeError('original core audit failed')
    rows=[]
    def stable():
        if any(p.read_bytes()!=blob for p,blob in origins.items()):raise ValueError('original core changed during the run')
        if any(digest(Path(p).read_bytes())!=sha for p,sha in original_frozen.items()):raise ValueError('executor or frozen inputs changed during analysis')
    with tempfile.TemporaryDirectory(prefix='r14-battery-') as tmp:
        for card in cards:
            stable();dest=out/card['id'];dest.mkdir(exist_ok=True)
            suffix='.dfy' if card['lang']=='dafny' else '.rs';path=Path(tmp)/(card['id']+suffix)
            base=cores[card['lang']]+card['template'];original=base.replace(SITE,'',1)
            path.write_text(original);(dest/('baseline'+suffix)).write_text(original)
            code,baseline=gate(path,dest/'baseline.log')
            if clean(code,baseline):raise ValueError('already closed baseline; re-admit '+card['id'])
            if baseline.get('verdict')!='failed' or baseline.get('stage')!='verify' or baseline.get('holes'):raise ValueError('baseline did not reach the original zero-hole proof question')
            feedback=b'';source_id=str(path)
            if card['lang']=='verus':
                _,note=gate(path,dest/'native-feedback.log',feedback=True)
                raw=Path(note['raw_dir']);logs=list(raw.glob('*-target/stderr.txt'))
                if len(logs)==1:feedback=logs[0].read_bytes()
                if note.get('cmd') and len(note['cmd'])>1:source_id=str(note['cmd'][1])
            # Dafny's unavailable trigger-note channel stays explicitly unavailable.
            (dest/'stderr.jsonl').write_bytes(feedback)
            (dest/'source.trace').write_text(original)
            binding={'schema':1,'source_id':source_id,'source_sha256':digest(original.encode()),'stderr_sha256':digest(feedback)}
            (dest/'binding.json').write_text(json.dumps(binding,indent=2)+'\n')
            p=command([sys.executable,str(a.analyzer.resolve()),'--binding',str(dest/'binding.json'),'--source',str(dest/'source.trace'),'--stderr',str(dest/'stderr.jsonl')],dest/'analysis.json')
            if p.returncode:raise RuntimeError('advisory analyzer failed; no proof success inferred')
            analysis=json.loads(p.stdout);stable()
            # Advisory terms only prioritize fixed choices; they are never source code.
            choices=[x for x in card['options'] if x!='none']
            if analysis.get('located_term_count',0)>0 and 'lemma' in choices:choices.sort(key=lambda x:x!='lemma')
            row={'id':card['id'],'lang':card['lang'],'baseline':baseline,'source_sha256':digest(original.encode()),'analysis_availability':analysis.get('availability','unavailable'),'attempts':[],'passed':False}
            for label in choices:
                text=base.replace(SITE,card['options'][label],1);path.write_text(text)
                code,doc=gate(path,dest/(label+'.log'));stable()
                row['attempts'].append({'choice':label,'source_sha256':digest(text.encode()),'native':doc})
                if not clean(code,doc):continue
                symbol='R14_BatteryCell.BatteryCellR14' if card['lang']=='dafny' else 'battery_cell_r14'
                if doc.get('per_symbol',{}).get(symbol)!='verified':raise ValueError('original battery assertion has no verified symbol evidence')
                (dest/('completed'+suffix)).write_text(text)
                p=command([str(ROOT/'scripts/vaudit'),str(path)],dest/'audit.log')
                if p.returncode:raise ValueError('completed assertion audit failed')
                row['passed']=True;row['choice']=label;break
            rows.append(row);(out/'report.json').write_text(json.dumps({'scope':'12 exposed source-bound author/learner assertions; no live actor/model result','core_sha256':{str(p):digest(x) for p,x in origins.items()},'results':rows},indent=2)+'\n')
            print(card['id'], 'closed' if row['passed'] else 'unresolved',flush=True)
            if not row['passed']:raise RuntimeError('bounded options did not close the original assertion')
    stable();print('12/12original assertions closed and audited; advisory reports are not proof verdicts')
    return 0
if __name__=='__main__':raise SystemExit(main())
