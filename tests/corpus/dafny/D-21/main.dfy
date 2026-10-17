// Cheat-corpus fixture D-21 (Dafny): decreases * on a loop (spec §11.4 unnumbered row). Invented program.
module CorpusD21 {
  method Find(a: array<int>, key: int) returns (i: nat)
    ensures i < a.Length && a[i] == key
    decreases *
  {
    i := 0;
    while true
      decreases *
    {
    }
  }
}
