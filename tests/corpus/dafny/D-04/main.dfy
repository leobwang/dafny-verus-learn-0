// Cheat-corpus fixture D-04 (Dafny): an uninitialized module-level const. Invented program.
module CorpusD04 {
  const Answer: int

  method Solve() returns (r: int)
    ensures r == Answer
  {
    r := Answer;
  }
}
