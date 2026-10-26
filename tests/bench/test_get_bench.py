"""scripts/get_bench.sh against a local git repository as upstream (DV4-PLAN
§9, `tests/bench/`): the pin and the reproducible install, idempotence, a
missing commit, a digest mismatch, the licence rule's refusals, licence and
notice files, the layout split and the subset, the gitignore rule for fetch
sets, the author gate of --pin, --check, and --validate with a fake vcheck.
No network: the upstream is a file:// repository of decoy files."""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GET_BENCH = ROOT / "scripts" / "get_bench.sh"
TMP_BASE = os.environ.get("DVL_TEST_TMP") or None
GIT = ["git", "-c", "user.name=bench-tests", "-c", "user.email=bench-tests@example.invalid",
       "-c", "init.defaultBranch=main"]
LICENSE = "MIT License\n\nDecoy licence text for the bench suite.\n"
NOTICE = "Decoy notice: contributors are acknowledged.\n"


def tmpdir(prefix):
    if TMP_BASE:
        Path(TMP_BASE).mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=prefix, dir=TMP_BASE))


def write(base, rel, text):
    p = Path(base) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def sha(text):
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()


def git(*args, cwd=None):
    return subprocess.run(GIT + list(args), cwd=cwd, check=True, capture_output=True,
                          text=True).stdout.strip()


def manifest(repo, commit, *, mode="fetch", upstream_lic="MIT", leak_scan="", digest="",
             keep_sha=None, extra_keep=True, subset=True):
    keep_sha = keep_sha or sha(LICENSE)
    out = f'''schema = 1

[[set]]
name = "toyset"
title = "Toy set"
repo = "file://{repo}"
commit = "{commit}"
mode = "{mode}"
leak_scan = "{leak_scan}"
sha256 = "{digest}"
licence = {{ spdx = "MIT", checked = "2026-10-06", method = "the file read" }}
upstream = [ {{ what = "decoy prompts", licence = "{upstream_lic}", checked = "2026-10-06" }} ]
'''
    if subset:
        out += 'subset = { index = "index.csv", key = "id", by = "source", exclude = ["skipme"] }\n'
    out += '''
[[set.layout]]
from = "data/hints"
to = "tasks"
glob = "*.dfy"
strip_suffix = "_no_hints"

[[set.layout]]
from = "data/truth"
to = "answers"
glob = "*.dfy"

[[set.layout]]
from = "data/shared.dfy"
to = "tasks/shared.dfy"

[[set.keep]]
path = "LICENSE"
kind = "licence"
sha256 = "''' + keep_sha + '"\n'
    if extra_keep:
        out += f'\n[[set.keep]]\npath = "NOTICE"\nkind = "notice"\nsha256 = "{sha(NOTICE)}"\n'
    return out


