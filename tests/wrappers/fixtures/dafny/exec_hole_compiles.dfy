// Wrapper fixture (tests/wrappers): exec holes that still compile (Δ2; DV0-REPORT
// §8 item 7). Each `assume false;` body is one counted hole (W-D03); under the
// learner loop's --allow-warnings the unit compiles, unrelated tests run, and a
// test that reaches a hole fails at run time.
module Fx_ExecHoles {
  method Inc(x: int) returns (y: int)
    ensures y == x + 1
  {
    assume false;
  }

  function Twice(x: int): int
    ensures Twice(x) == 2 * x
  {
    assume false; 0
  }

  lemma ProofHole(x: int)
    ensures x + 0 == x

  method {:test} UsesInc() {
    var r := Inc(1);
    expect r == 2;
  }

  method {:test} UsesTwice() {
    expect Twice(2) == 4;
  }

  method {:test} Unrelated() {
    expect 1 + 1 == 2;
  }
}
