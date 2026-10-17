// Wrapper fixture (tests/wrappers): a bodyless compiled method stops every test (Δ2).
module Fx_ExecHole {
  method Inc(x: int) returns (y: int)
    ensures y == x + 1

  method {:test} UsesInc() {
    var r := Inc(1);
    expect r == 2;
  }
}
