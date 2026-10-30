"""The sandbox library and scripts/mksandbox-run without Docker (DV4-PLAN §9,
DV4 step 1b): manifests and their refusals, materialization, the static
self-test, the return path from fabricated tar streams, the secret scan, the
access diagnosis against a fake docker, the golden --dry-run argv, and the
class tables kept in step with the guard and the checker.

Every fixture is a decoy in a throwaway root (sandbox_common.make_root); the
regression checks name what must be refused and never carry an exploit."""

import json
import os
import re
import stat
import subprocess
import sys
import tarfile
import tomllib
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sandbox_common as sc  # noqa: E402
from dvl import sandbox  # noqa: E402

GOLDEN = Path(__file__).resolve().parent / "golden"


class Base(unittest.TestCase):
    def setUp(self):
        self.root = sc.make_root(git=True)
        self.runs = sc.tmpdir("dvl0-sandbox-runs-")
        self.addCleanup(sc.cleanup, self.root, self.runs)

    def refused(self, m, want):
        with self.assertRaises(sandbox.ManifestError) as cm:
            sandbox.validate(m, self.root)
        text = "\n".join(cm.exception.problems)
        self.assertIn(want, text)
        return text


class SourceClasses(Base):
    """Each refused source class is refused before anything is copied (§5.3)."""

    SAMPLES = {
        "Solutions/dafny/Q/Q98_Sandbox/std/Q98_Sandbox.dfy": "reference",
        "paper/solutions/Q98_solutions.tex": "reference",
        "tests/instructor/leak_patterns/Q98.txt": "reference",
        "tests/instructor/fixtures/Q98_gold_answers.tex": "reference",
        "verus/q/q98_solutions/src/lib.rs": "reference",
        "notes/sealed.tar.age": "reference",
        "Hidden/labs/Q15/truth.dfy": "held-out",
        "instructor/ledger.md": "instructor",
        ".claude/skills/instructor/CORE.md": "guard",
        "CLAUDE.md": "guard",
        ".git/config": "history",
        "bench/public/decoyset/answers/t1.dfy": "bench-answers",
        "bench/local/q/card01/answers/answer.dfy": "bench-answers",
        "bench/manifest.toml": "bench-config",
        "research/runs/Q98/r1/run.json": "research",
        "docs/Q98_Sandbox.md": "chapters",
        "paper/rubrics/Q98_rubric.md": "written",
        "tests/corpus/dafny/G01/main.dfy": "tests",
        "sandbox/attested.toml": "sandbox-config",
        "verus/target/debug/x.vir": "build-output",
        "build/ci/latest/summary.txt": "build-output",
        "dafny/Q/Q98_Sandbox/std/Q98_Sandbox-py/x.py": "build-output",
        "Challenges/Q19/Heap.dfy": "solo",
        "agents/prover.py": "solo",
    }

    def test_every_sample_has_its_class(self):
        for path, cls in self.SAMPLES.items():
            self.assertEqual(sandbox.source_class(path), cls, path)

    def test_learner_and_course_files_are_not_refused_by_class(self):
        for path in (sc.AGENT_D, sc.GIVEN_D, sc.PROJ_D, "scripts/vcheck", "expected/Q98.counts",
                     "bench/public/decoyset/tasks/t1.dfy", "MODULES.toml"):
            self.assertIsNone(sandbox.source_class(path), path)

    def test_a_manifest_naming_a_refused_class_is_refused(self):
        for path in ("Solutions/dafny/Q/Q98_Sandbox/std/Q98_Sandbox.dfy",
                     "bench/public/decoyset/answers/t1.dfy", "docs/Q98_Sandbox.md"):
            m = sc.agent_manifest(self.root)
            m["file"].append(sc.entry(self.root, path, "given", dst=f"extra/{Path(path).name}"))
            self.refused(m, "refused source class")

    def test_the_snapshot_exception_is_one_named_path_at_a_commit(self):
        snap = "research/snapshots/Q98_Agent.dfy"
        ok = sc.agent_manifest(self.root)
        ok["file"].append(sc.entry(self.root, snap, "snapshot", rev="HEAD"))
        sandbox.validate(ok, self.root)
        no_rev = sc.agent_manifest(self.root)
        no_rev["file"].append(sc.entry(self.root, snap, "snapshot"))
        self.refused(no_rev, "refused source class (research)")
        as_given = sc.agent_manifest(self.root)
        as_given["file"].append(sc.entry(self.root, snap, "given", rev="HEAD"))
        self.refused(as_given, "refused source class (research)")
        two = sc.agent_manifest(self.root)
        two["file"].append(sc.entry(self.root, snap, "snapshot", rev="HEAD"))
        two["file"].append(sc.entry(self.root, snap, "snapshot", rev="HEAD", dst="snap2.dfy"))
        self.refused(two, "at most one snapshot")

    def test_class_tables_agree_with_the_guard_and_the_checker(self):
        self.assertEqual(sandbox.class_drift(sc.ROOT), [])

    def test_a_new_reference_directory_in_the_guard_is_drift(self):
        hook = sc.tmpdir("dvl0-sandbox-hook-") / "spoiler-guard.sh"
        self.addCleanup(sc.cleanup, hook.parent)
        src = (sc.ROOT / ".claude/hooks/spoiler-guard.sh").read_text(encoding="utf-8")
        hook.write_text(src.replace('RX_SPOIL_DIR="(/Solutions|', 'RX_SPOIL_DIR="(/Answerkeys|/Solutions|', 1))
        problems = sandbox.class_drift(sc.ROOT, hook=hook)
        self.assertTrue(any(p.startswith("Answerkeys/") for p in problems), problems)


class Manifests(Base):
    def test_a_well_formed_agent_manifest_validates(self):
        m = sandbox.validate(sc.agent_manifest(self.root), self.root)
        self.assertEqual((m.kind, m.network, m.returns), ("agent", "model", (sc.AGENT_D,)))
        self.assertEqual(m.limits["mem_gb"], 15.5)       # Dafny 8 + 1 + 2.5 + 4
        v = sandbox.validate(sc.verify_manifest(self.root), self.root)
        self.assertEqual(v.limits["mem_gb"], 11.5)       # Dafny 8 + 1 + 2.5

    def test_benchmark_task_paths_and_their_stratum_module(self):
        """A lab card's tasks/ (bench/local/<q|r>/<lab>/<card>/tasks/) is a benchmark
        task as a stratum's own tasks/ is, and a local task's module is its
        STRATUM.toml's `lab` (the module a generated oracle file runs under)."""
        for rel, want in (("bench/public/he/tasks/t.dfy", True),
                          ("bench/local/q/card01/tasks/task.dfy", True),
                          ("bench/local/q/lab2/d01-x/tasks/d01-x.dfy", True),
                          ("bench/local/q/lab2/a/b/tasks/x.dfy", False),
                          ("bench/local/q/lab2/d01-x/answers/x.dfy", False)):
            self.assertEqual(sandbox.bench_task(rel), want, rel)
        sc.write(self.root, "bench/local/q/lab7/STRATUM.toml", 'schema = 1\nlab = "Q98"\n')
        self.assertEqual(sandbox.stratum_module(self.root, "bench/local/q/lab7/c1/tasks/c1.dfy"),
                         "Q98")
        self.assertIsNone(sandbox.stratum_module(self.root, "bench/local/q/lab8/c1/tasks/c1.dfy"))
        self.assertIsNone(sandbox.stratum_module(self.root, "bench/public/he/tasks/t.dfy"))

    def test_no_field_can_weaken_isolation(self):
        for key in ("privileged", "devices", "network_mode", "capabilities", "socket", "gpus"):
            self.refused(sc.agent_manifest(self.root, **{key: True}), "unknown manifest key")
        m = sc.agent_manifest(self.root)
        m["limits"]["gpus"] = 1
        self.refused(m, "unknown [limits] key")
        m = sc.agent_manifest(self.root)
        m["file"][0]["mode"] = "rw"
        self.refused(m, "unknown key(s) ['mode']")

    def test_networks(self):
        self.refused(sc.verify_manifest(self.root, network="model"), "always network = \"none\"")
        self.refused(sc.agent_manifest(self.root, network="none"), "reaches its model")
        self.refused(sc.agent_manifest(self.root, network="host"), "network must be one of")
        m = sc.agent_manifest(self.root)
        m["agent"]["cli"] = "claude"
        self.refused(m, "network = \"anthropic\"")

    def test_roles_follow_the_module(self):
        m = sc.agent_manifest(self.root)
        m["file"].append(sc.entry(self.root, "dafny/Q/Q97_Other/agent/Q97_Agent.dfy", "editable"))
        self.refused(m, "not in Q98's agentic list")
        m = sc.agent_manifest(self.root)
        m["file"].append(sc.entry(self.root, sc.EX_D, "editable"))
        self.refused(m, "no finished exercise")
        m = sc.agent_manifest(self.root)
        m["file"].append(sc.entry(self.root, "dafny/given/Q/QG_L5_BigNat.dfy", "given"))
        self.refused(m, "not a given file of Q98's layer chain")
        m = sc.agent_manifest(self.root)
        m["file"].append(sc.entry(self.root, "scripts/ci.sh", "tool"))
        self.refused(m, "not one of the trusted course tools")
        m = sc.agent_manifest(self.root)
        m["file"].append(sc.entry(self.root, "expected/Q97.counts", "expected"))
        self.refused(m, "not one of Q98's pins")
        m = sc.agent_manifest(self.root)
        m["file"].append(sc.entry(self.root, sc.EX_D, "contract", dst="C2.md"))
        self.refused(m, "contract text is written inline")
        m = sc.agent_manifest(self.root)
        m["file"].append(sc.text_entry("extra.dfy", "given", "// x\n"))
        self.refused(m, "may carry inline text")

    def test_paths_content_and_links(self):
        m = sc.agent_manifest(self.root)
        m["file"][1]["sha256"] = "0" * 64
        self.refused(m, "does not match its sha256")
        m = sc.agent_manifest(self.root)
        m["file"][1]["dst"] = "../escape.dfy"
        self.refused(m, "dst must be a relative path")
        m = sc.agent_manifest(self.root)
        m["file"][1]["src"] = "/etc/hostname"
        self.refused(m, "src must be a course-relative path")
        link = Path(self.root) / "dafny/given/Q/QG_L2_BigNat.dfy"
        link.symlink_to("QG_L1_BigNat.dfy")
        m = sc.agent_manifest(self.root)
        m["file"].append({"src": "dafny/given/Q/QG_L2_BigNat.dfy", "dst": "g2.dfy", "role": "given",
                          "sha256": sc.sha((Path(self.root) / sc.GIVEN_D).read_bytes())})
        self.refused(m, "not a regular file")

    def test_returns(self):
        self.refused(sc.agent_manifest(self.root, **{"return": []}), "names its [[return]] paths")
        self.refused(sc.agent_manifest(self.root, **{"return": [sc.GIVEN_D]}),
                     "is not a staged editable file")
        self.refused(sc.verify_manifest(self.root, **{"return": [sc.AGENT_D]}), "returns nothing")

    def test_memory_above_the_pinned_bound_is_refused(self):
        m = sc.agent_manifest(self.root)
        m["limits"]["mem_gb"] = 64
        self.refused(m, "exceeds the pinned bound 15.5")

    def test_image_lock(self):
        bare = sc.make_root(git=False, lock=False)
        self.addCleanup(sc.cleanup, bare)
        with self.assertRaises(sandbox.ManifestError) as cm:
            sandbox.validate(sc.agent_manifest(bare), bare)
        self.assertIn("not in sandbox/images.lock", str(cm.exception))


