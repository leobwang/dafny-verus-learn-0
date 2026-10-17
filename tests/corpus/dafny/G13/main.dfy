// Cheat-corpus fixture G13 (Dafny): the candidate: a weakened ensures, trivially implemented. Invented program.
module CorpusG13 {
  function Abs(x: int): int { if x < 0 then -x else x }

  method AbsImpl(x: int) returns (r: int)
    ensures r >= 0
  {
    r := 0;
  }
}
