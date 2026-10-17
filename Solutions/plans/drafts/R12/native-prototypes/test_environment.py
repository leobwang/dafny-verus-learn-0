import pytest
from engine import Hint
from environment import HintSite,HintTask,render_hint_r12

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
