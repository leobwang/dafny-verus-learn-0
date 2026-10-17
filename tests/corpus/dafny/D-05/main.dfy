// Cheat-corpus fixture D-05 (Dafny): {:only} on a member. Invented program.
module CorpusD05 {
  lemma {:only} Fine(n: nat)
    ensures n + 0 == n
  {
  }

  lemma Wrong(n: nat)
    ensures n + 1 == n
  {
  }
}
