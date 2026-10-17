// Wrapper fixture (tests/wrappers): compiled tests that print (Δ43). A test's
// own output lands between its "Name: " prefix and its PASSED/FAILED status.
module Fx_PrintTests {
  function Double(x: int): int { 2 * x }

  method {:test} PrintsThenPasses() {
    print "double 2 = ", Double(2), "\n";
    expect Double(2) == 4;
  }

  @Test
  method PrintsThenFails() {
    print "checking double 2\n";
    expect Double(2) == 5, "two doubled";
  }

  method {:test} PrintsNoNewline() {
    print "no newline";
    expect Double(1) == 2;
  }

  method {:test} Quiet() {
    expect Double(0) == 0;
  }
}
