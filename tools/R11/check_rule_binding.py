#!/usr/bin/env python3
"""Check the specified agent's rule definition against canonical A4 validity.

Only pure definitions enter the independent consumer. No transport theorem or
implementation body is assumed. Full proof gates and original snapshots are
separate checks. Defaults read learner sources only. Use a capped native lane.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile


def models(core, path, lang):
    text = path.read_text()
    if lang == 'd':
        src = core.D.parse_source(text, str(path))
        defs = [d for d in src.decls if d.kind in core.D.DEFINITION_KINDS]
        if sum(d.name == 'RulesR11' for d in defs) != 1:
            raise ValueError('expected exactly one RulesR11 definition')
    else:
        src = core.V.vs.parse(text)
        defs = [d for d in src.walk() if d.kind == 'fn' and d.mode == 'spec']
        if sum(d.name == 'rules_r11' for d in defs) != 1:
            raise ValueError('expected exactly one rules_r11 definition')
    if any(d.body is None for d in defs):
        raise ValueError('model definitions must have bodies')
    return '\n'.join(text[src.toks[d.start].start:src.toks[d.body[1]].end] for d in defs)


def main():
    root = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--lang', choices=['d', 'v', 'both'], default='both')
    ap.add_argument('--dafny-file', type=Path, default=root/'dafny/R/R11_Theory/agent/R11_AgentMetatheory.dfy')
    ap.add_argument('--verus-file', type=Path, default=root/'verus/r/r11_theory/src/agent.rs')
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    out = args.out or Path(tempfile.mkdtemp(prefix='dvl0-r11-rule-binding-'))
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(root/'tests/wrappers'))
    import test_tools_common as common
    core = common.load_script('vcheck')
    report = {'claim': 'pure rule-model equality to canonical A4; no transport theorem assumed',
              'tool_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'results': {}}
    ok = True
    for lang, source, lib in [('d', args.dafny_file, core.D), ('v', args.verus_file, core.V)]:
        if args.lang not in [lang, 'both']:
            continue
        definitions = models(core, source, lang)
        report['results'][lang] = {'source': str(source.resolve()), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest()}
        if lang == 'd':
            names = ['RG_A1_Re', 'RG_A1b_Facts', 'RG_A2_Deriv', 'RG_A2_MatcherStatement', 'RG_A3_Syntax', 'RG_A4_Norm']
            text = ''.join('include '+json.dumps(str(root/'dafny/given/R'/(n+'.dfy')))+'\n' for n in names)
            text += 'module R11_AgentModels {\nimport opened RG_A1_Re\nimport opened RG_A4_Norm\n'+definitions+'\n}\n'
            text += '''module R11_RuleConsumer {
 import RG_A1_Re
 import RG_A4_Norm
 import A=R11_AgentModels
 lemma RulesAgreeR11(r:RG_A1_Re.Re,s:seq<char>,d:RG_A4_Norm.Derivation)
  ensures A.RulesR11(r,s,d)==RG_A4_Norm.CheckDeriv(r,s,d)
 {}
}
'''
            target = out/'consumer.dfy'
            target.write_text(text)
        else:
            text = 'use vstd::prelude::*;\nuse rg_re_a1::*;\nuse rg_re_a4::*;\nverus! {\n'+definitions
            text += '''
proof fn rules_agree_r11(d: ::rg_re_a4::Derivation,r: ::rg_re_a1::Re,s: ::vstd::seq::Seq<char>)
 ensures rules_r11(d,r,s)==::rg_re_a4::valid_word_r10(d,r,s),
 {}
}
'''
            target = out/'consumer-verus'
            (target/'src').mkdir(parents=True, exist_ok=True)
            (target/'src/lib.rs').write_text(text)
            cargo = '[package]\nname="r11_rule_consumer"\nversion="0.1.0"\nedition="2021"\nbuild=false\n[dependencies]\nvstd="=0.0.0-2026-09-20-0158"\n'
            for layer in ['a1', 'a1b', 'a2', 'a3', 'a4']:
                name = 'rg_re_'+layer
                cargo += name+'={path='+json.dumps(str(root/'verus/given'/name))+'}\n'
            (target/'Cargo.toml').write_text(cargo+'[package.metadata.verus]\nverify=true\n[workspace]\n')
        result = lib.verify(str(target), gate=True)
        report['results'][lang]['native'] = result.to_dict()
        passed = result.verdict == 'verified' and not result.holes
        ok &= passed
        print(f'{lang}: canonical rule binding {"proved" if passed else "not proved"} ({result.verdict})', flush=True)
        (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f'Retained model-only consumers and native evidence: {out}')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
