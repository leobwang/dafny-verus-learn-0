// Cheat-corpus fixture D-23 (Dafny): a partial method via decreases * (spec §11.4 unnumbered row). Invented program.
module CorpusD23 {
  method Search(lo: int, hi: int) returns (x: int)
    ensures lo <= x < hi
    decreases *
  {
    x := lo;
    while !(lo <= x < hi)
      decreases *
    {
      x := x + 1;
    }
  }
}