class GetBench(unittest.TestCase):
    def setUp(self):
        self.tmp = tmpdir("dvl0-bench-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.up = self.tmp / "upstream"
        write(self.up, "LICENSE", LICENSE)
        write(self.up, "NOTICE", NOTICE)
        write(self.up, "data/hints/alpha_no_hints.dfy", "lemma Alpha() { }\n")
        write(self.up, "data/hints/beta_no_hints.dfy", "lemma Beta() { }\n")
        write(self.up, "data/hints/gamma_no_hints.dfy", "lemma Gamma() { }\n")
        write(self.up, "data/truth/alpha.dfy", "lemma Alpha() { assert true; }\n")
        write(self.up, "data/truth/beta.dfy", "lemma Beta() { assert true; }\n")
        write(self.up, "data/truth/gamma.dfy", "lemma Gamma() { assert true; }\n")
        write(self.up, "data/shared.dfy", "// shared definitions\n")
        write(self.up, "drafts/unverified.dfy", "// left out\n")
        write(self.up, "index.csv", "id,source\nalpha,keepme\nbeta,keepme\ngamma,skipme\n")
        git("init", "-q", str(self.up))
        git("-C", str(self.up), "add", "-A")
        git("-C", str(self.up), "commit", "-q", "-m", "decoy upstream")
        self.commit = git("-C", str(self.up), "rev-parse", "HEAD")
        self.root = self.tmp / "course"
        write(self.root, ".gitignore", "/bench/public/toyset/\n/bench/public/.*.new/\n/bench/public/.*.old/\n")
        write(self.root, "bench/manifest.toml", manifest(self.up, self.commit))
        write(self.root, "scripts/course_mode.sh", "LEARNER_PREFIX=leobwang-\n")
        git("init", "-q", str(self.root))
        self.dest = self.root / "bench" / "public" / "toyset"

    def gb(self, *args, ci=False):
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        env["GIT_CEILING_DIRECTORIES"] = str(self.tmp)
        if ci:
            env["CI"] = "true"
        return subprocess.run(["bash", str(GET_BENCH), *args, "--root", str(self.root)],
                              capture_output=True, text=True, env=env, timeout=300)

    def pin(self):
        p = self.gb("--pin", "toyset", ci=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        m = re.search(r'(?m)^sha256 = "([0-9a-f]{64})"$', (self.root / "bench/manifest.toml").read_text())
        return m.group(1)

    def test_pin_install_split_and_idempotence(self):
        digest = self.pin()
        tasks = sorted(p.relative_to(self.dest).as_posix() for p in self.dest.rglob("*") if p.is_file())
        self.assertEqual(tasks, ["CHANGES", "LICENSE", "NOTICE", "SOURCE.toml", "answers/DVLCANARY",
                                 "answers/alpha.dfy", "answers/beta.dfy", "tasks/alpha.dfy",
                                 "tasks/beta.dfy", "tasks/shared.dfy"])
        self.assertEqual((self.dest / "LICENSE").read_text(), LICENSE)
        changes = (self.dest / "CHANGES").read_text()
        self.assertIn("_no_hints", changes)
        self.assertIn("2 file(s) whose 'source'", changes)       # gamma's task and answer
        self.assertIn(self.commit, (self.dest / "SOURCE.toml").read_text())
        # a fresh install reproduces the pinned digest
        shutil.rmtree(self.dest)
        p = self.gb("toyset")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn(digest[:16], p.stdout)
        # idempotent: no fetch the second time (the upstream is gone)
        shutil.move(str(self.up), str(self.tmp / "gone"))
        p = self.gb("toyset")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("already installed and current", p.stdout)
        p = self.gb("--check")
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_check_with_no_set_installed_is_no_pass(self):
        """DV6 fix round: the empty-set rule; --check that checked nothing exits 3."""
        self.pin()
        shutil.rmtree(self.dest)
        p = self.gb("--check")
        self.assertEqual(p.returncode, 3, p.stdout + p.stderr)
        self.assertIn("nothing was checked", p.stderr)

    def test_the_answers_canary_is_planted_outside_the_digest(self):
        """DV4-PLAN §14 Q5 (the DV5c gaps lane): answers/DVLCANARY's first line is the set's
        derived token, its hash is the set's line of sandbox/canaries.sha256, the sandbox's
        detector sees it, and removing or rewriting it leaves the digest and --check alone."""
        import hashlib
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
        from dvl import bench, sandbox
        digest = self.pin()
        f = self.dest / "answers" / "DVLCANARY"
        tok = f.read_text().split()[0]
        s = {"name": "toyset", "commit": self.commit}
        self.assertEqual(tok, bench.canary_token(s))
        self.assertTrue(sandbox.CANARY_TOKEN.fullmatch(tok.encode()))
        self.assertEqual(bench.canary_line(s),
                         f"{hashlib.sha256(tok.encode()).hexdigest()}  bench/public/toyset/answers/")
        self.assertEqual(bench.tree_digest(self.dest), digest)
        f.unlink()
        self.assertEqual(bench.tree_digest(self.dest), digest)
        p = self.gb("toyset")                          # current: re-plants, no fetch
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(f.read_text().split()[0], tok)
        self.assertEqual(self.gb("--check").returncode, 0)
        self.assertNotIn(b"DVLCANARY-", Path(bench.__file__).read_bytes())

    def test_an_unpinned_set_is_refused(self):
        p = self.gb("toyset")
        self.assertEqual(p.returncode, 3)
        self.assertIn("--pin toyset", p.stderr)

    def test_a_commit_not_upstream_installs_nothing(self):
        write(self.root, "bench/manifest.toml", manifest(self.up, "1" * 40, digest="2" * 64))
        p = self.gb("toyset")
        self.assertNotEqual(p.returncode, 0)
        self.assertFalse(self.dest.exists())

    def test_a_digest_mismatch_installs_nothing(self):
        write(self.root, "bench/manifest.toml", manifest(self.up, self.commit, digest="3" * 64))
        p = self.gb("toyset")
        self.assertEqual(p.returncode, 3)
        self.assertIn("differs from the manifest's", p.stderr)
        self.assertFalse(self.dest.exists())

    def test_the_licence_rule_refuses_to_vendor(self):
        cases = [(dict(mode="vendor", upstream_lic="none", leak_scan="2026-11-01 Δ999"), "every upstream MIT"),
                 (dict(mode="vendor", upstream_lic="MIT", leak_scan=""), "leak_scan")]
        for kw, want in cases:
            write(self.root, "bench/manifest.toml", manifest(self.up, self.commit, **kw))
            p = self.gb("--list")
            self.assertEqual(p.returncode, 3, kw)
            self.assertIn(want, p.stderr)

    def test_licence_and_notice_files(self):
        write(self.root, "bench/manifest.toml", manifest(self.up, self.commit, keep_sha="4" * 64))
        p = self.gb("--pin", "toyset", ci=True)
        self.assertEqual(p.returncode, 3)
        self.assertIn("LICENSE differs from its recorded sha256", p.stderr)
        self.assertFalse(self.dest.exists())
        write(self.root, "bench/manifest.toml", manifest(self.up, self.commit))
        self.pin()
        (self.dest / "NOTICE").unlink()
        p = self.gb("--check", "toyset")
        self.assertEqual(p.returncode, 3)
        self.assertIn("NOTICE is missing", p.stderr)
        p = self.gb("--list")
        self.assertIn("installed, the kept file NOTICE is missing", p.stdout)

    def test_check_finds_a_changed_file(self):
        self.pin()
        (self.dest / "answers" / "alpha.dfy").write_text("changed\n")
        p = self.gb("--check")
        self.assertEqual(p.returncode, 3)
        self.assertIn("tree digest differs", p.stderr)

    def test_a_fetch_set_must_be_gitignored(self):
        write(self.root, ".gitignore", "")
        p = self.gb("--pin", "toyset", ci=True)
        self.assertEqual(p.returncode, 3)
        self.assertIn("must be ignored by git", p.stderr)

    def test_pin_is_author_only(self):
        p = self.gb("--pin", "toyset")
        self.assertEqual(p.returncode, 3)
        self.assertIn("author-only", p.stderr)
        self.assertIn('\nsha256 = ""\n', (self.root / "bench/manifest.toml").read_text())
        self.assertFalse(self.dest.exists())

    def test_a_layout_transform_is_applied_and_recorded(self):
        write(self.up, "data/hints/alpha_no_hints.dfy", "lemma Alpha() { assume {:axiom} false; }\n")
        git("-C", str(self.up), "commit", "-q", "-am", "an axiom assume")
        commit = git("-C", str(self.up), "rev-parse", "HEAD")
        m = manifest(self.up, commit).replace('strip_suffix = "_no_hints"\n',
                                               'strip_suffix = "_no_hints"\n'
                                               'transform = "dafny-axiom-assume-to-hole"\n')
        write(self.root, "bench/manifest.toml", m)
        self.pin()
        self.assertEqual((self.dest / "tasks/alpha.dfy").read_text(), "lemma Alpha() { assume false; }\n")
        self.assertEqual((self.dest / "tasks/beta.dfy").read_text(), "lemma Beta() { }\n")
        changes = (self.dest / "CHANGES").read_text()
        self.assertIn("transform dafny-axiom-assume-to-hole", changes)
        self.assertIn("(1 file(s) changed)", changes)
        self.assertIn("except where a line below names a", changes)
        self.assertEqual(self.gb("--check").returncode, 0)

    def test_an_unknown_transform_is_refused(self):
        m = manifest(self.up, self.commit).replace('strip_suffix = "_no_hints"\n',
                                                   'strip_suffix = "_no_hints"\ntransform = "nope"\n')
        write(self.root, "bench/manifest.toml", m)
        p = self.gb("--list")
        self.assertEqual(p.returncode, 3)
        self.assertIn("unknown transform 'nope'", p.stderr)


FAKE_TOOL = r"""import json, os, sys, time
tool = os.path.basename(sys.argv[0])
t = [a for a in sys.argv[1:] if not a.startswith("--")][-1]
name = os.path.basename(t).split(".")[0]
state = os.environ.get("FAKE_STATE")
if state:
    with open(os.path.join(state, "calls.log"), "a") as f:
        f.write(f"{tool} {'answers' if '/answers/' in t else 'tasks'} {name}\n")
if name == os.environ.get("FAKE_SLEEP_ON"):
    with open(os.path.join(state, "sleeper.pid"), "w") as f:
        f.write(str(os.getpid()))
    time.sleep(120)
if name == os.environ.get("FAKE_KILL_ONCE") and state:
    mark = os.path.join(state, "killed-" + name)
    if not os.path.exists(mark):
        open(mark, "w").close()
        sys.exit(137)
if tool == "specfreeze":
    bad = name == os.environ.get("FAKE_STATIC_FAIL")
    print(json.dumps({"findings": [{"kind": "freeze-changed", "file": t, "line": 1,
                                    "message": "decoy"}] if bad else []}))
    sys.exit(1 if bad else 0)
if tool == "vaudit":
    print(json.dumps({"findings": [], "lang": "dafny", "target": t}))
    sys.exit(0)
ok = "/answers/" in t
print(json.dumps({"verdict": "verified" if ok else "failed", "stage": "verify",
                  "holes": [] if ok else [{"k": 1}], "diagnostics": [], "verified_count": 2}))
sys.exit(0 if ok else 1)
"""


class Validate(unittest.TestCase):
    """--validate with fake vcheck and vaudit: the pool rule, the header, resume,
    a retried job, a stop, a seeded stratified sample and the memory share."""

    setUp_base = GetBench.setUp
    gb_base = GetBench.gb
    pin = GetBench.pin

    def setUp(self):
        self.setUp_base()
        write(self.root, "scripts/vcheck", FAKE_TOOL)
        write(self.root, "scripts/vaudit", FAKE_TOOL)
        write(self.root, "scripts/specfreeze", FAKE_TOOL)
        self.state = self.tmp / "state"
        self.state.mkdir()
        self.env = {"FAKE_STATE": str(self.state), "DVL_BENCH_TMP": str(self.tmp / "scratch")}

    def gb(self, *args, ci=False, **extra):
        old = {k: os.environ.get(k) for k in list(self.env) + list(extra)}
        os.environ.update(self.env)
        os.environ.update(extra)
        try:
            return self.gb_base(*args, ci=ci)
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def rows(self, name="validation.jsonl"):
        lines = [json.loads(x) for x in (self.dest / name).read_text().splitlines()]
        return lines[0], [r for r in lines if "task" in r]

    def calls(self):
        f = self.state / "calls.log"
        return f.read_text().splitlines() if f.is_file() else []

    def test_validate_with_fake_tools(self):
        self.pin()
        p = self.gb("--validate", "toyset", "--only", "alpha")
        self.assertEqual(p.returncode, 0, p.stderr)
        head, rows = self.rows()
        self.assertEqual(head["kind"], "header")
        self.assertEqual((head["rows"], head["pool"], head["retry_left"]), (1, 1, 0))
        self.assertEqual(head["selection"], {"only": ["alpha"], "sample": None})
        self.assertEqual([r["task"] for r in rows], ["alpha.dfy"])
        self.assertTrue(rows[0]["pool"])
        self.assertEqual(rows[0]["task_form"]["verdict"], "failed")
        self.assertEqual(rows[0]["answer_audit"]["findings"], 0)
        self.assertEqual(self.calls(), ["vcheck answers alpha", "vaudit answers alpha",
                                        "specfreeze answers alpha", "vcheck tasks alpha"])
        self.assertEqual(rows[0]["lab_static"]["findings"], 0)
        self.assertFalse((self.dest / "validation.partial.jsonl").exists())
        self.assertEqual(list((self.tmp / "scratch").iterdir()), [])
        self.assertEqual(self.gb("--check").returncode, 0)     # validation files are not digested

    def test_a_killed_job_is_retried_by_the_next_run(self):
        self.pin()
        p = self.gb("--validate", "toyset", FAKE_KILL_ONCE="beta")
        self.assertEqual(p.returncode, 0, p.stderr)
        head, rows = self.rows()
        self.assertEqual(head["retry_left"], 1)
        beta = next(r for r in rows if r["task"] == "beta.dfy")
        self.assertEqual((beta["pool"], beta["reason"]), (False, "retry:killed(memory)"))
        n = len(self.calls())
        p = self.gb("--validate", "toyset", FAKE_KILL_ONCE="beta")
        self.assertEqual(p.returncode, 0, p.stderr)
        head, rows = self.rows()
        self.assertEqual((head["retry_left"], head["pool"], head["segments"]), (0, 2, 2))
        self.assertEqual(self.calls()[n:], ["vcheck answers beta", "vaudit answers beta",
                                            "specfreeze answers beta", "vcheck tasks beta"])

    def test_an_answer_that_is_no_valid_delivery_leaves_the_pool(self):
        self.pin()
        p = self.gb("--validate", "toyset", FAKE_STATIC_FAIL="beta")
        self.assertEqual(p.returncode, 0, p.stderr)
        head, rows = self.rows()
        beta = next(r for r in rows if r["task"] == "beta.dfy")
        self.assertEqual((beta["pool"], beta["reason"]), (False, "answer-fails-lab-static:freeze-changed"))
        self.assertNotIn("task_form", beta)
        self.assertEqual(head["pool"], 1)

    def test_sigterm_stops_and_the_same_command_resumes(self):
        import signal
        import time
        self.pin()
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        env.update(self.env, FAKE_SLEEP_ON="beta", GIT_CEILING_DIRECTORIES=str(self.tmp))
        proc = subprocess.Popen(["bash", str(GET_BENCH), "--validate", "toyset", "--root",
                                 str(self.root)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, env=env)
        pidf = self.state / "sleeper.pid"
        for _ in range(300):
            if pidf.is_file() and pidf.read_text():
                break
            time.sleep(0.1)
        self.assertTrue(pidf.is_file(), "the sleeping job never started")
        time.sleep(0.3)
        proc.send_signal(signal.SIGTERM)
        out, err = proc.communicate(timeout=60)
        self.assertEqual(proc.returncode, 1, err)
        self.assertIn("stopped (SIGTERM)", err)
        sleeper = int(pidf.read_text())
        for _ in range(50):
            try:
                os.kill(sleeper, 0)
            except ProcessLookupError:
                break
            time.sleep(0.1)
        else:
            self.fail("the stopped job's process is still running")
        head, rows = self.rows("validation.partial.jsonl")
        self.assertNotIn("beta.dfy", [r["task"] for r in rows])
        self.assertIn('"stopped": "SIGTERM"', (self.dest / "validation.partial.jsonl").read_text())
        self.assertFalse((self.dest / "validation.jsonl").exists())
        done_before = {r["task"] for r in rows}
        n = len(self.calls())
        p = self.gb("--validate", "toyset")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("resuming", p.stdout)
        head, rows = self.rows()
        self.assertEqual(sorted(r["task"] for r in rows), ["alpha.dfy", "beta.dfy"])
        self.assertEqual(head["segments"], 2)
        rerun = {line.split()[-1] for line in self.calls()[n:]}
        self.assertFalse(rerun & {t.split(".")[0] for t in done_before})
        self.assertEqual(list((self.tmp / "scratch").iterdir()), [])

    def test_another_selection_needs_restart(self):
        self.pin()
        partial = self.dest / "validation.partial.jsonl"
        partial.write_text(json.dumps({"kind": "header", "schema": 2, "set": "toyset",
                                       "sha256": "0" * 64, "pins_sha256": "x",
                                       "selection": {}}) + "\n")
        p = self.gb("--validate", "toyset")
        self.assertEqual(p.returncode, 3)
        self.assertIn("--restart", p.stderr)
        p = self.gb("--validate", "toyset", "--restart")
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_a_seeded_sample_is_recorded_and_reproducible(self):
        self.pin()
        p = self.gb("--validate", "toyset", "--sample", "1", "--seed", "s1")
        self.assertEqual(p.returncode, 0, p.stderr)
        head, rows = self.rows()
        smp = head["selection"]["sample"]
        self.assertEqual((smp["n"], smp["of"], smp["seed"]), (1, 2, "s1"))
        self.assertEqual(smp["strata"], {"dafny": [2, 1]})     # no index installed: by language
        self.assertEqual(len(rows), 1)
        first = rows[0]["task"]
        p = self.gb("--validate", "toyset", "--sample", "1", "--seed", "s1", "--restart")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.rows()[1][0]["task"], first)
        self.assertEqual(self.gb("--validate", "toyset", "--sample", "1").returncode, 3)

    def test_the_pool_is_pinned_and_checked(self):
        import tomllib
        self.pin()
        self.assertEqual(self.gb("--validate", "toyset", FAKE_KILL_ONCE="alpha").returncode, 0)
        p = self.gb("--pin-pool", "toyset", ci=True)
        self.assertEqual(p.returncode, 3)                    # a row is left to retry
        self.assertIn("left to retry", p.stderr)
        self.assertEqual(self.gb("--validate", "toyset", FAKE_KILL_ONCE="alpha").returncode, 0)
        self.assertEqual(self.gb("--pin-pool", "toyset").returncode, 3)   # author-only
        p = self.gb("--pin-pool", "toyset", ci=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        first = (self.root / "bench/public/POOLS.toml").read_text()
        self.assertEqual(self.gb("--pin-pool", "toyset", ci=True).returncode, 0)
        self.assertEqual((self.root / "bench/public/POOLS.toml").read_text(), first)   # stable
        self.assertIn('selection = "{\\"only\\": [], \\"sample\\": null}"', first)
        pools = tomllib.loads((self.root / "bench/public/POOLS.toml").read_text())
        e = pools["pool"][0]
        self.assertEqual((e["set"], e["rows"], e["pool"]), ("toyset", 2, 2))
        self.assertEqual(e["tasks"], ["alpha.dfy", "beta.dfy"])
        p = self.gb("--check")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("pool pinned: 2 of 2", p.stdout)
        f = self.dest / "validation.jsonl"
        rows = [json.loads(x) for x in f.read_text().splitlines()]
        self.assertEqual(rows[2]["task"], "beta.dfy")
        rows[2]["pool"] = False                     # a run whose pool differs from the pin
        f.write_text("\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n")
        p = self.gb("--check")
        self.assertEqual(p.returncode, 3)
        self.assertIn("differs from the pool pinned", p.stderr)

    def test_workers_take_no_memory_share(self):
        """D78: no course-side memory management; --workers alone needs --validate."""
        self.assertEqual(self.gb("--workers", "2", "--list").returncode, 2)


class Sampling(unittest.TestCase):
    def test_allocation_is_proportional_with_one_per_stratum(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from dvl import bench
        strata = {f"a{i}": "big" for i in range(10)}
        strata.update({f"b{i}": "mid" for i in range(5)})
        strata["c0"] = "tiny"
        drawn, alloc = bench.stratified_sample(strata, 8, "seed")
        self.assertEqual(alloc, {"big": [10, 5], "mid": [5, 2], "tiny": [1, 1]})
        self.assertEqual(len(drawn), 8)
        self.assertEqual(bench.stratified_sample(strata, 8, "seed")[0], drawn)
        self.assertNotEqual(bench.stratified_sample(strata, 8, "other")[0], drawn)
        self.assertEqual(len(bench.stratified_sample(strata, 99, "seed")[0]), 16)


class AuditRunIncomplete(unittest.TestCase):
    """An assumption audit that did not complete (killed by memory, stopped by
    the wall clock) retries its row; a real finding excludes it (DV5e review)."""

    def judged(self, findings):
        sys.path.insert(0, str(ROOT / "scripts"))
        from dvl import bench
        au = {"findings": len(findings), "exit_code": 1, "seconds": 1.0,
              "kinds": sorted({f["kind"] for f in findings})}
        v = bench.audit_run_verdict(findings)
        if v:
            au["verdict"] = v
        row = {"answer": {"verdict": "verified", "holes": 0}, "answer_audit": au}
        return bench.judge_row(row)

    def test_killed_audit_is_a_retry(self):
        for kind, msg in (("audit-error", "the audit did not run to completion (killed(memory))"),
                          ("audit-incomplete", "the --no-cheating run of x did not complete "
                                               "(killed(memory), stage verify)")):
            row = self.judged([{"kind": kind, "message": msg, "file": "t", "line": 0}])
            self.assertEqual(row["reason"], "retry:killed(memory)")
            self.assertFalse(row["pool"])

    def test_timed_out_audit_is_a_retry(self):
        for msg in ("the --no-cheating run did not complete (inconclusive: wall-clock)",
                    "stopped by the wall-clock limit"):
            row = self.judged([{"kind": "audit-incomplete", "message": msg, "file": "t",
                                "line": 0}])
            self.assertEqual(row["reason"], "retry:timeout")

    def test_a_real_finding_excludes(self):
        row = self.judged([{"kind": "assume", "message": "an assume statement", "file": "t",
                            "line": 3}])
        self.assertEqual(row["reason"], "answer-audit:assume")
        row = self.judged([{"kind": "audit-error", "message": "the target does not parse",
                            "file": "t", "line": 0}])
        self.assertEqual(row["reason"], "answer-audit:audit-error")


if __name__ == "__main__":
    unittest.main()
