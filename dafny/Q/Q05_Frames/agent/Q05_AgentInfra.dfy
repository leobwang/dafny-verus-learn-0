/* CONTRACT
goal: diagnose this file's two wiring failures from its RECEIPTS block, then repair them
allowed-files:
  - dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy
acceptance:
  - a DIAGNOSIS block, filled in this file before any other edit: one line per failure, naming the instrument that reports it, the cause, and the RECEIPTS line it rests on
  - `git diff` changes no line of a lemma, function, method or predicate (signature, contract or body): only lines outside every declaration change, and the DIAGNOSIS block
  - `scripts/vcheck --gate dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy` exits 0 and prints only the summary line
  - zero holes in the allowed file (tool-counted)
  - after every edit, re-run both `scripts/vcheck --json dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy` and `scripts/vaudit dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy`, never two edits between runs
  - `scripts/vaudit --compare expected/Q05_AgentInfra.audit dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy` reports no difference
*/
/*!
# Q05 AgentInfra — infra debugger, rung 5 (`/contract Q05`)

This file ships RED by design: it holds two planted wiring failures and no
hole. As shipped, `scripts/vcheck --json` on it exits 1 with exactly one error
and no hole, and `scripts/vaudit` exits 1 with three findings. Its
declarations are right as written, and each doc comment states the intended
behaviour; once the file is wired right, it verifies and its audit is clean. A wiring file (a dfyconfig.toml, MODULES.toml, anything under scripts/)
is never the fix: the guard refuses every edit there. The two instruments:

    scripts/vcheck --json dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy
    scripts/vaudit dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy

Done is the gate, with a clean audit:

    scripts/vcheck --gate dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy

Learner follow-up (the receipts come first; the audit afterwards is the
exercise):
1. Before the run: run both instruments above and copy into the RECEIPTS block
   at the end of this file, verbatim, each command, its exit code and every
   diagnostic or finding line; add the module's layer chain as MODULES.toml
   states it (the record's `layer`, and the given layers its units include).
   Do the same in the Verus half, verus/q/q05_frames/src/agent.rs.
2. In a FRESH session, run /contract Q05.
3. Audit the transcript and the diff: does each DIAGNOSIS line rest on a
   receipt, or on a guess? Did the contractor try to edit a wiring file (a
   guard refusal) or a declaration? Did it stop at a green gate before the
   audit was clean?
*/
module {:options "--function-syntax:4"} Q05_AgentInfra {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import Std.Wrappers

  // item: Q05.A1d S6

  /** The larger of two numerals, chosen by the layer's comparison `Cmp`:
      `b` when `a` compares below it, otherwise `a`. */
  method Larger(a: seq<nat>, b: seq<nat>) returns (r: seq<nat>)
    ensures r == a || r == b
  {
    r := if Cmp(a, b) < 0 then b else a;
  }

  /** The number of limbs of a numeral. */
  function Width(a: seq<nat>): nat
  {
    |a|
  }

  /* RECEIPTS (learner-owned; filled before the run, verbatim):
     $ scripts/vcheck --json dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy
       exit code   →
       diagnostics →
     $ scripts/vaudit dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy
       exit code   →
       findings    →
     layer chain (MODULES.toml) →
  */

  /* DIAGNOSIS (the contractor fills it before any other edit; one line per
     failure: instrument · cause · the RECEIPTS line it rests on):
  */
}