class ImagesLockArch(Base):
    """DELTAS Δ504: schema 2 has an entry per name and architecture; a host is
    offered (and accepts) only its own architecture's, and a schema-1 entry
    without an arch is amd64's."""

    def test_only_this_hosts_architecture(self):
        d = "sha256:" + "ab" * 32
        e = "sha256:" + "ef" * 32
        sc.write(self.root, "sandbox/images.lock",
                 f'schema = 2\n\n[[image]]\nname = "dvl-toolchain"\narch = "amd64"\ndigest = "{d}"\n\n'
                 f'[[image]]\nname = "dvl-toolchain"\narch = "arm64"\ndigest = "{e}"\n')
        self.assertEqual(list(sandbox.read_images_lock(self.root, "amd64")), [f"dvl-toolchain@{d}"])
        self.assertEqual(list(sandbox.read_images_lock(self.root, "arm64")), [f"dvl-toolchain@{e}"])
        mine = f"dvl-toolchain@{d if sandbox.host.docker_arch() == 'amd64' else e}"
        self.assertEqual(list(sandbox.read_images_lock(self.root)), [mine])
        sc.write(self.root, "sandbox/images.lock",
                 f'schema = 1\n\n[[image]]\nname = "dvl-toolchain"\ndigest = "{d}"\n')
        self.assertEqual(list(sandbox.read_images_lock(self.root, "amd64")), [f"dvl-toolchain@{d}"])
        self.assertEqual(list(sandbox.read_images_lock(self.root, "arm64")), [])


class Materialize(Base):
    def test_inputs_are_staged_read_only_in_a_private_run_dir(self):
        m = sandbox.validate(sc.agent_manifest(self.root), self.root)
        run = sandbox.materialize(m, self.root, base=self.runs)
        self.addCleanup(sandbox.remove_run, run)
        self.assertEqual(stat.S_IMODE(os.stat(run.path).st_mode), 0o700)
        for d in ("in", "work", "out", "state"):
            self.assertTrue((run.path / d).is_dir())
        staged = sorted(p.relative_to(run.inp).as_posix() for p in run.inp.rglob("*") if p.is_file())
        self.assertEqual(staged, sorted(e.dst for e in m.files))
        self.assertEqual(stat.S_IMODE(os.stat(run.inp / sc.AGENT_D).st_mode), 0o444)
        with self.assertRaises(PermissionError):
            (run.inp / "planted.txt").write_text("x")


class SelfTest(Base):
    def run_selftest(self, m, plant=None, answers=None, root=None):
        root = root or self.root
        man = sandbox.validate(m, root)
        run = sandbox.materialize(man, root, base=self.runs)
        self.addCleanup(sandbox.remove_run, run)
        if plant:
            os.chmod(run.inp, 0o755)
            (run.inp / plant).write_text("planted\n")
        return sandbox.selftest(man, run, root, answers=answers)

    def test_a_clean_run_passes_and_records_the_skipped_author_checks(self):
        rep = self.run_selftest(sc.agent_manifest(self.root))
        self.assertTrue(rep["ok"], rep)
        self.assertFalse(rep["checks"]["author"]["ran"])
        self.assertIn("study mode", rep["checks"]["author"]["skipped"])

    def test_closure_refuses_an_unlisted_file(self):
        rep = self.run_selftest(sc.agent_manifest(self.root), plant="extra.txt")
        self.assertFalse(rep["checks"]["closure"]["ok"])
        self.assertIn("not in the manifest", rep["checks"]["closure"]["problems"][0])

    def test_a_canary_prefix_is_refused_and_attributed_by_hash(self):
        token = "DVLCANARY-" + "q98decoy0001"
        sc.write(self.root, "sandbox/canaries.sha256", f"{sc.sha(token)}  the decoy tree\n")
        sc.write(self.root, sc.AGENT_D, sc.AGENT_TEXT + f"// {token}\n")
        rep = self.run_selftest(sc.agent_manifest(self.root))
        self.assertFalse(rep["ok"])
        self.assertIn("the decoy tree", rep["checks"]["canaries"]["problems"][0])
        sc.write(self.root, sc.AGENT_D, sc.AGENT_TEXT + "// DVLCANARY-unlisted42\n")
        rep = self.run_selftest(sc.agent_manifest(self.root))
        self.assertIn("an unlisted tree", rep["checks"]["canaries"]["problems"][0])

    def test_the_shipped_canary_list_names_each_planted_tree(self):
        """DV4-PLAN §14 Q5 (the DV5c gaps lane): the course's own sandbox/canaries.sha256
        lists one hash per tree, the reference trees, the hidden truth, the author cache
        and each public set's answers/ among them. It reads the list only, never a tree;
        sandbox_doors.py canary checks each planted file against its line."""
        real = Path(__file__).resolve().parents[2]
        listed = sandbox.read_canaries(real)
        trees = sorted(listed.values())
        self.assertEqual(len(trees), len(set(trees)), "a tree listed twice")
        for want in ("Solutions/", "paper/solutions/", "tests/instructor/leak_patterns/",
                     "tests/instructor/fixtures/", "Hidden/", "~/.cache/dafny-verus-learn-0/"):
            self.assertIn(want, trees)
        sys.path.insert(0, str(real / "scripts"))
        from dvl import bench
        _, sets = bench.load_manifest(real)
        for s in sets.values():
            line = bench.canary_line(s)
            self.assertEqual(listed.get(line.split()[0]), line.split(None, 1)[1], s["name"])

    def test_a_lab_task_card_needs_its_attestation(self):
        card = "bench/local/q/card01/tasks/task.dfy"
        m = sc.agent_manifest(self.root)
        m["file"].append(sc.entry(self.root, card, "task", dst="TASK.dfy"))
        rep = self.run_selftest(m)
        self.assertFalse(rep["checks"]["attestation"]["ok"])
        digest = sc.sha((Path(self.root) / card).read_bytes())
        sc.write(self.root, "sandbox/attested.toml",
                 f'schema = 1\n\n[[card]]\npath = "{card}"\nsha256 = "{digest}"\n')
        rep = self.run_selftest(m)
        self.assertTrue(rep["checks"]["attestation"]["ok"], rep)

    def _body(self, seed, n=60):
        return "\n".join(f"lemma L{seed}_{i}(x: nat) ensures x + {i} >= {i} {{ assert x >= 0; }}"
                         for i in range(n)) + "\n"

    def test_public_answers_equal_or_shared_windows_are_refused(self):
        body = self._body("pub")
        sc.write(self.root, "bench/public/decoyset/answers/t2.dfy", body)
        sc.write(self.root, sc.AGENT_D, sc.AGENT_TEXT + body)
        rep = self.run_selftest(sc.agent_manifest(self.root))
        self.assertFalse(rep["checks"]["public-answers"]["ok"])
        self.assertIn(f"windows of {sandbox.WINDOW_TOKENS} tokens",
                      rep["checks"]["public-answers"]["problems"][0])
        sc.write(self.root, sc.AGENT_D, body)
        rep = self.run_selftest(sc.agent_manifest(self.root))
        self.assertIn("equals", " ".join(rep["checks"]["public-answers"]["problems"]))

    def test_windows_in_given_text_or_the_matching_task_do_not_count(self):
        body = self._body("given")
        sc.write(self.root, "bench/public/decoyset/answers/t3.dfy", "// answer\n" + body)
        sc.write(self.root, sc.GIVEN_D, body)
        sc.write(self.root, sc.AGENT_D, sc.AGENT_TEXT + body)
        rep = self.run_selftest(sc.agent_manifest(self.root))
        self.assertTrue(rep["checks"]["public-answers"]["ok"], rep)
        body2 = self._body("task")
        sc.write(self.root, "bench/public/decoyset/tasks/t4.dfy", body2)
        sc.write(self.root, "bench/public/decoyset/answers/t4.dfy", "// answer\n" + body2)
        sc.write(self.root, sc.AGENT_D, sc.AGENT_TEXT + body2)
        rep = self.run_selftest(sc.agent_manifest(self.root))
        self.assertTrue(rep["checks"]["public-answers"]["ok"], rep)

    def test_shared_idioms_below_the_window_do_not_count(self):
        idiom = "forall i :: 0 <= i < |s| ==> s[i] >= 0\n"
        sc.write(self.root, "bench/public/decoyset/answers/t5.dfy", idiom * 3)
        sc.write(self.root, sc.AGENT_D, sc.AGENT_TEXT + "// " + idiom)
        rep = self.run_selftest(sc.agent_manifest(self.root))
        self.assertTrue(rep["checks"]["public-answers"]["ok"], rep)


