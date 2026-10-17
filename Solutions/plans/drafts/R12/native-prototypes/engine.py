"""R12 one deterministic search engine with fixed width/depth/priority.

Policies produce Hint data only. A trusted executor adapter supplies Outcome;
its accepted flag represents full native gate/audit/freeze acceptance, never
model output or a diagnostic substring. Model and tool attempts are recorded
separately; malformed proposals consume a node and the parent's width slot.
Budget prefixes do not change configuration or replay previous generation calls.
"""
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Hint:
    annotations:tuple[str,...]
    def __post_init__(self):
        if type(self.annotations) is not tuple or any(not isinstance(x,str) for x in self.annotations):raise ValueError('hint annotations must be a tuple of strings')
        if sum(len(x) for x in self.annotations)>65536:raise ValueError('hint too large')

@dataclass(frozen=True)
class Outcome:
    accepted:bool
    score:int|None
    feedback:object
    def __post_init__(self):
        if type(self.accepted) is not bool:raise ValueError('accepted is a trusted Boolean')
        if self.score is not None and (type(self.score) is not int or self.score<0):raise ValueError('score is a nonnegative obligation count or unavailable')

@dataclass(frozen=True)
class Request:
    node:int
    depth:int
    hint:Hint
    feedback:object

@dataclass(frozen=True)
class Attempt:
    index:int
    parent:int
    hint:Hint|None
    outcome:Outcome|None
    status:str

@dataclass
class Node:
    id:int
    depth:int
    hint:Hint
    outcome:Outcome
    expanded:int=0

class FrontierExhausted(LookupError):pass

class SearchR12:
    """Configuration is fixed before calls; ask/judge are injected capabilities."""
    def __init__(self,initial:Outcome,*,width:int,depth:int,priority:str):
        if type(width) is not int or width<1 or type(depth) is not int or depth<1:raise ValueError('positive fixed width/depth')
        if priority not in ['fifo','lifo','best']:raise ValueError('priority')
        self.width,self.depth,self.priority=width,depth,priority
        self.nodes=[Node(0,0,Hint(()),initial)]
        self.attempts=[]
        self.solved=initial.accepted

    # item: R12.H4py
    def expand(self,ask,judge)->Attempt:
        if self.solved:raise FrontierExhausted('already solved')
        eligible=[n for n in self.nodes if n.depth<self.depth and n.expanded<self.width]
        if not eligible:raise FrontierExhausted('fixed frontier exhausted')
        if self.priority=='fifo':parent=min(eligible,key=lambda n:n.id)
        elif self.priority=='lifo':parent=max(eligible,key=lambda n:n.id)
        else:parent=min(eligible,key=lambda n:(n.outcome.score if n.outcome.score is not None else math.inf,n.id))
        parent.expanded+=1
        index=len(self.attempts)
        try:
            hint=ask(Request(parent.id,parent.depth,parent.hint,parent.outcome.feedback))
            if not isinstance(hint,Hint):raise ValueError('a model returns Hint data, never Outcome or actions')
        except (ValueError,TypeError):
            row=Attempt(index,parent.id,None,None,'malformed');self.attempts.append(row);return row
        outcome=judge(hint)
        if not isinstance(outcome,Outcome):raise TypeError('trusted executor must return Outcome')
        node=Node(index+1,parent.depth+1,hint,outcome);self.nodes.append(node)
        self.solved=outcome.accepted
        row=Attempt(index,parent.id,hint,outcome,'accepted' if outcome.accepted else 'observed')
        self.attempts.append(row)
        return row
