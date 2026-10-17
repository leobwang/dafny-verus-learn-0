/*!
# Q03 — value-prediction checks (given-only check unit)

This file holds Q03's Dafny value prediction (P9). It imports only the given
spine layers L1 and L2, so it compiles and runs while the exercise file still
has holes. Fill the slot, record the first try with
`scripts/firsttry.sh Q03 --check`, and only then enable it (the `// SLOT: `
prefix removed, so the `expect` line is live).
*/
module Q03_Checks {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat

  // item: Q03.P9d S7 value
  /** **P9.** How many limbs does `FromNat` (layer L2) give for the number
      2^64, that is `BASE`?
      Answer form: numeral */
  @Test
  method P9d() {
    // SLOT: expect |FromNat(18446744073709551616)| == ???;
  }
}
