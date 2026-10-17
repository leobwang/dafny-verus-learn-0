// Cheat-corpus fixture D-09 (Dafny): a bodyless lemma with two ensures. Invented program.
module CorpusD09 {
  lemma Bounds(n: nat)
    ensures n >= 1
    ensures n < 1000

  lemma Positive(n: nat)
    ensures n > 0
  {
    Bounds(n);
  }
}
