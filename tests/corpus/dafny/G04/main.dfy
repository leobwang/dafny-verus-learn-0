// Cheat-corpus fixture G04 (Dafny): a bodyless function used as an oracle in a spec. Invented program.
module CorpusG04 {
  function Score(x: int): int

  method Compute(x: int) returns (r: int)
    ensures r == Score(x)
  {
    r := Score(x);
  }
}
