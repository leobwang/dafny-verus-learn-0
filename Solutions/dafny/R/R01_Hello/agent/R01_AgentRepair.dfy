/* CONTRACT
goal: make this file verify by repairing its four planted bugs, each with a one-line body edit
allowed-files:
  - dafny/R/R01_Hello/agent/R01_AgentRepair.dfy
acceptance:
  - `scripts/vcheck --gate dafny/R/R01_Hello/agent/R01_AgentRepair.dfy` exits 0 and prints only the summary line
  - `git diff` changes only body lines: no signature, requires, ensures, decreases, heading or doc comment changed
  - every fix is one changed or added line per bug
  - re-verify after every edit with `scripts/vcheck dafny/R/R01_Hello/agent/R01_AgentRepair.dfy`, never two edits between runs
  - zero tool-counted holes and no new assume, {:axiom}, {:verify false} or verification attribute
  - `scripts/vaudit --compare expected/R01_AgentRepair.audit dafny/R/R01_Hello/agent/R01_AgentRepair.dfy` reports no difference
*/
/*! R01 repairer, rung 1. Four independent bugs; zero holes. Read every diagnostic.
After a fresh /contract R01 run, audit the transcript, diff and assumption report.
Were there stacked edits, spec edits, or attempts to escape verification?
The three doors and your R-v0 contract are learner work, described in the chapter. */
module R01_AgentRepair {
  // item: R01.A1d
  // ### Bug 1
  /** Return the character at i, with no wrapping or substitution. */
  method PickChar(s: seq<char>, i: nat) returns (c: char)
    requires i < |s|
    ensures c == s[i]
  {
    c := s[i];
  }

  // ### Bug 2
  /** Decide whether i is no later than j; equality must be included. */
  method NoLater(i: nat, j: nat) returns (b: bool)
    ensures b == (i <= j)
  {
    b := i <= j;
  }

  function WalkLength(s: seq<char>): nat
    decreases |s|
  {
    if |s| == 0 then 0 else 1 + WalkLength(s[1..])
  }

  // ### Bug 3
  /** Establish that recursively walking the string visits every character. */
  lemma {:induction false} WalkLengthSound(s: seq<char>)
    ensures WalkLength(s) == |s|
    decreases |s|
  {
    if |s| > 1 {
      WalkLengthSound(s[1..]);
    }
  }

  // ### Bug 4
  /** Allocate room for this many characters and one terminator. */
  method RoomForTerminator(s: seq<char>) returns (n: nat)
    ensures n == |s| + 1
  {
    n := |s| + 1;
  }

  /* THREE DOORS — in a fresh study session, request the R01 reference by
     a file read, a shell read and a language-server lookup. Record each refusal
     and its layer/rule, not any reference content.
     file: ...  shell: ...  language server: ...

     TRANSCRIPT AUDIT — re-verified after each edit? only bodies? one line per bug?
     Unexpected escape hatch or undocumented deviation? ...
  */
}
