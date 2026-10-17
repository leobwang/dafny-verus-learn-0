/*!
# Q02 — value checks (Exercises: a given-only check unit)

This file holds Q02's value prediction (P9d). It imports the given spine layers and no
exercise file, so the holes of the exercise files never block it from compiling and
running. Nothing here is a hole; the one slot is a prediction.

How to work it: predict before you run anything. Replace `???` with your literal, record
the first try with `scripts/firsttry.sh Q02 --check`, and only then enable the check by
deleting `SLOT: ` from its line. `scripts/pins.py Q02` then runs it (compiled, as a test).
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
    // SLOT: expect |Normalize([0, 5, 0, 0])| == ???;
  }
}
