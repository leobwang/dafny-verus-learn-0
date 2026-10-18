/*! R07 Reference Solution. */
module R07_Checks {
  import opened RG_A2_Deriv
  import S = Std.Collections.Seq

  // item: R07.P1d value
  // Answer form: String literal.
  @Test method ClassSampleValueR07() {
    var cc := ClassRange('a', 'c');
    var sample := "cab?";
    expect S.Filter(c => ClassMember(cc, c), sample) == "cab";
  }
}
