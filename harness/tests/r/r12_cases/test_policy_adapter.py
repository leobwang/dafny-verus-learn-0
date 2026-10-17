import json
from pathlib import Path
import pytest
from fvh import protocol as P,executor,tools,backends
from fvh.tools import runners as R
from fvh_r.engine import HintTask,render_hint_r12
from fvh_r.engine import Hint
from fvh_r.engine import R12BestFirst,R12Independent,R12Repair,R12BestFirstRaw,source_task,native_outcome

META=json.dumps([dict(name='bounds',identifiers=['i','n'])],separators=(',',':'))
TEXT='// R12_HINT_SITES: '+META+'\nmodule Example {method M(n:nat){var i:=0;while i<n\n invariant /*R12_HINT:bounds*/ true\n {i:=i+1;}}}\n'
TASK,SPANS=source_task(TEXT)
GOOD=TEXT.replace('/*R12_HINT:bounds*/ true','(0<=i<=n)')
WEAK=TEXT.replace('/*R12_HINT:bounds*/ true','(true)')

def doc(target='task.dfy',good=False,**changes):
 d=dict(lang='dafny',target=target,verdict='verified' if good else 'failed',stage='verify',exit_code=0 if good else 1,verified_count=2 if good else 1,holes=[],findings=[],diagnostics=[] if good else [dict(file=target,line=3,col=2,severity='error',message='native obligation',code='')],per_symbol={})
 d.update(changes);return d

def ctx():return P.Context('fixture','dafny','R12_TASK_SHA256: '+P.text_sha256(TEXT)+'\noriginal fixed statement',('task.dfy',),(), 'task.dfy',material={'text':TEXT})

class RecordedShapeRunner(R.Runner):
 """Isolated fake acceptance for protocol tests; not a native proof result."""
 name='replay';isolated=True
 def __init__(self):self.texts=[]
 def execute(self,instrument,target,*,timeout_s=None):
  text=Path(target).read_text();self.texts.append(text)
  assert text in [TEXT,GOOD,WEAK], 'source escaped the exact rendered task frame'
  d=doc(str(target),text==GOOD)
  return tools.ToolResult(instrument,str(target),d,d['exit_code'],None,'replay','agent',P.text_sha256(json.dumps(d)))

@pytest.mark.parametrize('cls',[R12Independent,R12Repair,R12BestFirst,R12BestFirstRaw])
def test_seeded_policy_composes_frozen_executor_and_has_no_tool_capability(cls,tmp_path):
 calls=[]
 def ask(prompt,seed):calls.append((json.loads(prompt),seed));return json.dumps({'invariants':['0<=i<=n']})
 runner=RecordedShapeRunner();policy=cls(ask,[101,202,303]);e=executor.Executor(ctx(),{'task.dfy':TEXT},runner=runner,run_dir=tmp_path)
 result=e.run(policy)
 assert result.outcome=='verified' and result.files=={'task.dfy':GOOD}
 assert len(calls)==1 and calls[0][1]==101
 assert runner.texts==[TEXT,GOOD]
 assert policy.engine.solved and len(policy.engine.attempts)==1
 assert all(x in ['read','edit','verify','stop','refused'] for turn in e.history for x in [o.kind for o in turn.observations])

@pytest.mark.parametrize('response',[{'invariants':['true'],'accepted':True},{'actions':[]},{'invariants':['true; return 0']},{'invariants':['assume(false)']},{'invariants':[]},{'invariants':[True]}])
def test_model_fields_and_code_escape_never_become_executor_edits(response):
 calls=[]
 def ask(p,s):calls.append(1);return json.dumps(response)
 runner=RecordedShapeRunner();policy=R12BestFirst(ask,[1,2]);e=executor.Executor(ctx(),{'task.dfy':TEXT},runner=runner)
 result=e.run(policy)
 assert result.outcome=='malformed' and result.files=={'task.dfy':TEXT}
 assert len(calls)==1 and runner.texts==[TEXT]
 assert not policy.engine.solved and policy.engine.attempts[0].status=='malformed'


def test_generation_cap_and_pending_outcome_count_are_separate_from_executor_turns():
 calls=[]
 def ask(prompt,seed):calls.append(seed);return json.dumps({'invariants':['true']})
 p=R12Independent(ask,[11,22,33]);runner=RecordedShapeRunner();e=executor.Executor(ctx(),{'task.dfy':TEXT},runner=runner)
 result=e.run(p)
 assert calls==[11,22,33] and result.outcome=='failed'
 assert len(p.engine.attempts)==3 and p.engine.pending is None
 assert len(runner.texts)==4 # initial baseline plus exactly three native candidates
 assert all(row.status=='observed' for row in p.engine.attempts)


