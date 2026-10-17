/*!
# Q04 — value-prediction checks (Reference Solution)

Hole-free reference for `dafny/checks/Q04_checks.dfy` (author-only): the
value slot enabled with its answer. `Cmp` recurses on the tails first and
lets the heads decide only when the tails compare equal, so the most
significant limbs decide: `[5, 1]` against `[7, 0, 0]` compares the top
limbs 0 (a missing limb) and 0, then 1 and 0, so the result is 1, whatever
the low limbs 5 and 7 say. Silent under the gate.
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
    expect Cmp([5, 1], [7, 0, 0]) == 1;
  }
}
