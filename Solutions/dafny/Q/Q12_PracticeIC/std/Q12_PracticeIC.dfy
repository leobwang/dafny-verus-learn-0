/*!
# Q12 — Practice I-C + Lab 1: the practice block (Reference Solution)

Hole-free reference for `dafny/Q/Q12_PracticeIC/std/Q12_PracticeIC.dfy`
(author-only; never learner-visible). Same module, imports, names,
statements, item markers and order as the exercise file; H3's hole is
filled. The verdict answers of the stage specimens are in
`Solutions/slots/Q12.slots`, their hashes in `expected/Q12.pins`.

The file is silent: `scripts/vcheck --ref` on its unit prints only the
summary line. The module imports L1-L4 only and freezes its import list
(`// specfreeze: frozen-imports`, QPLAN §30 Q62): layer L5's `NormalizeTrim`
closes H3 in one call (the first `cfree:` line), and a module that does not
import L5 cannot name it, qualified or not (the second). A fuel attribute
on the lemma (`{:fuel Normalize, 4}`) with an empty body also verifies: that
is the item's construct (`uses: fuel`), an accepted answer, not a shortcut.
*/
module Q12_PracticeIC {
  // specfreeze: frozen-imports
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import opened QG_L4_BigNat

  // ===========================================================================
  // The prediction block. Q12's six predictions are the stage specimens
  // specimens/Q12/P1d.dfy.specimen … P6v.rs.specimen; commit every one of them
  // before you read past this block, and record the first tries:
  //     scripts/firsttry.sh Q12 --check
  // ===========================================================================

  // ===========================================================================
  // Holes
  // ===========================================================================

  // item: Q12.H3d S11
  // uses: fuel
  // cfree: { NormalizeTrim([5, 0, 0, 0], 1); }
  // cfree: { QG_L5_BigNat.NormalizeTrim([5, 0, 0, 0], 1); }
  /** **H3.** A literal, normalized. `Normalize` (layer L2) strips the most
      significant zero limbs, one call per limb. Prove the instance below
      from the definitions: unfold just enough of it. */
  lemma NormalizeLiteral()
    ensures Normalize([5, 0, 0, 0]) == [5]
  {
    assert [5, 0, 0, 0][..3] == [5, 0, 0];
    assert [5, 0, 0][..2] == [5, 0];
    assert [5, 0][..1] == [5];
  }
}
