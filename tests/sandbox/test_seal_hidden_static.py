"""sandbox/seal_hidden.py's pure parts (Δ409): the plaintext tree's manifest check, the
deterministic tar stream, and the pins written back into a STRATUM.toml for a refs archive
and (new, --tasks) for a topic (e) stratum's task archive. No age binary runs here."""
import hashlib
import importlib.util
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


if __name__ == "__main__":
    unittest.main()
