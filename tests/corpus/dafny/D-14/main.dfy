// Cheat-corpus fixture D-14 (Dafny): the candidate: a refining lemma that adds a requires. Invented program.
module CorpusD14 refines CorpusD14Spec {
  lemma HalfLe(n: nat)
    requires n > 100
  {
  }
}
