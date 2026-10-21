import pytest
from fvh_r.engine import Hint
from fvh_r.engine import HintSite,HintTask,render_hint_r12

def task():return HintTask('header\nwhile i<n\n invariant /*R12_HINT:bounds*/ true\n {i=i+1;}\n', (HintSite('bounds',('i','n','flags','len','take')),))

def test_valid_expression_changes_only_committed_site_and_keeps_code_exact():
 t=task();out=render_hint_r12(t,Hint(('0<=i && i<=n',)))
 assert out==t.template.replace(t.sites[0].marker,'(0<=i && i<=n)')
 assert '{i=i+1;}' in out

@pytest.mark.parametrize('expression',['true; return 0','true} fn injected(){}','true\nrequires false','# [verifier::external_body]','assume(false)','unsafe','unimplemented!()','/*comment*/true','//comment','panic!()','"literal"',"'c'",'unknown_model(i)','invariant false','0<=i\r\nreturn','true\x00false','use secret','decreases 0'])
def test_statement_attribute_comment_and_binding_escape_rejected(expression):
 with pytest.raises(ValueError):render_hint_r12(task(),Hint((expression,)))

@pytest.mark.parametrize('expression',['forall|j:int| 0<=j<i ==> flags@[j]','flags.len()==n','flags.take(i).len()<=n','false','i+1<=n'])
def test_native_pure_expression_forms_allowed_without_claiming_they_verify(expression):
 t=HintTask(task().template,(HintSite('bounds',('i','j','n','flags','take','len')),))
 assert '('+expression+')' in render_hint_r12(t,Hint((expression,)))

def test_wrong_count_unknown_duplicate_or_missing_sites_rejected():
 with pytest.raises(ValueError):render_hint_r12(task(),Hint(()))
 with pytest.raises(ValueError):HintTask('/*R12_HINT:other*/ true',task().sites)
 with pytest.raises(ValueError):HintTask(task().template,task().sites*2)
 with pytest.raises(ValueError):HintSite('bad',('assume',))
 with pytest.raises(ValueError):HintTask(task().template+'/*R12_HINT:other*/ true',task().sites)


def call_task():
    site=HintSite('step',('probe_index','probe_limit'),kind='calls',callees=('unfold_window_r12','transport_window_r12'))
    return HintTask('proof { '+site.marker+' }',(site,))

def test_approved_proof_calls_are_data_rendered_inside_fixed_ghost_context():
    task=call_task()
    assert render_hint_r12(task,Hint(('unfold_window_r12(probe_index+1,probe_limit); transport_window_r12(probe_index,probe_limit)',)))=='proof { unfold_window_r12(probe_index+1,probe_limit); transport_window_r12(probe_index,probe_limit); }'

@pytest.mark.parametrize('text',['assume(false)','unapproved(probe_index)','unfold_window_r12(probe_index); return 0','unfold_window_r12(probe_index)); injected(probe_limit)','unfold_window_r12("text")','unfold_window_r12(unknown)','unfold_window_r12(probe_index) } unsafe {',';','unfold_window_r12((probe_index,probe_limit)'])
def test_proof_call_sites_cannot_add_code_bindings_trust_or_new_callees(text):
    with pytest.raises(ValueError):render_hint_r12(call_task(),Hint((text,)))

def test_proof_call_metadata_requires_trusted_nonempty_callees():
    for kw in [dict(kind='calls'),dict(kind='calls',callees=('assume',)),dict(kind='expr',callees=('unfold_window_r12',))]:
        with pytest.raises(ValueError):HintSite('site',(),**kw)


# D63 (DELTAS Δ296): a site may carry no identifier list (any identifier outside the forbidden
# words), and a decreases site renders like an expression site from its verify-failing placeholder.
def open_task():
    return HintTask('header\nwhile i<n\n invariant /*R12_HINT:bounds*/ true\n decreases /*R12_DECREASES:measure*/ (0 as int)\n {i=i+1;}\n',
                    (HintSite('bounds',None),HintSite('measure',None,kind='decreases')))

def test_open_vocabulary_and_decreases_sites_render_like_expressions():
    t=open_task();out=render_hint_r12(t,Hint(('any_name(i) <= n','n - i')))
    assert ' invariant (any_name(i) <= n)\n decreases (n - i)\n' in out and '{i=i+1;}' in out

@pytest.mark.parametrize('pair',[('assume(false)','n - i'),('true','decreases 0'),('true','n - i; return 0'),('true','n - i} fn x(){}'),('true','unsafe')])
def test_open_vocabulary_still_rejects_forbidden_words_and_escapes(pair):
    with pytest.raises(ValueError):render_hint_r12(open_task(),Hint(pair))

def test_decreases_site_metadata_and_marker():
    assert HintSite('m',None,kind='decreases').marker=='/*R12_DECREASES:m*/ (0 as int)'
    with pytest.raises(ValueError):HintSite('m',None,kind='decreases',callees=('f',))
    with pytest.raises(ValueError):HintTask('x /*R12_DECREASES:other*/ (0 as int)',(HintSite('m',None,kind='decreases'),))
