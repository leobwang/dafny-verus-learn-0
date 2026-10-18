#!/usr/bin/env python3
"""Check fixed compiled frontend AST/span/error/cap observations.

Defaults read only the learner's two hand files. Complete their typed tasks
first. Exact public cases are exposed evidence, not a hidden or unseen set.
This finite check does not establish a general grammar theorem.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import tomllib

DAFNY_DRIVER = 'module R09_FrontendObservation {\n import F = R09_Frontend\n import opened RG_A1_Re\n import opened R09_Budget\n import opened RG_A3_Syntax\n method Describe(t:Syn)\n  decreases t\n {\n  print t.lo,",",t.hi,"#";\n  match t\n  case SEps(_,_) => print "E";\n  case SChr(c,_,_) => print "C",c as int;\n  case SClass(xs,_,_) =>\n   var rs := RG_A2_Deriv.ClassRanges(xs);\n   print "K[";\n   for j:=0 to |rs| { print rs[j].lo as int,":",rs[j].hi as int,";"; }\n   print "]";\n  case SAlt(a,c,_,_) => print "A(";Describe(a);print ",";Describe(c);print ")";\n  case SCat(a,c,_,_) => print "T(";Describe(a);print ",";Describe(c);print ")";\n  case SStar(a,_,_) => print "S(";Describe(a);print ")";\n  case SPlus(a,_,_) => print "P(";Describe(a);print ")";\n  case SOpt(a,_,_) => print "O(";Describe(a);print ")";\n  case SRep(a,n,m,_,_) => print "R",n,":",m,"(";Describe(a);print ")";\n  case SGroup(a,_,_) => print "G(";Describe(a);print ")";\n }\n method CountActualR09(r:Re) returns (n:nat)\n  ensures n==NodeCount(r)\n  decreases r\n {\n  match r\n  case Empty => n:=1;\n  case Eps => n:=1;\n  case Chr(_) => n:=1;\n  case Alt(a,b) => var x:=CountActualR09(a);var y:=CountActualR09(b);n:=1+x+y;\n  case Cat(a,b) => var x:=CountActualR09(a);var y:=CountActualR09(b);n:=1+x+y;\n  case Star(a) => var x:=CountActualR09(a);n:=1+x;\n }\n method ProbeOneR09(index:nat,pattern:seq<char>,cap:CostU32) {\n  var r:=F.FrontendR09(pattern,cap);\n  print "CASE ",index," ";\n  if r.Err? {print "ERR",r.pos;} else {Describe(r.value.0);var n:=CountActualR09(r.value.1);print "|N",n;}\n  print " END\\n";\n }\n'
VERUS_DRIVER = '#[cfg(test)]\nmod port_tests {\n use super::*;\n fn record(t:&Syn)->String {\n  let body=match &t.node {\n   SyntaxKind::Eps=>"E".to_string(),\n   SyntaxKind::Chr(c)=>format!("C{}",*c as u32),\n   SyntaxKind::Class(xs)=>{\n    let mut s="K[".to_string();for &(lo,hi) in xs.ranges().iter() {s+=&format!("{}:{};",lo,hi);}s+="]";s\n   },\n   SyntaxKind::Alt(a,b)=>format!("A({},{})",record(a),record(b)),\n   SyntaxKind::Cat(a,b)=>format!("T({},{})",record(a),record(b)),\n   SyntaxKind::Star(a)=>format!("S({})",record(a)),\n   SyntaxKind::Plus(a)=>format!("P({})",record(a)),\n   SyntaxKind::Opt(a)=>format!("O({})",record(a)),\n   SyntaxKind::RepRange(a,n,m)=>format!("R{}:{}({})",n,m,record(a)),\n   SyntaxKind::Group(a)=>format!("G({})",record(a)),\n  };format!("{},{}#{}",t.span.lo,t.span.hi,body)\n }\n fn count_actual(r:&Re)->u64 {match r {\n Re::Empty|Re::Eps|Re::Chr(_)=>1,\n Re::Alt(a,b)|Re::Cat(a,b)=>1+count_actual(a)+count_actual(b),\n Re::Star(a)=>1+count_actual(a),\n }}\n fn run_case(input:&str,cap:u32,expected:&str) {\n let chars:Vec<char>=input.chars().collect();let actual=match frontend_r09(&chars,cap) {\n Ok((tree,lowered))=>format!("{}|N{}",record(&tree),count_actual(&lowered)),Err(e)=>format!("ERR{}",e.pos),};\n assert_eq!(actual,expected,"input {:?}, cap {}",input,cap);\n }\n'

def run(root:Path,dafny_file:Path,verus_file:Path,out:Path)->int:
    sys.path.insert(0,str(root/'tests/wrappers'))
    import test_tools_common as common
    core=common.load_script('vcheck')
    cases_file=root/'tools/R09/frontend_cases.json'
    rows=json.loads(cases_file.read_text());assert rows
    out.mkdir(parents=True,exist_ok=True)
    report={'schema':1,'claim':'finite compiled frontend observations','cases':len(rows),'inputs':{},'results':{}}
    for path in [dafny_file,verus_file,cases_file,Path(__file__).resolve()]:
        report['inputs'][str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
    names=['RG_A1_Re.dfy','RG_A1b_Facts.dfy','RG_A2_Deriv.dfy','RG_A2_MatcherStatement.dfy','RG_A3_Syntax.dfy']
    d=''.join('include '+json.dumps(str(root/'dafny/given/R'/name))+'\n' for name in names)
    d+='include '+json.dumps(str(dafny_file))+'\n'+DAFNY_DRIVER
    for i,row in enumerate(rows):
        d+=f' @Test method FrontendCase{i:03}() {{ProbeOneR09({i},{json.dumps(row["pattern"],ensure_ascii=False)},{row["cap"]});}}\n'
    d+='}\n';dpath=out/'frontend.dfy';dpath.write_text(d)
    v=verus_file.read_text()+VERUS_DRIVER
    for i,row in enumerate(rows):
        v+=f' #[test] fn frontend_case_{i:03}() {{run_case({json.dumps(row["pattern"],ensure_ascii=False)},{row["cap"]},{json.dumps(row["expected"])});}}\n'
    v+='}\n';vp=out/'verus';(vp/'src').mkdir(parents=True,exist_ok=True);(vp/'src/lib.rs').write_text(v)
    manifest=root/'verus/r/r09_effects/Cargo.toml';deps=tomllib.loads(manifest.read_text())['dependencies']
    cargo='[package]\nname = "r09_frontend_observation"\nversion = "0.1.0"\nedition = "2021"\nbuild = false\n[lib]\npath = "src/lib.rs"\n[dependencies]\n'
    for name,dep in deps.items():
        cargo+=name+' = '+(json.dumps(dep) if isinstance(dep,str) else '{ path = '+json.dumps(str((manifest.parent/dep['path']).resolve()))+' }')+'\n'
    cargo+='[package.metadata.verus]\nverify = true\n[workspace]\n';(vp/'Cargo.toml').write_text(cargo)
    ok=True
    for lang,path,backend in [('dafny',dpath,core.D),('verus',vp,core.V)]:
        res=backend.test(str(path));doc=res.to_dict();accepted=res.verdict=='verified' and res.stage=='test' and not res.holes
        if accepted and lang=='dafny':
            logs=[p.read_text(errors='replace') for p in Path(res.raw_dir).rglob('*') if p.is_file() and 'stdout' in p.name]
            actual={int(m[1]):m[2] for text in logs for m in re.finditer(r'CASE (\d+) (.*?) END',text)}
            bad=[i for i,row in enumerate(rows) if actual.get(i)!=row['expected']]
            accepted=not bad and len(actual)==len(rows);doc['mismatched_case_ids']=bad
        elif accepted:
            accepted=len(res.per_symbol)==len(rows) and all(v=='passed' for v in res.per_symbol.values())
        report['results'][lang]={'accepted':accepted,'native':doc};ok=ok and accepted
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(f'{lang}: {res.verdict}/{res.stage}; holes={len(res.holes)}; fixed observations '+('pass' if accepted else 'fail'),flush=True)
    print(f'Retained artifacts: {out}')
    print('Exact AST/spans, raw canonical class vectors, scalar error positions and actual lowered node counts; finite cases only.')
    return 0 if ok else 1


def main()->int:
    root=Path(__file__).resolve().parents[2];ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dafny-file',type=Path,default=root/'dafny/R/R09_Effects/std/R09_Effects.dfy')
    ap.add_argument('--verus-file',type=Path,default=root/'verus/r/r09_effects/src/lib.rs')
    ap.add_argument('--out',type=Path);args=ap.parse_args()
    out=args.out or Path(tempfile.mkdtemp(prefix='dvl0-r09-frontend-'))
    return run(root,args.dafny_file.resolve(),args.verus_file.resolve(),out.resolve())


if __name__=='__main__':
    raise SystemExit(main())
