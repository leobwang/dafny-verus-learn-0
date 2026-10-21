"""tools/R12/plan.py over the schema-2 stratum (DVR4 plan section 3.8): structure and
binding controls on neutral fixtures only (no native admission claim, no model call)."""
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'harness'), str(ROOT / 'harness/r')]
from fvh import batch, prereg  # noqa: E402

spec = importlib.util.spec_from_file_location('r12_plan', ROOT / 'tools/R12/plan.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

CHECKS = {k: True for k in module.CHECKS}
# cluster id -> (kind, role, descriptive, languages)
LAYOUT = {'rx-a': ('regex', 'pilot', False, 'dv'), 'rx-b': ('regex', 'pilot', False, 'dv'),
          'rx-c': ('regex', 'pilot', False, 'dv'), 'pub-a': ('public', 'pilot', False, 'd'),
          'pub-b': ('public', 'pilot', False, 'v'), 'rx-d': ('regex', 'confirmatory', True, 'dv'),
          'rx-e': ('regex', 'confirmatory', False, 'dv'), 'pub-c': ('public', 'confirmatory', True, 'v'),
          'rx-f': ('regex', 'unassigned', False, 'dv')}


def write_root(root, layout=LAYOUT, mutate=None):
    lines = ['schema = 2', 'lab = "R12"']
    tasks = []
    for cid, (kind, role, desc, langs) in layout.items():
        ids = [cid + '-' + l for l in langs] if kind == 'regex' or len(langs) > 1 else [cid]
        lines += ['[[cluster]]', f'id = "{cid}"', f'kind = "{kind}"', f'role = "{role}"',
                  f'descriptive = {str(desc).lower()}', 'tasks = ' + json.dumps(ids)]
        for tid, l in zip(ids, langs):
            ext = '.dfy' if l == 'd' else '.rs'
            rel = f'bench/local/r/labalpha/{tid}/tasks/{tid}{ext}'
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('// neutral structure-only fixture ' + tid + '\n')
            src = hashlib.sha256(p.read_bytes()).hexdigest()
            adm = {'schema': 2, 'status': 'admitted', 'source_sha256': src, 'checks': dict(CHECKS)}
            row = dict(id=tid, cluster=cid, lang='dafny' if l == 'd' else 'verus', path=rel,
                       source_sha256=src, prompt_source_sha256=src, statement='Neutral fixture; no native admission claim.',
                       exposure='neutral fixture', admission=f'bench/local/r/labalpha/{tid}/ADMISSION.json')
            if mutate:
                mutate(row, adm)
            a = root / row['admission']
            a.write_text(json.dumps(adm))
            row['admission_sha256'] = hashlib.sha256(a.read_bytes()).hexdigest()
            tasks.append(row)
    for row in tasks:
        lines.append('[[task]]')
        lines += [f'{k} = {json.dumps(v)}' for k, v in row.items()]
    path = root / 'bench/local/r/labalpha/STRATUM.toml'
    path.write_text('\n'.join(lines) + '\n')
    (root / module.FREEZE).write_text('schema = 1\n')       # an incomplete placeholder
    return path


class PlanContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def plans(self, **kw):
        _, clusters, tasks = module.load_stratum(self.root, write_root(self.root, **kw))
        return module.build_plans(clusters, tasks, seed=1217, claude_subset_seed=4217)

    def test_three_role_plans_with_the_pilot_arithmetic(self):
        plans, subset, calls = self.plans()
        self.assertEqual(set(plans), {'pilot', 'confirmatory', 'descriptive', 'descriptive-claude'})
        self.assertEqual(calls['pilot'], {'tasks': 8, 'clusters': 5, 'runs': 96, 'generation_calls': 960})
        self.assertEqual(calls['confirmatory']['tasks'], 5)
        self.assertEqual(calls['descriptive']['clusters'], 2)
        self.assertEqual(len(subset), 3)          # rx-d-d, rx-d-v, pub-c
        for name, text in plans.items():
            p = self.root / (name + '.toml')
            p.write_text(text)
            plan = batch.load_plan(p, self.root)
            self.assertTrue(plan.lever_check)
            self.assertEqual(plan.role, 'descriptive' if name == 'descriptive-claude' else name)
            self.assertEqual(bool(plan.lab), name != 'pilot')
            self.assertEqual(plan.freeze, '' if name == 'pilot' else module.FREEZE)
            self.assertEqual(plan.system, (ROOT / 'tools/R12/lab_system.md').read_text())
            self.assertTrue(all(a.construct == 'seeded' and a.caps['turns'] == 12 and a.rounds == 10
                                and a.policy.startswith('fvh.labalpha:') for a in plan.arms))
            want = {'pilot': ['independent', 'repair', 'best', 'best-raw'], 'confirmatory': ['best', 'best-raw'],
                    'descriptive': ['independent', 'repair'], 'descriptive-claude': ['best']}[name]
            self.assertEqual([a.name for a in plan.arms], want)
            for t in plan.tasks:
                self.assertRegex(plan.task_statements[t], r'^R12_TASK_SHA256: [0-9a-f]{64}\nR12_CLUSTER: ')

    def test_the_primary_arms_run_in_adjacent_pairs_and_the_descriptive_arms_after(self):
        # Δ298: a pause at the GPU ceiling leaves whole best/best-raw pairs.
        plans, _, _ = self.plans()
        for name in ('pilot', 'confirmatory', 'descriptive'):
            p = self.root / (name + '.toml')
            p.write_text(plans[name])
            ids = [i.id for i in batch.load_plan(p, self.root).items()]
            arms = [i.split('/')[0] for i in ids]
            if name == 'descriptive':
                self.assertEqual(arms[:2], ['independent', 'repair'])
                continue
            primary = [i for i in ids if i.split('/')[0] in ('best', 'best-raw')]
            self.assertEqual(ids[:len(primary)], primary)      # every primary run first
            for a, b in zip(primary[::2], primary[1::2]):        # then pairs: same task, repeat
                self.assertEqual((a.split('/')[0], b.split('/')[0]), ('best', 'best-raw'))
                self.assertEqual(a.split('/')[1:], b.split('/')[1:])
        text = plans['confirmatory'].replace('interleave = [["best", "best-raw"]]\n', '')
        p = self.root / 'confirmatory-arm-major.toml'
        p.write_text(text)
        with self.assertRaisesRegex(batch.BatchError, 'interleaves its two primary arms'):
            batch.load_plan(p, self.root)

    def test_the_batch_role_rules_accept_the_pilot_and_hold_the_rest_to_the_freeze(self):
        plans, _, _ = self.plans()
        for name, ok in (('pilot', True), ('confirmatory', False), ('descriptive', False)):
            p = self.root / (name + '.toml')
            p.write_text(plans[name])
            plan = batch.load_plan(p, self.root)
            if ok:
                self.assertIsNone(prereg.check_roles(self.root, 'R12', plan))
            else:
                with self.assertRaisesRegex(prereg.FreezeRefused, 'incomplete'):
                    prereg.check_roles(self.root, 'R12', plan)

    def test_reproducible(self):
        self.assertEqual(self.plans(), self.plans())

    def test_stratum_refusals(self):
        cases = [
            (dict(mutate=lambda row, adm: adm['checks'].update({'wrong-hints-fail': False})), 'seven native'),
            (dict(mutate=lambda row, adm: adm.update(schema=1)), 'not bound'),
            (dict(mutate=lambda row, adm: row.update(source_sha256='0' * 64)), 'stale task source'),
            (dict(mutate=lambda row, adm: row.update(prompt_source_sha256='0' * 64)), 'prompt carries'),
            (dict(layout={'rx-a': ('regex', 'pilot', False, 'd')}), 'Dafny and its Verus'),
            (dict(layout={'pub-a': ('public', 'pilot', False, 'dv')}), 'cluster of its own'),
            (dict(layout={'rx-a': ('regex', 'pilot', True, 'dv')}), 'descriptive subset'),
            (dict(layout={'rx-a': ('regex', 'final', False, 'dv')}), 'role is one of'),
        ]
        for kw, msg in cases:
            with self.subTest(msg=msg), tempfile.TemporaryDirectory() as t:
                with self.assertRaisesRegex(ValueError, msg):
                    module.load_stratum(Path(t), write_root(Path(t), **kw))

    def test_a_sealed_task_counts_but_never_enters_a_learner_plan(self):
        def seal(row, adm):
            if row['id'].startswith('rx-d'):
                row['sealed'] = True
        path = write_root(self.root, mutate=seal)
        for tid in ('rx-d-d', 'rx-d-v'):
            (self.root / (f'bench/local/r/labalpha/{tid}/tasks/{tid}' + ('.dfy' if tid.endswith('d') else '.rs'))).unlink()
        _, clusters, tasks = module.load_stratum(self.root, path)
        self.assertFalse(tasks['rx-d-d']['unsealed'])
        plans, _, _ = module.build_plans(clusters, tasks, seed=1, roles=('pilot',))
        self.assertIn('pilot', plans)
        with self.assertRaisesRegex(ValueError, 'never enter a learner plan'):
            module.build_plans(clusters, tasks, seed=1, roles=('confirmatory',))
        # unsealed or not: a sealed task with its form present is refused just the same
        path = write_root(self.root, mutate=seal)
        _, clusters, tasks = module.load_stratum(self.root, path)
        with self.assertRaisesRegex(ValueError, 'never enter a learner plan'):
            module.build_plans(clusters, tasks, seed=1, roles=('confirmatory',))

    def test_the_toy_stratum_is_apparatus_smoke_never_data(self):
        with self.assertRaisesRegex(ValueError, 'schema 2'):
            module.load_stratum(ROOT, ROOT / 'bench/local/r/labalpha-smoke/STRATUM.toml')

    def test_bool_or_negative_seeds_refused(self):
        _, clusters, tasks = module.load_stratum(self.root, write_root(self.root))
        for seed in (True, -1):
            with self.assertRaises(ValueError):
                module.build_plans(clusters, tasks, seed=seed)

    def test_course_file_cannot_escape_or_discover_reference_material(self):
        (self.root / 'Solutions').mkdir()
        (self.root / 'Solutions/answer.rs').write_text('protected fixture')
        for path in ['../escape.rs', '/tmp/absolute.rs', 'Solutions/answer.rs', 'missing.rs']:
            with self.assertRaises(ValueError):
                module.course_path(self.root, path)


if __name__ == '__main__':
    unittest.main()
