/*!
# Q05 — value-prediction checks (given-only check unit)

This file holds Q05's Dafny value prediction (P8d). It imports only the given
spine layers L1–L3 (and one module of the standard library, which L3 needs),
so it compiles and runs while the exercise files still have holes. Fill the
slot, record the first try with `scripts/firsttry.sh Q05 --check`, and only
then enable it (the `// SLOT: ` prefix removed, so the `expect` line is live).
*/
module Q05_Checks {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat
  import opened QG_L3_BigNat
  import Std.Wrappers

  // item: Q05.P8d S7 value
  /** **P8d.** How many limbs does `AddLimb` (layer L2) give when it adds 1 to
      the two-limb numeral whose limbs are both `BASE - 1`
      (`18446744073709551615`)?
      Answer form: numeral */
  @Test
  method P8d() {
    // SLOT: expect |AddLimb([18446744073709551615, 18446744073709551615], 1)| == ???;
  }
}
