/*!
# Q01 — value checks (given-only check unit)

Q01's value prediction P5d. This unit imports only the given layer L1, never an
exercise file, so a hole in the exercise file never blocks it. Its checks are compiled
and run, not proved: `scripts/firsttry.sh Q01 --check` enables your filled slot in a
scratch copy, runs it once and records the first try.

How to answer: replace `???` in the SLOT line with your prediction and keep the line a
comment; then run `scripts/firsttry.sh Q01 --check`. Do not run the check yourself
first: its failure message would show the value.
*/
module Q01_Checks {
  import opened QG_L1_BigNat

  // item: Q01.P5d S1 value
  /** **P5d.** What is the value of the two-limb number `[3, 1]` (least significant limb
      first)? The check is compiled and run, not proved.
      Answer form: numeral */
  @Test
  method P5d()
  {
    // SLOT: expect ToNat([3, 1]) == ???;
  }
}
