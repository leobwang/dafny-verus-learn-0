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
    raise NotImplementedError("R12.A1py")


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
