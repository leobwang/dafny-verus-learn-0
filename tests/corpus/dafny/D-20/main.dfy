// Cheat-corpus fixture D-20 (Dafny): decreases * on a method (spec §11.4 unnumbered row). Invented program.
module CorpusD20 {
  method Spin(n: int) returns (r: int)
    ensures r == n + 1 && r == n + 2
    decreases *
  {
    r := Spin(n);
  }
}
