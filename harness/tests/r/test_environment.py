"""Provided committed-site model boundary; renderer semantics are tested in engine."""
import pytest
from fvh_r.environment import HintSite,HintTask

@pytest.mark.parametrize('name,identifiers',[('',()),('bad-name',()),('ok',('assume',)),('ok',('new name',))])
def test_invalid_task_vocabulary_is_rejected(name,identifiers):
 with pytest.raises(ValueError):HintSite(name,identifiers)

def test_every_committed_site_is_unique_and_listed_exactly_once():
 site=HintSite('one',('i',));text=site.marker
 with pytest.raises(ValueError):HintTask(text,(site,site))
 with pytest.raises(ValueError):HintTask(text+' '+text,(site,))
 with pytest.raises(ValueError):HintTask(text+' /*R12_HINT:other*/ true',(site,))
 with pytest.raises(ValueError):HintTask('no site',(site,))
