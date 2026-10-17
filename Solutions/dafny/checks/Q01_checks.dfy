/*!
# Q01 — value checks (Reference Solution)

Hole-free reference for `dafny/checks/Q01_checks.dfy`, Q01's given-only check unit: it
imports only the given layer L1, so a hole in the exercise file never blocks it. Its
value slot is enabled here with the captured value (`dafny test --target py` through
`scripts/pins.py --ref`). Silent: nothing here prints.
*/
module Q01_Checks {
  import opened QG_L1_BigNat

  // item: Q01.P5d S1 value
  /** **P5d.** What is the value of the two-limb number `[3, 1]` (least significant limb
      first)? The check is compiled and run, not proved.
      Answer form: numeral
      The value: 3 + 1 * 2^64. */
  @Test
  method P5d()
  {
    expect ToNat([3, 1]) == 18446744073709551619;
  }
}
