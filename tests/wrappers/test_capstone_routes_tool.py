"""Tool tests of the binary route (the user's decision D16, 2026-10-12): `scripts/vcheck
--bin` builds an invented crate's [[bin]] target with the pinned Verus 0.2026.09.27.3cf1832
(`verus --compile`, its layer chain first) and runs it on a tiny input. The fixture is
tests/wrappers/fixtures/verus/cli (a verified library over the chain fixture's bottom
crate, and a command line outside `verus!`); nothing here is course content.

Every job runs through dvl.verus under the CLAUDE.md §Resources memory cap (Verus 16G),
one at a time unless DVL_VERUS_JOBS says otherwise. Every expectation below was observed
on a real run. The suite fails, never skips, without the pinned toolchain.

Run: python3 -B -m unittest discover -s tests/wrappers -p 'test_capstone_routes_tool.py'
"""

import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_tools_common as C  # noqa: E402

CLI = "tests/wrappers/fixtures/verus/cli"


class BinRoute(unittest.TestCase):
    def test_builds_and_runs_the_tool_on_a_tiny_input(self):
        rc, out, err = C.tool("vcheck", "--bin", CLI, "--", "sum", "2", "40")
        self.assertEqual(rc, 0, out + err)
        self.assertEqual(out, f"vcheck: {CLI} [verus, bin tally]: built — 2 verified; ran "
                              "`tally sum 2 40`: exit 0\n42\n")
        self.assertEqual(err, "")

    def test_a_tool_that_exits_non_zero_fails(self):
        rc, out, err = C.tool("vcheck", "--bin", CLI, "--", "nope")
        self.assertEqual(rc, 1, out + err)
        self.assertEqual(out, f"vcheck: {CLI} [verus, bin tally]: built — 2 verified; ran "
                              "`tally nope`: exit 2\n")
        self.assertEqual(err, "usage: tally sum <a> <b> | tally twice <a>\n")

    def test_a_crate_with_no_binary_is_refused(self):
        rc, out, err = C.tool("vcheck", "--bin", "tests/wrappers/fixtures/verus/chain/tla")
        self.assertEqual(rc, 3, out + err)
        self.assertIn("[verus, bin]: refused — not built (stage cli)", out)
        self.assertIn("the crate has no [[bin]] target", out)


if __name__ == "__main__":
    unittest.main()
