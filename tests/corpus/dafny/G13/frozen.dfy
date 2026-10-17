// Cheat-corpus fixture G13 (Dafny): the frozen statement as shipped (the body is the hole). Invented program.
module CorpusG13 {
  function Abs(x: int): int { if x < 0 then -x else x }

  method AbsImpl(x: int) returns (r: int)
    ensures r == Abs(x)
}