class ReturnPath(Base):
    def setUp(self):
        super().setUp()
        self.m = sandbox.validate(sc.agent_manifest(self.root), self.root)
        self.staged = {e.dst: sandbox.read_source(self.root, e) for e in self.m.files}

    def parse(self, tb):
        return sandbox.parse_return(tb.stream(), self.m, self.staged)

    def test_a_returned_file_becomes_a_patch_under_its_course_path(self):
        new = sc.AGENT_TEXT.replace("{ }", "{ assert n + 0 == n; }")
        res = self.parse(sc.TarBuilder().dir(".").dir("./dafny").file(f"./{sc.AGENT_D}", new))
        self.assertEqual(list(res.returned), [sc.AGENT_D])
        self.assertIn(f"--- a/{sc.AGENT_D}", res.diff)
        self.assertIn("+lemma Decoy(n: nat) ensures n + 0 == n { assert n + 0 == n; }", res.diff)
        repo = sc.tmpdir("dvl0-sandbox-apply-")
        self.addCleanup(sc.cleanup, repo)
        sc.write(repo, sc.AGENT_D, sc.AGENT_TEXT)
        (repo / "p.diff").write_text(res.diff)
        subprocess.run(sc.GIT + ["init", "-q", str(repo)], check=True)
        p = subprocess.run(sc.GIT + ["-C", str(repo), "apply", "--check", "p.diff"],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_unchanged_and_deleted(self):
        res = self.parse(sc.TarBuilder().file(sc.AGENT_D, sc.AGENT_TEXT))
        self.assertEqual((res.unchanged, res.returned, res.deleted), ([sc.AGENT_D], {}, []))
        res = self.parse(sc.TarBuilder().dir("."))
        self.assertEqual(res.deleted, [sc.AGENT_D])
        self.assertIn("deleted file mode", res.diff)

    def test_everything_else_is_rejected_with_its_size_and_hash_only(self):
        tb = (sc.TarBuilder().file("notes.txt", "a new file\n")
              .special("link.dfy", tarfile.SYMTYPE, "/etc/hostname")
              .special("hard.dfy", tarfile.LNKTYPE, sc.AGENT_D)
              .special("pipe", tarfile.FIFOTYPE)
              .special("dev", tarfile.CHRTYPE)
              .file("../outside.txt", "x\n")
              .file("/abs.txt", "x\n")
              .file(sc.GIVEN_D, "changed given\n"))
        res = self.parse(tb)
        why = {r["name"]: r["why"] for r in res.rejected}
        self.assertIn("not a return path", why["notes.txt"])
        self.assertIn("symlink", why["link.dfy"])
        self.assertIn("hard link", why["hard.dfy"])
        self.assertIn("FIFO", why["pipe"])
        self.assertIn("device", why["dev"])
        self.assertIn("leaves /work", why["../outside.txt"])
        self.assertIn("leaves /work", why["/abs.txt"])
        self.assertIn("changed read-only input", why[sc.GIVEN_D])
        notes = next(r for r in res.rejected if r["name"] == "notes.txt")
        self.assertEqual((notes["size"], notes["sha256"]), (11, sc.sha("a new file\n")))
        self.assertEqual(res.returned, {})

    def test_size_cap_utf8_repeats_and_unchanged_read_only_inputs(self):
        big = "x" * (sandbox.RETURN_CAP_BYTES + 1)
        res = self.parse(sc.TarBuilder().file(sc.AGENT_D, big))
        self.assertIn("size cap", res.rejected[0]["why"])
        self.assertEqual(res.deleted, [])
        res = self.parse(sc.TarBuilder().file(sc.AGENT_D, b"\xff\xfe bad"))
        self.assertIn("UTF-8", res.rejected[0]["why"])
        res = self.parse(sc.TarBuilder().file(sc.AGENT_D, "a\n").file(sc.AGENT_D, "b\n"))
        self.assertIn("repeated member", res.rejected[0]["why"])
        res = self.parse(sc.TarBuilder().file(sc.AGENT_D, sc.AGENT_TEXT)
                         .file(sc.GIVEN_D, self.staged[sc.GIVEN_D]))
        self.assertEqual(res.rejected, [])

    def test_a_broken_stream_fails(self):
        import io
        with self.assertRaises(sandbox.SandboxError):
            sandbox.parse_return(io.BytesIO(b"not a tar stream at all" * 40), self.m, self.staged)

    def test_the_input_stream_holds_the_editable_files_only(self):
        run = sandbox.materialize(self.m, self.root, base=self.runs)
        self.addCleanup(sandbox.remove_run, run)
        import io
        with tarfile.open(fileobj=io.BytesIO(sandbox.input_stream(self.m, run))) as tf:
            names = [(t.name, t.isreg(), t.uid, t.mode) for t in tf]
        self.assertEqual(names, [(sc.AGENT_D, True, 1000, 0o644)])


class SecretScan(unittest.TestCase):
    def test_credential_formats_are_found_by_id_never_by_content(self):
        tok = "sk-ant-" + "oat01-" + "A" * 40
        samples = {
            "anthropic-token": f"log line {tok} end".encode(),
            "oauth-json-key": ('{"' + "accessToken" + '": "' + "B" * 30 + '"}').encode(),
            "bearer-header": ("Authorization: Bearer " + "C" * 40).encode(),
            "private-key": ("-----BEGIN " + "RSA PRIVATE KEY-----").encode(),
        }
        for want, data in samples.items():
            hits = sandbox.secret_scan(data)
            self.assertIn(want, [h[0] for h in hits], want)
        self.assertEqual(sandbox.secret_scan(b"a plain returned file\nlemma X() {}\n"), [])
        exact = "placeholder-" + "D" * 12
        self.assertEqual(sandbox.secret_scan(f"x {exact} y".encode(), exact=[exact])[0][0], "exact-token")
        rec = sandbox.withheld_record("t.txt", samples["anthropic-token"],
                                      sandbox.secret_scan(samples["anthropic-token"]))
        self.assertNotIn(tok, json.dumps(rec))


class Records(Base):
    def test_records_hold_the_manifest_hash_and_the_report(self):
        m = sandbox.validate(sc.agent_manifest(self.root), self.root)
        run = sandbox.materialize(m, self.root, base=self.runs)
        self.addCleanup(sandbox.remove_run, run)
        rep = sandbox.selftest(m, run, self.root)
        mj, sj = sandbox.write_records(self.runs / "rec", m, rep)
        doc = json.loads(mj.read_text())
        self.assertEqual(doc["sha256"], m.sha256())
        contract = next(f for f in doc["manifest"]["file"] if f["role"] == "contract")
        self.assertIsNone(contract["text"])
        self.assertEqual(json.loads(sj.read_text())["ok"], True)


class AccessDiagnosis(unittest.TestCase):
    """The read-only access check against fake docker, id and getent (§5.1)."""

    def setUp(self):
        self.bin = sc.tmpdir("dvl0-sandbox-bin-")
        self.addCleanup(sc.cleanup, self.bin)
        sc.fake_bin(self.bin, "docker", 'echo "permission denied while trying to connect to the '
                                        'docker API at unix:///var/run/docker.sock" >&2\nexit 1\n')
        sc.fake_bin(self.bin, "id", 'case "$1" in -un) echo learner ;; -nG) echo learner adm ;; esac\n')

    def check(self, getent_line):
        sc.fake_bin(self.bin, "getent", f'echo "{getent_line}"\n' if getent_line else "exit 2\n")
        return sc.run_mk(["--check-access"], path_first=self.bin)

    def test_not_listed_names_the_host_action_and_never_escalates(self):
        p = self.check("docker:x:983:")
        self.assertEqual(p.returncode, 3)
        self.assertIn("host action (H1) is not done", p.stderr)
        self.assertIn("sudo usermod -aG docker learner", p.stderr)
        self.assertIn("never escalates", p.stderr)

    def test_listed_but_stale_login(self):
        p = self.check("docker:x:983:learner")
        self.assertEqual(p.returncode, 3)
        self.assertIn("log in again", p.stderr)

    def test_no_group(self):
        p = self.check("")
        self.assertEqual(p.returncode, 3)
        self.assertIn("no docker group", p.stderr)

    def test_ci_environment_refuses_before_running_docker(self):
        marker = self.bin / "ran"
        sc.fake_bin(self.bin, "docker", f"touch {marker}\nexit 0\n")
        p = sc.run_mk(["--check-access"], path_first=self.bin, env_extra={"DVL_NO_DOCKER": "1"})
        self.assertEqual(p.returncode, 3)
        self.assertIn("DVL_NO_DOCKER=1", p.stderr)
        self.assertFalse(marker.exists())

    def test_a_working_daemon_is_reported(self):
        sc.fake_bin(self.bin, "docker", "echo 29.1.3\n")
        p = sc.run_mk(["--check-access"], path_first=self.bin)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("server 29.1.3", p.stdout)


class Cli(Base):
    def setUp(self):
        super().setUp()
        self.bin = sc.tmpdir("dvl0-sandbox-bin-")
        self.xdg = sc.tmpdir("dvl0-sandbox-xdg-")
        self.addCleanup(sc.cleanup, self.bin, self.xdg)

    def mk(self, args, **kw):
        kw.setdefault("runtime", self.xdg)
        return sc.run_mk(args, **kw)

    def test_dry_run_prints_the_golden_argv_and_runs_nothing(self):
        marker = self.bin / "ran"
        sc.fake_bin(self.bin, "docker", f"touch {marker}\nexit 0\n")
        man = sc.write_manifest(self.runs, sc.agent_manifest(self.root))
        p = self.mk(["--dry-run", str(man), "--root", str(self.root)], path_first=self.bin)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertFalse(marker.exists())
        lines = [x.strip() for x in p.stdout.splitlines() if x.startswith("  docker ")]
        golden = (GOLDEN / "dry_run_agent.txt").read_text().splitlines()
        self.assertEqual(lines, golden)
        run = next(x for x in lines if x.startswith("docker run "))
        # Route C (DELTAS Δ504): the sandbox's one network is the run's --internal one
        for flag in ("--cap-drop ALL", "--read-only", "--network dvl-int-q98-run1",
                     "--user 1000:1000", "--security-opt no-new-privileges",
                     "--memory 15.5g --memory-swap 15.5g", "--init",
                     "destination=/run/dvl/relays.json,readonly"):
            self.assertIn(flag, run)
        for never in ("--privileged", "docker.sock", "--network host", "--pid host", "--device",
                      "--gpus", "--cap-add", str(self.root), ".sock"):
            self.assertNotIn(never, run)
        nets = [x for x in lines if x.startswith("docker network create ")]
        self.assertEqual(len(nets), 2)
        self.assertIn("--internal --opt com.docker.network.bridge.inhibit_ipv4=true", nets[0])
        gate = next(x for x in lines if x.startswith("docker create --name dvl-gate-q98-run1 "))
        for flag in ("--cap-drop ALL", "--read-only", "--user 1000:1000", "--network dvl-up-q98-run1",
                     "--security-opt no-new-privileges", "--memory 128m --memory-swap 128m",
                     "/opt/dvl/bin/entry gate"):
            self.assertIn(flag, gate)
        self.assertLess(lines.index(gate), lines.index(run))
        self.assertEqual(list(Path(self.xdg).glob("dvl-runs/*")), [])    # the run dir is gone

    def test_dry_run_of_a_verify_manifest(self):
        man = sc.write_manifest(self.runs, sc.verify_manifest(self.root))
        p = self.mk(["--dry-run", str(man), "--root", str(self.root)])
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        lines = [x.strip() for x in p.stdout.splitlines() if x.startswith("  docker ")]
        self.assertEqual(lines, (GOLDEN / "dry_run_verify.txt").read_text().splitlines())

    def test_dry_run_refuses_an_unlocked_image_after_showing_the_run(self):
        bare = sc.make_root(git=True, lock=False)
        self.addCleanup(sc.cleanup, bare)
        man = sc.write_manifest(self.runs, sc.agent_manifest(bare))
        p = self.mk(["--dry-run", str(man), "--root", str(bare)])
        self.assertEqual(p.returncode, 3)
        self.assertIn("docker run", p.stdout)
        self.assertIn("not in sandbox/images.lock", p.stderr)

    def test_a_refused_manifest_exits_3(self):
        m = sc.agent_manifest(self.root)
        m["file"].append(sc.entry(self.root, "docs/Q98_Sandbox.md", "given"))
        man = sc.write_manifest(self.runs, m)
        p = self.mk(["--dry-run", str(man), "--root", str(self.root)])
        self.assertEqual(p.returncode, 3)
        self.assertIn("refused source class (chapters)", p.stderr)

    def test_selftest_only_prints_json_and_exits_1_on_failure(self):
        man = sc.write_manifest(self.runs, sc.agent_manifest(self.root))
        p = self.mk(["--selftest-only", str(man), "--root", str(self.root),
                     "--records", str(self.runs / "rec")])
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(json.loads(p.stdout)["ok"])
        self.assertTrue((self.runs / "rec" / "manifest.json").is_file())
        sc.write(self.root, sc.AGENT_D, sc.AGENT_TEXT + "// DVLCANARY-planted01\n")
        man = sc.write_manifest(self.runs, sc.agent_manifest(self.root), name="m2.json")
        p = self.mk(["--selftest-only", str(man), "--root", str(self.root)])
        self.assertEqual(p.returncode, 1)
        self.assertFalse(json.loads(p.stdout)["checks"]["canaries"]["ok"])

    def test_materialize_and_release(self):
        man = sc.write_manifest(self.runs, sc.verify_manifest(self.root))
        p = self.mk(["--materialize", str(man), "--root", str(self.root)])
        self.assertEqual(p.returncode, 0, p.stderr)
        run = Path(p.stdout.strip())
        self.assertEqual(run.parent, Path(self.xdg) / "dvl-runs")
        self.assertTrue((run / "in" / sc.AGENT_D).is_file())
        p = self.mk(["--release", str(run)])
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertFalse(run.exists())
        p = self.mk(["--release", str(self.root)])
        self.assertEqual(p.returncode, 3)

    def test_a_live_run_refuses_root_and_an_image_not_in_the_lock(self):
        man = sc.write_manifest(self.runs, sc.agent_manifest(self.root))
        p = self.mk([str(man), "--root", str(self.root)])
        self.assertEqual(p.returncode, 3)
        self.assertIn("--root serves the tests", p.stderr)
        # this checkout: a valid verify manifest whose image is not in
        # sandbox/images.lock is refused before any container starts
        marker = self.bin / "ran"
        sc.fake_bin(self.bin, "docker", f"touch {marker}\necho 29.1.3\n")
        agent = "dafny/Q/Q04_ProofCraft/agent/Q04_AgentRetriever.dfy"
        live = sc.verify_manifest(sc.ROOT, module="Q04",
                                  file=[sc.entry(sc.ROOT, agent, "editable"),
                                        sc.entry(sc.ROOT, "dafny/given/Q/QG_L1_BigNat.dfy", "given")])
        p = self.mk([str(sc.write_manifest(self.runs, live, name="live.json"))], path_first=self.bin)
        self.assertEqual(p.returncode, 3, p.stderr)
        self.assertIn("not in sandbox/images.lock", p.stderr)
        self.assertFalse(marker.exists())

    def test_author_forms_gate_themselves(self):
        plain = sc.make_root(git=False)
        self.addCleanup(sc.cleanup, plain)
        man = sc.write_manifest(self.runs, sc.agent_manifest(plain))
        p = self.mk(["--author", "--selftest-only", str(man), "--root", str(plain)],
                    env_extra={"GIT_CEILING_DIRECTORIES": str(plain.parent)})
        self.assertEqual(p.returncode, 3)
        self.assertIn("author-only", p.stderr)
        p = self.mk(["--author", "--attest", "bench/local/q/card01/tasks/task.dfy", "--root", str(plain)],
                    env_extra={"GIT_CEILING_DIRECTORIES": str(plain.parent)})
        self.assertEqual(p.returncode, 3)
        self.assertIn("author-only", p.stderr)
        p = self.mk(["--attest", "x"])
        self.assertEqual(p.returncode, 2)


class Attest(unittest.TestCase):
    """--author --attest in a linked worktree (the three-condition test holds)."""

    def setUp(self):
        self.repo = sc.make_root(git=True)
        self.wt = sc.tmpdir("dvl0-sandbox-wt-")
        self.addCleanup(sc.cleanup, self.repo, self.wt)
        os.rmdir(self.wt)
        subprocess.run(sc.GIT + ["-C", str(self.repo), "worktree", "add", "-q", "-b", "authoring",
                                 str(self.wt)], check=True)
        sc.write(self.wt, "tests/instructor/leak_patterns/Q98.txt", "# decoy pattern\nDecoyAnswerName\n")
        sc.write(self.wt, "Solutions/dafny/Q/Q98_Sandbox/std/Q98_Sandbox.dfy",
                 "// decoy exercise\nlemma Twin(x: nat) ensures x * 1 == x { calc { x * 1; == x; } }\n")

    def test_a_clean_card_is_attested_and_a_matching_one_is_not(self):
        card = "bench/local/q/card01/tasks/task.dfy"
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        p = subprocess.run([sys.executable, "-B", str(sc.MKSANDBOX), "--author", "--attest", card,
                            "--root", str(self.wt)], capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn(sc.sha((self.wt / card).read_bytes()), (self.wt / "sandbox/attested.toml").read_text())
        sc.write(self.wt, "bench/local/q/card02/tasks/task.dfy", "uses DecoyAnswerName here\n")
        ok, msg = sandbox.attest(self.wt, "bench/local/q/card02/tasks/task.dfy")
        self.assertFalse(ok)
        self.assertIn("leak pattern", msg)
        sc.write(self.wt, "bench/local/q/card03/tasks/task.dfy",
                 "lemma Twin(x: nat) ensures x * 1 == x { calc { x * 1; == x; } }\n")
        ok, msg = sandbox.attest(self.wt, "bench/local/q/card03/tasks/task.dfy")
        self.assertFalse(ok)
        self.assertIn("answer lines", msg)


class AttestRecalibrated(unittest.TestCase):
    """The recalibrated author scan (DV5d): text a learner-visible course file
    shows never counts, and a hit is a whole span of a twin's answer lines (at
    least SPAN_TOKENS tokens), so a card that copies definitions is attested
    and a planted answer line is still caught. Decoy texts only."""

    DEFS = ("function Weight(s: seq<nat>): nat\n  decreases |s|\n"
            "{\n  if |s| == 0 then 0 else s[0] + 7 * Weight(s[1..])\n}\n")
    ANSWER = "  DecoyStep(s[1..], t[1..], 7 * Weight(s[1..]));\n"

    def setUp(self):
        self.repo = sc.make_root(git=True)
        self.wt = sc.tmpdir("dvl0-sandbox-wt-")
        self.addCleanup(sc.cleanup, self.repo, self.wt)
        os.rmdir(self.wt)
        subprocess.run(sc.GIT + ["-C", str(self.repo), "worktree", "add", "-q", "-b", "authoring",
                                 str(self.wt)], check=True)
        # the given layer shows the definition; the learner file imports it and
        # holds a hole where the twin holds the answer line and a copy of the
        # definition (the shape every Lab 2 card met in the first scan)
        sc.write(self.wt, "dafny/given/Q/QG_L98_Decoy.dfy", "module QG_L98_Decoy {\n" + self.DEFS + "}\n")
        sc.write(self.wt, "dafny/Q/Q98_Sandbox/std/Q98_Sandbox.dfy",
                 "import opened QG_L98_Decoy\nlemma DecoyLemma(s: seq<nat>, t: seq<nat>)\n{\n}\n")
        sc.write(self.wt, "Solutions/dafny/Q/Q98_Sandbox/std/Q98_Sandbox.dfy",
                 self.DEFS + "lemma DecoyLemma(s: seq<nat>, t: seq<nat>)\n{\n" + self.ANSWER + "}\n")

    def card(self, rel, body):
        sc.write(self.wt, rel, "// a decoy lab card\n" + self.DEFS + body)
        return rel

    def test_a_card_that_copies_definitions_is_attested(self):
        rel = self.card("bench/local/q/lab9/c01/tasks/c01.dfy",
                        "method Decoy(s: seq<nat>) returns (r: nat)\n{\n  r := Weight(s);\n}\n")
        # the first scan's unit (a single 7-token shingle of the twin's
        # non-learner lines) meets the copied definition
        twin = (self.wt / "Solutions/dafny/Q/Q98_Sandbox/std/Q98_Sandbox.dfy").read_text()
        self.assertTrue(sandbox._shingles(self.DEFS, "x.dfy") & sandbox._shingles(twin, "x.dfy"))
        ok, msg = sandbox.attest(self.wt, rel)
        self.assertTrue(ok, msg)
        self.assertIn(sc.sha((self.wt / rel).read_bytes()), (self.wt / "sandbox/attested.toml").read_text())

    def test_a_planted_answer_line_is_still_caught(self):
        rel = self.card("bench/local/q/lab9/c02/tasks/c02.dfy",
                        "lemma Other(s: seq<nat>, t: seq<nat>)\n{\n" + self.ANSWER.replace("  ", "    ")
                        + "}\n")
        ok, msg = sandbox.attest(self.wt, rel)
        self.assertFalse(ok)
        self.assertIn("span(s) of a reference twin's answer lines", msg)
        self.assertIn("Solutions/dafny/Q/Q98_Sandbox/std/Q98_Sandbox.dfy", msg)
        self.assertNotIn(sc.sha((self.wt / rel).read_bytes()), sandbox.read_attested(self.wt))

    def test_a_shared_fragment_is_no_hit(self):
        rel = self.card("bench/local/q/lab9/c03/tasks/c03.dfy",
                        "method Pair(s: seq<nat>, t: seq<nat>)\n{\n  Other(s[1..], t[1..]);\n}\n")
        ok, msg = sandbox.attest(self.wt, rel)
        self.assertTrue(ok, msg)

    def test_a_lab_reference_is_a_twin_too(self):
        sc.write(self.wt, "bench/local/q/lab9/c04/tasks/c04.dfy", "lemma C04(n: nat)\n{\n}\n")
        sc.write(self.wt, "Solutions/bench/local/q/lab9/c04/c04.dfy",
                 "lemma C04(n: nat)\n{\n  assert n * 3 + 1 > n * 2 by { DecoyArith(n, 3, 2); }\n}\n")
        rel = self.card("bench/local/q/lab9/c05/tasks/c05.dfy",
                        "lemma C05(n: nat)\n{\n  assert n * 3 + 1 > n * 2 by { DecoyArith(n, 3, 2); }\n}\n")
        ok, msg = sandbox.attest(self.wt, rel)
        self.assertFalse(ok)
        self.assertIn("Solutions/bench/local/q/lab9/c04/c04.dfy", msg)

    def test_attest_data_records_a_sealed_card(self):
        data = b"// a decoy sealed crate file\nfn main() {}\n"
        rel = "bench/local/q/crate9/x01/tasks/src/lib.rs"
        ok, msg = sandbox.attest_data(self.wt, rel, data, source="sealed: decoy archive")
        self.assertTrue(ok, msg)
        att = sandbox.read_attested(self.wt)
        self.assertEqual(att[sc.sha(data)], rel)
        self.assertIn('source = "sealed: decoy archive"', (self.wt / "sandbox/attested.toml").read_text())
        ok, msg = sandbox.attest_data(self.wt, rel, data)
        self.assertTrue(ok)
        self.assertIn("already attested", msg)
        ok, msg = sandbox.attest_data(self.wt, "tasks/elsewhere.rs", data)
        self.assertFalse(ok)
        text = (self.wt / "sandbox/attested.toml").read_text()
        self.assertIn(f'scan = "{sandbox.SCAN_RULE}"', text)     # the rule it passed
        self.assertIn('pools = "2 files, sha256 ', text)          # the decoy set's task and answer


class AttestGenericAndRenamed(unittest.TestCase):
    """The DV5e recalibration (the user's decision D25): generic structure (the
    definitions a card gives, language structure, shapes common to the public pools)
    does not count, while a copied answer run still does, renamed or not. Decoy texts
    only: the decoy twin's answer region stands for a reference solution."""

    DEFS = ("function Weight(s: seq<nat>): nat\n  decreases |s|\n"
            "{\n  if |s| == 0 then 0 else s[0] + 7 * Weight(s[1..])\n}\n")
    SIG = "method DecoyScan(s: seq<nat>) returns (r: nat)\n  ensures r == Weight(s)\n"
    HELPER = "lemma DecoyHelper(s: seq<nat>, t: seq<nat>, k: nat)\n"
    # a shape no reference twin holds (checked with ScanIndex.hits over this file)
    LOOP = ("  r := 0;\n  var i := 0;\n  while i != |s|\n    invariant i <= |s|\n"
            "    invariant DecoyInv(s, i, r)\n    decreases |s| - i\n")
    BODY = ["    i := i + 1;\n", "    r := 7 * r + s[i - 1] % 5;\n", "    DecoyFold(s, i, r);\n"]

    def setUp(self):
        self.repo = sc.make_root(git=True)
        self.wt = sc.tmpdir("dvl0-sandbox-wt-")
        self.addCleanup(sc.cleanup, self.repo, self.wt)
        os.rmdir(self.wt)
        subprocess.run(sc.GIT + ["-C", str(self.repo), "worktree", "add", "-q", "-b", "authoring",
                                 str(self.wt)], check=True)
        sc.write(self.wt, "dafny/given/Q/QG_L98_Decoy.dfy", "module QG_L98_Decoy {\n" + self.DEFS + "}\n")
        # the learner file: the signatures and empty bodies; the twin: the answer region
        sc.write(self.wt, "dafny/Q/Q98_Sandbox/std/Q98_Sandbox.dfy",
                 "import opened QG_L98_Decoy\n" + self.SIG + "{\n}\n")
        sc.write(self.wt, "Solutions/dafny/Q/Q98_Sandbox/std/Q98_Sandbox.dfy",
                 self.DEFS + self.HELPER + "{\n}\n" + self.SIG + "{\n" + self.LOOP + "  {\n"
                 + "".join(self.BODY) + "  }\n}\n")

    def card(self, name, body, defs=True):
        rel = f"bench/local/q/lab9/{name}/tasks/{name}.dfy"
        sc.write(self.wt, rel, "// a decoy lab card\n" + (self.DEFS if defs else "") + body)
        return rel

    def attest(self, rel):
        return sandbox.attest(self.wt, rel)

    @staticmethod
    def rename(text):
        for a, b in (("DecoyFold", "CardStep"), ("acc", "acc0"), ("r", "acc"), ("s", "q"),
                     ("i", "j")):
            text = re.sub(rf"\b{a}\b", b, text)
        return text

    def kinds(self, rel):
        idx = sandbox.scan_index(self.wt)
        return sorted(k for _, k in idx.hits((self.wt / rel).read_text(), rel))

    def test_a_card_that_copies_its_given_definitions_passes(self):
        ok, msg = self.attest(self.card("g01", "method G01(q: seq<nat>) returns (m: nat)\n{\n"
                                        "  m := Weight(q);\n}\n"))
        self.assertTrue(ok, msg)
        # renamed too: the given layer shows the definition's shape
        renamed = self.DEFS.replace("Weight", "Mass").replace("(s", "(q").replace("|s|", "|q|") \
            .replace("s[", "q[")
        ok, msg = self.attest(self.card("g02", renamed + "method G02() {}\n", defs=False))
        self.assertTrue(ok, msg)

    def test_a_copied_answer_run_of_the_reference_is_caught(self):
        rel = self.card("g03", self.SIG + "{\n" + self.LOOP + "  {\n" + "".join(self.BODY)
                        + "  }\n}\n")
        ok, msg = self.attest(rel)
        self.assertFalse(ok)
        self.assertIn("span(s) of a reference twin's answer lines", msg)
        self.assertIn("Solutions/dafny/Q/Q98_Sandbox/std/Q98_Sandbox.dfy", msg)
        self.assertIn("whole", self.kinds(rel))
        self.assertNotIn(sc.sha((self.wt / rel).read_bytes()), sandbox.read_attested(self.wt))

    def test_a_short_answer_line_is_caught_inside_a_longer_copied_run(self):
        short = self.BODY[0]
        self.assertLess(len(sandbox.tokens(short, "x.dfy")), sandbox.SPAN_TOKENS)
        ok, msg = self.attest(self.card("g04", "method G04(i: nat)\n{\n  var i := i;\n" + short + "}\n"))
        self.assertTrue(ok, msg)            # alone: the known limit
        rel = self.card("g05", "method G05(s: seq<nat>, i: nat) returns (r: nat)\n{\n"
                        + "".join(self.BODY) + "}\n")
        ok, msg = self.attest(rel)
        self.assertFalse(ok)
        self.assertIn("span(s) of a reference twin's answer lines", msg)

    def test_a_renamed_copy_is_caught(self):
        run = self.rename(self.LOOP + "  {\n" + "".join(self.BODY) + "  }\n")
        self.assertNotIn("DecoyFold", run)
        rel = self.card("g06", "method G06(q: seq<nat>) returns (acc: nat)\n{\n" + run + "}\n")
        # the DV5d unit (every exact shingle of a span) does not see it
        have = sandbox._shingles((self.wt / rel).read_text(), rel)
        self.assertFalse(any(sh <= have for _, sh in sandbox.answer_spans(self.wt)))
        ok, msg = self.attest(rel)
        self.assertFalse(ok)
        self.assertIn("renamed", msg)
        self.assertEqual(set(self.kinds(rel)), {"renamed"})

    def test_language_structure_does_not_count_when_renamed(self):
        # the twin's helper is a declaration header only: its shape is structure
        ok, msg = self.attest(self.card("g07", "lemma CardHelper(a: seq<nat>, b: seq<nat>, n: nat)\n{\n}\n"))
        self.assertTrue(ok, msg)
        # an exact copy of the twin's own header still counts
        ok, msg = self.attest(self.card("g08", self.HELPER + "{\n}\n"))
        self.assertFalse(ok)
        self.assertIn("1 whole", msg)

    def test_shapes_common_to_the_public_pools_do_not_count(self):
        def shape(text, names):
            for a, b in zip(("DecoyInv", "s", "i", "r"), names):
                text = re.sub(rf"\b{a}\b", b, text)
            return text
        body = "method G09(q: seq<nat>) returns (m: nat)\n{\n" + \
            shape(self.LOOP, ("Inv9", "q", "k", "m")) + "  {\n    k := k + 1;\n  }\n}\n"
        rel = self.card("g09", body)
        ok, msg = self.attest(rel)
        self.assertFalse(ok)                # no pool shows the shape: a renamed hit
        self.assertIn("renamed", msg)
        pool = "method P(a: seq<int>) returns (t: int)\n{\n" + \
            shape(self.LOOP, ("PInv", "a", "j", "t")) + "  {\n    j := j + 1;\n  }\n}\n"
        sc.write(self.wt, "bench/public/decoyset/tasks/p1.dfy", pool)
        ok, msg = self.attest(rel)
        self.assertFalse(ok, "one public file is not common")
        sc.write(self.wt, "bench/public/decoyset/answers/p2.dfy", pool.replace("P(", "Q("))
        ok, msg = self.attest(rel)
        self.assertTrue(ok, msg)

    def test_an_exact_copy_of_a_pool_common_shape_still_counts(self):
        """DV5e review: pool-common shapes are set aside for the renamed test only; a
        card that holds a twin's span word for word is refused even when its shape is
        common to the public pools (fail-closed; ScanIndex's docstring)."""
        run = self.LOOP + "  {\n" + "".join(self.BODY) + "  }\n"
        pool = self.rename(run)
        sc.write(self.wt, "bench/public/decoyset/tasks/p1.dfy",
                 "method P(q: seq<nat>) returns (acc: nat)\n{\n" + pool + "}\n")
        sc.write(self.wt, "bench/public/decoyset/answers/p2.dfy",
                 "method Q(q: seq<nat>) returns (acc: nat)\n{\n" + pool + "}\n")
        ok, msg = self.attest(self.card("g12", "method G12(q: seq<nat>) returns (acc: nat)\n{\n"
                                        + pool + "}\n"))
        self.assertTrue(ok, msg)            # the renamed copy: a pool-common shape
        rel = self.card("g13", "method G13(s: seq<nat>) returns (r: nat)\n{\n" + run + "}\n")
        ok, msg = self.attest(rel)
        self.assertFalse(ok)                # the exact copy: still a copied answer run
        self.assertIn("whole", self.kinds(rel))

    def test_an_entry_of_an_earlier_rule_is_rescanned(self):
        clean = self.card("g10", "method G10() {}\n")
        dirty = self.card("g11", self.SIG + "{\n" + self.LOOP + "}\n")
        att = self.wt / "sandbox/attested.toml"
        old = "".join(f'\n[[card]]\npath = "{r}"\nsha256 = "{sc.sha((self.wt / r).read_bytes())}"\n'
                      f'attested = "2026-10-12"\nsource = "earlier"\n' for r in (clean, dirty))
        att.write_text("schema = 1\n" + old)
        ok, msg = self.attest(clean)
        self.assertTrue(ok, msg)
        self.assertIn("re-attested", msg)
        ok, msg = self.attest(dirty)
        self.assertFalse(ok)
        self.assertIn("withdrawn", msg)
        text = att.read_text()
        self.assertEqual(text.count("[[card]]"), 1)
        entry = tomllib.loads(text)["card"][0]
        self.assertEqual((entry["path"], entry["scan"], entry["source"]),
                         (clean, sandbox.SCAN_RULE, "earlier"))
        ok, msg = self.attest(clean)
        self.assertIn("already attested", msg)



class AttestSealedReferences(unittest.TestCase):
    """The user's decision D31: at attestation the scan also reads Lab 2's sealed reference
    specifications (the truth archive a local stratum's lab names) and Lab 3's reference
    deliveries (beside a sealed stratum) as twins, in memory only. Decoy texts in throwaway
    roots; the fake age decodes a base64 'archive', so no plaintext sits on disk, and each
    sealed decoy carries a canary word that must never reach a message, a repr or a file."""

    CANARY2 = "Zq98CanaryWord"          # inside the sealed Lab 2 decoy reference only
    CANARY3 = "zq97_canary_fact"        # inside the Lab 3 decoy reference delivery only
    FORM2 = ("// a decoy Lab 2 card\nmethod DecoyPick(s: seq<nat>, k: nat) returns (r: nat)\n"
             "{\n  r := s[k % 3] + k;\n}\n")
    SPEC2 = ("  requires |s| >= 3 && k < 40\n"
             f"  ensures r == s[k % 3] + k && {CANARY2}(r, k) && r >= k\n")
    STUB3 = ("use vstd::prelude::*;\nverus! {\npub fn decoy_sum(a: u64, b: u64) -> (r: u64)\n"
             "    requires a < 100, b < 100,\n    ensures r == a + b,\n{\n"
             "    // HOLE\n}\n}\n")
    BODY3 = ("    let t = a + b;\n    proof { " + CANARY3 + "(a as int, b as int, t as int); }\n"
             "    assert(t == a + b && t < 200);\n    t\n")

    def setUp(self):
        self.repo = sc.make_root(git=True)
        self.wt = sc.tmpdir("dvl0-sandbox-wt-")
        self.aux = sc.tmpdir("dvl0-sandbox-aux-")
        self.addCleanup(sc.cleanup, self.repo, self.wt, self.aux)
        os.rmdir(self.wt)
        subprocess.run(sc.GIT + ["-C", str(self.repo), "worktree", "add", "-q", "-b", "authoring",
                                 str(self.wt)], check=True)
        fake = self.aux / "fake-age"
        fake.write_text(f"#!{sys.executable}\nimport base64, sys\nsys.stdout.buffer.write("
                        "base64.b64decode(open(sys.argv[-1], 'rb').read()))\n")
        fake.chmod(0o755)
        self.key = self.aux / "key.txt"
        self.key.write_text("AGE-SECRET-KEY-DECOY\n")
        refs = self.aux / "refs"
        sc.write(refs, "x01/src/lib.rs", self.STUB3.replace("    // HOLE\n", self.BODY3))
        for name, val in (("AGE", str(fake)), ("SEALED_REFERENCE_DIRS",
                                                 {"bench/local/q/crate8": str(refs)})):
            self.addCleanup(setattr, sandbox, name, getattr(sandbox, name))
            setattr(sandbox, name, val)
        self.addCleanup(sandbox._SCAN_INDEX.clear)
        sandbox._SCAN_INDEX.clear()
        self.card2 = "bench/local/q/lab8/c01/tasks/c01.dfy"
        sc.write(self.wt, self.card2, self.FORM2)
        sc.write(self.wt, "bench/local/q/lab8/STRATUM.toml", 'schema = 1\nlab = "Q98"\n')
        program = self.FORM2.replace(") returns (r: nat)\n", ") returns (r: nat)\n" + self.SPEC2)
        reference = (f'id = "c01"\nlang = "dafny"\ntask_form = "{self.card2}"\n'
                     'requires = ["|s| >= 3 && k < 40"]\n'
                     f'ensures = ["r == s[k % 3] + k && {self.CANARY2}(r, k) && r >= k"]\n')
        lab2 = {"tasks/c01/c01.dfy": program.encode(), "tasks/c01/reference.toml": reference.encode()}
        arc2, man2 = self.seal("Hidden/labs/Q98/verdicts.tar.age", "Q98", lab2, prefixed=True)
        self.crate = "bench/local/q/crate8/x01/tasks/src/lib.rs"
        arc3, man3 = self.seal("bench/local/q/crate8/tasks.tar.age", "Q97",
                               {"x01/tasks/src/lib.rs": self.STUB3.encode()}, prefixed=False)
        sc.write(self.wt, "bench/local/q/crate8/STRATUM.toml",
                 'schema = 1\nlab = "Q97"\nmodule = "Q97"\n'
                 'archive = "bench/local/q/crate8/tasks.tar.age"\n'
                 f'archive_sha256 = "{arc3}"\nrecipient = "age1decoyrecipient"\nfiles = 1\n'
                 f'manifest_sha256 = "{man3}"\n\n[[card]]\nid = "x01"\nlang = "verus"\n'
                 'kind = "possible"\n')
        sc.write(self.wt, "sandbox/truth.toml",
                 'schema = 1\n\n[[lab]]\nid = "Q98"\narchive = "Hidden/labs/Q98/verdicts.tar.age"\n'
                 f'recipient = "age1decoyrecipient"\nidentity = "{self.key}"\n'
                 f'age_sha256 = "{sc.sha(fake.read_bytes())}"\nsha256 = "{arc2}"\nfiles = 2\n'
                 f'manifest_sha256 = "{man2}"\n')

    def seal(self, rel, lab, files, *, prefixed):
        import base64
        import io
        name = (lambda k: f"labs/{lab}/{k}") if prefixed else (lambda k: k)
        man = "".join(f"{sc.sha(v)}  {name(k)}\n" for k, v in sorted(files.items())).encode()
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tf:
            for k, v in sorted({**files, "MANIFEST.sha256": man}.items()):
                ti = tarfile.TarInfo(f"labs/{lab}/{k}")
                ti.size = len(v)
                tf.addfile(ti, io.BytesIO(v))
        data = base64.b64encode(buf.getvalue())
        (self.wt / rel).parent.mkdir(parents=True, exist_ok=True)
        (self.wt / rel).write_bytes(data)
        return sc.sha(data), sc.sha(man)

    def invented(self, name, body, ext="dfy"):
        rel = f"bench/local/q/lab9/{name}/tasks/{name}.{ext}"
        sc.write(self.wt, rel, "// an invented decoy card\n" + body)
        return rel

    def no_canary(self, *texts):
        for t in texts:
            self.assertNotIn(self.CANARY2, t)
            self.assertNotIn(self.CANARY3, t)

    def no_canary_on_disk(self):
        """No file holds the sealed decoy's canary, but the invented cards that plant it."""
        planted = self.wt / "bench/local/q/lab9"
        for top in (self.wt, self.repo, self.aux / "fake-age", self.key):
            for q in ([top] if top.is_file() else top.rglob("*")):
                if q.is_file() and not q.is_symlink() and planted not in q.parents:
                    self.assertNotIn(self.CANARY2.encode(), q.read_bytes(), str(q))

    def test_the_sealed_references_are_twins(self):
        twins, refs = sandbox.sealed_reference_twins(self.wt)
        self.assertEqual(sorted(t.label for t in twins),
                         ["sealed Q98 tasks/c01/c01.dfy", "sealed Q98 tasks/c01/reference.toml",
                          "sealed bench/local/q/crate8 reference x01/src/lib.rs"])
        self.assertRegex(refs, r"^3 twins, sha256 [0-9a-f]{16}$")
        idx = sandbox.scan_index(self.wt)
        self.no_canary(refs, repr(twins), repr(idx.spans), idx.refs)

    def test_the_lab3_references_from_their_sealed_archive(self):
        """DV6 fix round: a sealed stratum's refs_archive (refs/<card>/<path>) is read, with
        no directory of plaintext deliveries, and gives the same twins."""
        before = sandbox.sealed_reference_twins(self.wt)[1]
        body = self.STUB3.replace("    // HOLE\n", self.BODY3).encode()
        arc, man = self.seal("Hidden/labs/Q97/refs.tar.age", "Q97",
                             {"refs/x01/src/lib.rs": body}, prefixed=True)
        st = self.wt / "bench/local/q/crate8/STRATUM.toml"
        text = st.read_text()
        st.write_text(text.replace("\n\n[[card]]", f'\nrefs_archive = "Hidden/labs/Q97/refs.tar.age"\n'
                                   f'refs_sha256 = "{arc}"\nrefs_files = 1\n'
                                   f'refs_manifest_sha256 = "{man}"\n\n[[card]]', 1))
        setattr(sandbox, "SEALED_REFERENCE_DIRS", {})
        sandbox._SCAN_INDEX.clear()
        twins, refs = sandbox.sealed_reference_twins(self.wt)
        self.assertIn("sealed bench/local/q/crate8 reference x01/src/lib.rs",
                      [t.label for t in twins])
        self.assertEqual(refs, before)
        # a wrong pin refuses, naming the archive and never its text
        st.write_text(st.read_text().replace(f'refs_sha256 = "{arc}"', 'refs_sha256 = "0"'))
        with self.assertRaises(sandbox.SealedRefsError) as cm:
            sandbox.sealed_reference_twins(self.wt)
        self.assertIn("refs.tar.age", str(cm.exception))
        self.no_canary(str(cm.exception))
        # no refs archive and no directory: the stratum names no source
        st.write_text(text)
        with self.assertRaises(sandbox.SealedRefsError):
            sandbox.sealed_reference_twins(self.wt)

    def test_an_author_runs_self_test_reads_no_sealed_source(self):
        """DV6 review: the self-test's author scan (sealed=False) neither reads nor needs the
        sealed references; the attestation's (sealed=True) refuses when one is unreadable."""
        setattr(sandbox, "SEALED_REFERENCE_DIRS", {"bench/local/q/crate8": str(self.aux / "gone")})
        sandbox._SCAN_INDEX.clear()
        files = {"t.dfy": self.FORM2.encode()}
        self.assertEqual(sandbox.author_scan(self.wt, files, sealed=False), [])
        sandbox._SCAN_INDEX.clear()
        with self.assertRaises(sandbox.SealedRefsError):
            sandbox.author_scan(self.wt, files)
        import inspect
        self.assertIn("sealed=False", inspect.getsource(sandbox.selftest))

    def test_the_cards_themselves_are_attested_with_the_references_recorded(self):
        ok, msg = sandbox.attest(self.wt, self.card2)
        self.assertTrue(ok, msg)
        stub = self.STUB3.encode()
        ok, msg = sandbox.attest_data(self.wt, self.crate, stub, source="sealed: decoy")
        self.assertTrue(ok, msg)
        text = (self.wt / "sandbox/attested.toml").read_text()
        self.assertEqual(text.count('refs = "3 twins, sha256 '), 2)
        self.assertIn(f'scan = "{sandbox.SCAN_RULE}"', text)
        self.no_canary(text)
        self.no_canary_on_disk()

    def test_a_planted_lab2_reference_is_caught(self):
        rel = self.invented("p01", "method Other(s: seq<nat>, k: nat) returns (r: nat)\n"
                            + self.SPEC2 + "{\n  r := k;\n}\n")
        ok, msg = sandbox.attest(self.wt, rel)
        self.assertFalse(ok)
        self.assertIn("sealed Q98 tasks/c01/", msg)
        self.no_canary(msg)
        self.assertNotIn(sc.sha((self.wt / rel).read_bytes()), sandbox.read_attested(self.wt))
        self.no_canary_on_disk()

    def test_a_planted_lab3_reference_delivery_is_caught(self):
        rel = self.invented("p02", self.STUB3.replace("decoy_sum", "other_sum")
                            .replace("    // HOLE\n", self.BODY3), ext="rs")
        ok, msg = sandbox.attest(self.wt, rel)
        self.assertFalse(ok)
        self.assertIn("sealed bench/local/q/crate8 reference x01/src/lib.rs", msg)
        self.no_canary(msg)

    def test_a_sealed_reference_counts_even_when_the_pools_show_it(self):
        """Lab 2's public cards come from the installed upstream sets, which hold their
        statements: the pool rule does not set a sealed reference's exact copy aside."""
        for i in (1, 2):
            sc.write(self.wt, f"bench/public/decoyset/{'tasks' if i == 1 else 'answers'}/u{i}.dfy",
                     f"method Up{i}(s: seq<nat>, k: nat) returns (r: nat)\n" + self.SPEC2
                     + "{\n  r := s[k % 3] + k;\n}\n")
        sandbox._SCAN_INDEX.clear()
        rel = self.invented("p03", "method Other(s: seq<nat>, k: nat) returns (r: nat)\n"
                            + self.SPEC2 + "{\n  r := k;\n}\n")
        ok, msg = sandbox.attest(self.wt, rel)
        self.assertFalse(ok, msg)
        self.assertIn("sealed Q98", msg)

    def test_an_unreadable_source_refuses_and_changes_nothing(self):
        ok, msg = sandbox.attest(self.wt, self.card2)
        self.assertTrue(ok, msg)
        att = self.wt / "sandbox/attested.toml"
        before = att.read_bytes()
        self.key.unlink()
        sandbox._SCAN_INDEX.clear()
        for rel in (self.card2, self.invented("p04", "method P04() {}\n")):
            ok, msg = sandbox.attest(self.wt, rel)
            self.assertFalse(ok)
            self.assertIn("unchanged", msg)
            self.assertIn("key", msg)
        self.assertEqual(att.read_bytes(), before)      # nothing withdrawn, nothing added
        ok, rows = sandbox.rescan_attested(self.wt)
        self.assertFalse(ok)
        self.assertIn("nothing re-scanned", rows[0]["detail"])
        self.assertEqual(att.read_bytes(), before)

    def test_a_changed_archive_or_reference_source_refuses(self):
        arc = self.wt / "Hidden/labs/Q98/verdicts.tar.age"
        arc.write_bytes(arc.read_bytes() + b"\n")
        sandbox._SCAN_INDEX.clear()
        ok, msg = sandbox.attest(self.wt, self.card2)
        self.assertFalse(ok)
        self.assertIn("pinned sha256", msg)
        self.no_canary(msg)

    def test_a_crash_while_the_references_are_in_memory_dumps_none_of_them(self):
        real = sandbox.structure_line

        def boom(line, name=""):
            if "Zq98" in line or "zq97" in line:
                raise ValueError(f"cannot read {line!r}")
            return real(line, name)
        self.addCleanup(setattr, sandbox, "structure_line", real)
        sandbox.structure_line = boom
        sandbox._SCAN_INDEX.clear()
        att = (self.wt / "sandbox/attested.toml").read_bytes()
        import contextlib
        import io as _io
        import traceback
        out, err = _io.StringIO(), _io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            ok, msg = sandbox.attest(self.wt, self.card2)
            try:
                sandbox.scan_index(self.wt)
                tb = ""
            except sandbox.SealedRefsError:
                tb = traceback.format_exc()
        self.assertFalse(ok)
        self.assertIn("withheld", msg)
        self.assertIn("withheld", tb)
        self.no_canary(msg, tb, out.getvalue(), err.getvalue())
        self.assertEqual((self.wt / "sandbox/attested.toml").read_bytes(), att)
        # a crash in the per-card lookup is withheld the same way
        sandbox.structure_line = real
        sandbox._SCAN_INDEX.clear()

        def hits(self_, text, name):
            raise RuntimeError(f"{[s.shingles for s in self_.spans]}")
        orig = sandbox.ScanIndex.hits
        self.addCleanup(setattr, sandbox.ScanIndex, "hits", orig)
        sandbox.ScanIndex.hits = hits
        ok, msg = sandbox.attest(self.wt, self.card2)
        self.assertFalse(ok)
        self.assertIn("withheld", msg)
        self.no_canary(msg)
        self.no_canary_on_disk()

    def test_every_entry_is_rescanned_once_with_a_result_each(self):
        planted = self.invented("p05", "method Other(s: seq<nat>, k: nat) returns (r: nat)\n"
                                + self.SPEC2 + "{\n  r := k;\n}\n")
        old = []
        for rel, data in ((self.card2, (self.wt / self.card2).read_bytes()),
                          (self.crate, self.STUB3.encode()),
                          (planted, (self.wt / planted).read_bytes()),
                          ("bench/local/q/lab9/gone/tasks/gone.dfy", b"// not in the tree\n")):
            old.append(f'\n[[card]]\npath = "{rel}"\nsha256 = "{sc.sha(data)}"\n'
                       'attested = "2026-10-13"\nscan = "DV5e"\npools = "0 files, sha256 x"\n')
        att = self.wt / "sandbox/attested.toml"
        att.write_text("schema = 1\n" + "".join(old))
        ok, rows = sandbox.rescan_attested(self.wt)
        self.assertTrue(ok, rows)
        self.assertEqual([r["result"] for r in rows], ["re-attested", "re-attested", "withdrawn", "stale"])
        self.assertIn("sealed Q98", rows[2]["detail"])
        self.no_canary(*(r["detail"] for r in rows))
        entries = tomllib.loads(att.read_text())["card"]
        self.assertEqual(sorted(e["path"] for e in entries),
                         sorted([self.card2, self.crate, "bench/local/q/lab9/gone/tasks/gone.dfy"]))
        ok, rows = sandbox.rescan_attested(self.wt)
        self.assertEqual([r["result"] for r in rows], ["already", "already", "stale"])
        # a re-seal (other sealed references) makes every entry current no more
        sc.write(Path(sandbox.SEALED_REFERENCE_DIRS["bench/local/q/crate8"]), "x01/src/lib.rs",
                 self.STUB3.replace("    // HOLE\n", self.BODY3 + "    // revised\n"))
        sandbox._SCAN_INDEX.clear()
        ok, rows = sandbox.rescan_attested(self.wt)
        self.assertEqual([r["result"] for r in rows], ["re-attested", "re-attested", "stale"])
        self.no_canary_on_disk()

    def test_the_cli_reports_each_entry(self):
        ok, msg = sandbox.attest(self.wt, self.card2)
        self.assertTrue(ok, msg)
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        p = subprocess.run([sys.executable, "-B", str(sc.MKSANDBOX), "--attest-rescan",
                            "--root", str(self.wt)], capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 2)
        self.assertIn("author-only form", p.stderr)
        # the CLI's own run (the real age path is not the fake one, so the sealed decoys
        # are taken away first: a root with no sealed source reads none)
        for rel in ("sandbox/truth.toml", "bench/local/q/lab8/STRATUM.toml",
                    "bench/local/q/crate8/STRATUM.toml"):
            (self.wt / rel).unlink()
        att = self.wt / "sandbox/attested.toml"
        att.write_text(att.read_text().replace(f'scan = "{sandbox.SCAN_RULE}"', 'scan = "DV5e"'))
        cmd = [sys.executable, "-B", str(sc.MKSANDBOX), "--author", "--attest-rescan", "--root",
               str(self.wt)]
        p = subprocess.run(cmd, capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn(f"re-attested {sc.sha((self.wt / self.card2).read_bytes())[:16]}  {self.card2}",
                      p.stdout)
        self.assertIn(f"re-scan: re-attested 1 of 1 entries (rule {sandbox.SCAN_RULE})", p.stdout)
        p = subprocess.run(cmd, capture_output=True, text=True, env=env)
        self.assertIn("re-scan: already 1 of 1 entries", p.stdout)
        self.no_canary(p.stdout, p.stderr)

if __name__ == "__main__":
    unittest.main()
