// Cheat-corpus fixture G03 (Dafny): a bodyless member of an abstract module. Invented program.
abstract module CorpusG03 {
  function Square(n: int): int { n * n }

  lemma SquareNegative(n: int)
    ensures Square(n) < 0

  lemma Consequence(n: int)
    ensures n * n < 0
  {
    SquareNegative(n);
  }
}
