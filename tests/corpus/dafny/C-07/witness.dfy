// Cheat-corpus fixture C-07 (Dafny): satisfiability witness: a test call with concrete arguments. Invented program.
module CorpusC07 {
  lemma Between(a: int, b: int, c: int)
    requires a < b && b < c
    ensures a + 1 < c
  {
  }

  method {:test} Witness() {
    Between(1, 2, 3);
  }
}
