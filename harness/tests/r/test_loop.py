"""Provided immutable trace boundary; drive semantics are tested in engine."""
from dataclasses import FrozenInstanceError
import pytest
from fvh_r.loop import Trace

@pytest.mark.parametrize('reason',['verified','unknown','',None])
def test_unknown_stop_labels_are_rejected(reason):
 with pytest.raises(ValueError):Trace((),reason)

def test_stop_record_cannot_be_relabelled_after_collection():
 trace=Trace((),'budget')
 with pytest.raises(FrozenInstanceError):trace.reason='accepted'
 with pytest.raises(ValueError):Trace([None],'budget')
