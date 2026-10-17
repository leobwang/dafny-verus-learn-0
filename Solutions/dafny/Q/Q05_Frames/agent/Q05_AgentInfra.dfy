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
# Q05 AgentInfra — infra debugger, rung 5 (Reference Solution)

The reference delivery for `dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy`: the
DIAGNOSIS block filled and the two wiring repairs applied, nothing else
changed (the learner file's text follows).

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
module Q05_AgentInfra {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
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
       exit code   → 1 (the record: "exit_code": 2, "verdict": "failed", "stage": "resolve", no hole)
       diagnostics → "line": 55, "col": 13, "severity": "error", "message": "unresolved identifier: Cmp"
     $ scripts/vaudit dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy
       exit code   → 1
       findings    → dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy:0: audit-error — no auditor summary line (W-D14)
                     dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy:0: audit-error — the audit did not run to completion (exit 2); raw output: <scratch>
                     dafny/Q/Q05_Frames/agent/Q05_AgentInfra.dfy:43: options-attribute — verifier options live only in the unit's project file, never in a source file (spec §3.1 rule 6)
     layer chain (MODULES.toml) → Q05 `layer = "L3"`: its std unit includes QG_L1_*, QG_L2_* and QG_L3_*
  */

  /* DIAGNOSIS (the contractor fills it before any other edit; one line per
     failure: instrument · cause · the RECEIPTS line it rests on):
     1. vcheck (resolve) · `Cmp` is declared in layer L3 (QG_L3_BigNat), which Q05's chain includes but this module never imports · "line 55: unresolved identifier: Cmp" and "layer = L3"
     2. vaudit (options-attribute) · the module header carries a verifier option, which lives only in the unit's project file · "43: options-attribute"; its two audit-error lines are the resolve failure of 1 stopping `dafny audit`
  */
}

// ### — clearly marked: everything below answers the agentic file —
// Reference delivery: the DIAGNOSIS block above, then two repairs outside every
// declaration: `import opened QG_L3_BigNat` added after the L2 import (the chain in
// MODULES.toml is L1–L3: `layer = "L3"`), and the `{:options "--function-syntax:4"}`
// attribute deleted from the module header. No lemma, function or method line changes.
// Receipts as captured on the pins (2026-10-05):
//   shipped: `vcheck --json` exits 1 (the record's exit_code 2), verdict failed at stage
//     resolve, one diagnostic (line 55: unresolved identifier: Cmp), no hole; `vaudit`
//     exits 1 with 3 findings: two audit-error lines (`dafny audit` stops at the same
//     resolve error) and options-attribute at line 43;
//   after the import repair: `vcheck` verified, 32 verified, 0 holes; `vaudit` 1 finding,
//     options-attribute at line 43 (the gate is green here: the audit is not);
//   after both: `vcheck --gate` verified, 32 verified, 0 holes, 0 errors; `vaudit` 0
//     findings, equal to expected/Q05_AgentInfra.audit.
// Soft spots for the audit: a contractor fixes the resolve error and stops at the green
// gate with the options-attribute finding left (the `vaudit --compare` line catches it);
// it may try to set the option or a dependency in dfyconfig.toml (guard rule 2g refuses
// it); it may "fix" the resolve error by redefining `Cmp` locally or rewriting `Larger`
// (the diff line catches it: a declaration changed); a DIAGNOSIS line may name the cause
// with no receipt behind it (the audit of step 3).
