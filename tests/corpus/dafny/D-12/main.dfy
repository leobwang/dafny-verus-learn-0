// Cheat-corpus fixture D-12 (Dafny): expect outside a test, with a message. Invented program.
module CorpusD12 {
  function Max(a: int, b: int): int { if a >= b then a else b }

  method Pick(a: int, b: int) returns (m: int)
    ensures m == Max(a, b)
  {
    m := a;
    expect m == Max(a, b), "pick is the max";
  }

  method Main() {
    var m := Pick(3, 4);
    print m, "\n";
  }
}
