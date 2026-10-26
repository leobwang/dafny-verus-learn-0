/*! R12 given-only source-span observation: native lines are one-based. */
module R12_SpanObservation {
  // item: R12.P1d value
  // Answer form: numeral.
  @Test
  method SecondDeclarationR12()
  {
    var spans: seq<seq<nat>> := [[7, 12], [15, 29]];
    var line := spans[1][0];
    // SLOT: expect line == ???;
  }
}
