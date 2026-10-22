"""Topic (e)'s local strata (QPLAN §32.3, §33.4, §34.4; DELTAS Δ405, Δ408): the shape of every
bench/local/q/agentic/<stratum>/STRATUM.toml, each card's task form on disk with its pinned
sha256, the course-local and public counts within the fallback-(b) targets, ids unique
across strata, and no answer material in the learner tree. Tool-free; the solver half of
admission is the author's (Solutions/tools/agentic/admit_task.py, in `--author` CI)."""

import hashlib
import math
import re
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENTIC = ROOT / "bench" / "local" / "q" / "agentic"
TARGETS = {"q31-dev": (40, 24, 16), "q32-dev": (50, 30, 20),   # D76 fallback (b), Δ405
           "q31-heldout": (60, 36, 24), "q32-t1": (40, 24, 16), "q32-t2": (40, 24, 16),
           "q32-t3": (40, 24, 16)}
CARD = re.compile(r"(cl|pd|pv)-[dv]\d+-[a-z0-9-]+")


def strata():
    return sorted(AGENTIC.glob("*/STRATUM.toml")) if AGENTIC.is_dir() else []


class Strata(unittest.TestCase):
    def test_every_stratum(self):
        seen = set()
        for st in strata():
            d = tomllib.loads(st.read_text(encoding="utf-8"))
            name = st.parent.name
            with self.subTest(stratum=name):
                self.assertEqual((d["schema"], d["stratum"]), (1, name))
                self.assertIn(d["module"], ("Q31", "Q32", "Q33"))
                cards = d.get("card", [])
                cl = sum(1 for c in cards if c["source"] == "course-local")
                pub = sum(1 for c in cards if c["source"] == "public" and c.get("role", "card") == "card")
                spares = [c for c in cards if c["source"] == "public" and c.get("role") == "spare"]
                t = d["target"]
                # D76: about 20 % spare public cards, rounded up per part, in a 1..n spare order
                self.assertLessEqual(len(spares), math.ceil(0.2 * t["public"]))
                self.assertEqual(sorted(c["spare_order"] for c in spares), list(range(1, len(spares) + 1)))
                for c in cards:
                    if c["source"] == "public":
                        self.assertIn(c.get("role", "card"), ("card", "spare"))
                        self.assertIn(c["set"], ("dafnybench", "vericoding", "humaneval-verus"))
                        self.assertRegex(c["id"], r"^p[dv]-")
                if name in TARGETS:
                    self.assertEqual((t["total"], t["course_local"], t["public"]), TARGETS[name])
                self.assertLessEqual(cl, t["course_local"])
                self.assertLessEqual(pub, t["public"])
                for c in cards:
                    self.assertRegex(c["id"], CARD)
                    self.assertNotIn(c["id"], seen, "a card id is unique across strata")
                    seen.add(c["id"])
                    self.assertTrue(c["admitted"])
                    self.assertRegex(c["admission_sha256"], r"^[0-9a-f]{64}$")
                    self.assertRegex(c["form_sha256"], r"^[0-9a-f]{64}$")
                    if d.get("sealed"):
                        # a sealed card names its form inside the archive; nothing is on disk
                        self.assertTrue(c["form"].startswith(f"labs/{d['lab']}/{c['id']}/tasks/"))
                        self.assertFalse((ROOT / c["form"]).exists())
                        self.assertEqual(c["lang"], "dafny" if c["form"].endswith(".dfy") else "verus")
                        continue
                    form = ROOT / c["form"]
                    self.assertTrue(form.is_file(), c["form"])
                    self.assertEqual(hashlib.sha256(form.read_bytes()).hexdigest(), c["form_sha256"])
                    self.assertEqual(c["lang"], "dafny" if form.suffix == ".dfy" else "verus")

    def test_a_sealed_stratum_pins_its_archives(self):
        for st in strata():
            d = tomllib.loads(st.read_text(encoding="utf-8"))
            if not d.get("sealed"):
                continue
            with self.subTest(stratum=st.parent.name):
                self.assertEqual(sorted(p.name for p in st.parent.iterdir()), ["STRATUM.toml"])
                self.assertTrue(d["archive"].startswith("Hidden/") and d["refs_archive"].startswith("Hidden/"))
                for key, pin in (("archive", "archive_sha256"), ("refs_archive", "refs_sha256")):
                    if d[pin] == "PENDING":
                        continue
                    arc = ROOT / d[key]
                    self.assertTrue(arc.is_file(), d[key])
                    self.assertEqual(hashlib.sha256(arc.read_bytes()).hexdigest(), d[pin])
                    self.assertFalse(arc.read_bytes().startswith(b"labs/"), "an archive is never plaintext")
                if d["archive_sha256"] != "PENDING":
                    self.assertEqual(d["files"], 1 * len(d.get("card", [])))

    def test_no_answer_in_the_learner_tree(self):
        for st in strata():
            for f in st.parent.rglob("*"):
                if f.is_file() and f.name != "STRATUM.toml":
                    self.assertEqual(f.parent.name, "tasks", f"{f}: only task forms ship")


if __name__ == "__main__":
    unittest.main()
