"""R12 per-symbol profiler; isolated measurements are never a full acceptance gate.

The runner is a trusted wrapper adapter. Records preserve failed/inconclusive
outcomes and unavailable resources, with requested and reported symbols separate.
No model-generated code is evaluated here. Gate/audit/snapshot acceptance remains
a separate original-task operation through the frozen executor/provenance rules.
"""
from dataclasses import dataclass
import json
from extractor import result_stream

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
            parsed=result_stream([json.dumps(document)])[0].document
            if 'wall_s' not in parsed or 'resource_count' not in parsed:raise ValueError('wrapper omitted requested measurements')
            matches=[v for k,v in parsed['per_symbol'].items() if k==symbol or k.endswith('.'+symbol) or k.endswith('::'+symbol)]
            selected=matches[0] if len(matches)==1 else None
            rows.append(SymbolProfile(symbol,repeat,parsed['lang'],parsed['verdict'],parsed['stage'],selected,len(parsed['holes']),float(parsed['wall_s']),None if parsed['resource_count'] is None else float(parsed['resource_count']),parsed))
    return tuple(rows)
