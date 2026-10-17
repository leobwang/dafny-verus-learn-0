// Cheat-corpus fixture D-11 (Dafny): a bodyless lemma with only a requires. Invented program.
module CorpusD11 {
  lemma Helper(n: nat)
    requires n > 3

  lemma Main(n: nat)
    requires n > 3
    ensures n + n > 6
  {
    Helper(n);
  }
}
