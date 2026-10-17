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
# Q15 Pipeline forensic, Dafny half — rung 11 (Reference Solution)

Hole-free reference for `dafny/Q/Q15_PracticeIIC/agent/Q15_AgentForensic.dfy`
(author-only; never learner-visible): the delivery a correct contract run
ends with. Same CONTRACT, module, imports, statements and order; each
attempt repaired, ATTRIBUTIONS filled from the captured tool output
(Solutions/plans/Q15-code-notes.md §6).
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
  {
    assert [d0, d1] == [d0] + [d1];
    ToNatCons(d0, [d1]);
    ToNatSingleton(d1);
  }

  /** D2. A non-zero digit is its own one-limb numeral. The attempt delivered:

          {
            FromNatSingle(d);
          }
  */
  lemma FromNatOneLimb(d: nat)
    requires 0 < d < BASE
    ensures FromNat(d) == [d]
  {
    assert d / BASE == 0 && d % BASE == d;
  }

  /** D3. Adding the empty numeral keeps the value. The attempt delivered:

          {
            AddCorrect(a, a);
          }
  */
  lemma AddEmptyValue(a: seq<nat>)
    requires Valid(a)
    ensures ToNat(Add(a, [])) == ToNat(a)
  {
    AddCorrect(a, []);
  }

  /** D4. The value of two limbs, low limb first, as a nat; its test is
      `TestTwoLimbValue` below. The attempt delivered:

          {
            v := d0 + d1;
          }
  */
  method TwoLimbValue(d0: nat, d1: nat) returns (v: nat)
    ensures d0 <= v
  {
    v := d0 + BASE * d1;
  }

  method {:test} TestTwoLimbValue()
  {
    var v := TwoLimbValue(5, 1);
    expect v == 5 + BASE;
  }
}

// ATTRIBUTIONS (the contractor's; one row per delivery)
//   delivery | stage | instrument (the command whose output shows it) | root cause
//   D1       | parse   | scripts/vcheck <file>: `missing semicolon at end of statement`, stage parse | the second call lacks its `;`
//   D2       | resolve | scripts/vcheck <file>: `unresolved identifier: FromNatSingle`, stage resolve | it calls a lemma no layer declares; the definition unfolds by itself
//   D3       | verify  | scripts/vcheck <file>: `a postcondition could not be proved` | it applies AddCorrect to (a, a), which says nothing about Add(a, [])
//   D4       | test    | scripts/vcheck --test <file>: `FAILED …TestTwoLimbValue`, an expectation violation | the weak ensures admits d0 + d1; the test asks for d0 + BASE * d1

// AUDIT (learner-owned; after the contract run)
//   each row right or wrong, with the command that settles it:
//   did it change a statement, or touch a file outside its allowlist:
//   where its attributions differ from your first pass, and who was right:
