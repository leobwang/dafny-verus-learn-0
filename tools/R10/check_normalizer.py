#!/usr/bin/env python3
"""Compile the specified R10 normalizers against fixed, finite observations.

Defaults read learner files only. Full gates precede runtime tests. Generated
Dafny Python is retained before the wrapper's normal cleanup for inspection
of erased fields and builder bodies. Use a capped native lane.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile


def expression(tree, lang):
    op = tree[0]
    if op in ['Z', 'E']:
        return ('Re::' if lang == 'v' else '') + {'Z': 'Empty', 'E': 'Eps'}[op]
    if op == 'C':
        return ('Re::' if lang == 'v' else '') + 'Chr(' + repr(tree[1]) + ')'
    parts = [expression(x, lang) for x in tree[1:]]
    if lang == 'v':
        parts = ['Box::new(' + x + ')' for x in parts]
    return ('Re::' if lang == 'v' else '') + {'A': 'Alt', 'K': 'Cat', 'S': 'Star'}[op] + '(' + ','.join(parts) + ')'


def main():
    root = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dafny-file', type=Path, default=root/'dafny/R/R10_TypeInvariants/std/R10_TypeInvariants.dfy')
    ap.add_argument('--verus-file', type=Path, default=root/'verus/r/r10_type_invariants/src/lib.rs')
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    out = args.out or Path(tempfile.mkdtemp(prefix='dvl0-r10-normalizer-'))
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(root/'tests/wrappers'))
    import test_tools_common as common
    core = common.load_script('vcheck')
    cases_path = root/'tools/R10/normalizer_cases.json'
    cases = json.loads(cases_path.read_text())
    report = {'claim': 'finite actual-source compiled normalization observations', 'cases': len(cases),
              'words_per_case': 11, 'inputs': {}, 'results': {}}
    for p in [args.dafny_file, args.verus_file, cases_path, Path(__file__).resolve()]:
        report['inputs'][str(p.resolve())] = hashlib.sha256(p.read_bytes()).hexdigest()
    names = ['RG_A1_Re', 'RG_A1b_Facts', 'RG_A2_Deriv', 'RG_A2_MatcherStatement', 'RG_A3_Syntax', 'RG_A4_Norm']
    d = ''.join('include '+json.dumps(str(root/'dafny/given/R'/(n+'.dfy')))+'\n' for n in names)
    # Keep the actual implementation in the root file: Dafny skips included bodies.
    d += args.dafny_file.read_text() + '\n'
    d += '''module R10_RuntimeObservations {
 import opened RG_A1_Re
 import opened RG_A2_Deriv
 import opened RG_A4_Norm
 import P = R10_TypeInvariants
 method DescribeR10(r:Re) decreases r {
  match r
  case Empty => print "Z";
  case Eps => print "E";
  case Chr(c) => print "C",c as int;
  case Alt(a,b) => print "A(";DescribeR10(a);print ",";DescribeR10(b);print ")";
  case Cat(a,b) => print "K(";DescribeR10(a);print ",";DescribeR10(b);print ")";
  case Star(a) => print "S(";DescribeR10(a);print ")";
 }
 method ObserveR10(id:nat,r:Re,expected:Re,wasNormal:bool,nodes:nat) {
  var original:=Normal(r);expect original==wasNormal;
  var packet:=P.NormalizePacketR10(r);
  expect packet.expr==expected && Normal(packet.expr) && NodeCount(packet.expr)==nodes;
  print "CASE ",id," ";DescribeR10(packet.expr);print "|N",NodeCount(packet.expr),"|B",original," END\\n";
  var words:seq<seq<char>>:=["","a","b","δ","aa","ab","ba","bb","aδ","δa","aaa"];
  for j:=0 to |words| {
   var originalMatches:=DerivMatch(r,words[j]);var normalizedMatches:=DerivMatch(packet.expr,words[j]);
   expect originalMatches==normalizedMatches;
  }
 }
'''
    for i, row in enumerate(cases):
        inp, expected = expression(row['input'], 'd'), expression(row['expected'], 'd')
        d += (f' @Test method {{:fuel Norm,8}} Case{i:03}() {{assert Norm({inp})=={expected};'
              f'ObserveR10({i},{inp},{expected},{str(row["normal"]).lower()},{row["expected_nodes"]});}}\n')
    d += '}\n'
    dpath = out/'observations.dfy'
    dpath.write_text(d)
    v = args.verus_file.read_text() + '\nverus! {\n'
    for i, row in enumerate(cases):
        v += f'proof fn observed_model_{i:03}() {{reveal_with_fuel(norm,8);assert(norm({expression(row["input"],"v")})=={expression(row["expected"],"v")});}}\n'
    v += '''}
#[cfg(test)] mod r10_observations {
 use super::*;
 fn record(r:&Re)->String {match r {
  Re::Empty=>"Z".to_string(),Re::Eps=>"E".to_string(),Re::Chr(c)=>format!("C{}",*c as u32),
  Re::Alt(a,b)=>format!("A({},{})",record(a),record(b)),Re::Cat(a,b)=>format!("K({},{})",record(a),record(b)),Re::Star(a)=>format!("S({})",record(a)),
 }}
 fn count(r:&Re)->usize {match r {Re::Empty|Re::Eps|Re::Chr(_)=>1,Re::Alt(a,b)|Re::Cat(a,b)=>1+count(a)+count(b),Re::Star(a)=>1+count(a)}}
 fn check(r:Re,expected:&str) {
  let original=is_normal_exec_r10(&r);let packet=normalize_packet_r10(&r);let repr=packet.pattern_ref_r10();
  assert!(is_normal_exec_r10(repr));assert_eq!(format!("{}|N{}|B{}",record(repr),count(repr),original),expected);
  for word in ["","a","b","δ","aa","ab","ba","bb","aδ","δa","aaa"] {
   let chars:Vec<char>=word.chars().collect();assert_eq!(rg_re_a2::deriv_match(&r,&chars),rg_re_a2::deriv_match(repr,&chars));
  }
 }
'''
    for i, row in enumerate(cases):
        v += f' #[test] fn case_{i:03}() {{check({expression(row["input"],"v")},{json.dumps(row["record"])});}}\n'
    v += ' #[test] fn erased_packet_layout() {assert_eq!(std::mem::size_of::<NormPacketR10>(),std::mem::size_of::<NormRe>());}\n}\n'
    vpath = out/'observations-verus'
    (vpath/'src').mkdir(parents=True, exist_ok=True)
    (vpath/'src/lib.rs').write_text(v)
    cargo = '[package]\nname="r10_runtime_observations"\nversion="0.1.0"\nedition="2021"\nbuild=false\n[dependencies]\nvstd="=0.0.0-2026-09-20-0158"\n'
    for layer in ['a1', 'a1b', 'a2', 'a3', 'a4']:
        name = 'rg_re_'+layer
        cargo += name+'={path='+json.dumps(str(root/'verus/given'/name))+'}\n'
    (vpath/'Cargo.toml').write_text(cargo+'[package.metadata.verus]\nverify=true\n[workspace]\n')
    def retain_python(program):
        if program is not None and program.scratch is not None:
            for p in program.scratch.rglob('*.py'):
                dest = out/'generated-python'/p.relative_to(program.scratch)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dest)
        discard(program)
    discard = core.D.discard
    ok = True
    try:
        core.D.discard = retain_python
        for lang, path, lib in [('d', dpath, core.D), ('v', vpath, core.V)]:
            gate = lib.verify(str(path), gate=True)
            report['results'][lang] = {'gate': gate.to_dict()}
            passed = gate.verdict == 'verified' and not gate.holes
            if passed:
                result = lib.test(str(path))
                report['results'][lang]['test'] = result.to_dict()
                passed = result.verdict == 'verified' and result.stage == 'test' and not result.holes
                passed &= len(result.per_symbol) >= len(cases) and all(v == 'passed' for v in result.per_symbol.values())
                if passed and lang == 'd':
                    stdout = (Path(result.raw_dir)/'stdout.txt').read_text()
                    actual = {int(m[1]): m[2] for m in re.finditer(r'CASE (\d+) (.*?) END', stdout)}
                    passed = actual == {i: row['record'] for i, row in enumerate(cases)}
            ok &= passed
            print(f'{lang}: finite observations {"passed" if passed else "failed"}', flush=True)
            (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    finally:
        core.D.discard = discard
    print(f'Retained source, native logs and generated Python: {out}')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
