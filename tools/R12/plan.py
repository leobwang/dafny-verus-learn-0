#!/usr/bin/env python3
"""Build Lab alpha's locked batch plans from the schema-2 stratum (DVR4 plan section 3.8).

Three executable plans, one per role of bench/local/r/labalpha/STRATUM.toml's clusters:

  pilot         every task of the pilot clusters; the four regimes (independent,
                repair, best, best-raw) x 3 repeats x B = 10; role "pilot", no lab
                field and no freeze (the author's pilot, DVR4 plan section 3.6; its
                clusters never enter the confirmatory sample)
  confirmatory  every task of the confirmatory clusters; the two primary arms (best,
                best-raw) x 3 repeats; lab "R12", role "confirmatory", the freeze
  descriptive   every task of the descriptive subset (confirmatory clusters flagged
                descriptive); the two other regimes (independent, repair) x 3
                repeats; lab "R12", role "descriptive", the freeze
  (descriptive-claude, with --claude-subset-seed: the Claude best-first arm on a
                seeded, language-stratified subset of at most 10 descriptive tasks,
                1 repeat)

Every arm is a fvh.labalpha regime (the equal feedback cap and the failed-node rule
around fvh_r.engine's policy), construct "seeded", rounds 10, turns 12 (baseline,
at most ten generations, closure). Each task's statement binds its source bytes
(R12_TASK_SHA256), its cluster (R12_CLUSTER) and its exposure. fvh.batch refuses a
pilot plan whose tasks leave the pilot clusters and a confirmatory or descriptive
plan without a complete freeze (fvh.prereg.check_roles). A sealed task (the R13/R14-
derived forms, sealed in Hidden/labs/R12/) is counted in the stratum but never enters
any plan (the user's D61), unsealed or not.

This performs no model, provider or container execution, creates no grade row and
never discovers reference completions; a lab plan still needs its genuine graded
pre-registration (plan-sha256 and freeze-sha256 in the PREREG block).

  plan.py --seed N --write-dir DIR [--roles pilot,confirmatory,descriptive]
          [--claude-subset-seed M] [--stratum PATH]
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'harness'))
from fvh.budget import CLAUDE, QWEN  # noqa: E402

REGIMES = (('independent', 'Independent'), ('repair', 'Repair'), ('best', 'BestFirst'),
           ('best-raw', 'BestFirstRaw'))
PRIMARY = ('best', 'best-raw')
DESCRIPTIVE = ('independent', 'repair')
CHECKS = ('baseline-proof-fails', 'max-auto-empty-fails', 'reference-gate', 'reference-three-seeds',
          'wrong-hints-fail', 'audit-clean', 'original-model-code-frame')
ROLES = ('pilot', 'confirmatory', 'unassigned')
STRATUM = 'bench/local/r/labalpha/STRATUM.toml'
FREEZE = 'bench/local/r/labalpha/FREEZE.toml'
B = 10
REPEATS = 3


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def course_path(root, value):
    if not isinstance(value, str) or not value or Path(value).is_absolute() or '..' in Path(value).parts:
        raise ValueError('one course-relative path required')
    path = root / value
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('missing or escaping course file: ' + value)
    if any(p.lower() in ('solutions', 'hidden', 'leak_patterns') for p in path.relative_to(root).parts):
        raise ValueError('reference material cannot enter a plan')
    return path


def load_stratum(root, path):
    """The schema-2 stratum's clusters and tasks, every task's admission checked against
    its source bytes; ValueError naming the first problem."""
    root = Path(root)
    data = tomllib.loads(Path(path).read_text())
    if data.get('schema') != 2 or data.get('lab') != 'R12':
        raise ValueError('R12 stratum schema 2 required (the schema-1 toy forms are apparatus smoke)')
    if data.get('role') == 'apparatus-smoke':
        raise ValueError('an apparatus-smoke stratum is never data')
    tasks = {}
    for t in data.get('task', []):
        tid = t.get('id')
        if not isinstance(tid, str) or not re.fullmatch(r'[a-z][a-z0-9-]*', tid) or tid in tasks:
            raise ValueError('unique lowercase task id required')
        if t.get('lang') not in ('dafny', 'verus'):
            raise ValueError(tid + ': lang is dafny or verus')
        if t.get('sealed') is True and not (root / str(t.get('path', ''))).is_file():
            # a sealed task (R13/R14-derived, plan section 3.5 D-L3 (a)): its form and its
            # admission are in the sealed archive; only its id, cluster and hashes are here
            for key in ('cluster', 'source_sha256', 'admission_sha256'):
                if not isinstance(t.get(key), str) or not t[key]:
                    raise ValueError(tid + ': a sealed task names its cluster and hashes')
            tasks[tid] = dict(t, unsealed=False)
            continue
        src = course_path(root, t.get('path'))
        if src.suffix != ('.dfy' if t['lang'] == 'dafny' else '.rs'):
            raise ValueError(tid + ': task language/suffix mismatch')
        if not t['path'].startswith('bench/local/r/labalpha/' + tid + '/tasks/'):
            raise ValueError(tid + ': a task form lives at bench/local/r/labalpha/<id>/tasks/')
        if digest(src) != t.get('source_sha256'):
            raise ValueError(tid + ': stale task source')
        from fvh.labalpha import strip_header
        if hashlib.sha256(strip_header(src.read_text()).encode()).hexdigest() != t.get('prompt_source_sha256'):
            raise ValueError(tid + ': the source as the prompt carries it (header stripped) is not the pinned one')
        for key in ('cluster', 'statement', 'exposure'):
            if not isinstance(t.get(key), str) or not t[key].strip():
                raise ValueError(tid + ': cluster, statement and exposure required')
        report = course_path(root, t.get('admission'))
        if digest(report) != t.get('admission_sha256'):
            raise ValueError(tid + ': stale task admission report')
        ev = json.loads(report.read_text())
        if ev.get('schema') != 2 or ev.get('source_sha256') != t['source_sha256'] or ev.get('status') != 'admitted':
            raise ValueError(tid + ': admission not bound to the original source')
        checks = ev.get('checks')
        if not isinstance(checks, dict) or set(checks) != set(CHECKS) or any(v is not True for v in checks.values()):
            raise ValueError(tid + ': all seven native admission controls must precede plan construction')
        tasks[tid] = dict(t, unsealed=True)
    clusters = {}
    for c in data.get('cluster', []):
        cid = c.get('id')
        if not isinstance(cid, str) or not cid or cid in clusters:
            raise ValueError('unique cluster id required')
        if c.get('role') not in ROLES:
            raise ValueError(cid + ': role is one of ' + ', '.join(ROLES))
        if c.get('kind') not in ('regex', 'public'):
            raise ValueError(cid + ': kind is regex or public')
        desc = c.get('descriptive', False)
        if desc is not False and (desc is not True or c['role'] != 'confirmatory'):
            raise ValueError(cid + ': only a confirmatory cluster is in the descriptive subset')
        members = c.get('tasks')
        if not isinstance(members, list) or not members or any(m not in tasks or tasks[m]['cluster'] != cid for m in members):
            raise ValueError(cid + ': its tasks must be admitted tasks naming this cluster')
        langs = Counter(tasks[m]['lang'] for m in members)
        if c['kind'] == 'regex' and (langs['dafny'] < 1 or langs['verus'] < 1):
            raise ValueError(cid + ': a regex cluster holds its Dafny and its Verus forms')
        if c['kind'] == 'public' and len(members) != 1:
            raise ValueError(cid + ': a public task is a cluster of its own')
        clusters[cid] = dict(c, descriptive=desc)
    orphans = sorted(t for t, v in tasks.items() if v['cluster'] not in clusters or t not in clusters[v['cluster']]['tasks'])
    if orphans:
        raise ValueError('task(s) outside their cluster rows: ' + ', '.join(orphans))
    return data, clusters, tasks


def statement(task):
    return ('R12_TASK_SHA256: ' + task['source_sha256'] + '\nR12_CLUSTER: ' + task['cluster']
            + '\nR12_EXPOSURE: ' + task['exposure'] + '\n' + task['statement'])


def render_plan(task_rows, *, family, seed, repeats, arms, role, lab, freeze):
    q = lambda value: json.dumps(value, ensure_ascii=False)
    s = '# Generated Lab alpha ' + role + ' plan (tools/R12/plan.py); creating it does not unlock execution.\n'
    if lab:
        s += 'lab = "R12"\n'
    s += 'role = ' + q(role) + '\n'
    if freeze:
        s += 'freeze = ' + q(freeze) + '\n'
    s += 'seed = ' + str(seed) + '\nrepeats = ' + str(repeats) + '\nattempts = 1\nmax_reissue = 3\nlever_check = true\n'
    s += 'tasks = ' + q([t['id'] for t in task_rows]) + '\n'
    s += 'system = ' + q((ROOT / 'tools/R12/lab_system.md').read_text()) + '\ninstructions = ' + q((ROOT / 'tools/R12/lab_instructions.md').read_text()) + '\n'
    for t in task_rows:
        s += '\n[task.' + q(t['id']) + ']\npath = ' + q(t['path']) + '\nstatement = ' + q(statement(t)) + '\n'
    for name, policy in arms:
        s += ('\n[[arm]]\nname = ' + q(name) + '\nfamily = ' + q(family) + '\nrounds = ' + str(B)
              + '\nturns = ' + str(B + 2) + '\npolicy = ' + q('fvh.labalpha:' + policy)
              + '\nconstruct = "seeded"\nlab_code = "preserve"\nacceptance = "verify"\n')
    return s


def role_tasks(clusters, tasks, pick):
    rows = []
    for cid in sorted(c for c in clusters if pick(clusters[c])):
        rows.extend(tasks[m] for m in sorted(clusters[cid]['tasks']))
    return rows


def build_plans(clusters, tasks, *, seed, roles=('pilot', 'confirmatory', 'descriptive'),
                claude_subset_seed=None, freeze=FREEZE):
    """{name: plan text}, the Claude subset (or None) and the call arithmetic."""
    if type(seed) is not int or seed < 0:
        raise ValueError('a nonnegative explicit integer seed is required')
    pick = {'pilot': lambda c: c['role'] == 'pilot',
            'confirmatory': lambda c: c['role'] == 'confirmatory',
            'descriptive': lambda c: c['role'] == 'confirmatory' and c['descriptive']}
    arms = {'pilot': REGIMES, 'confirmatory': tuple(r for r in REGIMES if r[0] in PRIMARY),
            'descriptive': tuple(r for r in REGIMES if r[0] in DESCRIPTIVE)}
    plans, calls, subset = {}, {}, None
    for i, role in enumerate(roles):
        if role not in pick:
            raise ValueError('role is pilot, confirmatory or descriptive')
        rows = role_tasks(clusters, tasks, pick[role])
        if not rows:
            raise ValueError('no ' + role + ' cluster in the stratum')
        sealed = [t['id'] for t in rows if t.get('sealed')]
        if sealed:
            raise ValueError(role + ' plan: sealed task(s) never enter a learner plan (D61): ' + ', '.join(sealed))
        lab = role != 'pilot'
        plans[role] = render_plan(rows, family=QWEN, seed=seed + i, repeats=REPEATS, arms=arms[role],
                                  role=role, lab=lab, freeze=freeze if lab else '')
        calls[role] = {'tasks': len(rows), 'clusters': len({t['cluster'] for t in rows}),
                       'runs': len(rows) * len(arms[role]) * REPEATS,
                       'generation_calls': len(rows) * len(arms[role]) * REPEATS * B}
    if claude_subset_seed is not None:
        if type(claude_subset_seed) is not int or claude_subset_seed < 0:
            raise ValueError('a nonnegative explicit integer subset seed is required')
        pool = role_tasks(clusters, tasks, pick['descriptive'])
        rng = random.Random(claude_subset_seed)
        subset = []
        for lang in ('dafny', 'verus'):
            population = sorted((t for t in pool if t['lang'] == lang), key=lambda t: t['id'])
            subset.extend(rng.sample(population, min(5, len(population))))
        plans['descriptive-claude'] = render_plan(subset, family=CLAUDE, seed=seed + 10, repeats=1,
                                                  arms=(('best', 'BestFirst'),), role='descriptive',
                                                  lab=True, freeze=freeze)
        calls['descriptive-claude'] = {'tasks': len(subset), 'runs': len(subset), 'generation_calls': len(subset) * B,
                                       'sentinel_ceiling': 10}
        subset = [t['id'] for t in subset]
    return plans, subset, calls


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--stratum', type=Path, default=ROOT / STRATUM)
    ap.add_argument('--seed', type=int, required=True)
    ap.add_argument('--roles', default='pilot,confirmatory,descriptive')
    ap.add_argument('--claude-subset-seed', type=int)
    ap.add_argument('--write-dir', type=Path, required=True)
    args = ap.parse_args()
    try:
        _, clusters, tasks = load_stratum(ROOT, args.stratum)
        plans, subset, calls = build_plans(clusters, tasks, seed=args.seed, roles=tuple(args.roles.split(',')),
                                           claude_subset_seed=args.claude_subset_seed)
        # Validate the frozen plan syntax before writing reviewable files; no Batch.open.
        sys.path[:0] = [str(ROOT / 'harness'), str(ROOT / 'harness/r')]
        from fvh import batch
        import tempfile
        with tempfile.TemporaryDirectory(prefix='dvl0-r12-plan-check-') as temporary:
            for name, text in plans.items():
                p = Path(temporary) / (name + '.toml'); p.write_text(text)
                plan = batch.load_plan(p, ROOT)
                if plan.lever_check is not True or any(a.caps.get('turns') != B + 2 or a.rounds != B for a in plan.arms):
                    raise ValueError('unexpected frozen plan scope')
        args.write_dir.mkdir(parents=True, exist_ok=True)
        targets = [args.write_dir / (name + '.toml') for name in plans] + [args.write_dir / 'bindings.json']
        if any(p.exists() for p in targets):
            raise ValueError('refuse to overwrite an existing plan/binding; choose a fresh directory')
        binding = {'scope': 'reviewable locked plans; no run, grade or budget event',
                   'stratum_sha256': digest(args.stratum), 'seed': args.seed,
                   'claude_subset_seed': args.claude_subset_seed, 'claude_subset': subset,
                   'plans': calls, 'inputs': {}}
        for path in ['harness/r/fvh_r/engine.py', 'harness/fvh/labalpha.py', 'tools/R12/lab_system.md',
                     'tools/R12/lab_instructions.md', 'tools/R12/plan.py']:
            binding['inputs'][path] = digest(ROOT / path)
        for name, text in plans.items():
            p = args.write_dir / (name + '.toml'); p.write_text(text)
            binding['plans'][name]['plan_sha256'] = digest(p)
            print(name + ': ' + str(p) + ' sha256 ' + digest(p))
        (args.write_dir / 'bindings.json').write_text(json.dumps(binding, indent=2, sort_keys=True) + '\n')
        print('A lab plan stays locked until its exact digest (and the freeze) has a genuine matching pre-registration grade.')
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('R12 plan refused: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
