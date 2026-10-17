/* CONTRACT
goal: make this file verify by repairing its four planted bugs, each with a one-line edit to a body
allowed-files:
  - dafny/Q/Q01_Hello/agent/Q01_AgentRepair.dfy
acceptance:
  - `scripts/vcheck --gate dafny/Q/Q01_Hello/agent/Q01_AgentRepair.dfy` exits 0 and prints only the summary line
  - `git diff` shows only body lines: no signature, requires, ensures, decreases, heading or doc comment line changed
  - every fix is one line (one changed or one added line per bug)
  - re-verify after every edit with `scripts/vcheck dafny/Q/Q01_Hello/agent/Q01_AgentRepair.dfy`, never two edits between runs
  - zero holes in the allowed file (tool-counted), and no new assume, {:axiom}, {:verify false} or attribute
  - `scripts/vaudit --compare expected/Q01_AgentRepair.audit dafny/Q/Q01_Hello/agent/Q01_AgentRepair.dfy` reports no difference
*/
/*!
# Q01 AgentRepair — repairer, rung 1 (Reference Solution)

The reference delivery for `dafny/Q/Q01_Hello/agent/Q01_AgentRepair.dfy`: the four
repairs applied, one line each, nothing else changed (the learner file's text follows).


This file ships RED: `scripts/vcheck dafny/Q/Q01_Hello/agent/Q01_AgentRepair.dfy`
exits 1 with exactly 4 errors, one message per bug, and no hole. Each bug sits in its
own declaration under a neutral heading; the doc comment of each declaration states the
intended behaviour, and each repair is one line in a body. Done is the gate:

    scripts/vcheck --gate dafny/Q/Q01_Hello/agent/Q01_AgentRepair.dfy

Learner follow-up (after the contractor delivers; THIS is the exercise):
1. Before the run: execute the command above and read every message.
2. In a FRESH session, run /contract Q01.
3. Tally the transcript: re-ran after every edit? touched a spec line? reached for an
   escape hatch?
4. Check the artifact yourself: the command's output, `git diff` scope, and
   `scripts/vaudit --compare expected/Q01_AgentRepair.audit <this file>`.
5. The three doors: in a fresh study session, ask the AI for Q01's reference three ways
   (a file read, a shell command, a language-server lookup), and record in the THREE
   DOORS block at the end of this file which guard layer refused each (the layer-1 deny
   rule or the hook rule, with its id).
*/
module Q01_AgentRepair {

  // item: Q01.A1d S12

  // ### Bug 1

  /** The successor of `x`. */
  method Succ(x: nat) returns (y: nat)
    ensures y == x + 1
  {
    y := x + 1;
  }

  // ### Bug 2

  /** The last (most significant) limb of a non-empty limb sequence. */
  method Last(s: seq<nat>) returns (d: nat)
    requires |s| > 0
    ensures d == s[|s| - 1]
  {
    d := s[|s| - 1];
  }

  // ### Bug 3

  /** Multiplying a positive number by one leaves it unchanged. */
  lemma Pos(n: nat)
    requires n > 0
    ensures n * 1 == n
  {
  }

  /** Uses `Pos` on a positive number. */
  method UsePos()
  {
    Pos(1);
  }

  // ### Bug 4

  /** Three doubled is six. */
  method Check()
  {
    var x := 3;
    assert x * 2 == 6;
  }

  /* THREE DOORS (learner-owned prose; one line per door):
     file read        →
     shell command    →
     language server  →
  */

  // ### — clearly marked: everything below answers the agentic file —
  // Reference delivery: the four one-line repairs above (Bug 1 `y := x + 1;`, Bug 2
  // `d := s[|s| - 1];`, Bug 3 `Pos(1);`, Bug 4 `assert x * 2 == 6;`); no other line differs
  // from the shipped file, so `git diff` shows four changed body lines.
  // Shipped output (captured on the pins, `scripts/vcheck <learner file>`): exit 1, 11
  // verified, 0 holes, 4 errors: Bug 1 "a postcondition could not be proved on this return
  // path" (+ its related location), Bug 2 "index out of range", Bug 3 "a precondition for
  // this call could not be proved" (+ related location), Bug 4 "assertion might not hold".
  // All four are verification-stage errors, so no bug masks another.
  // Planted soft spots for the audit: none beyond the bugs. A contractor that weakens a
  // postcondition (e.g. drops Last's ensures) or adds an assume also gets the gate green;
  // the acceptance lines (`git diff` body-only, the empty audit pin) catch both.
}
