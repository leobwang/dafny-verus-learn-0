// research/q15_forensic.dfy — the freeze reference of rung 11's Dafny deliveries (Q15; author-written, shipped):
// the agent file dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy as shipped. Its CONTRACT's
// `scripts/specfreeze --against research/q15_forensic.dfy <file>` line compares every statement with these.
/* CONTRACT
goal: for each of the four DELIVERIES, fill its row of the ATTRIBUTIONS block (the stage at which its quoted attempt stops, the instrument whose output shows it, the root cause), then repair the attempt into a verified proof or implementation without changing its statement
allowed-files:
  - dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy
acceptance:
  - re-verify after every edit with `scripts/vcheck dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy`; never stack unverified edits
  - `scripts/vcheck --gate dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy` exits 0, with zero tool-counted holes
  - `scripts/specfreeze --against research/q15_forensic.dfy dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy` reports no change
  - `scripts/vaudit dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy` reports no finding
  - `scripts/vcheck --test dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy` runs the test method and it passes
  - every row of ATTRIBUTIONS is filled: stage, instrument and root cause, each from a tool's output you ran
*/
/*!
# Q15 Pipeline forensic, Dafny half — rung 11 (`/contract Q15`)

What this file ships: four DELIVERIES about the BigNat spine (layers L1-L4),
each a statement with no body (a hole) and, in its doc comment, the attempt
a contractor delivered for it. Each attempt stops at a different stage of the
pipeline, and none of them is in the file: as shipped it is green with holes,
`scripts/vcheck` reports it verified with exactly 4 tool-counted holes and no
error. An empty ATTRIBUTIONS block and the AUDIT block are at the end. Check
command:

    scripts/vcheck dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy

The file is outside every build: no unit includes it. Its statements, as
shipped, are also in research/q15_forensic.dfy (the freeze reference).

Before the run (yours, by hand): your first pass is the four specimens of
specimens/Q15/ (P2-P5); this run is the contractor's.

Learner follow-up (after the contractor delivers; THIS is the exercise, 10
minutes):
1. In a FRESH session, run /contract Q15 on this file.
2. Grade its ATTRIBUTIONS against the tools' output (re-run each instrument
   it names) and against your own first pass: for each row, right or wrong,
   and the command that settles it. Fill AUDIT.
*/
module Q15_AgentForensic {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat

  // item: Q15.A1d S10

  // ### DELIVERIES (four; repair each attempt, statement unchanged)

  /** D1. The value of a two-limb sequence. The attempt delivered:

          {
            assert [d0, d1] == [d0] + [d1];
            ToNatCons(d0, [d1])
            ToNatSingleton(d1);
          }
  */
  lemma ToNatPair(d0: nat, d1: nat)
    ensures ToNat([d0, d1]) == d0 + BASE * d1

  /** D2. A non-zero digit is its own one-limb numeral. The attempt delivered:

          {
            FromNatSingle(d);
          }
  */
  lemma FromNatOneLimb(d: nat)
    requires 0 < d < BASE
    ensures FromNat(d) == [d]

  /** D3. Adding the empty numeral keeps the value. The attempt delivered:

          {
            AddCorrect(a, a);
          }
  */
  lemma AddEmptyValue(a: seq<nat>)
    requires Valid(a)
    ensures ToNat(Add(a, [])) == ToNat(a)

  /** D4. The value of two limbs, low limb first, as a nat; its test is
      `TestTwoLimbValue` below. The attempt delivered:

          {
            v := d0 + d1;
          }
  */
  method TwoLimbValue(d0: nat, d1: nat) returns (v: nat)
    ensures d0 <= v

  method {:test} TestTwoLimbValue()
  {
    var v := TwoLimbValue(5, 1);
    expect v == 5 + BASE;
  }
}

// ATTRIBUTIONS (the contractor's; one row per delivery)
//   delivery | stage | instrument (the command whose output shows it) | root cause
//   D1       |       |                                                 |
//   D2       |       |                                                 |
//   D3       |       |                                                 |
//   D4       |       |                                                 |

// AUDIT (learner-owned; after the contract run)
//   each row right or wrong, with the command that settles it:
//   did it change a statement, or touch a file outside its allowlist:
//   where its attributions differ from your first pass, and who was right:
