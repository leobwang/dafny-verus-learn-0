// Wrapper fixture (tests/wrappers): compiled tests (Δ43), one misspelled attribute.
module Fx_Tests {
  function Double(x: int): int { 2 * x }

  method {:test} PassOne() {
    expect Double(2) == 4;
  }

  @Test
  method FailOne() {
    expect Double(2) == 5, "two doubled";
  }

  method {:test} PassTwo() {
    expect Double(0) == 0;
  }

  method {:tset} NeverRuns() {
    expect Double(1) == 3;
  }
}
