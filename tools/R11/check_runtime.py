#!/usr/bin/env python3
"""Gate actual R11 implementations, then compare compiled finite observations.

Defaults read learner sources only. Expected acceptance and certificate validity
come from independent finite interpreters here, not a candidate proof theorem.
Dafny implementations are embedded in the verified root (includes are not enough).
Run in a capped native lane. These finite checks do not prove metatheory.
"""
from __future__ import annotations
import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys
import tempfile

WORDS = ['', 'a', 'b', 'δ', 'aa', 'ab', 'ba', 'bb', 'aδ', 'δa', 'aaa']


def freeze(x):
    return tuple(freeze(v) if isinstance(v, list) else v for v in x)


@lru_cache(None)
def accepts(r, s):
    op = r[0]
    if op == 'Z': return False
    if op == 'E': return s == ''
    if op == 'C': return s == r[1]
    if op == 'A': return accepts(r[1], s) or accepts(r[2], s)
    if op == 'K': return any(accepts(r[1], s[:i]) and accepts(r[2], s[i:]) for i in range(len(s)+1))
    if op == 'S': return s == '' or any(accepts(r[1], s[:i]) and accepts(r, s[i:]) for i in range(1, len(s)+1))
    raise ValueError(op)


def valid(d, r, s):
    op = d[0]
    if op == 'E': return r[0] == 'E' and not s
    if op == 'C': return r[0] == 'C' and s == r[1]
    if op in ['L', 'R']: return r[0] == 'A' and valid(d[1], r[1 if op == 'L' else 2], s)
    if op == 'K': return r[0] == 'K' and d[1] <= len(s) and valid(d[2], r[1], s[:d[1]]) and valid(d[3], r[2], s[d[1]:])
    if op == 'N': return r[0] == 'S' and not s
    if op == 'S': return r[0] == 'S' and 0 < d[1] <= len(s) and valid(d[2], r[1], s[:d[1]]) and valid(d[3], r, s[d[1]:])
    raise ValueError(op)


def expr(t, lang, certificate=False):
    op = t[0]
    names = ({'E':'DEps','C':'DChr','L':'DAltL','R':'DAltR','K':'DCat','N':'DStarNil','S':'DStarCons'}
             if certificate else {'Z':'Empty','E':'Eps','C':'Chr','A':'Alt','K':'Cat','S':'Star'})
    prefix = ('Derivation::' if certificate else 'Re::') if lang == 'v' else ''
    args = []
    for x in t[1:]:
        if isinstance(x, (list, tuple)):
            a = expr(x, lang, certificate)
            args.append('Box::new('+a+')' if lang == 'v' else a)
        else:
            args.append(repr(x) if isinstance(x, str) else str(x))
    return prefix+names[op]+('('+','.join(args)+')' if args else '')


def cert_cases():
    a, b = ('C','a'), ('C','b')
    rows = [(('E',),'',('E',)), (a,'a',('C',)), (a,'b',('C',)), (('Z',),'',('E',)),
            (('A',a,b),'a',('L',('C',))), (('A',a,b),'b',('R',('C',))),
            (('A',a,b),'b',('L',('C',))), (('K',a,b),'ab',('K',1,('C',),('C',))),
            (('K',('K',a,b),a),'aba',('K',2,('K',1,('C',),('C',)),('C',))),
            (('S',a),'',('N',)), (('S',a),'a',('S',1,('C',),('N',))),
            (('S',a),'aa',('S',1,('C',),('S',1,('C',),('N',)))),
            (('S',a),'ab',('S',1,('C',),('N',))),
            (('S',('E',)),'',('S',0,('E',),('N',)))]
    for k in [0, 2, 3, 2**64-1]:
        rows.extend([(('K',a,b),'ab',('K',k,('C',),('C',))),
                     (('S',a),'aa',('S',k,('C',),('N',)))])
    for d in [('E',),('C',),('L',('C',)),('R',('C',)),('K',1,('C',),('C',)),('N',),('S',1,('C',),('N',))]:
        rows.append((a,'a',d))
    return rows


