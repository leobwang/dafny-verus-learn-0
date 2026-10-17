# Reference Solution.
"""R12 per-symbol profiler; isolated measurements are never a full acceptance gate.

The runner is a trusted wrapper adapter. Records preserve failed/inconclusive
outcomes and unavailable resources, with requested and reported symbols separate.
No model-generated code is evaluated here. Gate/audit/snapshot acceptance remains
a separate original-task operation through the frozen executor/provenance rules.
"""
from dataclasses import dataclass
import math
import copy
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

@dataclass(frozen=True)
class SymbolProfile:
    symbol:str
    repeat:int
    lang:str
    verdict:str
    stage:str
    selected_status:str|None
    holes:int
    wall_s:float
    resource_count:float|None
    document:dict

# item: R12.A1py
def profile_symbols_r12(target:str,symbols,*,repeats:int,run)->tuple[SymbolProfile,...]:
    if not isinstance(target,str) or not target:raise ValueError('nonempty target')
    symbols=tuple(symbols)
    if not symbols or any(not isinstance(s,str) or not s for s in symbols) or len(set(symbols))!=len(symbols):raise ValueError('unique nonempty requested symbols')
    if type(repeats) is not int or repeats<1:raise ValueError('positive repeats')
    rows=[]
    for symbol in symbols:
        for repeat in range(repeats):
            document=run(['scripts/vcheck','--json','--measures','--symbol',symbol,'--isolate',target])
            parsed=copy.deepcopy(document)
            required={'lang','verdict','stage','per_symbol','holes','wall_s','resource_count'}
            if not isinstance(parsed,dict) or not required<=set(parsed):raise ValueError('wrapper omitted profile fields')
            if parsed['lang'] not in ('dafny','verus') or parsed['verdict'] not in ('verified','failed','inconclusive','refused','killed(memory)','error') or parsed['stage'] not in ('cli','parse','resolve','verify','compile','test','run'):raise ValueError('native profile status')
            if not isinstance(parsed['holes'],list) or any(not isinstance(h,dict) for h in parsed['holes']):raise ValueError('native hole records')
            if not isinstance(parsed['per_symbol'],dict) or any(not isinstance(k,str) or not k or not isinstance(v,str) or not v for k,v in parsed['per_symbol'].items()):raise ValueError('native symbol statuses')
            for field in ['wall_s','resource_count']:
                v=parsed[field]
                if v is None and field=='resource_count':continue
                if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0:raise ValueError('invalid profile measurement')
            matches=[v for k,v in parsed['per_symbol'].items() if k==symbol or k.endswith('.'+symbol) or k.endswith('::'+symbol)]
            selected=matches[0] if len(matches)==1 else None
            rows.append(SymbolProfile(symbol,repeat,parsed['lang'],parsed['verdict'],parsed['stage'],selected,len(parsed['holes']),float(parsed['wall_s']),None if parsed['resource_count'] is None else float(parsed['resource_count']),parsed))
    return tuple(rows)


def _r12_source_hash(target):
    path=Path(target)
    files=[path] if path.is_file() else [path/'Cargo.toml',*sorted((path/'src').rglob('*.rs'))]
    if not files or any(not p.is_file() for p in files):raise ValueError('target must be one native file or a Verus crate')
    digest=hashlib.sha256()
    for p in files:
        digest.update(str(p.relative_to(path) if path.is_dir() else p.name).encode())
        digest.update(b'\0');digest.update(p.read_bytes());digest.update(b'\0')
    return digest.hexdigest()


def _r12_wrapper_result(argv):
    root=Path(__file__).resolve().parents[2]
    if root.name=='Solutions':root=root.parent
    process=subprocess.run(argv,cwd=root,capture_output=True,text=True)
    document=json.loads(process.stdout)
    if not isinstance(document,dict):raise ValueError('profile one native target per invocation')
    return document


def main(argv=None,*,run=None,out=None):
    ap=argparse.ArgumentParser(description='Per-symbol isolated measurements; run a separate full gate for acceptance.')
    ap.add_argument('target',type=Path)
    ap.add_argument('--symbol',action='append',required=True)
    ap.add_argument('--repeats',type=int,default=3)
    args=ap.parse_args(argv);target=args.target.resolve();out=out or sys.stdout
    try:
        before=_r12_source_hash(target)
        rows=profile_symbols_r12(str(target),args.symbol,repeats=args.repeats,run=run or _r12_wrapper_result)
        after=_r12_source_hash(target)
        if before!=after:raise ValueError('target source changed during profiling')
        from dataclasses import asdict
        report={'scope':'per-symbol isolation only; not a full acceptance gate','target':str(target),'source_sha256':before,'tool_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'results':[asdict(row) for row in rows]}
        out.write(json.dumps(report,ensure_ascii=False,sort_keys=True)+'\n')
        return 0
    except (OSError,ValueError) as error:
        print('profiler: '+str(error),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
