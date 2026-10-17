"""R12 obligation localization over normalized pinned-wrapper documents.

One target per JSON line; no raw-tool text heuristics or success adjudication.
Preserve documents and order. Localization uses caller-supplied trusted source
spans, matches exact language/file paths and keeps unlocalized failures visible.
An empty obligation list is never evidence of a full gate or original fidelity.
"""
from __future__ import annotations
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import copy
import json
import math

VERDICTS=frozenset(['verified','failed','inconclusive','refused','killed(memory)','error'])
STAGES=frozenset(['cli','parse','resolve','verify','compile','test','run'])
LANGS=frozenset(['dafny','verus'])
SEVERITIES=frozenset(['error','warning','info','related'])

@dataclass(frozen=True)
class NativeRun:
    line:int
    document:dict

@dataclass(frozen=True)
class SourceSpan:
    lang:str
    file:str
    symbol:str
    start:int
    end:int
    def __post_init__(self):
        if self.lang not in LANGS or not isinstance(self.file,str) or not self.file or not isinstance(self.symbol,str) or not self.symbol:
            raise ValueError('span language/file/symbol')
        if any(isinstance(x,bool) or not isinstance(x,int) for x in [self.start,self.end]) or not 1<=self.start<=self.end:
            raise ValueError('span bounds')

@dataclass(frozen=True)
class Obligation:
    run:int
    lang:str
    target:str
    stage:str
    verdict:str
    kind:str
    symbol:str|None
    file:str
    line:int
    col:int
    message:str


def _integer(value, *, minimum=0, nullable=False):
    return (nullable and value is None) or (not isinstance(value,bool) and isinstance(value,int) and value>=minimum)


def _string(value, *, empty=False):
    return isinstance(value,str) and (empty or bool(value))


def _pairs(pairs):
    out={}
    for k,v in pairs:
        if k in out:raise ValueError('duplicate key')
        out[k]=v
    return out


# item: R12.H1py
def result_stream(lines:Iterable[str])->tuple[NativeRun,...]:
    out=[]
    for number,line in enumerate(lines,1):
        try:
            d=json.loads(line,object_pairs_hook=_pairs,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
            if not isinstance(d,dict):raise ValueError('expected one result object')
            if d.get('lang') not in LANGS or d.get('verdict') not in VERDICTS or d.get('stage') not in STAGES:raise ValueError('language/verdict/stage')
            if not _string(d.get('target')):raise ValueError('target')
            if 'exit_code' not in d or not _integer(d['exit_code'],minimum=-2**63,nullable=True):raise ValueError('exit_code')
            if 'verified_count' not in d or not _integer(d['verified_count'],nullable=True):raise ValueError('verified_count')
            if not isinstance(d.get('per_symbol'),dict) or any(not _string(k) or not _string(v) for k,v in d['per_symbol'].items()):raise ValueError('per_symbol')
            for field in ['holes','diagnostics','findings']:
                if not isinstance(d.get(field),list) or any(not isinstance(x,dict) for x in d[field]):raise ValueError(field)
            for x in d['diagnostics']:
                if not _string(x.get('file'),empty=True) or not _integer(x.get('line')) or not _integer(x.get('col')) or x.get('severity') not in SEVERITIES or not _string(x.get('message'),empty=True):raise ValueError('diagnostic')
                if 'code' in x and not _string(x['code'],empty=True):raise ValueError('diagnostic code')
            for x in d['holes']:
                if not _string(x.get('file')) or not _integer(x.get('line'),minimum=1) or not _integer(x.get('col')) or not _string(x.get('kind')):raise ValueError('hole')
                if 'label' in x and not _string(x['label'],empty=True):raise ValueError('hole label')
            for x in d['findings']:
                if not _string(x.get('file'),empty=True) or not _integer(x.get('line')) or not _string(x.get('kind')) or not _string(x.get('message'),empty=True):raise ValueError('finding')
            for key in ['wall_s','resource_count']:
                if key not in d:continue
                value=d[key]
                if value is None and key=='resource_count':continue
                if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:raise ValueError(key)
        except (TypeError,ValueError) as e:
            raise ValueError(f'line {number}: malformed wrapper result ({e})') from e
        out.append(NativeRun(number,copy.deepcopy(d)))
    return tuple(out)


# item: R12.H2py
def localize(runs:Sequence[NativeRun],spans:Sequence[SourceSpan])->tuple[Obligation,...]:
    out=[]
    for number,run in enumerate(runs):
        d=run.document
        def emit(kind,file='',line=0,col=0,message='',symbol=None):
            out.append(Obligation(number,d['lang'],d['target'],d['stage'],d['verdict'],kind,symbol,file,line,col,message))
        errors=[x for x in d['diagnostics'] if x['severity']=='error']
        seen=set()
        for diagnostic in errors:
            candidates=[s for s in spans if s.lang==d['lang'] and s.file==diagnostic['file'] and s.start<=diagnostic['line']<=s.end]
            innermost=[s for s in candidates if not any(t.start>=s.start and t.end<=s.end and (t.start>s.start or t.end<s.end) for t in candidates)]
            names={s.symbol for s in innermost}
            symbol=next(iter(names)) if len(names)==1 else None
            if symbol is not None:seen.add(symbol)
            emit('diagnostic' if symbol is not None else 'unlocalized',diagnostic['file'],diagnostic['line'],diagnostic['col'],diagnostic['message'],symbol)
        for symbol,status in d['per_symbol'].items():
            if status not in ['verified','passed'] and symbol not in seen:emit('symbol-status',message=status,symbol=symbol)
        for hole in d['holes']:emit('unfinished',hole['file'],hole['line'],hole['col'],hole['kind'])
        for finding in d['findings']:emit('finding',finding['file'],finding['line'],0,finding['kind']+': '+finding['message'])
        if d['verdict']!='verified' and not errors and not any(x.run==number for x in out):emit('status',message=d['verdict'])
        if d['verdict']=='verified' and d['stage']!='verify':emit('non-proof-stage',message=d['stage'])
        if d['verdict']=='verified' and (d['verified_count'] is None or d['verified_count']==0):emit('missing-proof-count',message='verified_count unavailable or zero')
    return tuple(out)
