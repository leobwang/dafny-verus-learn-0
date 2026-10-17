// Cheat-corpus fixture G12 (Dafny): a vacuous (contradictory) requires. Invented program.
module CorpusG12 {
  lemma Squeeze(a: int, b: int)
    requires a < b && b < a
    ensures a == b + 7
  {
  }
}
