// Cheat-corpus fixture G12 (Dafny): satisfiability witness: a test call with concrete arguments. Invented program.
module CorpusG12 {
  lemma Squeeze(a: int, b: int)
    requires a < b && b < a
    ensures a == b + 7
  {
  }

  method {:test} Witness() {
    Squeeze(1, 2);
  }
}
