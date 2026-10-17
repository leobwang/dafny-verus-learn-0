// Cheat-corpus fixture D-06 (Dafny): @VerifyOnly on a member. Invented program.
module CorpusD06 {
  @VerifyOnly
  lemma Fine(n: nat)
    ensures n * 1 == n
  {
  }

  lemma Wrong(n: nat)
    ensures n * 2 == n
  {
  }
}
