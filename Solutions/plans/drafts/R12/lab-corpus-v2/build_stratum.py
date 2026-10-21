#!/usr/bin/env python3
"""Author tool (DVR4 step 3): assemble bench/local/r/labalpha/STRATUM.toml (schema 2) from
the admitted family records under this directory and the public ADMISSION.json files.

  build_stratum.py ROOT [--roles ROLES.json] [--freeze REL]
      ROLES.json: {cluster id: {"role": "pilot"|"confirmatory"|"unassigned",
                   "descriptive": bool}}; clusters it does not name are "unassigned".

A cluster enters only when its family record says "admitted" and every task's
ADMISSION.json is schema 2, status admitted, all seven controls true and bound to the
form's current bytes. Every other family is listed in a comment with its status, so the
stratum shows what was tried. The file names no reference body and no private path
beyond the reference file names the plan already lists."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKS = ('baseline-proof-fails', 'max-auto-empty-fails', 'reference-gate', 'reference-three-seeds',
          'wrong-hints-fail', 'audit-clean', 'original-model-code-frame')
SEALED_SLOT = ('R08 (rebuilt), R13- and R14-derived regex families: a later step, after the other '
               'lane rebuilds those modules; R13/R14 tasks are sealed under Hidden/labs/R12/ (D-L3 (a)) '
               'and enter as a separate sealed stratum with its own statements pin')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def q(v):
    return json.dumps(v, ensure_ascii=False)


def task_row(root, tid, fam):
    lang = fam['lang'] if fam['kind'] == 'public' else ('dafny' if tid.endswith('-d') else 'verus')
    ext = '.dfy' if lang == 'dafny' else '.rs'
    rel = f'bench/local/r/labalpha/{tid}/tasks/{tid}{ext}'
    adm_rel = f'bench/local/r/labalpha/{tid}/ADMISSION.json'
    src, adm = root / rel, root / adm_rel
    if fam.get('sealed'):          # R13/R14-derived: the author's copy; the stratum names the
        src = HERE / 'sealed' / tid / 'tasks' / f'{tid}{ext}'      # unseal target paths
        adm = HERE / 'sealed' / tid / 'ADMISSION.json'
    a = json.loads(adm.read_text())
    ok = (a.get('schema') == 2 and a.get('status') == 'admitted' and a.get('source_sha256') == sha(src)
          and set(a.get('checks', {})) == set(CHECKS) and all(v is True for v in a['checks'].values()))
    if not ok:
        raise ValueError(tid + ': admission incomplete or stale')
    s = fam.get('source') or {'set': fam.get('set', ''), 'upstream': fam.get('upstream_task', ''),
                              'licence': (fam.get('licence') or '').replace('pass: ', ''),
                              'flag': fam.get('licence_flag')}
    if fam['kind'] == 'regex':
        statement = (f"Complete the proof of the target lemma {a['target']} ({s['module']} {s['lemma']}) by "
                     "filling every hint site; the provided definitions, helper lemmas and the statement are fixed.")
        exposure = ('course-authored lemma from the ' + s['module'] + ' reference, written 2026-10, after the '
                    "pinned model's release; course-derived, not an independent unseen benchmark")
    else:
        statement = ('Complete the verification of the target ' + a['target'] + ' (public task ' + s.get('upstream', '')
                     + ') by filling every hint site; the specification and the code are fixed.')
        exposure = ('public benchmark task (' + s.get('set', '') + ', ' + s.get('licence', '') + '); treat as '
                    'possibly seen in 2023-2025 public repositories (contamination flag: possibly-seen)'
                    + ('; licence flag: ' + s['flag'] if s.get('flag') else ''))
    if fam.get('sealed'):
        exposure = ('course-authored lemma from the ' + s['module'] + ' reference, written 2026-10; SEALED in '
                    'Hidden/labs/R12/tasks.tar.age (plan section 3.5, D-L3 (a)): a learner at R12 sees its id '
                    'and verdict only')
    sys.path.insert(0, str(root / 'harness'))
    from fvh.labalpha import strip_header
    prompt_sha = hashlib.sha256(strip_header(src.read_text()).encode()).hexdigest()
    row = {'id': tid, 'cluster': fam['cluster'], 'lang': lang, 'path': rel, 'source_sha256': sha(src),
           'prompt_source_sha256': prompt_sha,
            'statement': statement, 'exposure': exposure, 'admission': adm_rel, 'admission_sha256': sha(adm),
            'target': a['target'], 'sites': len(a.get('sites', []))}
    if fam.get('sealed'):
        row['sealed'] = True
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=Path)
    ap.add_argument('--roles', type=Path)
    ap.add_argument('--freeze')
    args = ap.parse_args()
    root = args.root.resolve()
    roles = json.loads(args.roles.read_text()) if args.roles else {}
    fams = [json.loads(p.read_text()) for p in sorted((HERE / 'families').glob('*.json'))]
    fams += [dict(json.loads(p.read_text()), sealed=True) for p in sorted((HERE / 'sealed' / 'families').glob('*.json'))]
    pools = root / 'bench/public/POOLS.toml'
    head = ['# bench/local/r/labalpha/STRATUM.toml: Lab alpha\'s stratum, schema 2 (DVR4 plan sections 3.5, 3.8).',
            '# Built by the author tool Solutions/plans/drafts/R12/lab-corpus-v2/build_stratum.py from the admitted',
            '# family records; every task bound to its form bytes and its seven-control ADMISSION.json.',
            '# Cluster rule: one cluster per source lemma family (a lemma and the helpers it calls); its Dafny',
            '# and Verus forms are its tasks; several hint-site forms of one lemma are tasks of the same cluster;',
            '# a public task is a cluster of its own. Roles: pilot (the 5-cluster pilot, excluded from the',
            '# confirmatory sample), confirmatory (drawn at the freeze), unassigned (admitted, not drawn).',
            'schema = 2', 'lab = "R12"', 'authored = "2026-10-18"',
            'cluster_rule = "one cluster per source lemma family; its Dafny and Verus forms are its tasks; a public task is a cluster of its own"',
            'pools = "bench/public/POOLS.toml"', 'pools_sha256 = ' + q(sha(pools)),
            'sealed_slot = ' + q(SEALED_SLOT)]
    if args.freeze:
        head.append('freeze = ' + q(args.freeze))
    out, tasks, skipped = [], [], []
    for fam in fams:
        if fam.get('status') != 'admitted':
            skipped.append(f"# not admitted: {fam['cluster']} ({fam.get('status')})")
            continue
        rows = [task_row(root, t, fam) for t in fam['tasks']]
        r = roles.get(fam['cluster'], {})
        s = fam.get('source') or {'set': fam.get('set', ''), 'upstream': fam.get('upstream_task', ''),
                                  'licence': (fam.get('licence') or '').replace('pass: ', '')}
        src = (s['module'] + ' ' + s['lemma'] + ' (' + '; '.join(s['reference'].values()) + ')') \
            if fam['kind'] == 'regex' else (s.get('set', '') + ' ' + s.get('upstream', '') + ' (' + s.get('licence', '') + ')')
        out += ['', '[[cluster]]', 'id = ' + q(fam['cluster']), 'kind = ' + q(fam['kind']), 'source = ' + q(src),
                'role = ' + q(r.get('role', 'unassigned')), 'descriptive = ' + ('true' if r.get('descriptive') else 'false'),
                'tasks = ' + q([x['id'] for x in rows])]
        tasks += rows
    for t in tasks:
        out += ['', '[[task]]'] + [f'{k} = {q(v)}' for k, v in t.items()]
    text = '\n'.join(head + skipped + out) + '\n'
    (root / 'bench/local/r/labalpha/STRATUM.toml').write_text(text)
    n = {k: sum(1 for f in fams if f.get('status') == 'admitted' and f['kind'] == k) for k in ('regex', 'public')}
    print(f"STRATUM.toml: {n['regex']} regex + {n['public']} public clusters, {len(tasks)} tasks; "
          f"{len(skipped)} families not admitted", file=sys.stderr)


if __name__ == '__main__':
    main()
