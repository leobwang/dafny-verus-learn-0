/*!
# Q02 — value checks (Reference Solution)

Hole-free reference for `dafny/checks/Q02_checks.dfy` (author-only): the value slot is
filled and enabled. `Normalize` strips the most significant zero limbs only, so the zero
at position 0 stays: the result is `[0, 5]`. Pinned by `scripts/pins.py --ref` (the test
runs compiled; it must pass). Silent under `scripts/vcheck --ref`.
*/
module Q02_Checks {
  import opened QG_L1_BigNat
  import opened QG_L2_BigNat

  // item: Q02.P9d S1 value
  /** **P9d.** `Normalize` is QG_L2_BigNat's. How many limbs does `Normalize([0, 5, 0, 0])`
      keep? Predict the number, then fill the slot.
      Answer form: numeral */
  @Test
  method P9d() {
    expect |Normalize([0, 5, 0, 0])| == 2;
  }
}
