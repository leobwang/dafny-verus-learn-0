// Cheat-corpus fixture D-16 (Dafny): the candidate: the spec function's definition changed. Invented program.
module CorpusD16 {
  function Triple(x: int): int { 0 }

  method TripleImpl(x: int) returns (r: int)
    ensures r == Triple(x)
  {
    r := 0;
  }
}
