"""sandbox/seal_hidden.py's pure parts (Δ409): the plaintext tree's manifest check, the
deterministic tar stream, and the pins written back into a STRATUM.toml for a refs archive
and (new, --tasks) for a topic (e) stratum's task archive; and (Δ418, --part) the pins of a
challenge's sealed part written into its own [[lab]] of truth.toml, never a sibling's; and
(Δ421) a par-agent pin's par_gated, read from its plaintext fragment. No age binary runs
here."""
import contextlib
import hashlib
import importlib.util
import io
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("seal_hidden", ROOT / "sandbox/seal_hidden.py")
seal = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(ROOT / "scripts"))
spec.loader.exec_module(seal)


def sha(b):
    return hashlib.sha256(b).hexdigest()


class SealHidden(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory(prefix="dvl-seal-")
        self.addCleanup(t.cleanup)
        self.d = Path(t.name)

    def tree(self, files):
        base = self.d / "src" / "labs" / "Q31"
        for rel, data in files.items():
            (base / rel).parent.mkdir(parents=True, exist_ok=True)
            (base / rel).write_bytes(data)
        man = "".join(f"{sha(v)}  labs/Q31/{k}\n" for k, v in sorted(files.items()))
        (base / "MANIFEST.sha256").write_text(man)
        return self.d / "src"

    def test_plaintext_and_tar_are_checked_and_deterministic(self):
        src = self.tree({"c1/tasks/c1.dfy": b"module A {}\n", "c2/tasks/c2.rs": b"fn x() {}\n"})
        files, man = seal.plaintext(src, "Q31")
        self.assertEqual(len(files), 3)
        self.assertEqual(seal.tar_stream(files), seal.tar_stream(dict(reversed(files.items()))))
        (src / "labs/Q31/c1/tasks/extra.dfy").write_text("x")
        with self.assertRaises(ValueError):
            seal.plaintext(src, "Q31")

    def test_the_stratum_pins(self):
        st = self.d / "STRATUM.toml"
        st.write_text('schema = 1\nmodule = "Q31"\narchive = "Hidden/Agentic/Q31/heldout.tar.age"\n'
                      'archive_sha256 = "PENDING"\nfiles = 0\nmanifest_sha256 = "PENDING"\n'
                      'refs_archive = "Hidden/Agentic/Q31/heldout-refs.tar.age"\n'
                      'refs_sha256 = "PENDING"\nrefs_files = 0\nrefs_manifest_sha256 = "PENDING"\n\n'
                      '[[card]]\nid = "cl-d101-q31h"\nfiles = 9\n')
        seal.update_stratum_pins(st, "a" * 64, 36, "b" * 64, prefix="")
        seal.update_stratum_pins(st, "c" * 64, 36, "d" * 64)
        d = tomllib.loads(st.read_text())
        self.assertEqual((d["archive_sha256"], d["files"], d["manifest_sha256"]), ("a" * 64, 36, "b" * 64))
        self.assertEqual((d["refs_sha256"], d["refs_files"]), ("c" * 64, 36))
        self.assertEqual(d["card"][0]["files"], 9)          # tables below are never touched

    def test_a_part_pin_is_written_into_its_own_lab_table(self):
        truth = self.d / "truth.toml"
        block = ('[[lab]]\nid = "{id}"\n{part}archive = "{arc}"\nrecipient = "age1x"\n'
                 'sha256 = "PENDING"\nfiles = 0\nmanifest_sha256 = "PENDING"\n\n')
        truth.write_text("schema = 1\n\n" + block.format(id="Q15", part="", arc="a.age")
                         + block.format(id="Q31", part='part = "cheats"\n', arc="c.age")
                         + block.format(id="Q31", part='part = "bench"\n', arc="b.age"))
        seal.update_pins("Q31", "e" * 64, 7, "f" * 64, part="bench", truth=truth)
        labs = {(x["id"], x.get("part")): x for x in tomllib.loads(truth.read_text())["lab"]}
        self.assertEqual((labs[("Q31", "bench")]["sha256"], labs[("Q31", "bench")]["files"]),
                         ("e" * 64, 7))
        self.assertEqual(labs[("Q31", "cheats")]["sha256"], "PENDING")
        self.assertEqual(labs[("Q15", None)]["sha256"], "PENDING")
        with self.assertRaises(ValueError):           # Q31 has no part-less pin
            seal.update_pins("Q31", "e" * 64, 7, "f" * 64, truth=truth)
        with self.assertRaises(ValueError):
            seal.update_pins("Q15", "e" * 64, 7, "f" * 64, part="cheats", truth=truth)

    def test_a_par_agent_pin_takes_par_gated_from_its_fragment(self):
        """Δ421: the host cannot read par's sealed fragment, so its pin says whether it has
        a gated arm (fvh.sealed refuses a mismatch with the learner's plan before staging)."""
        frag = b'[arm]\nconstruct = "model"\npolicy = "par_q32.policy:render"\n'
        files = {"labs/Q32/par/PLAN.toml": frag}
        self.assertFalse(seal.par_gated(files, "Q32"))
        files["labs/Q32/par/PLAN.toml"] = frag.replace(b"[arm]\n", b'[arm]\nacceptance = "gate"\n')
        self.assertTrue(seal.par_gated(files, "Q32"))
        files["labs/Q32/par/PLAN.toml"] = frag + b'[census]\nacceptance = "gate"\n'
        self.assertTrue(seal.par_gated(files, "Q32"))
        for bad in ({}, {"labs/Q32/par/PLAN.toml": b"[arm\n"}):
            with self.assertRaises(ValueError):
                seal.par_gated(bad, "Q32")
        truth = self.d / "truth.toml"
        block = ('[[lab]]\nid = "{id}"\npart = "{part}"\narchive = "{arc}"\nrecipient = "age1x"\n'
                 'sha256 = "PENDING"\nfiles = 0\nmanifest_sha256 = "PENDING"\n\n')
        truth.write_text("schema = 1\n\n" + block.format(id="Q32", part="par-agent", arc="p.age")
                         + block.format(id="Q32", part="bench", arc="b.age"))
        seal.update_pins("Q32", "e" * 64, 4, "f" * 64, part="par-agent", truth=truth,
                         extra={"par_gated": "true"})
        labs = {(x["id"], x.get("part")): x for x in tomllib.loads(truth.read_text())["lab"]}
        self.assertIs(labs[("Q32", "par-agent")]["par_gated"], True)
        self.assertNotIn("par_gated", labs[("Q32", "bench")])
        seal.update_pins("Q32", "e" * 64, 4, "f" * 64, part="par-agent", truth=truth,
                         extra={"par_gated": "false"})          # rewritten in place, once
        self.assertEqual(truth.read_text().count("par_gated"), 1)
        labs = {(x["id"], x.get("part")): x for x in tomllib.loads(truth.read_text())["lab"]}
        self.assertIs(labs[("Q32", "par-agent")]["par_gated"], False)

    def test_part_usage_is_refused_before_anything_runs(self):
        for argv in (["Q31", "--src", "x", "--part", "Cheats"],
                     ["Q31", "--src", "x", "--part", "cheats", "--tasks", "bench/local/q/x"],
                     ["Q31", "--src", "x", "--part", "cheats", "--stratum", "bench/local/q/x"]):
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(seal.main(argv), 2, argv)


if __name__ == "__main__":
    unittest.main()