def test_stale_feedback_and_frame_changes_rejected_before_sampling():
 policy=R12BestFirst(lambda p,s:pytest.fail('stale context reached model'),[1])
 c=ctx();files={'task.dfy':P.text_sha256(TEXT)}
 assert policy.propose(P.State('fixture',0,files,None,()),c,P.Budget(None,None,None,None))==[P.Verify()]
 for changed_files,feedback in [(files,{**doc(),'files_sha256':{'task.dfy':'stale'}}),({'task.dfy':P.text_sha256('changed')},{**doc(),'files_sha256':{'task.dfy':P.text_sha256('changed')}})]:
  with pytest.raises(P.Malformed):policy.propose(P.State('fixture',1,changed_files,feedback,()),c,P.Budget(None,None,None,None))

@pytest.mark.parametrize('changes',[{'stage':'compile'},{'verified_count':0},{'holes':[dict(file='x',line=1,col=0,kind='assume')]},{'diagnostics':[dict(file='x',line=1,col=0,severity='error',message='bad')]},{'per_symbol':{'M':'failed'}}])
def test_green_native_text_with_wrong_scope_or_unfinished_evidence_not_accepted(changes):
 with pytest.raises(ValueError,match='full gate'):native_outcome(doc(good=True,**changes),ctx(),[])


def test_synthetic_kill_preserves_unknown_phase_and_no_favorable_score():
 d=dict(verdict='killed(memory)',killed='memory',exit_code=137,holes=[],diagnostics=[],verified_count=0)
 outcome=native_outcome(d,ctx(),[])
 assert outcome.accepted is False and outcome.score is None and outcome.feedback['native']==d


def test_transport_failure_keeps_frozen_truncation_or_deferral_status():
 for problem,want in [(backends.TransportError('proxy','offline',had_output=False),'truncated:proxy'),(backends.Deferred('window closed'),'deferred')]:
  def ask(p,s):raise problem
  runner=RecordedShapeRunner();e=executor.Executor(ctx(),{'task.dfy':TEXT},runner=runner)
  result=e.run(R12BestFirst(ask,[1]))
  assert result.outcome==want and result.outcome!='malformed'


@pytest.mark.parametrize('change',[lambda t:t.replace('original','changed'),lambda t:t.replace('var i:=0','var i:=1'),lambda t:t.replace('module Example','module Replaced')])
def test_buggy_renderer_cannot_change_fixed_source_frame(monkeypatch,change):
 import fvh_r.engine as adapter
 altered=change(GOOD)
 if altered==GOOD:altered=GOOD.replace('method M','method Changed')
 monkeypatch.setattr(adapter,'render_hint_r12',lambda task,hint:altered)
 runner=RecordedShapeRunner();policy=adapter.R12BestFirst(lambda p,s:json.dumps({'hints':['0<=i<=n']}),[1])
 result=executor.Executor(ctx(),{'task.dfy':TEXT},runner=runner).run(policy)
 assert result.outcome=='malformed' and result.files=={'task.dfy':TEXT}
 assert runner.texts==[TEXT]

@pytest.mark.parametrize('inserted',['true); assume(false); assert(true','true } method Injected() {','true /*hide*/','true\nreturn 0'])
def test_independent_frame_guard_rejects_structural_escape_even_if_renderer_is_wrong(inserted):
 from fvh_r.engine import check_source_frame
 with pytest.raises(ValueError):check_source_frame(TASK,TEXT.replace(TASK.sites[0].marker,inserted))


@pytest.mark.parametrize('statement',['unbound source','R12_TASK_SHA256: '+'0'*64,'R12_TASK_SHA256: '+P.text_sha256(TEXT)+'\nR12_TASK_SHA256: '+P.text_sha256(TEXT)])
def test_plan_digest_rejects_changed_unbound_or_duplicate_original_before_sampling_or_editing(statement):
 c=P.Context('fixture','dafny',statement,('task.dfy',),(),'task.dfy',material={'text':TEXT})
 runner=RecordedShapeRunner()
 result=executor.Executor(c,{'task.dfy':TEXT},runner=runner).run(R12BestFirst(lambda p,s:pytest.fail('unbound source reached model'),[1]))
 assert result.outcome=='malformed' and result.files=={'task.dfy':TEXT} and runner.texts==[TEXT] # frozen executor final check, no policy edit or model call


def test_green_original_benchmark_cannot_count_as_zero_call_model_success():
 class GreenOriginal(RecordedShapeRunner):
  def execute(self,instrument,target,*,timeout_s=None):
   self.texts.append(Path(target).read_text());d=doc(str(target),good=True)
   return tools.ToolResult(instrument,str(target),d,0,None,'replay','agent',P.text_sha256(json.dumps(d)))
 runner=GreenOriginal()
 result=executor.Executor(ctx(),{'task.dfy':TEXT},runner=runner).run(R12BestFirst(lambda p,s:pytest.fail('inadmissible baseline reached model'),[1]))
 assert result.outcome=='malformed' and result.files=={'task.dfy':TEXT} and runner.texts==[TEXT]
