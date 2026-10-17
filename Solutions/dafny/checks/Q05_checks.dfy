/*!
# Q05 — value-prediction checks (Reference Solution)

Hole-free reference for `dafny/checks/Q05_checks.dfy` (author-only): the
value slot enabled with its answer. `AddLimb([BASE - 1, BASE - 1], 1)` carries
out of both limbs: `[0] + AddLimb([BASE - 1], 1)`, then `[0] + AddLimb([], 1)`,
which is `[1]`; so the result is `[0, 0, 1]`, three limbs. Silent under the
gate.
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
    expect |AddLimb([18446744073709551615, 18446744073709551615], 1)| == 3;
  }
}
