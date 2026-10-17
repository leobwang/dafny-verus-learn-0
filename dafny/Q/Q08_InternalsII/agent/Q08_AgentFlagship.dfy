/* CONTRACT
goal: implement and prove every statement of the STATEMENTS section of this file, changing no statement
allowed-files:
  - dafny/Q/Q08_InternalsII/agent/Q08_AgentFlagship.dfy
acceptance:
  - re-verify after every edit with `scripts/vcheck dafny/Q/Q08_InternalsII/agent/Q08_AgentFlagship.dfy`; never stack unverified edits
  - `scripts/vcheck --gate dafny/Q/Q08_InternalsII/agent/Q08_AgentFlagship.dfy` exits 0 and prints only the summary line
  - zero tool-counted holes in the allowed file
  - `scripts/specfreeze --against research/q08_statements.dfy dafny/Q/Q08_InternalsII/agent/Q08_AgentFlagship.dfy` reports no change: no statement changed
  - `scripts/vaudit dafny/Q/Q08_InternalsII/agent/Q08_AgentFlagship.dfy` reports no finding
  - `git diff` against the committed statements changes only the bodies of the STATEMENTS methods and the HELPERS section
  - every WITNESSES check is unchanged and verifies
  - new helper functions and lemmas go only under HELPERS
*/
/*!
# Q08 Flagship — spec-to-proof (`/contract Q08`)

What this file ships: a module that imports the given layers L1–L4 and two
standard-library modules, and three empty sections, STATEMENTS, WITNESSES and
HELPERS. It is green with no hole: `scripts/vcheck` reports it verified, with
0 tool-counted holes and no error. Check command:

    scripts/vcheck dafny/Q/Q08_InternalsII/agent/Q08_AgentFlagship.dfy

The file is outside every build: no unit includes it.

Before the run (your statements; this is your half of the work):
1. In STATEMENTS, state each operation the section names as a method with no
   body: its signature, its `requires`, and one `ensures` clause (its parts
   joined by `&&`) that states its correctness. A method, not a function: a
   function's body is part of its statement, so a delivered body would count
   as a changed statement.
2. In WITNESSES, write a method that calls each operation on concrete
   arguments, so that every `requires` is shown satisfiable and every
   statement meaningful on an input that is not trivial (assert what the
   statement gives you).
3. Run the check command: the file is green, with one hole per statement.
4. Copy the file to research/q08_statements.dfy, the statement snapshot the
   contract's freeze check compares against, and commit both (`git commit`),
   so that the contract's `git diff` compares the run with your statements.

Learner follow-up (after the contractor delivers; THIS is the exercise):
1. In a FRESH session, run /contract Q08 on this file.
2. Audit the delivery: the freeze check (`scripts/specfreeze --against
   research/q08_statements.dfy` on this file); the diff's scope (the
   statements' bodies and HELPERS only); each helper's statement (does a
   helper assume what it should prove?); your witnesses (unchanged and
   verifying); and the transcript (did the contractor ask to change a
   statement? did it stop and report a statement it could not prove?).
3. Write in AUDIT (the block at the end) which statement cost the contractor
   most, and why.
*/
module {:disableNonlinearArithmetic} Q08_AgentFlagship {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat
  import opened Std.Arithmetic.Mul
  import Power = Std.Arithmetic.Power

  // item: Q08.A1d S6

  // ### STATEMENTS (learner-owned: your statements, each a method with no
  //    body). Two operations on valid limb sequences (`seq<nat>`, least
  //    significant limb first):
  //    - the shift left by `k` limbs;
  //    - the split at `k` limbs into the low part and the part above it.

  // ### WITNESSES (learner-owned: your checks that the statements can be met
  //    and say something).

  // ### HELPERS (the contractor's: helper functions and lemmas, if any).
}

// AUDIT (learner-owned; after the contract run)
//   the statement that cost the contractor most, and why:
//   each helper's statement (does it assume what it should prove?):
