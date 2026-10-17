"""scripts/contract_local.sh's refusal paths and dry run (DV4-PLAN §6; DV4
step 1b): the registry and budget refusals, the CONTRACT header and its
allowed paths as /contract validates them, the starting state found from the
snapshot's commit (never the learner's tree after the run), the acceptance-line
forms, the contract text, and the live replay's refusals before anything runs
(its runs against a fake docker are tests/sandbox/test_agent_run.py's). A
throwaway git root holds the invented module Q98 and decoy files only."""

import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sandbox_common as sc  # noqa: E402
from dvl import contract_local as cl  # noqa: E402

CL = sc.ROOT / "scripts" / "contract_local.sh"
SNAP = "research/snapshots/Q98_Agent.dfy"
CLAUDE_MD = """# CLAUDE.md (decoy)

## §Roles

A decoy section that never enters a sandbox.

## §Contractor contract

Contract v0 is written by the learner. The fallback rules:

- re-verify after every edit through the pinned wrapper;
- never weaken a spec.

<!-- learner-owned below: contract v0/v1/v2 -->

<!-- Slot format (spec §5.2). A decoy slot comment. -->

### Q-v0 — Q03, 2026-10-01
1. a decoy learner rule — earned by: a decoy run — a decoy moment
"""


def header(allowed=(sc.AGENT_D,), acceptance=None, snap=SNAP):
    acc = acceptance if acceptance is not None else [
        f"`scripts/vcheck --gate {sc.AGENT_D}` exits 0 and prints only the summary line",
        "zero tool-counted holes in the allowed file",
        f"`scripts/specfreeze --against {snap} {sc.AGENT_D}` reports no change",
        f"`scripts/vaudit --compare expected/Q98_Agent.audit {sc.AGENT_D}` reports no difference",
        "`git diff` against the committed snapshot changes only the goal's body",
        "re-verify after every edit; never stack unverified edits",
    ]
    return ("/* CONTRACT\ngoal: a decoy goal for the replay suite\nallowed-files:\n"
            + "".join(f"  - {p}\n" for p in allowed) + "acceptance:\n"
            + "".join(f"  - {a}\n" for a in acc) + "*/\n")


