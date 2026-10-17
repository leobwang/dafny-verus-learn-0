// Cheat-corpus fixture D-10 (Dafny): a bodyless method with no ensures. Invented program.
module CorpusD10 {
  method Shuffle(a: array<int>)
    modifies a

  method Caller(a: array<int>)
    modifies a
  {
    Shuffle(a);
  }
}
