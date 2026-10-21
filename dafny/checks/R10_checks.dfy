/*! R10 provided-operation value prediction (given-only check unit). */
module R10_PredictNormal {
  import opened RG_A1_Re
  import opened RG_A4_Norm

  // item: R10.P1d value
  // Answer form: numeral.
  @Test
  method SmartCountR10()
  {
    var result := MkCat(Eps, Chr('k'));
    var value := NodeCount(result);
    // SLOT: expect value == ???;
  }
}