class ContractLocal(unittest.TestCase):
    def setUp(self):
        self.root = sc.make_root(git=False, lock=False)     # no image built in this root
        self.addCleanup(sc.cleanup, self.root)
        self.bin = sc.tmpdir("dvl0-cl-bin-")
        self.xdg = sc.tmpdir("dvl0-cl-xdg-")
        self.addCleanup(sc.cleanup, self.bin, self.xdg)
        sc.fake_bin(self.bin, "docker", 'echo "permission denied while trying to connect to the '
                                        'docker API" >&2\nexit 1\n')
        sc.write(self.root, "CLAUDE.md", CLAUDE_MD)
        self.start = header() + "lemma Goal(n: nat) ensures n + 0 == n\n"
        sc.write(self.root, sc.AGENT_D, self.start)
        sc.write(self.root, SNAP, "// the learner's snapshot of the frozen part\n")
        subprocess.run(sc.GIT + ["init", "-q", str(self.root)], check=True)
        self.commit("the starting state")
        self.first = self.git("rev-parse", "HEAD")
        # the learner's /contract run then changed the agentic file
        sc.write(self.root, sc.AGENT_D, self.start.replace("== n\n", "== n { }\n"))
        self.commit("after the contract run")

    def git(self, *args):
        return subprocess.run(sc.GIT + ["-C", str(self.root), *args], capture_output=True, text=True,
                              check=True).stdout.strip()

    def commit(self, msg):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)

    def cl(self, *args, docker_ok=False):
        env = {k: v for k, v in os.environ.items() if k not in ("CI", "DVL_NO_DOCKER", "FVH_APPARATUS")}
        if docker_ok:
            sc.fake_bin(self.bin, "docker", "echo 29.1.3\n")
        env["PATH"] = f"{self.bin}:{env.get('PATH', '/usr/bin:/bin')}"
        env["XDG_RUNTIME_DIR"] = str(self.xdg)
        env["GIT_CEILING_DIRECTORIES"] = str(self.root.parent)
        return subprocess.run(["bash", str(CL), *args, "--root", str(self.root)], capture_output=True,
                              text=True, env=env, timeout=300)

    def registry(self, **kw):
        text = sc.REGISTRY
        for k, v in kw.items():
            text = re.sub(rf"(?m)^{k} = .*$", f"{k} = {v}", text, count=1)
        sc.write(self.root, "MODULES.toml", text)

    # --- the dry run -------------------------------------------------------------------

    def test_the_dry_run_stages_the_snapshots_commit_never_the_tree_after_the_run(self):
        sc.write(self.root, sc.AGENT_D, self.start + "// an uncommitted edit\n")
        p = self.cl("Q98", "--file", sc.AGENT_D, "--dry-run")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn(f"starting state: {self.first}", p.stdout)
        self.assertIn("the commit that last changed the snapshot", p.stdout)
        raw = cl.build_manifest(self.root, cl.record(self.root, "Q98"), cl.parse_header(self.start),
                                self.first, SNAP, "qwen3.8:latest")
        ed = next(f for f in raw["file"] if f["role"] == "editable")
        self.assertEqual((ed["src"], ed["rev"], ed["sha256"]), (sc.AGENT_D, self.first, sc.sha(self.start)))
        snap = next(f for f in raw["file"] if f["role"] == "snapshot")
        self.assertEqual((snap["dst"], snap["rev"]), (SNAP, self.first))
        roles = {f["role"] for f in raw["file"]}
        self.assertEqual(roles, {"editable", "snapshot", "given", "project", "tool", "expected", "contract"})
        self.assertIn("expected/Q98_Agent.audit", [f.get("src") for f in raw["file"]])
        self.assertEqual(raw["return"], [sc.AGENT_D])
        self.assertIn("docker run", p.stdout)
        self.assertIn("not yet available: the sandbox images are not built yet", p.stdout)

    def test_acceptance_lines_are_sorted_into_checked_forms_and_the_audit_list(self):
        forms = [cl.classify_line(a)[0] for a in cl.parse_header(self.start)["acceptance"]]
        self.assertEqual(forms, ["vcheck-gate", "zero-holes", "specfreeze-against", "vaudit-compare",
                                 "git-diff", "audit"])
        self.assertEqual(cl.classify_line(f"`scripts/vaudit {sc.AGENT_D}` reports no finding")[0], "vaudit")

    def test_the_contract_text_is_the_contract_and_the_contractor_section_only(self):
        text = cl.contract_text(self.root, cl.record(self.root, "Q98"), cl.parse_header(self.start), [])
        self.assertIn("goal: a decoy goal", text)
        self.assertIn("never weaken a spec", text)
        self.assertIn("### Q-v0 — Q03, 2026-10-01", text)
        self.assertNotIn("§Roles", text)
        self.assertNotIn("Slot format", text)

    # --- refusals ------------------------------------------------------------------------

    def test_registry_refusals(self):
        for kw, want in ((dict(status='"planned"'), "planned"), (dict(solo="true"), "solo"),
                         (dict(agentic="[]"), "no agentic exercise"),
                         (dict(engines='["contract"]'), "do not include agent"),
                         (dict(budget="{ qwen_calls = 40, qwen_runs = 0, gpu_hours = 1 }"), "allows no Qwen run")):
            self.registry(**kw)
            p = self.cl("Q98", "--file", sc.AGENT_D, "--dry-run")
            self.assertEqual(p.returncode, 3, kw)
            self.assertIn(want, p.stderr)
        p = self.cl("Q42", "--dry-run")
        self.assertEqual(p.returncode, 3)

    def test_header_refusals(self):
        bad = {"line 1 does not open": "// a comment first\n" + self.start,
               "a key 'scope'": self.start.replace("goal:", "scope: x\ngoal:"),
               "lacks 'goal'": re.sub(r"(?m)^goal: .*\n", "", self.start),
               "'allowed-files' is empty": header(allowed=()),
               "never closed": self.start.replace("*/\n", "")}
        for want, text in bad.items():
            sc.write(self.root, sc.AGENT_D, text)
            self.commit(want)
            p = self.cl("Q98", "--file", sc.AGENT_D, "--dry-run")
            self.assertEqual(p.returncode, 3, want)
            self.assertIn(want, p.stderr)

    def test_allowed_path_refusals(self):
        self.registry(agentic=f'["{sc.AGENT_D}", "research/"]')
        for path, want in (("dafny/Q/Q97_Other/agent/Q97_Agent.dfy", "not in Q98's agentic list"),
                           ("research/runs/Q98/r1/run.json", "run-record"),
                           ("research/ledger-heads.jsonl", "run-record"),
                           ("../escape.dfy", "not a repo-relative path")):
            sc.write(self.root, sc.AGENT_D, header(allowed=(sc.AGENT_D, path)) + "lemma G() {}\n")
            self.commit(path)
            p = self.cl("Q98", "--file", sc.AGENT_D, "--dry-run")
            self.assertEqual(p.returncode, 3, path)
            self.assertIn(want, p.stderr)

    def test_starting_state_refusals(self):
        sc.write(self.root, sc.AGENT_D, header(acceptance=["zero holes in the allowed file"]) + "lemma G() {}\n")
        self.commit("no snapshot named")
        p = self.cl("Q98", "--file", sc.AGENT_D, "--dry-run")
        self.assertEqual(p.returncode, 3)
        self.assertIn("names no snapshot", p.stderr)
        p = self.cl("Q98", "--file", sc.AGENT_D, "--dry-run", "--from", self.first)
        self.assertEqual(p.returncode, 0, p.stderr)
        sc.write(self.root, sc.AGENT_D, header(snap="research/snapshots/other.dfy") + "lemma G() {}\n")
        self.commit("names an untracked snapshot")
        p = self.cl("Q98", "--file", sc.AGENT_D, "--dry-run")
        self.assertIn("is missing", p.stderr)
        sc.write(self.root, "research/snapshots/other.dfy", "// untracked\n")
        p = self.cl("Q98", "--file", sc.AGENT_D, "--dry-run")
        self.assertIn("is not tracked", p.stderr)
        sc.write(self.root, sc.AGENT_D, self.start)
        self.commit("back to the named snapshot")
        sc.write(self.root, SNAP, "// changed after its commit\n")
        p = self.cl("Q98", "--file", sc.AGENT_D, "--dry-run")
        self.assertIn("differs from its committed version", p.stderr)

    def test_an_allowed_file_absent_at_the_starting_commit_is_refused(self):
        self.registry(agentic=f'["{sc.AGENT_D}", "{sc.AGENT_V}"]')
        (self.root / sc.AGENT_V).unlink()
        sc.write(self.root, SNAP, "// a new snapshot\n")
        sc.write(self.root, sc.AGENT_D, header(allowed=(sc.AGENT_D, sc.AGENT_V)) + "lemma G() {}\n")
        self.commit("a snapshot without the Verus file")
        sc.write(self.root, sc.AGENT_V, "// written after the snapshot, never committed\n")
        p = self.cl("Q98", "--file", sc.AGENT_D, "--dry-run")
        self.assertEqual(p.returncode, 3)
        self.assertIn("did not exist at the starting commit", p.stderr)

    def test_only_a_pinned_model_tag(self):
        p = self.cl("Q98", "--file", sc.AGENT_D, "--dry-run", "--model", "qwen3.8-flash-next:UD-Q4_K_XL")
        self.assertEqual(p.returncode, 3)
        self.assertIn("not a pinned tag", p.stderr)

    def test_available_reports_every_reason_and_the_live_run_refuses_on_the_first(self):
        p = self.cl("Q98", "--available")
        self.assertEqual(p.returncode, 3)
        self.assertIn("apparatus", p.stderr)
        self.assertIn("the sandbox images are not built yet", p.stderr)
        # the diagnosis reads this host's id and getent: whichever case holds here
        # (H1 not done, a stale login, or a daemon that does not answer), it names
        # the refusal and never escalates
        self.assertIn("docker refused (permission denied", p.stderr)
        self.assertNotRegex(p.stderr, r"(?m)^\s*sudo ")
        p = self.cl("Q98", "--file", sc.AGENT_D)
        self.assertEqual(p.returncode, 3)
        self.assertIn("refused", p.stderr)
        sc.write(self.root, "sandbox/apparatus.toml", "# decoy apparatus pins\n")
        p = self.cl("Q98", "--file", sc.AGENT_D, docker_ok=True)
        self.assertEqual(p.returncode, 3)
        self.assertIn("schema None", p.stderr)              # the apparatus file is checked
        p = self.cl("Q98", "--available", docker_ok=True)
        self.assertEqual(p.returncode, 3)
        self.assertNotIn("docker refused", p.stderr)

    def test_an_anchored_ledger_that_is_missing_is_refused(self):
        sc.write(self.root, "research/ledger-heads.jsonl",
                 '{"module": "Q98", "event": "open", "seq": 0, "head": "00", "planned": 1}\n')
        p = self.cl("Q98", "--available")
        self.assertIn("ledger.jsonl is missing", p.stderr)


if __name__ == "__main__":
    unittest.main()
