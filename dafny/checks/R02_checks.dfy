/*! R02 given-only value prediction. Fill the slot and record its first try before running it. */
module R02_Checks {
  import opened RG_A1_Re
  // item: R02.P5d value
  // Answer form: bool literal
  @Test method NullableValue() {
    // SLOT: expect Nullable(Cat(Star(Empty), Alt(Eps, Chr('a')))) == ???;
  }
}
