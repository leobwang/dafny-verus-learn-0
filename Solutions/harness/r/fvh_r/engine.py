# Reference Solution.
"""R12 driving — fixed native result schema, localized obligations and one search engine.

All five Python learner functions live here so the frozen single-file reference
overlay can check their composition. extractor.py, loop.py and environment.py
are public API facades. Commit the predictions before running acceptance tests.
Policies produce invariant data; the frozen fvh executor owns all file/tool work.
A positive score, diagnostic text or an empty obligation list is never acceptance.
Read the original contracts below and preserve every provided model/signature.
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
    """Read one normalized wrapper-result object per nonblank JSON line, in order.
    Required fields are lang, target, exit_code, verdict, stage, verified_count,
    holes, diagnostics, findings and per_symbol, under the documented native types.
    Accept only Dafny/Verus, preserve all six verdicts and seven native stages and
    all extra fields; reject duplicate keys, nonfinite numbers, bool measurements,
    blank/nonobject/malformed/missing data atomically with its one-based line number.
    Keep nullable counts/resources unavailable, never zero; empty stream returns ().
    Diagnostic coordinates may be zero; hole lines start at1. Preserve warning and
    related diagnostics too. This parser does not decide whole-task acceptance."""
    # did: validate complete native rows while preserving failure, stage and order.
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
# triv: return ()


# item: R12.H2py
def localize(runs:Sequence[NativeRun],spans:Sequence[SourceSpan])->tuple[Obligation,...]:
    """Return ordered obligations while retaining run/language/native stage scope.
    Use exact language/file identity and unique innermost trusted source spans for
    error diagnostics; ambiguity or unknown paths remain unlocalized. Never infer a
    symbol from message text. Include unsupplemented failing per-symbol statuses,
    unfinished holes, findings, non-proof green stages, missing proof counts and
    nonverified results without locations. Preserve all original documents; an empty
    obligation list is not a success predicate. Treat input documents as read-only."""
    # did: bind only exact unique source spans and keep unknown statuses visible.
    out=[]
    for number,run in enumerate(runs):
        d=run.document
        # reference-only
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
# triv: return ()

# item: R12.W3py
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
        self.pending=None

    def stage(self,ask)->Attempt:
        return self._transition('stage',ask)

    def observe(self,outcome:Outcome)->Attempt:
        return self._transition('observe',outcome)

    def expand(self,ask,judge)->Attempt:
        row=self.stage(ask)
        if row.status=='malformed':return row
        return self.observe(judge(row.hint))

    # item: R12.H4py
    def _transition(self,event,payload)->Attempt:
        """Implement stage/observe for one fixed width/depth/priority search engine.
        Stage chooses eligible parents (depth<cap, expanded<width), consumes one width
        slot and records the request. FIFO/LIFO use stable ids; best uses the smallest
        trusted obligation count with id tie-break, unavailable scores last. Malformed
        data consumes a request without a tool call; other provider errors remain
        recorded and propagate. Observe binds one pending request to trusted Outcome,
        adds its child, replaces the pending row and stops only on accepted evidence.
        Reject double staging or observation without a request. Parameters never depend
        on the current budget point; expand is the supplied synchronous composition."""
        # did: stage a bounded parent expansion and bind its actual executor observation.
        if event=='observe':
            if self.pending is None:raise RuntimeError('no staged node to observe')
            if not isinstance(payload,Outcome):raise TypeError('trusted executor must return Outcome')
            index,parent_id,depth,hint=self.pending
            self.nodes.append(Node(index+1,depth,hint,payload))
            self.solved=payload.accepted
            row=Attempt(index,parent_id,hint,payload,'accepted' if payload.accepted else 'observed')
            self.attempts[index]=row
            self.pending=None
            return row
        if event!='stage':raise ValueError('transition event')
        if self.pending is not None:raise RuntimeError('observe the staged node before another generation')
        if self.solved:raise FrontierExhausted('already solved')
        eligible=[n for n in self.nodes if n.depth<self.depth and n.expanded<self.width]
        if not eligible:raise FrontierExhausted('fixed frontier exhausted')
        if self.priority=='fifo':parent=min(eligible,key=lambda n:n.id)
        elif self.priority=='lifo':parent=max(eligible,key=lambda n:n.id)
        else:parent=min(eligible,key=lambda n:(n.outcome.score if n.outcome.score is not None else math.inf,n.id))
        parent.expanded+=1
        index=len(self.attempts)
        try:
            hint=payload(Request(parent.id,parent.depth,parent.hint,parent.outcome.feedback))
            if not isinstance(hint,Hint):raise ValueError('a model returns Hint data, never Outcome or actions')
        except (ValueError,TypeError):
            row=Attempt(index,parent.id,None,None,'malformed');self.attempts.append(row);return row
        except Exception:
            self.attempts.append(Attempt(index,parent.id,None,None,'proposal-error'))
            raise
        self.pending=(index,parent.id,parent.depth+1,hint)
        row=Attempt(index,parent.id,hint,None,'pending')
        self.attempts.append(row)
        return row
    # triv: return Attempt(0,0,None,None,'malformed')

# item: R12.W4py
from dataclasses import dataclass

@dataclass(frozen=True)
class Trace:
    attempts:tuple
    reason:str
    def __post_init__(self):
        if self.reason not in ('budget','accepted','frontier'):raise ValueError('trace stop reason')
        if type(self.attempts) is not tuple or any(not isinstance(x,Attempt) for x in self.attempts):raise ValueError('trace attempt records')

# item: R12.H3py
def drive_r12(engine,ask,judge,*,nodes:int)->Trace:
    """Expand at most nodes further requests using the unchanged engine configuration.
    Count malformed requests and keep pending requests if the trusted executor fails.
    No tools/files/model transport belong here: ask supplies data and judge is the
    trusted executor adapter. Stop on accepted evidence or an exhausted frontier;
    return the new attempts and the actual stop reason, with prefixes reproducible.
    Validate the cap before callbacks and propagate trusted infrastructure failures."""
    # did: charge each requested node and stop only on trusted acceptance.
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
# triv: return Trace((), 'budget')

# item: R12.W5py
from dataclasses import dataclass
import re

_TOKEN=re.compile(r'[A-Za-z_][A-Za-z0-9_]*|[0-9]+|<==>|==>|&&|\|\||<=|>=|==|!=|::|[()\[\].@,:|+*/%<>=!&-]')
_IDENTIFIER=re.compile(r'[A-Za-z_][A-Za-z0-9_]*\Z')
_KEYWORDS=frozenset(['forall','exists','as','int','nat','bool','true','false'])
_FORBIDDEN=frozenset(['assume','admit','axiom','unsafe','external_body','proof_note','fn','method','function','lemma','module','mod','import','use','requires','ensures','decreases','invariant','return','while','loop','for','let','var','reveal','broadcast','unimplemented','panic','expect','print','println'])

@dataclass(frozen=True)
class HintSite:
    name:str
    identifiers:tuple[str,...]
    kind:str="expr"
    callees:tuple[str,...]=()
    def __post_init__(self):
        if not _IDENTIFIER.fullmatch(self.name):raise ValueError('site name')
        if any(not _IDENTIFIER.fullmatch(x) or x in _FORBIDDEN for x in self.identifiers):raise ValueError('allowed identifiers')
        if self.kind not in ('expr','calls'):raise ValueError('site kind')
        if self.kind=='expr' and self.callees:raise ValueError('expression site has no statement callees')
        if self.kind=='calls' and (not self.callees or len(set(self.callees))!=len(self.callees)):raise ValueError('unique nonempty proof callees')
        if any(not _IDENTIFIER.fullmatch(x) or x in _FORBIDDEN or x in _KEYWORDS for x in self.callees):raise ValueError('proof callee')
    @property
    def marker(self):return ('/*R12_HINT:'+self.name+'*/ true') if self.kind=='expr' else ('/*R12_CALLS:'+self.name+'*/')

@dataclass(frozen=True)
class HintTask:
    template:str
    sites:tuple[HintSite,...]
    def __post_init__(self):
        if not self.sites or len({s.name for s in self.sites})!=len(self.sites):raise ValueError('unique nonempty sites')
        if any(self.template.count(s.marker)!=1 for s in self.sites):raise ValueError('each frozen site exactly once')
        if len({self.template[:self.template.index(s.marker)].count('\n') for s in self.sites})!=len(self.sites):raise ValueError('one hint site per source line')
        rest=self.template
        for site in self.sites:rest=rest.replace(site.marker,'')
        if 'R12_HINT:' in rest or 'R12_CALLS:' in rest:raise ValueError('unlisted hint marker')

def _check_expression(expression,identifiers):
    allowed=set(identifiers)|_KEYWORDS
    at=0
    while at<len(expression):
        if expression[at] in ' \t':at+=1;continue
        token=_TOKEN.match(expression,at)
        if token is None:raise ValueError('only proof-expression tokens')
        word=token.group()
        if _IDENTIFIER.fullmatch(word) and (word not in allowed or word in _FORBIDDEN):raise ValueError('identifier outside frozen task vocabulary')
        at=token.end()


def _proof_calls(expression,site):
    chunks=expression.split(';')
    if not chunks[-1].strip():chunks.pop()
    if not 1<=len(chunks)<=8:raise ValueError('bounded nonempty proof call list')
    calls=[]
    for chunk in chunks:
        match=re.fullmatch(r'\s*([A-Za-z_][A-Za-z0-9_]*)\s*\((.*)\)\s*',chunk)
        if match is None or match[1] not in site.callees:raise ValueError('only approved proof callees')
        arguments=match[2]
        _check_expression(arguments,site.identifiers)
        stack=[]
        for char in arguments:
            if char in '([':stack.append(char)
            elif char in ')]':
                if not stack or stack.pop()!=('(' if char==')' else '['):raise ValueError('argument delimiters')
        if stack:raise ValueError('argument delimiters')
        calls.append(match[1]+'('+arguments+');')
    return ' '.join(calls)


# item: R12.H5py
def render_hint_r12(task:HintTask,hint:Hint)->str:
    """Replace exactly one bounded proof hint per committed site. Expression sites
    use the provided token grammar and vocabulary; call sites use only their approved
    proof callees and bounded call lists. Reject code, declarations, attributes,
    quotes, comments, newlines, NUL, unknown identifiers, wrong counts and oversized
    hints. Preserve every byte outside the sites. Rendering is pure data work, not
    execution or acceptance. The form-admission tool independently checks native
    statement/model identity and executable-code erasure for every allowed site."""
    # did: validate proof hints before replacing only committed annotation sites.
    if len(hint.annotations)!=len(task.sites):raise ValueError('one hint per fixed site')
    rendered=task.template
    for site,expression in zip(task.sites,hint.annotations):
        if not expression or len(expression)>8192 or any(x in expression for x in ['\n','\r','\x00','//','/*','*/']):raise ValueError('invalid hint text')
        if site.kind=='expr':
            _check_expression(expression,site.identifiers)
            replacement='('+expression+')'
        else:replacement=_proof_calls(expression,site)
        rendered=rendered.replace(site.marker,replacement,1)
    return rendered
# triv: return task.template

# item: R12.W6py
import json
import re
from fvh import protocol as P


def unique(pairs):
    d={}
    for key,value in pairs:
        if key in d:raise ValueError('duplicate key')
        d[key]=value
    return d


def source_task(text):
    rows=re.findall(r'^// R12_HINT_SITES: (.+)$',text,re.M)
    if len(rows)!=1:raise ValueError('one committed hint-site manifest required')
    sites=json.loads(rows[0],object_pairs_hook=unique)
    if not isinstance(sites,list) or any(not isinstance(s,dict) or not {'name','identifiers'}<=set(s) or not set(s)<={'name','identifiers','kind','callees'} for s in sites):raise ValueError('hint-site manifest')
    task=HintTask(text,tuple(HintSite(s['name'],tuple(s['identifiers']),s.get('kind','expr'),tuple(s.get('callees',()))) for s in sites))
    spans=re.findall(r'^// R12_SOURCE_SPANS: (.+)$',text,re.M)
    if len(spans)>1:raise ValueError('at most one source-span manifest')
    raw=json.loads(spans[0],object_pairs_hook=unique) if spans else []
    if not isinstance(raw,list) or any(not isinstance(s,dict) or set(s)!={'symbol','start','end'} for s in raw):raise ValueError('span manifest')
    return task,raw


def check_source_frame(task,text):
    """Independent structural guard; no learner renderer controls this check.

    Headers, models, declarations and executable bytes outside sites are fixed.
    Insertions cannot close a block, add attributes/comments/strings/new lines or
    use trust/control/runtime-check statements. Calls sites belong to proof
    contexts validated by the native form-admission step, never arbitrary code.
    Identifier/argument validity and exact data-to-text rendering remain H5 work.
    """
    if not isinstance(text,str):raise ValueError('rendered source must be text')
    ordered=sorted(task.sites,key=lambda s:task.template.index(s.marker))
    cursor=0;pattern=''
    for site in ordered:
        at=task.template.index(site.marker,cursor)
        pattern+=re.escape(task.template[cursor:at])+r'([^\n\r{}#"\']*)'
        cursor=at+len(site.marker)
    pattern+=re.escape(task.template[cursor:])
    match=re.fullmatch(pattern,text)
    if match is None:raise ValueError('source changed outside a committed proof site')
    forbidden={'assume','admit','axiom','external_body','proof_note','unsafe','expect','print','println','return','while','loop','for','fn','method','function','lemma','module','import','use','requires','ensures','decreases'}
    for site,inserted in zip(ordered,match.groups()):
        if not inserted or len(inserted)>8192 or any(x in inserted for x in ['//','/*','*/','\x00']):raise ValueError('structural proof-site escape')
        if site.kind=='expr':
            if ';' in inserted:raise ValueError('statement in expression site')
            _check_expression(inserted,site.identifiers)
        else:_proof_calls(inserted,site)
        if set(re.findall(r'[A-Za-z_][A-Za-z0-9_]*',inserted))&forbidden:raise ValueError('trust/control statement in proof site')


def hint_data(text,task):
    obj=json.loads(text,object_pairs_hook=unique)
    if not isinstance(obj,dict) or set(obj) not in ({'hints'},{'invariants'}) or not isinstance(obj.get('hints',obj.get('invariants')),list):raise ValueError('only one hints array is permitted (invariants is the expression-only legacy spelling)')
    if 'invariants' in obj and any(s.kind!='expr' for s in task.sites):raise ValueError('proof-call sites use the hints spelling')
    hint=Hint(tuple(obj.get('hints',obj.get('invariants'))))
    check_source_frame(task,render_hint_r12(task,hint)) # independent of the learner renderer
    return hint


def native_outcome(doc,ctx,raw_spans,*,raw_feedback=False):
    # Frozen executor synthesizes reduced documents for kills/unavailable stages.
    # Preserve them as unknown feedback; never invent the missing native phase.
    if doc.get('verdict') in ['killed(memory)','inconclusive','refused','error'] and not all(k in doc for k in ['lang','target','stage','per_symbol','findings']):
        return Outcome(False,None,{'kind':'native-stage-unavailable','native':doc})
    parsed=result_stream([json.dumps(doc)])[0].document
    if parsed['lang']!=ctx.lang:raise ValueError('native language changed')
    clean=(parsed['verdict']=='verified' and parsed['stage']=='verify' and parsed['exit_code']==0 and type(parsed['verified_count']) is int and parsed['verified_count']>0 and not parsed['holes'] and not parsed['findings'] and not any(x['severity']=='error' for x in parsed['diagnostics']) and all(x in ['verified','passed'] for x in parsed['per_symbol'].values()))
    if parsed['verdict']=='verified' and not clean:raise ValueError('full gate did not provide clean proof-stage evidence')
    spans=[SourceSpan(ctx.lang,parsed['target'],s['symbol'],s['start'],s['end']) for s in raw_spans]
    obligations=localize((NativeRun(1,parsed),),spans)
    errors=[x for x in parsed['diagnostics'] if x['severity']=='error']
    score=0 if clean else (len(obligations) if parsed['stage']=='verify' and errors else None)
    feedback=parsed if raw_feedback else [dict(kind=o.kind,symbol=o.symbol,file=o.file,line=o.line,col=o.col,message=o.message,stage=o.stage,verdict=o.verdict) for o in obligations]
    return Outcome(clean,score,feedback)


class R12Policy:
    config=(3,10,'best')
    raw_feedback=False
    def __init__(self,ask,seeds):
        self.ask=ask;self.seeds=tuple(seeds)
        if not self.seeds or any(type(x) is not int for x in self.seeds):raise ValueError('pre-registered generation seeds')
        self.engine=None;self.task=None;self.spans=[];self.expected=None;self.context=None

    def propose(self,state,ctx,budget):
        try:
            if self.task is None:
                if ctx.lang not in ['dafny','verus'] or ctx.editable!=(ctx.target,):raise ValueError('one native task file required')
                text=ctx.material['text']
                original=P.text_sha256(text)
                if re.findall(r'^R12_TASK_SHA256: ([0-9a-f]{64})$',ctx.statement,re.M)!=[original]:raise ValueError('plan task digest does not bind original source')
                self.task,self.spans=source_task(text)
                self.context=(ctx.task_id,ctx.target,P.text_sha256(text),ctx.statement)
                self.expected=P.text_sha256(text)
                if state.files.get(ctx.target)!=self.expected:raise ValueError('initial source differs from committed task material')
                return [P.Verify(mode='gate')]
            if self.context!=(ctx.task_id,ctx.target,P.text_sha256(ctx.material['text']),ctx.statement):raise ValueError('task context changed')
            if state.files.get(ctx.target)!=self.expected:raise ValueError('executor source differs from rendered hint')
            doc=state.last_verify
            if not isinstance(doc,dict) or doc.get('files_sha256')!=dict(state.files):raise ValueError('missing or stale native feedback')
            outcome=native_outcome(doc,ctx,self.spans,raw_feedback=self.raw_feedback)
            if self.engine is None:
                if outcome.accepted:raise ValueError('original benchmark form already verifies; re-admit the registered stratum')
                w,d,p=self.config;self.engine=SearchR12(outcome,width=w,depth=d,priority=p)
            else:self.engine.observe(outcome)
            if self.engine.solved:return [P.Stop('done','full original-task gate passed')]
            if budget.exhausted or len(self.engine.attempts)>=len(self.seeds):return [P.Stop('give-up','generation budget exhausted')]
            def ask(request):
                prompt=json.dumps({'task':ctx.task_id,'statement':ctx.statement,'source':self.task.template,'parent_hints':list(request.hint.annotations),'feedback':request.feedback,'instructions':ctx.material.get('instructions',''),'response':{'actions':[{'type':'edit','path':ctx.target,'old':'','new':'a JSON string containing exactly {"hints":[one bounded hint per fixed site]}'}]}},ensure_ascii=False)
                return hint_data(self.ask(prompt,self.seeds[len(self.engine.attempts)]),self.task)
            staged=self.engine.stage(ask)
            if staged.status=='malformed':raise ValueError('model supplied invalid hint data')
            text=render_hint_r12(self.task,staged.hint);check_source_frame(self.task,text);self.expected=P.text_sha256(text)
            return [P.Edit(ctx.target,'',text),P.Verify(mode='gate')]
        except FrontierExhausted:
            return [P.Stop('give-up','fixed search frontier exhausted')]
        except (KeyError,ValueError,TypeError) as e:
            raise P.Malformed(str(e)) from e

class R12Independent(R12Policy):config=(10,1,'fifo')
class R12Repair(R12Policy):config=(1,10,'lifo')
class R12BestFirst(R12Policy):config=(3,10,'best')
class R12BestFirstRaw(R12BestFirst):raw_feedback=True
