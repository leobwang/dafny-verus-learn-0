#!/usr/bin/env python3
"""Compile finite, nonvacuous observations of the specified R10 constructors.

Use check_statements.py, original human snapshots and full gates separately.
Defaults read learner files only; no reference or answer pattern is opened.
Run under a capped native lane.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from check_normalizer import expression


def main():
    root = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dafny-file', type=Path, default=root/'dafny/R/R10_TypeInvariants/agent/R10_AgentFlagship.dfy')
    ap.add_argument('--verus-file', type=Path, default=root/'verus/r/r10_type_invariants/src/agent.rs')
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    out = args.out or Path(tempfile.mkdtemp(prefix='dvl0-r10-constructors-'))
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(root/'tests/wrappers'))
    import test_tools_common as common
    core = common.load_script('vcheck')
    leaf = [['Z'], ['E'], ['C', 'a'], ['C', 'b'], ['S', ['C', 'a']], ['A', ['C', 'a'], ['C', 'b']], ['K', ['C', 'a'], ['C', 'b']]]
    pairs = [(0, 2), (2, 0), (1, 2), (2, 1), (2, 2), (2, 3), (3, 2), (4, 1), (5, 6), (6, 4)]
    cases = [(op, leaf[a], leaf[b]) for op in ['alt', 'cat'] for a, b in pairs]
    cases += [('star', x, None) for x in leaf]
    names = ['RG_A1_Re', 'RG_A1b_Facts', 'RG_A2_Deriv', 'RG_A2_MatcherStatement', 'RG_A3_Syntax', 'RG_A4_Norm']
    d = ''.join('include '+json.dumps(str(root/'dafny/given/R'/(n+'.dfy')))+'\n' for n in names)
    # Keep the actual implementation in the root file: Dafny skips included bodies.
    d += args.dafny_file.read_text() + '\n'
    d += '''module R10_ConstructorObservations {
 import opened RG_A1_Re
 import opened RG_A2_Deriv
 import opened RG_A4_Norm
 import P = R10_AgentFlagship
 method ObserveR10(original:Re,out:Re) {
  expect Normal(out);
  var words:seq<seq<char>>:=["","a","b","δ","aa","ab","ba","bb","aδ","δa","aaa"];
  for j:=0 to |words| {
   var x:=DerivMatch(original,words[j]);var y:=DerivMatch(out,words[j]);expect x==y;
  }
 }
'''
    v = args.verus_file.read_text() + '\n#[cfg(test)] mod constructor_observations {\n use super::*;\n'
    v += ''' fn observe(original:Re,out:NormRe) {
  let repr=out.pattern_ref_r10();assert!(is_normal_exec_r10(repr));
  for word in ["","a","b","δ","aa","ab","ba","bb","aδ","δa","aaa"] {
   let chars:Vec<char>=word.chars().collect();assert_eq!(rg_re_a2::deriv_match(&original,&chars),rg_re_a2::deriv_match(repr,&chars));
  }
 }
'''
    for i, (op, a, b) in enumerate(cases):
        raw = [{'alt': 'A', 'cat': 'K', 'star': 'S'}[op], a] + ([b] if b is not None else [])
        dargs = expression(a, 'd') + (','+expression(b, 'd') if b is not None else '')
        vargs = 'NormRe::from_normal_r10('+expression(a, 'v')+')' + (',NormRe::from_normal_r10('+expression(b, 'v')+')' if b is not None else '')
        d += f' @Test method Case{i:03}() {{var out:=P.Build{op.title()}R10({dargs});ObserveR10({expression(raw,"d")},out);}}\n'
        v += f' #[test] fn case_{i:03}() {{let out=build_{op}_r10({vargs});observe({expression(raw,"v")},out);}}\n'
    d += '}\n'
    v += '}\n'
    dp = out/'observations.dfy'
    dp.write_text(d)
    vp = out/'observations-verus'
    (vp/'src').mkdir(parents=True, exist_ok=True)
    (vp/'src/lib.rs').write_text(v)
    cargo = '[package]\nname="r10_constructor_observations"\nversion="0.1.0"\nedition="2021"\nbuild=false\n[dependencies]\nvstd="=0.0.0-2026-09-20-0158"\n'
    for layer in ['a1', 'a1b', 'a2', 'a3', 'a4']:
        name = 'rg_re_'+layer
        cargo += name+'={path='+json.dumps(str(root/'verus/given'/name))+'}\n'
    (vp/'Cargo.toml').write_text(cargo+'[package.metadata.verus]\nverify=true\n[workspace]\n')
    report = {'claim': 'finite actual-constructor observations; no universal strength claim', 'cases_each': len(cases), 'words_per_case': 11,
              'inputs': {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in [args.dafny_file, args.verus_file, Path(__file__).resolve()]}, 'results': {}}
    ok = True
    for lang, path, lib in [('d', dp, core.D), ('v', vp, core.V)]:
        gate = lib.verify(str(path), gate=True)
        report['results'][lang] = {'gate': gate.to_dict()}
        passed = gate.verdict == 'verified' and not gate.holes
        if passed:
            result = lib.test(str(path))
            report['results'][lang]['test'] = result.to_dict()
            passed = (result.verdict == 'verified' and result.stage == 'test' and not result.holes and
                      len(result.per_symbol) == len(cases) and all(v == 'passed' for v in result.per_symbol.values()))
        ok &= passed
        print(f'{lang}: constructor observations {"passed" if passed else "failed"}', flush=True)
        (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f'Retained original-source hashes, generated drivers and native evidence: {out}')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
