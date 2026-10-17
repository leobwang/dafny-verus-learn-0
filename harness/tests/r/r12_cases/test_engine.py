import pytest
from fvh_r.engine import SearchR12,Hint,Outcome,FrontierExhausted
from fvh_r.engine import drive_r12

def initial(score=3):return Outcome(False,score,{'stage':'verify','original':True})
def make(width,depth,priority):return SearchR12(initial(),width=width,depth=depth,priority=priority)
def ask(req):return Hint((str(req.node),str(req.depth)))
def fail(hint):return Outcome(False,3,{'not_a_pass':'verified'})

@pytest.mark.parametrize('width,depth,priority,parents',[(10,1,'fifo',[0]*10),(1,10,'lifo',list(range(10)))])
def test_independent_and_repair_are_configurations_of_one_engine(width,depth,priority,parents):
    e=make(width,depth,priority);trace=drive_r12(e,ask,fail,nodes=10)
    assert [x.parent for x in trace.attempts]==parents and trace.reason=='budget'

def test_best_first_selects_actual_lower_obligation_parent_with_stable_ties():
    scores=iter([5,1,4,0]);e=make(3,10,'best')
    trace=drive_r12(e,ask,lambda _:Outcome(False,next(scores),None),nodes=4)
    assert [x.parent for x in trace.attempts]==[0,0,2,2]
    assert not e.solved # score zero is not trusted acceptance

@pytest.mark.parametrize('config',[(10,1,'fifo'),(1,10,'lifo'),(3,10,'best')])
def test_budget_prefixes_equal_one_continuous_run(config):
    e=make(*config);whole=drive_r12(e,ask,fail,nodes=10)
    e2=make(*config);prefix=[]
    for _ in range(10):prefix.extend(drive_r12(e2,ask,fail,nodes=1).attempts)
    assert tuple(prefix)==whole.attempts
    for b in range(11):
        fresh=make(*config);assert drive_r12(fresh,ask,fail,nodes=b).attempts==whole.attempts[:b]

def test_equal_cap_counts_malformed_samples_and_parent_width_without_tool_call():
    calls=[];e=make(3,2,'fifo')
    def malformed(req):calls.append(req);return {'accepted':True}
    trace=drive_r12(e,malformed,lambda _:pytest.fail('malformed data reached executor'),nodes=10)
    assert len(trace.attempts)==3 and len(calls)==3 and trace.reason=='frontier'
    assert all(x.status=='malformed' for x in trace.attempts) and not e.solved

def test_stops_only_on_trusted_acceptance_not_text_or_model_fields():
    e=make(10,1,'fifo');calls=[]
    def judge(h):calls.append(h);return Outcome(len(calls)==3,0,{'text':'verified'})
    trace=drive_r12(e,ask,judge,nodes=10)
    assert len(calls)==3 and trace.reason=='accepted'
    assert len(drive_r12(e,lambda _:pytest.fail('already solved sampled'),judge,nodes=9).attempts)==0

def test_unavailable_score_is_not_favorable_and_initial_success_samples_nothing():
    e=make(3,3,'best');scores=iter([None,1]);trace=drive_r12(e,ask,lambda _:Outcome(False,next(scores),None),nodes=2)
    assert [x.parent for x in trace.attempts]==[0,0]
    solved=SearchR12(Outcome(True,0,None),width=3,depth=3,priority='best')
    assert drive_r12(solved,lambda _:pytest.fail(),lambda _:pytest.fail(),nodes=4).reason=='accepted'

def test_zero_budget_no_generation_no_judgement_and_infrastructure_failure_propagates():
    e=make(2,2,'fifo');assert drive_r12(e,lambda _:pytest.fail(),lambda _:pytest.fail(),nodes=0).reason=='budget'
    def broken(h):raise RuntimeError('runner unavailable')
    with pytest.raises(RuntimeError,match='runner unavailable'):drive_r12(e,ask,broken,nodes=1)

@pytest.mark.parametrize('config',[(True,2,'fifo'),(0,2,'fifo'),(2,-1,'fifo'),(2,2,'score-is-proof')])
def test_bad_fixed_configuration_rejected(config):
    with pytest.raises(ValueError):make(*config)

@pytest.mark.parametrize('nodes',[True,-1,1.5])
def test_bad_budget_rejected(nodes):
    with pytest.raises(ValueError):drive_r12(make(2,2,'fifo'),ask,fail,nodes=nodes)


def test_async_stage_counts_generation_and_needs_trusted_observation():
    e=make(3,3,'best');row=e.stage(ask)
    assert len(e.attempts)==1 and row.status=='pending' and not e.solved
    with pytest.raises(RuntimeError,match='observe'):e.stage(ask)
    completed=e.observe(Outcome(False,1,{'stage':'verify'}))
    assert completed.status=='observed' and completed.index==row.index
    assert len(e.attempts)==1 and e.pending is None
    with pytest.raises(RuntimeError,match='no staged'):e.observe(Outcome(True,0,None))


def test_trusted_runner_failure_keeps_pending_generation_in_accounting():
    e=make(2,2,'fifo')
    def broken(h):raise RuntimeError('runner unavailable')
    with pytest.raises(RuntimeError):e.expand(ask,broken)
    assert len(e.attempts)==1 and e.attempts[0].status=='pending' and not e.solved


def test_sync_and_async_paths_have_identical_topology_and_prefixes():
    a=make(3,10,'best');b=make(3,10,'best')
    for _ in range(10):
        sync=a.expand(ask,fail);staged=b.stage(ask);async_result=b.observe(fail(staged.hint))
        assert sync==async_result and a.attempts==b.attempts


def test_provider_exception_is_recorded_then_propagated_without_acceptance():
    e=make(3,3,'best')
    def unavailable(request):raise RuntimeError('transport unavailable')
    with pytest.raises(RuntimeError,match='transport unavailable'):e.stage(unavailable)
    assert len(e.attempts)==1 and e.attempts[0].status=='proposal-error'
    assert not e.solved and e.nodes[0].expanded==1
