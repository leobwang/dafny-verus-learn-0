#!/usr/bin/env python3
"""Gate and compile actual R12 native clients against fixed finite observations.

Defaults read learner implementations only. Flag arrays are input data, not
proof evidence. Every present source is gated before compilation; no Dafny
included implementation is assumed. Use a capped native lane.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile


def main():
    root=Path(__file__).resolve().parents[2]
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dafny-file',type=Path,default=root/'dafny/R/R12_Driving/std/R12_Driving.dfy')
    ap.add_argument('--verus-file',type=Path,default=root/'verus/r/r12_driving/src/lib.rs')
    ap.add_argument('--out',type=Path)
    args=ap.parse_args();out=args.out or Path(tempfile.mkdtemp(prefix='dvl0-r12-clients-'));out.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(root/'tests/wrappers'));import test_tools_common as common
    core=common.load_script('vcheck')
    cases=[]
    for length in range(6):
        for mask in range(1<<length):
            flags=[bool(mask&(1<<i)) for i in range(length)]
            cases.append({'flags':flags,'count':sum(flags),'first':flags.index(False) if False in flags else length})
    (out/'expected.json').write_text(json.dumps(cases,indent=2)+'\n')
    report={'scope':'finite actual-source compiled clients, not proof-result adjudication','flag_cases':len(cases),'budget_cases':3,'inputs':{},'results':{}}
    for p in [args.dafny_file,args.verus_file,Path(__file__)]:report['inputs'][str(p.resolve())]=hashlib.sha256(p.read_bytes()).hexdigest()
    # Actual implementation in the root: Dafny does not verify included bodies.
    d=args.dafny_file.read_text()+'''\nmodule R12_RuntimeObservations {
 import P=R12_HintSites
'''
    v=args.verus_file.read_text()+'''\n#[cfg(test)] mod r12_observations {use super::*;
'''
    for i,row in enumerate(cases):
        flags=str(row['flags']).lower()
        d+=f' @Test method Case{i:03}() {{var flags:seq<bool>:={flags};var count:=P.CountAcceptedR12(flags);var first:=P.FirstRejectionR12(flags);expect count=={row["count"]} && first=={row["first"]};}}\n'
        v+=f' #[test] fn case_{i:03}() {{let flags=vec!{flags};assert_eq!(count_accepted_r12(&flags),{row["count"]});assert_eq!(first_rejection_r12(&flags),{row["first"]});}}\n'
    for i,(spent,limit) in enumerate([(0,0),(0,7),(3,7)]):
        d+=f' @Test method Budget{i}() {{var remaining:=P.RemainingBudgetR12({spent},{limit});expect remaining=={limit-spent};}}\n'
        v+=f' #[test] fn budget_{i}() {{assert_eq!(remaining_budget_r12({spent},{limit}),{limit-spent});}}\n'
    d+='}\n';v+='}\n';dp=out/'observations.dfy';dp.write_text(d);vp=out/'observations-verus';(vp/'src').mkdir(parents=True,exist_ok=True);(vp/'src/lib.rs').write_text(v)
    (vp/'Cargo.toml').write_text('[package]\nname="r12_runtime_observations"\nversion="0.1.0"\nedition="2021"\nbuild=false\n[dependencies]\nvstd="=0.0.0-2026-09-20-0158"\n[package.metadata.verus]\nverify=true\n[workspace]\n')
    ok=True
    for lang,path,lib in [('d',dp,core.D),('v',vp,core.V)]:
        gate=lib.verify(str(path),gate=True);row={'gate':gate.to_dict()};report['results'][lang]=row;passed=gate.verdict=='verified' and not gate.holes
        if passed:
            result=lib.test(str(path));row['test']=result.to_dict();passed=result.verdict=='verified' and result.stage=='test' and not result.holes and len(result.per_symbol)>=66 and all(v=='passed' for v in result.per_symbol.values())
        row['passed']=passed;ok &= passed;print(lang+': actual-source compiled clients '+('passed' if passed else 'failed'),flush=True);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Retained finite client evidence: '+str(out))
    return 0 if ok else 1


if __name__=='__main__':raise SystemExit(main())
