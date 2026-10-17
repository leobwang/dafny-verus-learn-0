"""fvh.verdicts — the gate words and the cheat classes, as plain data
(DV4-PLAN §3.7; spec §5.6).

  PASS, FAIL, UNKNOWN   the three words a gate prints
  GATE_WORDS            (PASS, FAIL, UNKNOWN)
  XCLASSES              spec §5.6's cheat taxonomy: class id -> title, X01..X18
                        in order (a read-only mapping)
  GRADER_ONLY           the classes that need an oracle the learner never sees:
                        ("X07", "X08", "X14"). On them a gate must answer
                        UNKNOWN, never PASS (spec §5.6; design §11.2)

Frozen (guard rule 2f), standard library only. This module holds names and
titles only: no gate logic, and nothing about which instrument catches which
class.
"""

from types import MappingProxyType

__all__ = ["FAIL", "GATE_WORDS", "GRADER_ONLY", "PASS", "UNKNOWN", "XCLASSES"]

PASS = "PASS"
FAIL = "FAIL"
UNKNOWN = "UNKNOWN"
GATE_WORDS = (PASS, FAIL, UNKNOWN)

# Spec §5.6's table, verbatim.
XCLASSES = MappingProxyType({
    "X01": "bare hole",
    "X02": "hole in a helper",
    "X03": "rogue axiom",
    "X04": "trusted native evaluation",
    "X05": "ignored error (green by exit-code confusion)",
    "X06": "weakened statement",
    "X07": "vacuous hypotheses (needs a satisfiability witness)",
    "X08": "weakened spec (hidden spec implication)",
    "X09": "notation shadowing",
    "X10": "checker-skip option",
    "X11": "foreign/extern implementation lies",
    "X12": "partial/unsafe definitions",
    "X13": "termination proof faked with a hole",
    "X14": "lookup-table overfitting (hidden tests only)",
    "X15": "harness tampering",
    "X16": "resource DoS",
    "X17": "held-out exfiltration",
    "X18": "tool use by the policy process",
})

GRADER_ONLY = ("X07", "X08", "X14")
