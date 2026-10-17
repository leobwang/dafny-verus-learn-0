/*!
# Q04 — value-prediction checks (given-only check unit)

This file holds Q04's Dafny value prediction (P2). It imports only the given
spine layers L1–L3, so it compiles and runs while the exercise files still
have holes. Fill the slot, record the first try with
`scripts/firsttry.sh Q04 --check`, and only then enable it (the `// SLOT: `
prefix removed, so the `expect` line is live).
*/
module Q04_Checks {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat

  // item: Q04.P2d S1 value
  /** **P2.** What does `Cmp` (layer L3) return for the limb sequences
      `[5, 1]` and `[7, 0, 0]`?
      Answer form: numeral */
  @Test
  method P2d() {
    // SLOT: expect Cmp([5, 1], [7, 0, 0]) == ???;
  }
}
