/*!
# Q03 — value-prediction checks (Reference Solution)

Hole-free reference for `dafny/checks/Q03_checks.dfy` (author-only): the
value slot enabled with its answer. `FromNat(BASE)` is `[0] + FromNat(1)`,
that is `[0, 1]`: two limbs (0 + BASE * 1). Silent under the gate.
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
    expect |FromNat(18446744073709551616)| == 2;
  }
}
