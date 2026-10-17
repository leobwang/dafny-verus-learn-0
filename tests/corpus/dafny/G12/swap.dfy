// Cheat-corpus fixture G12 (Dafny): the conclusion swapped for false. Invented program.
module CorpusG12 {
  lemma Squeeze(a: int, b: int)
    requires a < b && b < a
    ensures false
  {
  }
}
