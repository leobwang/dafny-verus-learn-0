// Cheat-corpus fixture G05 (Dafny): {:verify false} on a declaration. Invented program.
module CorpusG05 {
  lemma {:verify false} Wrong(n: nat)
    ensures n * 2 == n + 3
  {
  }

  lemma Fine(n: nat)
    ensures n * 2 == n + n
  {
  }
}
