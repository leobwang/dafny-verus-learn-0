// Cheat-corpus fixture D-07 (Dafny): assert {:only}. Invented program.
module CorpusD07 {
  lemma Wrong(n: nat)
    ensures n + 1 == n
  {
    assert n + 1 == n;
    assert {:only} n + 0 == n;
  }
}
