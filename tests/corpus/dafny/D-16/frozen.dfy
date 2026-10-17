// Cheat-corpus fixture D-16 (Dafny): the frozen statement as shipped (the body is the hole). Invented program.
module CorpusD16 {
  function Triple(x: int): int { x * 3 }

  method TripleImpl(x: int) returns (r: int)
    ensures r == Triple(x)
}
