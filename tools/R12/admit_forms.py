#!/usr/bin/env python3
"""Check fixed R12 proof sites with the native parsers and executable skeleton.

Defaults read explicit learner/course forms only. No completion or reference is
located. Every site must leave native declarations/models and executable tokens
unchanged when probed, and every approved callee must be a local proof declaration.
The optional native baseline check must fail at verify with zero unfinished holes.
This does not prove that a good completion exists or unlock a live lab run.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def analyze_form(path,core,source_task):
    text=path.read_text();task,spans=source_task(text)
    lang='d' if path.suffix=='.dfy' else 'v' if path.suffix=='.rs' else None
    if lang is None:raise ValueError('one Dafny or Verus form file required')
    native_lang='dafny' if lang=='d' else 'verus'
    if lang=='d':
        src=core.D.parse_source(text,str(path));decls=src.decls
        proof={d.name for d in decls if d.kind in ['lemma','colemma'] or (d.kind=='method' and 'ghost' in d.modifiers)}
        code={d.name for d in decls if d.kind in ['method','constructor'] and 'ghost' not in d.modifiers}
    else:
        src=core.V.vs.parse(text);decls=[d for d in src.walk() if d.kind=='fn']
        proof={d.name for d in decls if d.mode=='proof'}
        code={d.name for d in decls if d.mode=='exec'}
    statement=core.statement_table(path,lang,text=text)[0]
    skeleton=core.LC.skeleton(text,native_lang,annotations=True,target='r12_unused_target',witness='r12_unused_witness')
    checked=[]
    for site in task.sites:
        if site.kind=='expr':probes=['false']
        else:
            if not set(site.callees)<=proof or set(site.callees)&code:raise ValueError(f'{site.name}: callees must be unambiguous local proof declarations')
            probes=[name+'();' for name in site.callees]
        for replacement in probes:
            variant=text.replace(site.marker,replacement,1)
            if core.statement_table(path,lang,text=variant)[0]!=statement:raise ValueError(f'{site.name}: site changes a frozen declaration or model')
            got=core.LC.skeleton(variant,native_lang,annotations=True,target='r12_unused_target',witness='r12_unused_witness')
            if got!=skeleton:raise ValueError(f'{site.name}: site changes executable code')
        checked.append({'name':site.name,'kind':site.kind,'callee_bindings':list(site.callees)})
    fingerprint=lambda value:hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
    return {'source':str(path.resolve()),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'lang':native_lang,'sites':checked,'statement_sha256':fingerprint(statement),'code_sha256':fingerprint(skeleton)}


def main():
    root=Path(__file__).resolve().parents[2]
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('forms',type=Path,nargs='+')
    ap.add_argument('--native',action='store_true',help='also require a zero-hole failing proof-stage baseline and clean audit')
    ap.add_argument('--out',type=Path)
    args=ap.parse_args();out=args.out or Path(tempfile.mkdtemp(prefix='dvl0-r12-forms-'));out.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(root/'tests/wrappers'));import test_tools_common as common
    core=common.load_script('vcheck')
    sys.path.insert(0,str(root/'harness'));sys.path.insert(0,str(root/'harness/r'))
    from fvh_r.engine import source_task
    rows=[];ok=True
    for index,path in enumerate(args.forms):
        row={'source':str(path.resolve())}
        try:
            row=analyze_form(path,core,source_task)
            if args.native:
                for name,cmd in [('baseline',['scripts/vcheck','--module','R12','--gate','--json',str(path.resolve())]),('audit',['scripts/vaudit','--json',str(path.resolve())])]:
                    p=subprocess.run(cmd,cwd=root,capture_output=True,text=True);(out/(str(index)+'-'+name+'.stdout')).write_text(p.stdout);(out/(str(index)+'-'+name+'.stderr')).write_text(p.stderr)
                    document=json.loads(p.stdout);row[name]=document;row[name+'_exit']=p.returncode
                d=row['baseline']
                if row['baseline_exit']!=core.EXIT_FAIL or d.get('verdict')!='failed' or d.get('stage')!='verify' or d.get('holes'):raise ValueError('baseline must fail at verify with zero holes; this is not an admissible form')
                audit=row['audit']
                if row['audit_exit']!=0 or not isinstance(audit,dict) or not isinstance(audit.get('findings'),list) or audit['findings']:raise ValueError('baseline assumption audit must be clean and complete')
            row['status']='native-baseline-and-frame-checked' if args.native else 'static-frame-checked'
        except (OSError,ValueError,TypeError,KeyError) as e:
            row['status']='rejected';row['reason']=str(e);ok=False
        rows.append(row);print(path.name+': '+row['status'],flush=True)
        (out/'report.json').write_text(json.dumps({'scope':'form frames/baseline only; completion, three seeds, negative controls and lab locks remain separate','results':rows},indent=2)+'\n')
    print('Retained form-admission evidence: '+str(out))
    return 0 if ok else 1


if __name__=='__main__':raise SystemExit(main())
