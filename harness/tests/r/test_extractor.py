"""Provided extractor data boundary; full parsing/localization is tested in engine."""
from dataclasses import FrozenInstanceError
import pytest
from fvh_r.extractor import SourceSpan,NativeRun

@pytest.mark.parametrize('start,end',[(True,2),(0,2),(3,2),(1,False)])
def test_invalid_native_coordinate_domains_are_rejected(start,end):
 with pytest.raises(ValueError):SourceSpan('dafny','x.dfy','M',start,end)

def test_only_supported_language_and_original_file_identity_are_admitted():
 with pytest.raises(ValueError):SourceSpan('python','x.py','M',1,2)
 span=SourceSpan('dafny','nested/x.dfy','M',1,2)
 with pytest.raises(FrozenInstanceError):span.file='different/x.dfy'
 assert span.file=='nested/x.dfy'
