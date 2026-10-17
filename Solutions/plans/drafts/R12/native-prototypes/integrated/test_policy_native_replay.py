"""Replay own real native results only for exact captured source hashes.

No live policy, model or container run. Only file/diagnostic paths are remapped
for frozen executor staging; original native documents/sources remain retained.
"""
from pathlib import Path
import copy,json,hashlib
import pytest
from fvh import protocol as P,executor,tools,budget,backends
from fvh.tools import runners as R
from policy_adapter import R12Independent,R12Repair,R12BestFirst,R12BestFirstRaw

B=Path('/tmp/dvl0-dvr2-r12/policy-native')

class CapturedNativeRunner(R.Runner):
 name='replay';isolated=True
 def __init__(self,lang):
  self.cases={};self.seen=[]
  for case in ['baseline','good','weak']:
   source=B/(case+'-'+lang+('.dfy' if lang=='d' else '.rs'));data=source.read_bytes();doc=json.loads((B/(case+'-'+lang+'.json')).read_text());self.cases[hashlib.sha256(data).hexdigest()]=(case,doc)
 def execute(self,instrument,target,*,timeout_s=None):
  assert instrument=='vcheck --gate'
  sha=hashlib.sha256(Path(target).read_bytes()).hexdigest();assert sha in self.cases,'uncaptured source cannot receive a replay verdict'
  case,original=self.cases[sha];self.seen.append(case);doc=copy.deepcopy(original);old=doc['target'];doc['target']=str(target)
  for field in ['diagnostics','findings','holes']:
   for item in doc[field]:
    if item.get('file')==old:item['file']=str(target)
  return tools.ToolResult(instrument,str(target),doc,doc['exit_code'],None,'replay','agent',hashlib.sha256(json.dumps(doc,sort_keys=True).encode()).hexdigest())

class ScriptedHintTransport:
 def __init__(self,target,hints):self.target=target;self.hints=list(hints);self.calls=[]
 def complete(self,message,*,system,seed):
  self.calls.append((json.loads(message),seed));hint=self.hints[len(self.calls)-1]
  proposal={'actions':[{'type':'edit','path':self.target,'old':'','new':json.dumps(hint)}]}
  return backends.Completion(json.dumps(proposal),structured=proposal,usage={'input_tokens':1,'output_tokens':2})

@pytest.mark.parametrize('lang',['d','v'])
@pytest.mark.parametrize('cls',[R12Independent,R12Repair,R12BestFirst,R12BestFirstRaw])
def test_real_native_source_hashes_through_candidate_codec_meter_and_executor(lang,cls,tmp_path):
 text=(B/('template-'+lang+'.txt')).read_text();good=json.loads((B/('good-hint-'+lang+'.json')).read_text());target='task'+('.dfy' if lang=='d' else '.rs');native_lang='dafny' if lang=='d' else 'verus'
 ctx=P.Context('native-'+lang,native_lang,'R12_TASK_SHA256: '+P.text_sha256(text)+'\noriginal invariant-repair goal',(target,),(),target,material={'text':text})
 meter=budget.Meter(budget.Caps(calls=2,turns=4))
 transport=ScriptedHintTransport(target,[{'invariants':['true','true']},good])
 ask=backends.candidate_ask(transport,target=target,meter=meter)
 policy=cls(ask,[101,202]);runner=CapturedNativeRunner(lang)
 ex=executor.Executor(ctx,{target:text},runner=runner,meter=meter,run_dir=tmp_path)
 result=ex.run(policy)
 assert result.outcome=='verified' and result.ended_by=='stop'
 assert runner.seen==['baseline','weak','good']
 assert [seed for _,seed in transport.calls]==[101,202]
 assert result.usage['calls']==2 and result.usage['turns']==4
 assert result.usage['input_tokens']==2 and result.usage['output_tokens']==4
 assert policy.engine.solved and len(policy.engine.attempts)==2 and policy.engine.pending is None
 good_source=(B/('good-'+lang+('.dfy' if lang=='d' else '.rs'))).read_text()
 assert result.files[target]==good_source
 assert all(row.outcome is not None for row in policy.engine.attempts)

@pytest.mark.parametrize('lang',['d','v'])
def test_localized_feedback_refers_to_original_native_source_symbols(lang,tmp_path):
 text=(B/('template-'+lang+'.txt')).read_text();good=json.loads((B/('good-hint-'+lang+'.json')).read_text());target='task'+('.dfy' if lang=='d' else '.rs');native_lang='dafny' if lang=='d' else 'verus'
 ctx=P.Context('native-'+lang,native_lang,'R12_TASK_SHA256: '+P.text_sha256(text)+'\noriginal goal',(target,),(),target,material={'text':text});meter=budget.Meter(budget.Caps(calls=1,turns=3));transport=ScriptedHintTransport(target,[good]);runner=CapturedNativeRunner(lang)
 result=executor.Executor(ctx,{target:text},runner=runner,meter=meter).run(R12BestFirst(backends.candidate_ask(transport,target=target,meter=meter),[31]))
 feedback=transport.calls[0][0]['feedback']
 assert feedback and any(x.get('symbol') is not None for x in feedback)
 assert all(x['stage']=='verify' and x['verdict']=='failed' for x in feedback)
 assert result.outcome=='verified'
