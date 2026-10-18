# Reference Solution.
"""R14 advisory trigger-note analysis; it never decides proof acceptance.
Only the explicitly supplied source snapshot is available. Byte digests bind
published capture bytes, not authenticity or a successful verification.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict,dataclass
import hashlib
import json
from pathlib import Path
import re


def sha_r14(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class CaptureR14:
    source_id:str
    source:bytes
    stderr:bytes
    source_sha256:str
    stderr_sha256:str

    def __post_init__(self):
        if not isinstance(self.source_id,str) or not self.source_id.strip():
            raise ValueError('explicit source identity required')
        if type(self.source) is not bytes or type(self.stderr) is not bytes:
            raise ValueError('capture bytes required')
        if len(self.source)>4000000 or len(self.stderr)>4000000:
            raise ValueError('capture size limit')
        if sha_r14(self.source)!=self.source_sha256 or sha_r14(self.stderr)!=self.stderr_sha256:
            raise ValueError('capture digest mismatch; do not rebind old notes to new source')
        self.source.decode('utf-8')
        self.stderr.decode('utf-8')


@dataclass(frozen=True)
class TermR14:
    identity:str|None
    start:int|None
    end:int|None
    line:int|None
    text:str|None
    status:str


@dataclass(frozen=True)
class PatternR14:
    ordinal:int
    total:int
    terms:tuple[TermR14,...]


@dataclass(frozen=True)
class GroupR14:
    selection:str
    patterns:tuple[PatternR14,...]


@dataclass(frozen=True)
class TriggerScanR14:
    source_sha256:str
    stderr_sha256:str
    groups:tuple[GroupR14,...]
    unparsed_lines:int
    orphan_patterns:int

    @property
    def located_terms(self):
        return tuple(t for g in self.groups for p in g.patterns for t in p.terms if t.status=='source')

    @property
    def availability(self):
        return 'reported' if self.located_terms else 'unavailable'


# PROVIDED: decode the native JSONL channel without turning notes into verdicts.
def diagnostic_lines_r14(capture):
    records=[]
    unparsed=0
    for line in capture.stderr.decode().splitlines():
        if not line.strip():
            continue
        try:
            d=json.loads(line)
        except json.JSONDecodeError:
            unparsed+=1
            continue
        if not isinstance(d,dict) or d.get('$message_type')!='diagnostic' or not isinstance(d.get('message'),str) or not isinstance(d.get('spans'),list):
            unparsed+=1
            continue
        records.append(d)
    return records,unparsed


# PROVIDED: exact native byte offsets into the original supplied snapshot only.
def bound_terms_r14(capture,spans):
    terms=[]
    if not spans:
        return (TermR14(None,None,None,None,None,'unlocated'),)
    for sp in spans:
        if not isinstance(sp,dict):
            terms.append(TermR14(None,None,None,None,None,'invalid-span'))
            continue
        identity=sp.get('file_name')
        if identity!=capture.source_id:
            terms.append(TermR14(identity if isinstance(identity,str) else None,None,None,None,None,'external'))
            continue
        a,z,line=sp.get('byte_start'),sp.get('byte_end'),sp.get('line_start')
        if any(type(x) is not int for x in [a,z,line]) or not 0<=a<z<=len(capture.source) or line!=capture.source[:a].count(b'\n')+1:
            terms.append(TermR14(identity,None,None,None,None,'invalid-span'))
            continue
        try:
            text=capture.source[a:z].decode('utf-8')
        except UnicodeDecodeError:
            terms.append(TermR14(identity,None,None,None,None,'invalid-span'))
            continue
        terms.append(TermR14(identity,a,z,line,text,'source'))
    return tuple(terms)


@dataclass(frozen=True)
class QuantifierR14:
    kind:str
    qid:str|None
    patterns:tuple[str,...]
    line:int


# PROVIDED: the quantifiers of one SMT log written by `vcheck --smt-log DIR`
# (Verus's `--log smt`), each with its `:qid` and its `:pattern` terms as
# printed. A pattern is what the solver was given, not an instance it made.
def smt_quantifiers_r14(text:str)->tuple[QuantifierR14,...]:
    tokens=re.finditer(r'\|[^|]*\||"(?:[^"]|"")*"|;[^\n]*|[()]|[^\s()|";]+',text)
    stack=[[]]
    for tok in tokens:
        t=tok.group(0)
        if t.startswith(';'):
            continue
        if t=='(':
            node=[]
            node_line=text.count('\n',0,tok.start())+1
            stack[-1].append((node,node_line))
            stack.append(node)
        elif t==')':
            if len(stack)==1:
                raise ValueError('unbalanced SMT log: a closing parenthesis without an opening one')
            stack.pop()
        else:
            stack[-1].append((t,None))
    if len(stack)!=1:
        raise ValueError('unbalanced SMT log: an expression is not closed')

    def show(item):
        value,_=item
        if isinstance(value,str):
            return value
        return '('+' '.join(show(x) for x in value)+')'

    found=[]

    def visit(items):
        for value,line in items:
            if not isinstance(value,list):
                continue
            head=value[0][0] if value else None
            if head in ('forall','exists') and len(value)==3:
                qid=None
                patterns=[]
                body=value[2][0]
                if isinstance(body,list) and body and body[0][0]=='!':
                    attrs=body[2:]
                    for i in range(0,len(attrs)-1,2):
                        key=attrs[i][0]
                        if key==':pattern':
                            patterns.append(show(attrs[i+1]))
                        elif key==':qid' and isinstance(attrs[i+1][0],str):
                            qid=attrs[i+1][0]
                found.append(QuantifierR14(head,qid,tuple(patterns),line))
            visit(value)

    visit(stack[0])
    return tuple(found)


# item: R14.A1py
def scan_trigger_notes_r14(capture:CaptureR14)->TriggerScanR14:
    """Group native automatic/selected headers and each numbered trigger in order.
    Preserve all candidate alternatives and multi-term spans. No-source/library
    terms remain external or unlocated; never read another file or guess a term
    from its message. Keep unparsed line and orphan-pattern counts. An orphan
    numbered trigger is retained in an 'unattached' group. A numbered note must
    satisfy 1<=ordinal<=total; malformed counts increase unparsed_lines instead.
    Empty or unrecognized source reports stay unavailable, never 'no triggers'.
    Compose the provided decoder/byte binder. This is advisory analysis, not a
    gate, source repair, instantiation trace or verification result."""
    records,unparsed=diagnostic_lines_r14(capture)
    groups=[]
    selection=None
    patterns=[]
    orphans=0
    headers={'selected triggers for this expression:':'selected','automatically chose triggers for this expression:':'automatic'}

    def flush():
        if selection is not None:
            groups.append(GroupR14(selection,tuple(patterns)))

    for record in records:
        msg=record['message']
        if msg in headers:
            flush()
            selection=headers[msg]
            patterns=[]
        else:
            match=re.fullmatch(r'\s*trigger (\d+) of (\d+):',msg)
            if not match:
                continue
            ordinal,total=map(int,match.groups())
            if not 1<=ordinal<=total:
                unparsed+=1
                continue
            if selection is None:
                selection='unattached'
                patterns=[]
            if selection=='unattached':
                orphans+=1
            patterns.append(PatternR14(ordinal,total,bound_terms_r14(capture,record['spans'])))
    flush()
    return TriggerScanR14(capture.source_sha256,capture.stderr_sha256,tuple(groups),unparsed,orphans)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binding',type=Path)
    p.add_argument('--source',type=Path)
    p.add_argument('--stderr',type=Path)
    p.add_argument('--smt',type=Path,help='list the quantifiers of an SMT log from vcheck --smt-log (provided)')
    a=p.parse_args()
    if a.smt is not None:
        found=smt_quantifiers_r14(a.smt.read_text(encoding='utf-8',errors='replace'))
        doc={'scope':'patterns the solver was given; not instantiations, not a proof verdict','quantifiers':[asdict(q) for q in found]}
        print(json.dumps(doc,indent=2))
        return 0
    if a.binding is None or a.source is None or a.stderr is None:
        p.error('--binding, --source and --stderr are required without --smt')
    binding=json.loads(a.binding.read_text())
    c=CaptureR14(binding['source_id'],a.source.read_bytes(),a.stderr.read_bytes(),binding['source_sha256'],binding['stderr_sha256'])
    result=scan_trigger_notes_r14(c)
    doc=asdict(result)
    doc.update(scope='advisory native trigger notes; not a proof verdict',availability=result.availability,located_term_count=len(result.located_terms))
    print(json.dumps(doc,indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
