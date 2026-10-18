"""Author-only R12 corpus composition; real captured native results, scripted hints.

No models, containers, live ledgers, pre-registration rows or provider windows.
The runner returns evidence only for the exact captured source SHA; path fields
are remapped for frozen executor staging. Correct hints stay protected here.
"""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import re
import shutil
import sys
import tempfile
import tomllib

ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'harness'),str(ROOT/'harness/r')]
from fvh import backends,batch,budget,executor,protocol as P,tools
from fvh.tools import runners as runners
spec=importlib.util.spec_from_file_location('r12_corpus_complete_engine',ROOT/'Solutions/harness/r/fvh_r/engine.py')
engine=importlib.util.module_from_spec(spec);sys.modules[spec.name]=engine;spec.loader.exec_module(engine)


class Captured(runners.Runner):
    name='replay'
    isolated=True
    def __init__(self,card,root=ROOT):
        self.cases={};self.seen=[]
        private=root/'Solutions/plans/drafts/R12/lab-corpus'/card['id']
        summary=json.loads((root/card['admission']).read_text())
        report_path=private/'admission.json'
        assert hashlib.sha256(report_path.read_bytes()).hexdigest()==summary['private_evidence_sha256']
        report=json.loads(report_path.read_text())
        for case,path in [('form',root/card['path']),('good',root/'Solutions'/card['path'])]:
            sha=hashlib.sha256(path.read_bytes()).hexdigest()
            assert sha==report['source_sha256' if case=='form' else 'reference_source_sha256'],'native evidence is bound to different source bytes'
            doc=report['evidence'][case+'-gate']['document']
            self.cases[sha]=(case,doc)
    def execute(self,instrument,target,*,timeout_s=None):
        assert instrument=='vcheck --gate'
        sha=hashlib.sha256(Path(target).read_bytes()).hexdigest()
        assert sha in self.cases,'uncaptured bytes cannot receive a native replay verdict'
        case,original=self.cases[sha];self.seen.append(case);doc=copy.deepcopy(original);old=doc['target'];doc['target']=str(target)
        for field in ['diagnostics','findings','holes']:
            for record in doc[field]:
                if record.get('file')==old:record['file']=str(target)
        return tools.ToolResult(instrument,str(target),doc,doc['exit_code'],None,'replay','agent',P.text_sha256(json.dumps(doc,sort_keys=True)))


class Scripted:
    def __init__(self,target,hints):self.target=target;self.hints=hints;self.calls=[]
    def complete(self,message,*,system,seed):
        self.calls.append((json.loads(message),seed))
        proposal={'actions':[{'type':'edit','path':self.target,'old':'','new':json.dumps(self.hints)}]}
        return backends.Completion(json.dumps(proposal),structured=proposal,usage={'input_tokens':1,'output_tokens':2})


def hints_for(template,complete):
    task,_=engine.source_task(template);at=0;pattern=''
    for site in sorted(task.sites,key=lambda s:template.index(s.marker)):
        start=template.index(site.marker,at);pattern+=re.escape(template[at:start])+r'\(([^\n]*)\)';at=start+len(site.marker)
    pattern+=re.escape(template[at:]);match=re.fullmatch(pattern,complete)
    assert match,'completion must preserve original byte frame'
    hints={'hints':list(match.groups())}
    assert engine.render_hint_r12(task,engine.Hint(tuple(hints['hints'])))==complete
    return hints


def main():
    data=tomllib.loads((ROOT/'bench/local/r/labalpha-smoke/STRATUM.toml').read_text());cards=data['card'];assert len(cards)==40
    plan=batch.load_plan(ROOT/'bench/local/r/labalpha-smoke/plans/qwen.toml',ROOT)
    passed=0
    with tempfile.TemporaryDirectory(prefix='dvl0-r12-corpus-replay-') as directory:
        for card in cards:
            target=card['path'];text=(ROOT/target).read_text();complete=(ROOT/'Solutions'/target).read_text()
            assert P.text_sha256(text)==card['source_sha256']
            ctx=P.Context(card['id'],card['lang'],plan.task_statements[card['id']],(target,),(),target,material={'text':text,'instructions':plan.instructions})
            for arm,cls in [('independent',engine.R12Independent),('repair',engine.R12Repair),('best',engine.R12BestFirst),('best-raw',engine.R12BestFirstRaw)]:
                for kind,payload,want in [('correct',hints_for(text,complete),'verified'),('malformed',{'hints':[]},'malformed')]:
                    seed=batch.derive_seed(plan.seed,arm+'/'+card['id']+'/0/0',1)
                    meter=budget.Meter(budget.Caps(calls=1,turns=3));transport=Scripted(target,payload);runner=Captured(card)
                    ask=backends.candidate_ask(transport,target=target,meter=meter,system=plan.system)
                    run_dir=Path(directory)/(card['id']+'-'+arm+'-'+kind)
                    result=executor.Executor(ctx,{target:text},runner=runner,meter=meter,run_dir=run_dir).run(cls(ask,[seed]))
                    assert result.outcome==want,(card['id'],arm,kind,result.outcome)
                    assert result.files=={target:complete if kind=='correct' else text}
                    assert runner.seen==(['form','good'] if kind=='correct' else ['form'])
                    assert result.usage['calls']==1 and len(transport.calls)==1 and transport.calls[0][1]==seed
                    passed+=1
    assert passed==320
    # The recorded success may never be rebound to an edited reference body.
    card=cards[0]
    with tempfile.TemporaryDirectory(prefix='dvl0-r12-replay-drift-') as temporary:
        root=Path(temporary)
        for relative in [Path(card['path']),Path('Solutions')/card['path'],Path(card['admission']),Path('Solutions/plans/drafts/R12/lab-corpus')/card['id']/'admission.json']:
            dest=root/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/relative,dest)
        changed=root/'Solutions'/card['path'];changed.write_text(changed.read_text()+'// edited reference bytes\n')
        try:Captured(card,root)
        except AssertionError:pass
        else:raise AssertionError('edited reference received an old native success')
    print('R12 corpus replay:320/320controls passed (40tasks × 4fixed policies × correct/malformed).')
    print('Reference-drift control:old native success cannot be rebound to changed bytes.')
    print('Retained native evidence replay only; no live experiment, grade, model or container claim.')
    return 0


if __name__=='__main__':raise SystemExit(main())
