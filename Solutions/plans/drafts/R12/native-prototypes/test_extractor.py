import copy,json
import pytest
from extractor import NativeRun,SourceSpan,Obligation,result_stream,localize

def doc(**kw):
    d=dict(lang='dafny',target='sample.dfy',exit_code=0,verdict='verified',stage='verify',verified_count=2,holes=[],diagnostics=[],findings=[],per_symbol={})
    d.update(kw);return d

def error(file='sample.dfy',line=9,**kw):
    d=dict(file=file,line=line,col=3,severity='error',message='postcondition could not be proved',code='W-D10');d.update(kw);return d

def run(d):return result_stream([json.dumps(d)])[0]

def test_order_all_verdicts_and_all_fields_retained():
    docs=[doc(verdict=v,stage='parse' if i%2 else 'verify',metadata={'literal':'verified is just text'},resource_count=None) for i,v in enumerate(['verified','failed','inconclusive','refused','killed(memory)','error'])]
    rows=result_stream(map(json.dumps,docs));assert [r.line for r in rows]==list(range(1,7));assert [r.document for r in rows]==docs

def test_empty_stream_is_empty_and_not_proof():
    assert result_stream([])==();assert localize((),())==()

@pytest.mark.parametrize('change',[{'lang':'rust'},{'verdict':'ok'},{'stage':'translate'},{'target':''},{'exit_code':True},{'exit_code':'0'},{'verified_count':False},{'verified_count':-1},{'holes':{}},{'diagnostics':[{}]},{'findings':[{}]},{'per_symbol':[]},{'per_symbol':{'a':False}},{'wall_s':False},{'wall_s':None},{'wall_s':-1},{'wall_s':float('inf')},{'resource_count':float('nan')},{'resource_count':'1'},{'diagnostics':[error(line=-1)]},{'diagnostics':[error(col=True)]},{'diagnostics':[error(severity='hint')]},{'holes':[dict(file='x',line=0,col=0,kind='assume')]}])
def test_malformed_row_fails_atomically_with_one_based_line(change):
    with pytest.raises(ValueError,match='line 2:'):
        result_stream([json.dumps(doc()),json.dumps(doc(**change)),json.dumps(doc())])

@pytest.mark.parametrize('key',['lang','target','verdict','stage','verified_count','exit_code','holes','diagnostics','findings','per_symbol'])
def test_missing_required_key_rejected(key):
    d=doc();del d[key]
    with pytest.raises(ValueError,match='line 1:'):result_stream([json.dumps(d)])

@pytest.mark.parametrize('line',['','   ','[]','null','{}','not-json','{"lang":"dafny","lang":"verus"}'])
def test_nonobject_blank_invalid_and_duplicate_fields_rejected(line):
    with pytest.raises(ValueError,match='line 1:'):result_stream([line])

def test_diagnostic_exact_span_and_nested_innermost():
    d=doc(verdict='failed',exit_code=1,diagnostics=[error()]);spans=[SourceSpan('dafny','sample.dfy','Outer',1,20),SourceSpan('dafny','sample.dfy','Inner',7,11)]
    assert localize([run(d)],spans)==(Obligation(0,'dafny','sample.dfy','verify','failed','diagnostic','Inner','sample.dfy',9,3,error()['message']),)

@pytest.mark.parametrize('spans',[[SourceSpan('verus','sample.dfy','WrongLanguage',1,20)],[SourceSpan('dafny','elsewhere/sample.dfy','WrongPath',1,20)],[SourceSpan('dafny','sample.dfy','After',10,20)],[SourceSpan('dafny','sample.dfy','A',1,20),SourceSpan('dafny','sample.dfy','B',1,20)]])
def test_unknown_path_language_position_and_ambiguity_remain_unlocalized(spans):
    assert localize([run(doc(verdict='failed',diagnostics=[error()]))],spans)[0].symbol is None
    assert localize([run(doc(verdict='failed',diagnostics=[error()]))],spans)[0].kind=='unlocalized'

def test_symbol_failures_no_duplicate_for_diagnostic_and_no_text_guessing():
    d=doc(verdict='failed',diagnostics=[error(message='verified F2 completed')],per_symbol={'F1':'failed','F2':'inconclusive'})
    rows=localize([run(d)],[SourceSpan('dafny','sample.dfy','F1',1,20)])
    assert [x.kind for x in rows]==['diagnostic','symbol-status'];assert [x.symbol for x in rows]==['F1','F2'];assert rows[1].message=='inconclusive'

@pytest.mark.parametrize('verdict',['failed','inconclusive','refused','killed(memory)','error'])
def test_empty_diagnostic_failure_stays_visible(verdict):
    rows=localize([run(doc(verdict=verdict,diagnostics=[]))],[])
    assert len(rows)==1 and rows[0].kind=='status' and rows[0].verdict==verdict

def test_loop_green_holes_compile_and_zero_counts_not_adjudicated_as_proof():
    d=doc(holes=[dict(file='x',line=4,col=0,kind='assume',label='')]);assert localize([run(d)],[])[0].kind=='unfinished'
    assert localize([run(doc(stage='compile'))],[])[0].kind=='non-proof-stage'
    assert localize([run(doc(verified_count=0))],[])[0].kind=='missing-proof-count'
    assert localize([run(doc(verified_count=None))],[])[0].kind=='missing-proof-count'

def test_warning_related_and_extra_metadata_not_lost_or_executed():
    d=doc(diagnostics=[error(severity='warning'),error(severity='related')],unsafe_text='$(never executed)')
    parsed=run(d);assert parsed.document==d;assert localize([parsed],[])==()

def test_different_runs_and_languages_never_combined():
    docs=[doc(verdict='failed',diagnostics=[error()]),doc(lang='verus',verdict='failed',diagnostics=[error()])]
    rows=localize(result_stream(map(json.dumps,docs)),[SourceSpan('dafny','sample.dfy','D',1,20),SourceSpan('verus','sample.dfy','V',1,20)])
    assert [(r.run,r.lang,r.symbol) for r in rows]==[(0,'dafny','D'),(1,'verus','V')]
