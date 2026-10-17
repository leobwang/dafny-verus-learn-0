// Cheat-corpus fixture D-03 (Dafny): a bodyless trait member. Invented program.
module CorpusD03 {
  trait Shape {
    function Area(): int

    lemma AreaPositive()
      ensures Area() > 0
  }

  method Report(s: Shape) returns (a: int)
    ensures a > 0
  {
    a := s.Area();
    s.AreaPositive();
  }
}
