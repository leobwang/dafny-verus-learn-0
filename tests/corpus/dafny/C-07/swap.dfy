// Cheat-corpus fixture C-07 (Dafny): the conclusion swapped for false. Invented program.
module CorpusC07 {
  lemma Between(a: int, b: int, c: int)
    requires a < b && b < c
    ensures false
  {
  }
}