def main():
    root = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--lang', choices=['d','v','both'], default='both')
    ap.add_argument('--dafny-file',type=Path,default=root/'dafny/R/R11_Theory/std/R11_Theory.dfy')
    ap.add_argument('--verus-file',type=Path,default=root/'verus/r/r11_theory/src/lib.rs')
    ap.add_argument('--out',type=Path)
    args = ap.parse_args()
    out = args.out or Path(tempfile.mkdtemp(prefix='dvl0-r11-runtime-'))
    out.mkdir(parents=True,exist_ok=True)
    cases_path = root/'tools/R11/runtime_cases.json'
    cases = json.loads(cases_path.read_text())
    certs = cert_cases()
    sys.path.insert(0,str(root/'tests/wrappers'))
    import test_tools_common as common
    core = common.load_script('vcheck')
    report = {'claim':'finite compiled actual-source observations; not general metatheory',
              'patterns':len(cases),'words_per_pattern':len(WORDS),'certificate_cases':len(certs),
              'inputs':{},'results':{}}
    for p in [cases_path,Path(__file__).resolve()]+([args.dafny_file] if args.lang in ['d','both'] else [])+([args.verus_file] if args.lang in ['v','both'] else []):
        report['inputs'][str(p.resolve())]=hashlib.sha256(p.read_bytes()).hexdigest()
    (out/'expected.json').write_text(json.dumps({'words':WORDS,'acceptance':[[accepts(freeze(r),w) for w in WORDS] for r in cases],
                                               'certificates':[{'pattern':r,'word':s,'tree':d,'valid':valid(d,r,s)} for r,s,d in certs]},indent=2)+'\n')
    targets=[]
    if args.lang in ['d','both']:
        d=''.join('include '+json.dumps(str(root/'dafny/given/R'/(n+'.dfy')))+'\n' for n in ['RG_A1_Re','RG_A1b_Facts','RG_A2_Deriv','RG_A2_MatcherStatement','RG_A3_Syntax','RG_A4_Norm'])
        d+=args.dafny_file.read_text()+'''
module R11_RuntimeObservations {
 import opened RG_A1_Re
 import opened RG_A4_Norm
 import K=R11_Kernel
 import S=R11_Search
 import P=R11_Streaming
 method Observe(r:Re,s:seq<char>,expected:bool,prefixes:seq<bool>) {
  var result:=S.SearchR11(r,s);
  expect result.HasCertR11?==expected;
  if result.HasCertR11? {var checked:=K.CheckCertificateR11(r,s,result.value);expect checked;}
  var accepted,trace:=P.PrefixMatchesR11(r,s);
  expect accepted==expected && trace==prefixes;
 }
'''
        for i,r in enumerate(cases):
            d+=f' @Test method Case{i:03}() {{\n'
            for w in WORDS:
                flags=[accepts(freeze(r),w[:j]) for j in range(1,len(w)+1)]
                d+=f'Observe({expr(r,"d")},{json.dumps(w,ensure_ascii=False)},{str(accepts(freeze(r),w)).lower()},'+str(flags).lower()+');\n'
            d+='}\n'
        for i,(r,s,tree) in enumerate(certs):
            d+=f' @Test method Certificate{i:03}() {{var b:=K.CheckCertificateR11({expr(r,"d")},{json.dumps(s)},{expr(tree,"d",True)});expect b=={str(valid(tree,r,s)).lower()};}}\n'
        d+='}\n'
        p=out/'observations.dfy';p.write_text(d);targets.append(('d',p,core.D,len(cases)+len(certs)))
    if args.lang in ['v','both']:
        v=args.verus_file.read_text()+'''
#[cfg(test)] mod r11_observations {
 use super::*;
 fn observe(r:Re,word:&str,expected:bool,prefixes:&[bool]) {
  let chars:Vec<char>=word.chars().collect();
  // Shifted slice exercises word-relative certificate splits.
  let mut padded=vec!['!'];padded.extend(chars.iter().copied());padded.push('?');
  let result=search_r11(&r,&padded,1,padded.len()-1);
  assert_eq!(result.is_some(),expected);
  if let Some(tree)=result {assert!(check_certificate_r11(&tree,&r,&padded,1,padded.len()-1));}
  let report=prefix_matches_r11(&r,&chars);
  assert_eq!(report.accepted,expected);assert_eq!(report.trace,prefixes);
 }
'''
        for i,r in enumerate(cases):
            v+=f' #[test] fn case_{i:03}() {{\n'
            for w in WORDS:
                flags=[accepts(freeze(r),w[:j]) for j in range(1,len(w)+1)]
                v+=f'observe({expr(r,"v")},{json.dumps(w,ensure_ascii=False)},{str(accepts(freeze(r),w)).lower()},&'+str(flags).lower()+');\n'
            v+='}\n'
        for i,(r,s,tree) in enumerate(certs):
            v+=f' #[test] fn certificate_{i:03}() {{let r={expr(r,"v")};let d={expr(tree,"v",True)};let s:Vec<char>={json.dumps("!"+s+"?")}.chars().collect();assert_eq!(check_certificate_r11(&d,&r,&s,1,s.len()-1),{str(valid(tree,r,s)).lower()});}}\n'
        v+=''' #[test] fn invalid_slice_bounds() {
 let r=Re::Eps;let d=Derivation::DEps;let s=vec!['a'];
 assert!(!check_certificate_r11(&d,&r,&s,1,0));
 assert!(!check_certificate_r11(&d,&r,&s,0,2));
 assert!(!check_certificate_r11(&d,&r,&s,usize::MAX,usize::MAX));
 }
 #[test] fn arena_append_and_link_frames() {
 let mut a=empty_arena_r11();
 for c in ['a','b','δ'] {let index=append_node_r11(&mut a,c);assert_eq!(a.nodes[index].label,c);assert!(a.nodes[index].first.is_none()&&a.nodes[index].second.is_none());}
 link_first_r11(&mut a,0,2);link_first_r11(&mut a,1,1);
 assert_eq!(a.nodes[0].first,Some(2));assert_eq!(a.nodes[1].first,Some(1));assert_eq!(a.nodes[2].first,None);
 assert_eq!(a.nodes.iter().map(|n|n.label).collect::<Vec<_>>(),vec!['a','b','δ']);
 assert!(a.nodes.iter().all(|n|n.second.is_none()));
 append_node_r11(&mut a,'z');assert_eq!(a.nodes[0].first,Some(2));assert_eq!(a.nodes[1].first,Some(1));
 link_first_r11(&mut a,0,3);assert_eq!(a.nodes[0].first,Some(3));assert_eq!(a.nodes[1].first,Some(1));
 }
}
'''
        p=out/'observations-verus';(p/'src').mkdir(parents=True,exist_ok=True);(p/'src/lib.rs').write_text(v)
        cargo='[package]\nname="r11_runtime_observations"\nversion="0.1.0"\nedition="2021"\nbuild=false\n[dependencies]\nvstd="=0.0.0-2026-09-20-0158"\n'
        for layer in ['a1','a1b','a2','a3','a4']:
            name='rg_re_'+layer;cargo+=name+'={path='+json.dumps(str(root/'verus/given'/name))+'}\n'
        (p/'Cargo.toml').write_text(cargo+'[package.metadata.verus]\nverify=true\n[workspace]\n')
        targets.append(('v',p,core.V,len(cases)+len(certs)+2))
    ok=True
    for lang,path,lib,count in targets:
        gate=lib.verify(str(path),gate=True)
        row={'gate':gate.to_dict(),'expected_test_count':count};report['results'][lang]=row
        passed=gate.verdict=='verified' and not gate.holes
        if passed:
            result=lib.test(str(path));row['test']=result.to_dict()
            passed=result.verdict=='verified' and result.stage=='test' and not result.holes
            passed &= len(result.per_symbol)>=count and all(x=='passed' for x in result.per_symbol.values())
        ok &= passed
        row['passed']=bool(passed)
        print(f'{lang}: compiled runtime observations {"passed" if passed else "failed"}',flush=True)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'Retained actual source, independent expectations and native logs: {out}')
    return 0 if ok else 1


if __name__=='__main__':
    raise SystemExit(main())
