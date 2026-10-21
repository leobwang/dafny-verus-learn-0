#!/usr/bin/env python3
"""Check fixed R12 proof sites with the native parsers and executable skeleton,
and (author mode, --admit) run the seven Lab alpha admission controls.

Defaults read explicit learner/course forms only. No completion or reference is
located: --admit is given the reference hint data explicitly (an author file) and
writes its evidence where it is told. Every site must leave native declarations/
models and executable tokens unchanged when probed, and every approved callee must
be a local proof declaration. The optional native baseline check must fail at
verify with zero unfinished holes. This does not unlock a live lab run.

  admit_forms.py FORM... [--native] [--out DIR]
      frame checks (and, with --native, the failing baseline and a clean audit)
  admit_forms.py FORM --admit HINTS.json --evidence DIR [--admission OUT.json]
      the seven controls of DVR4 plan section 3.5, in order, resumable from
      DIR/report.json (a changed form or reference refuses reuse):
        original-model-code-frame  native frame checks; the reference renders
                                   from the hint data inside the frame; the
                                   target span is the target declaration's
        baseline-proof-fails       vcheck --module R12 --gate: failed at verify,
                                   no holes, the target symbol failed
        reference-gate             the lab gate (--lab-task FORM) verifies the
                                   rendered reference
        reference-three-seeds      vcheck --module R12 --seed S, S = 1, 2, 3
        audit-clean                vaudit: no finding
        max-auto-empty-fails       the target's empty body fails under every
                                   empty-body run (Dafny maxauto and the shipped
                                   seeds; Verus every applicable mode x seed)
        wrong-hints-fail           every expression site `false`, every call
                                   site empty: failed at verify, no holes
      HINTS.json is {"hints": [...]} in site order; the target is the first
      R12_SOURCE_SPANS symbol. --admission writes the public summary
      (no reference body, no private path).
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

KEYS=('original-model-code-frame','baseline-proof-fails','reference-gate','reference-three-seeds','audit-clean','max-auto-empty-fails','wrong-hints-fail')
SEEDS=(1,2,3)


def analyze_form(path,core,source_task):
    text=path.read_text();task,spans=source_task(text)
    lang='d' if path.suffix=='.dfy' else 'v' if path.suffix=='.rs' else None
    if lang is None:raise ValueError('one Dafny or Verus form file required')
    native_lang='dafny' if lang=='d' else 'verus'
    if lang=='d':
        src=core.D.parse_source(text,str(path));decls=src.decls
        proof_decls=[d for d in decls if d.kind in ['lemma','colemma'] or (d.kind=='method' and 'ghost' in d.modifiers)]
        namespace=lambda d:d.container
        code={d.name for d in decls if d.kind in ['method','constructor'] and 'ghost' not in d.modifiers}
    else:
        src=core.V.vs.parse(text);decls=[d for d in src.walk() if d.kind=='fn']
        proof_decls=[d for d in decls if d.mode=='proof' and d.owner is None]
        namespace=lambda d:d.path
        code={d.name for d in decls if d.mode=='exec'}
    statement=core.statement_table(path,lang,text=text)[0]
    skeleton=core.LC.skeleton(text,native_lang,annotations=True,target='r12_unused_target',witness='r12_unused_witness')
    checked=[]
    for site in task.sites:
        if site.kind=='expr':probes=['false']
        else:
            position=text.index(site.marker)
            callers=[d for d in proof_decls if d.body and src.toks[d.body[0]].start<position<src.toks[d.body[1]].end]
            if len(callers)!=1:raise ValueError(f'{site.name}: calls require a native proof-declaration body')
            caller=callers[0]
            proof=Counter(d.name for d in proof_decls if namespace(d)==namespace(caller))
            # A bare callee must bind to the declared local helper. Existing uses,
            # parameters or local bindings of that name need a different explicit
            # wrapper; this deliberately small grammar does not guess shadowing.
            tokens=[t.text for t in src.toks[caller.start:caller.body[1]+1]]
            if any(proof[name]!=1 or tokens.count(name)!=(1 if name==caller.name else 0) for name in site.callees) or set(site.callees)&code:raise ValueError(f'{site.name}: callees must be unambiguous local proof declarations without shadowing')
            probes=[name+'();' for name in site.callees]
        for replacement in probes:
            variant=text.replace(site.marker,replacement,1)
            if core.statement_table(path,lang,text=variant)[0]!=statement:raise ValueError(f'{site.name}: site changes a frozen declaration or model')
            got=core.LC.skeleton(variant,native_lang,annotations=True,target='r12_unused_target',witness='r12_unused_witness')
            if got!=skeleton:raise ValueError(f'{site.name}: site changes executable code')
        checked.append({'name':site.name,'kind':site.kind,'callee_bindings':list(site.callees)})
    fingerprint=lambda value:hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
    return {'source':str(path.resolve()),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'lang':native_lang,'sites':checked,'statement_sha256':fingerprint(statement),'code_sha256':fingerprint(skeleton)}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def render_reference(engine,text,hints):
    """The reference as the frozen hint grammar renders it (expression sites in
    parentheses, call sites as normalized call lists), checked by the provided
    independent source-frame guard; never the learner renderer."""
    task,spans=engine.source_task(text)
    if type(hints) is not list or len(hints)!=len(task.sites) or any(not isinstance(h,str) or not h for h in hints):raise ValueError('one nonempty reference hint per site')
    out=text
    for site,hint in zip(task.sites,hints):
        if site.kind=='expr':engine._check_expression(hint,site.identifiers);out=out.replace(site.marker,'('+hint+')',1)
        else:out=out.replace(site.marker,engine._proof_calls(hint,site),1)
    engine.check_source_frame(task,out)
    return task,spans,out


def wrong_text(task,text):
    for site in task.sites:text=text.replace(site.marker,'false' if site.kind=='expr' else '',1)
    return text


def target_span(core,path,lang,text,symbol):
    """(start, end) lines of the target declaration, from the native parser."""
    if lang=='d':
        src=core.D.parse_source(text,str(path));d=src.decl(symbol)
        if d is None:raise ValueError('target symbol '+symbol+' is not declared')
        return d.line,text[:src.toks[d.body[1]].start].count('\n')+1
    src=core.V.vs.parse(text)
    fns=[d for d in src.walk() if d.kind=='fn' and d.name==symbol and d.owner is None]
    if len(fns)!=1:raise ValueError('target fn '+symbol+' must be declared once')
    d=fns[0];token=next(k for k in range(d.start,d.body[0]) if src.toks[k].text=='fn')
    return text[:src.toks[token].start].count('\n')+1,text[:src.toks[d.body[1]].start].count('\n')+1


def admit(root,core,engine,form,hints_path,evidence,admission=None,log=print,shipped_induction=False):
    """The seven controls (module docstring); returns the public summary."""
    form=Path(form).resolve();evidence=Path(evidence).resolve();evidence.mkdir(parents=True,exist_ok=True)
    lang='d' if form.suffix=='.dfy' else 'v' if form.suffix=='.rs' else None
    if lang is None:raise ValueError('one Dafny or Verus form file required')
    native='dafny' if lang=='d' else 'verus';lib=core.D if lang=='d' else core.V
    text=form.read_text();hints=json.loads(Path(hints_path).read_text()).get('hints')
    task,spans,ref_text=render_reference(engine,text,hints)
    if not spans:raise ValueError('R12_SOURCE_SPANS must name the target first')
    symbol=spans[0]['symbol']
    # the rendered reference and the wrong-hint control are verified from a scratch copy:
    # vcheck refuses to run (and print) reference material where it lives
    work=Path(os.environ.get('DVL_SCRATCH') or tempfile.gettempdir())/('dvl0-r12-admit-'+form.stem);work.mkdir(parents=True,exist_ok=True)
    ref=work/('reference'+form.suffix);wrong=work/('wrong'+form.suffix)
    ref.write_text(ref_text);wrong.write_text(wrong_text(task,text))
    state=evidence/'report.json'
    fresh={'schema':2,'id':form.stem,'lang':native,'target':symbol,'source_sha256':sha(form),'reference_sha256':sha(ref),'reference_copy':str(ref),'hints_sha256':sha(hints_path),'status':'authoring','checks':{k:False for k in KEYS},'evidence':{}}
    report=json.loads(state.read_text()) if state.exists() else fresh
    if any(report.get(k)!=fresh[k] for k in ('source_sha256','reference_sha256','hints_sha256','target')):report=fresh
    def save():state.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    def cli(name,cmd):
        p=subprocess.run(cmd,cwd=root,capture_output=True,text=True)
        (evidence/(name+'.stdout')).write_text(p.stdout);(evidence/(name+'.stderr')).write_text(p.stderr)
        if p.returncode in (137,143,-9,-15):raise RuntimeError(name+': killed(memory) ('+str(p.returncode)+'): no verdict')
        try:return p.returncode,json.loads(p.stdout)
        except ValueError:return p.returncode,{'verdict':'error','stage':'cli','stdout':p.stdout[-2000:]}
    def key_symbol(per_symbol):
        hits=[v for k,v in per_symbol.items() if k==symbol or k.endswith('.'+symbol) or k.endswith('::'+symbol)]
        return hits
    def checked(key,name,passed,document):
        report['evidence'][name]=dict(passed=bool(passed),document=document);save()
        if not passed:report['status']='rejected';report['rejected_at']=key;save();raise ValueError(key+' ('+name+') failed')
    vcheck=str(root/'scripts/vcheck');vaudit=str(root/'scripts/vaudit')
    c=report['checks']
    if not c['original-model-code-frame']:
        entry=analyze_form(form,core,engine.source_task)
        same_table=core.statement_table(form,lang,text=text)[0]==core.statement_table(ref,lang,text=ref_text)[0]
        same_code=core.LC.skeleton(text,native,annotations=True,target='unused',witness='unused')==core.LC.skeleton(ref_text,native,annotations=True,target='unused',witness='unused')
        start,end=target_span(core,form,lang,text,symbol)
        span_ok=spans[0]['start']==start and spans[0]['end']==end
        checked('original-model-code-frame','frame',same_table and same_code and span_ok,dict(native_form={k:v for k,v in entry.items() if k!='source'},validated_span=spans[0],native_span=[start,end],statement_equal=same_table,code_equal=same_code))
        c['original-model-code-frame']=True;save()
    if not c['baseline-proof-fails']:
        code,d=cli('baseline',[vcheck,'--module','R12','--gate','--json',str(form)])
        hits=key_symbol(d.get('per_symbol',{}))
        # QPLAN section 30 Q66 (vcheck's reading): a run that ends inconclusive at the
        # verify stage (out of resources at the pin) did not prove the form: it fails
        checked('baseline-proof-fails','baseline',code==core.EXIT_FAIL and d.get('verdict') in ('failed','inconclusive') and d.get('stage')=='verify' and not d.get('holes') and hits and all(h!='verified' for h in hits),d)
        c['baseline-proof-fails']=True;save()
    if not c['reference-gate']:
        code,d=cli('reference-gate',[vcheck,'--module','R12','--gate','--json','--lab-task',str(form),str(ref)])
        hits=key_symbol(d.get('per_symbol',{}))
        checked('reference-gate','reference-gate',code==0 and d.get('verdict')=='verified' and d.get('stage')=='verify' and not d.get('holes') and not d.get('findings') and hits==['verified'],d)
        c['reference-gate']=True;save()
    if not c['reference-three-seeds']:
        for s in SEEDS:
            name='seed-'+str(s)
            if report['evidence'].get(name,{}).get('passed'):continue
            code,d=cli(name,[vcheck,'--module','R12','--json','--seed',str(s),str(ref)])
            checked('reference-three-seeds',name,code==0 and d.get('verdict')=='verified' and d.get('stage')=='verify' and not d.get('holes'),d)
        c['reference-three-seeds']=True;save()
    if not c['audit-clean']:
        code,d=cli('audit',[vaudit,'--json',str(ref)])
        checked('audit-clean','audit',code==0 and isinstance(d,dict) and d.get('findings')==[],d)
        c['audit-clean']=True;save()
    if not c['max-auto-empty-fails']:
        r=lib.empty_body(str(ref),symbol)
        statuses=list(r.per_symbol.values())
        # vcheck's own reading: a variant that does not reach verification (no-verify) did not
        # close the item and counts as failing, and so does a wall-clock kill (killed(harness),
        # Delta 58); a memory kill is never a verdict. The plain empty body must reach
        # verification and fail.
        if any(v=='killed(memory)' for v in statuses):raise RuntimeError('empty-automation: a variant was killed(memory): no verdict')
        # D55 (Lab alpha tasks only): with shipped_induction, Dafny's maxauto run (automatic
        # induction turned back on) is recorded but does not gate; every shipped run (the
        # units' --manual-lemma-induction, the setting the lab gate's lever check holds a
        # delivery to) must fail. Verus has no such run: its reading is unchanged.
        gating={k:v for k,v in r.per_symbol.items() if not (shipped_induction and lang=='d' and k=='maxauto')}
        plain=[v for k,v in gating.items() if k in ('maxauto',) or k.startswith(('E0 ','shipped:'))]
        ok=bool(gating) and bool(plain) and all(v in ('failed','inconclusive') or v.startswith('fails(') for k,v in gating.items() if k in ('maxauto',) or k.startswith(('E0 ','shipped:'))) and all(v in ('failed','inconclusive','killed(harness)') or v.startswith(('fails(','no-verify(')) for v in gating.values()) and (r.verdict=='failed' or (shipped_induction and lang=='d'))
        checked('max-auto-empty-fails','empty-automation',ok,r.to_dict())
        report['empty_variants']=len(statuses);report['max_auto_reading']='shipped --manual-lemma-induction (D55; maxauto recorded: '+str(r.per_symbol.get('maxauto'))+')' if (shipped_induction and lang=='d') else 'maximal automation';c['max-auto-empty-fails']=True;save()
    if not c['wrong-hints-fail']:
        code,d=cli('wrong-hints',[vcheck,'--module','R12','--gate','--json',str(wrong)])
        checked('wrong-hints-fail','wrong-hints',d.get('verdict') in ('failed','inconclusive') and d.get('stage')=='verify' and not d.get('holes'),d)
        report['wrong_hint_kind']='expression sites false, call sites empty'+(' (no expression site: equals the baseline)' if all(s.kind=='calls' for s in task.sites) else '')
        c['wrong-hints-fail']=True;save()
    assert all(c.values())
    report['status']='admitted';save()
    frame=report['evidence']['frame']['document']
    summary={'schema':2,'id':form.stem,'lang':native,'target':symbol,'status':'admitted','source_sha256':report['source_sha256'],
             'checks':dict(c),'sites':[dict(name=s.name,kind=s.kind) for s in task.sites],'validated_span':spans[0],
             'frame':{'statement_sha256':frame['native_form']['statement_sha256'],'code_sha256':frame['native_form']['code_sha256']},
             'seeds':list(SEEDS),'empty_variants':report['empty_variants'],'max_auto_reading':report.get('max_auto_reading','maximal automation'),'wrong_hint_kind':report['wrong_hint_kind'],
             'private_evidence_sha256':sha(state),'scope':'author native task-validity controls; no learner grade or live run'}
    if admission:Path(admission).write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    log(form.name+': admitted')
    return summary


def main():
    root=Path(__file__).resolve().parents[2]
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('forms',type=Path,nargs='+')
    ap.add_argument('--native',action='store_true',help='also require a zero-hole failing proof-stage baseline and clean audit')
    ap.add_argument('--out',type=Path)
    ap.add_argument('--admit',type=Path,metavar='HINTS.json',help='author mode: the reference hint data of the one FORM')
    ap.add_argument('--evidence',type=Path,help='with --admit: the private evidence directory')
    ap.add_argument('--admission',type=Path,help='with --admit: write the public ADMISSION.json here')
    ap.add_argument('--shipped-induction',action='store_true',help="with --admit (D55, Lab alpha tasks only): read max-auto-empty-fails for Dafny under the units' shipped --manual-lemma-induction; the maxauto run is recorded, not gating")
    args=ap.parse_args()
    sys.path.insert(0,str(root/'tests/wrappers'));import test_tools_common as common
    core=common.load_script('vcheck')
    sys.path.insert(0,str(root/'harness'));sys.path.insert(0,str(root/'harness/r'))
    from fvh_r import engine
    from fvh_r.engine import source_task
    if args.admit:
        if len(args.forms)!=1 or args.evidence is None:ap.error('--admit takes one FORM and --evidence')
        try:admit(root,core,engine,args.forms[0],args.admit,args.evidence,args.admission,shipped_induction=args.shipped_induction);return 0
        except (OSError,ValueError,TypeError,KeyError) as e:print(args.forms[0].name+': rejected: '+str(e),file=sys.stderr);return 1
        except RuntimeError as e:print(args.forms[0].name+': '+str(e),file=sys.stderr);return 3
    out=args.out or Path(tempfile.mkdtemp(prefix='dvl0-r12-forms-'));out.mkdir(parents=True,exist_ok=True)
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
