import pytest
from profiler import profile_symbols_r12

def doc(**kw):
 d=dict(lang='dafny',target='x.dfy',exit_code=0,verdict='verified',stage='verify',verified_count=1,holes=[],diagnostics=[],findings=[],per_symbol={'M.F':'verified'},wall_s=.25,resource_count=None);d.update(kw);return d

def test_exact_commands_repeats_order_scopes_and_unavailable_resources():
 calls=[]
 def run(argv):calls.append(argv);return doc(per_symbol={argv[4]:'verified'})
 rows=profile_symbols_r12('x.dfy',['M.F','M.G'],repeats=2,run=run)
 assert [(r.symbol,r.repeat,r.resource_count) for r in rows]==[('M.F',0,None),('M.F',1,None),('M.G',0,None),('M.G',1,None)]
 assert all(c==['scripts/vcheck','--json','--measures','--symbol',r.symbol,'--isolate','x.dfy'] for c,r in zip(calls,rows))
 assert all(r.selected_status=='verified' for r in rows)

@pytest.mark.parametrize('verdict',['failed','inconclusive','refused','killed(memory)','error'])
def test_bad_native_outcomes_are_retained_not_dropped_or_promoted(verdict):
 rows=profile_symbols_r12('x',['M.F'],repeats=1,run=lambda _:doc(verdict=verdict,resource_count=0,per_symbol={'M.F':verdict}))
 assert rows[0].verdict==verdict and rows[0].selected_status==verdict and rows[0].resource_count==0

def test_missing_or_ambiguous_selected_symbol_visible_without_guessing():
 for per in [{},{'Other.F':'verified'},{'A::F':'verified','B::F':'failed'}]:
  sym='F' if 'A::F' in per else 'M.F'
  assert profile_symbols_r12('x',[sym],repeats=1,run=lambda _:doc(per_symbol=per))[0].selected_status is None

def test_measurements_required_even_if_result_looks_green():
 def run(_):d=doc();del d['wall_s'];return d
 with pytest.raises(ValueError):profile_symbols_r12('x',['F'],repeats=1,run=run)

@pytest.mark.parametrize('target,symbols,repeats',[('', ['F'],1),('x',[],1),('x',['F','F'],1),('x',[None],1),('x',['F'],True),('x',['F'],0)])
def test_invalid_requests_fail_before_any_native_call(target,symbols,repeats):
 with pytest.raises(ValueError):profile_symbols_r12(target,symbols,repeats=repeats,run=lambda _:pytest.fail())
