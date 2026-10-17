"""R12 fixed-site invariant environment; policies supply expression data only.

Templates, allowed identifiers, models and executable bodies are committed task
inputs. Expressions cannot add declarations, statements, attributes, comments,
strings, new lines or new lever keywords. Rendering is pure; only the frozen
executor may stage edits or run tools, with agent provenance and full acceptance.
This bounded hint space is not unrestricted proof/program synthesis.
"""
from dataclasses import dataclass
import re
from engine import Hint

_TOKEN=re.compile(r'[A-Za-z_][A-Za-z0-9_]*|[0-9]+|<==>|==>|&&|\|\||<=|>=|==|!=|::|[()\[\].@,:|+*/%<>=!&-]')
_IDENTIFIER=re.compile(r'[A-Za-z_][A-Za-z0-9_]*\Z')
_KEYWORDS=frozenset(['forall','exists','as','int','nat','bool','true','false'])
_FORBIDDEN=frozenset(['assume','admit','axiom','unsafe','external_body','proof_note','fn','method','function','lemma','module','mod','import','use','requires','ensures','decreases','invariant','return','while','loop','for','let','var','reveal','broadcast','unimplemented','panic'])

@dataclass(frozen=True)
class HintSite:
    name:str
    identifiers:tuple[str,...]
    def __post_init__(self):
        if not _IDENTIFIER.fullmatch(self.name):raise ValueError('site name')
        if any(not _IDENTIFIER.fullmatch(x) or x in _FORBIDDEN for x in self.identifiers):raise ValueError('allowed identifiers')
    @property
    def marker(self):return '/*R12_HINT:'+self.name+'*/ true'

@dataclass(frozen=True)
class HintTask:
    template:str
    sites:tuple[HintSite,...]
    def __post_init__(self):
        if not self.sites or len({s.name for s in self.sites})!=len(self.sites):raise ValueError('unique nonempty sites')
        if any(self.template.count(s.marker)!=1 for s in self.sites):raise ValueError('each frozen site exactly once')
        rest=self.template
        for site in self.sites:rest=rest.replace(site.marker,'')
        if 'R12_HINT:' in rest:raise ValueError('unlisted hint marker')

# item: R12.H5py
def render_hint_r12(task:HintTask,hint:Hint)->str:
    if len(hint.annotations)!=len(task.sites):raise ValueError('one expression per fixed site')
    rendered=task.template
    for site,expression in zip(task.sites,hint.annotations):
        if not expression or len(expression)>8192 or any(x in expression for x in ['\n','\r','\x00','//','/*','*/']):raise ValueError('invalid expression text')
        allowed=set(site.identifiers)|_KEYWORDS
        at=0
        while at<len(expression):
            if expression[at] in ' \t':at+=1;continue
            token=_TOKEN.match(expression,at)
            if token is None:raise ValueError('only invariant-expression tokens')
            word=token.group()
            if _IDENTIFIER.fullmatch(word) and (word not in allowed or word in _FORBIDDEN):raise ValueError('identifier outside frozen task vocabulary')
            at=token.end()
        rendered=rendered.replace(site.marker,'('+expression+')',1)
    return rendered
