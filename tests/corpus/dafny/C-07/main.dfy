// Cheat-corpus fixture C-07 (Dafny): healthy control. Invented program.
module CorpusC07 {
  lemma Between(a: int, b: int, c: int)
    requires a < b && b < c
    ensures a + 1 < c
  {
  }
}
