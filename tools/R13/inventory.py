#!/usr/bin/env python3
"""Provided R-half delivery inventory. Reads source bytes; executes no delivery/tool.

The frozen corpus loader owns partitioning. Only Delivery fields are exposed;
manifest labels/expected outcomes are evaluator data and do not drive this view.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'harness'))
from fvh.corpus import load_half

# An unlabelled mixed delivery draw; healthy controls must not be accused.
DRAW = frozenset((('dafny','G02'),('dafny','G12'),('dafny','D-05'),('dafny','D-07'),
                  ('dafny','C-02'),('dafny','C-08'),('verus','V02'),('verus','V11'),
                  ('verus','V12b'),('verus','V13b'),('verus','C-2'),('verus','C-8')))

def inventory(*, all_rows: bool = False) -> dict:
    rows = []
    seen = set()
    for lang in ('dafny','verus'):
        for fixture in load_half(lang,'R',root=ROOT,covered=all_rows):
            d = fixture.delivery
            if not all_rows and (lang,d.id) not in DRAW:
                continue
            seen.add((lang,d.id))
            files = {}
            base = ROOT / 'tests/corpus' / lang / d.id
            for rel in d.files:
                p = ROOT / rel
                if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(base.resolve()):
                    raise ValueError('delivery file leaves its fixture or is not a plain file: '+rel)
                files[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
            rows.append({'id': d.id, 'lang': d.lang, 'half': d.half,
                         'target': d.target, 'files_sha256': files,
                         'source_available': bool(files)})
    if not all_rows and seen != DRAW:
        raise ValueError('the fixed R13 delivery draw is incomplete')
    return {'schema':1, 'half':'R', 'scope':'source inventory, not verification or diagnosis',
            'deliveries': rows}

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--all',action='store_true',help='include all R rows, including refusal-only rows without source')
    a=p.parse_args()
    print(json.dumps(inventory(all_rows=a.all),indent=2))
    return 0
if __name__=='__main__':
    raise SystemExit(main())
