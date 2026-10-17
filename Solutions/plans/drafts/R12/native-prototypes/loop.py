"""R12 bounded verdict loop. Callbacks are the policy and trusted executor.

No subprocess, file write, model call, source eval or acceptance heuristic lives
here. Every generated node counts, including malformed output. Exhaustion and
accepted initial forms stop without a generation call. A failure in the trusted
executor propagates; it is infrastructure failure rather than a fake outcome.
"""
from dataclasses import dataclass
from engine import FrontierExhausted

@dataclass(frozen=True)
class Trace:
    attempts:tuple
    reason:str

# item: R12.H3py
def drive_r12(engine,ask,judge,*,nodes:int)->Trace:
    if type(nodes) is not int or nodes<0:raise ValueError('nonnegative node cap')
    start=len(engine.attempts)
    reason='budget'
    for _ in range(nodes):
        if engine.solved:reason='accepted';break
        try:row=engine.expand(ask,judge)
        except FrontierExhausted:reason='frontier';break
        if row.status=='accepted':reason='accepted';break
    if engine.solved:reason='accepted'
    return Trace(tuple(engine.attempts[start:]),reason)
