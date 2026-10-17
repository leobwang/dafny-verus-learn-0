/*! R01 — Reference Solution (author-only).
Complete, silent twin; declarations and item order match the learner source.
All prediction switches and supplied checks are enabled. */
module R01_Checks {
  // item: R01.P5d value
  /** What integer is (-7) / 2 in compiled Dafny?
      Answer form: numeral */
  @Test
  method P5d() {
    expect (-7) / 2 == -4;
  }
}
