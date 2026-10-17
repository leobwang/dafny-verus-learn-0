#!/usr/bin/env python3
"""Finite compiled observations of explicit R13 repair sources, after full gates.

Defaults are learner files. No reference lookup. The Dafny client embeds actual
source in its root (include alone would not verify its bodies); Rust verifies
literal preconditions inside verus! and executes the same source's functions.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[2]

def invoke(args):
    p=subprocess.run([str(ROOT/'scripts/vcheck'),*args],cwd=ROOT,capture_output=True,text=True)
    try:doc=json.loads(p.stdout)
    except json.JSONDecodeError:raise RuntimeError(p.stdout+p.stderr)
    return p.returncode,doc

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--d',type=Path,default=ROOT/'dafny/R/R13_Pipelines/std/R13_Pipelines.dfy')
    ap.add_argument('--v',type=Path,default=ROOT/'verus/r/r13_pipelines/src/lib.rs')
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    mx=2**64-1
    sums=[(0,0),(0,mx),(mx,0),(mx,1),(1,mx),(mx,mx),(mx-2,1),(mx-2,3),(17,29)]
    # usize boundary inputs remain valid under both verifier word sizes.
    # u64 saturation still exercises its full64bit boundary. No sum is executed in Rust
    # just to calculate the oracle: expected values are computed here as integers.
    portable_max=2**32-1
    ranges=[(0,0,0),(0,1,0),(1,0,0),(0,portable_max,portable_max),(portable_max,0,portable_max),(portable_max,1,portable_max),(portable_max,portable_max,portable_max),(2,3,5),(3,3,5)]
    indices=[(0,1),(1,1),(17,4),(2,4),(portable_max,portable_max)]
    chars=[('a','b'),('z','z'),('\u03bb','\u03a9')]
    rows=[]
    with tempfile.TemporaryDirectory(prefix='r13-compiled-') as tmp:
        for lang,path in [('d',a.d.resolve()),('v',a.v.resolve())]:
            original=path.read_bytes();sha=hashlib.sha256(original).hexdigest()
            code,gate=invoke(['--json','--module','R13','--gate',str(path)])
            row={'lang':lang,'source':str(path),'sha256':sha,'gate':gate,'compiled_cases':0}
            if code or gate.get('verdict')!='verified' or gate.get('holes'):
                row['status']='gate-failed';rows.append(row);continue
            calls=[]
            for n,(x,y) in enumerate(sums):
                z=min(x+y,mx)
                calls.append(f'var s{n}:=SaturatingSumR13({x},{y});expect s{n}=={z};' if lang=='d' else f'let s{n}=saturating_sum_r13({x}u64,{y}u64);assert(s{n}=={z}u64);')
            for n,(x,y,z) in enumerate(ranges):
                want=str(x+y<=z).lower()
                calls.append(f'var f{n}:=RangeFitsR13({x},{y},{z});expect f{n}=={want};' if lang=='d' else f'let f{n}=range_fits_r13({x}usize,{y}usize,{z}usize);assert(f{n}=={want});')
            for n,(x,y) in enumerate(indices):
                z=min(x,y-1)
                calls.append(f'var i{n}:=ClampIndexR13({x},{y});expect i{n}=={z};' if lang=='d' else f'let i{n}=clamp_index_r13({x}usize,{y}usize);assert(i{n}=={z}usize);')
            for n,(x,y) in enumerate(chars):
                calls.append(f"var w{n}:=PairWitnessR13('{x}','{y}');expect w{n}==['{x}','{y}'];" if lang=='d' else f"let w{n}=pair_witness_r13('{x}','{y}');assert(w{n}.len()==2 && w{n}[0]=='{x}' && w{n}[1]=='{y}');")
            text=original.decode()
            if lang=='d':
                text+='\nmodule R13_CompiledClient {import opened R13_Repairs\n method {:test} ObserveR13(){\n'+'\n'.join(calls)+'\n}}\n'
            else:
                # A proof-context exec client checks literals and contracts before
                # Rust's native test harness runs it. No arbitrary-source oracle.
                proof_calls=calls[:-len(chars)]+[f"let w{n}=pair_witness_r13('{x}','{y}');assert(w{n}.len()==2);" for n,(x,y) in enumerate(chars)]
                text+='\nverus! {pub fn observe_compiled_r13(){\n'+'\n'.join(proof_calls)+'\n}}\n#[test] fn observed_r13(){observe_compiled_r13();\n'+'\n'.join(calls).replace('assert(', 'assert!(')+'\n}\n'
            unit=Path(tmp)/lang;unit.mkdir(exist_ok=True)
            if lang=='d':
                p=unit/'client.dfy'
                config=(ROOT/'dafny/R/R13_Pipelines/std/dfyconfig.toml').read_text().replace('../../../given/',str(ROOT/'dafny/given')+'/')
                (unit/'dfyconfig.toml').write_text(config)
            else:
                p=unit/'src/lib.rs';p.parent.mkdir(exist_ok=True)
                config=(ROOT/'verus/r/r13_pipelines/Cargo.toml').read_text().replace('r13_pipelines','r13_runtime_observations').replace('../../given/',str(ROOT/'verus/given')+'/')+'\n[workspace]\n'
                (unit/'Cargo.toml').write_text(config)
            p.write_text(text)
            (a.output/('client.dfy' if lang=='d' else 'client.rs')).write_text(text)
            code,test=invoke(['--json','--test',str(unit)])
            row['compiled']=test;row['status']='passed' if code==0 and test.get('verdict')=='verified' and test.get('stage')=='test' else 'failed'
            row['compiled_cases']=len(calls) if row['status']=='passed' else 0
            if path.read_bytes()!=original:raise RuntimeError('original source changed during observations')
            rows.append(row)
    (a.output/'report.json').write_text(json.dumps(rows,indent=2)+'\n')
    for row in rows:print(row['lang'],row['status'],row['compiled_cases'])
    return 0 if all(row['status']=='passed' for row in rows) else 1
if __name__=='__main__':raise SystemExit(main())
