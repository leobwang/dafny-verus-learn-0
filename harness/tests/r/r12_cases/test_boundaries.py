"""Provided model-boundary controls alongside all five learner algorithms."""
from dataclasses import FrozenInstanceError
import pytest
from fvh_r.engine import SourceSpan,NativeRun

@pytest.mark.parametrize('start,end',[(True,2),(0,2),(3,2),(1,False)])
def test_invalid_native_coordinate_domains_are_rejected(start,end):
 with pytest.raises(ValueError):SourceSpan('dafny','x.dfy','M',start,end)

def test_only_supported_language_and_original_file_identity_are_admitted():
 with pytest.raises(ValueError):SourceSpan('python','x.py','M',1,2)
 span=SourceSpan('dafny','nested/x.dfy','M',1,2)
 with pytest.raises(FrozenInstanceError):span.file='different/x.dfy'
 assert span.file=='nested/x.dfy'

from dataclasses import FrozenInstanceError
import pytest
from fvh_r.engine import Trace

@pytest.mark.parametrize('reason',['verified','unknown','',None])
def test_unknown_stop_labels_are_rejected(reason):
 with pytest.raises(ValueError):Trace((),reason)

def test_stop_record_cannot_be_relabelled_after_collection():
 trace=Trace((),'budget')
 with pytest.raises(FrozenInstanceError):trace.reason='accepted'
 with pytest.raises(ValueError):Trace([None],'budget')

import pytest
from fvh_r.engine import HintSite,HintTask

@pytest.mark.parametrize('name,identifiers',[('',()),('bad-name',()),('ok',('assume',)),('ok',('new name',))])
def test_invalid_task_vocabulary_is_rejected(name,identifiers):
 with pytest.raises(ValueError):HintSite(name,identifiers)

def test_every_committed_site_is_unique_and_listed_exactly_once():
 site=HintSite('one',('i',));text=site.marker
 with pytest.raises(ValueError):HintTask(text,(site,site))
 with pytest.raises(ValueError):HintTask(text+' '+text,(site,))
 with pytest.raises(ValueError):HintTask(text+' /*R12_HINT:other*/ true',(site,))
 with pytest.raises(ValueError):HintTask('no site',(site,))

