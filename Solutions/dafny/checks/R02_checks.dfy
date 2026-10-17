/*! R02 — Reference Solution. Complete, silent twin with the prediction enabled. */
module R02_Checks {
  import opened RG_A1_Re
  // item: R02.P5d value
  // Answer form: bool literal
  @Test method NullableValue() {
    expect Nullable(Cat(Star(Empty), Alt(Eps, Chr('a')))) == true;
  }
}
