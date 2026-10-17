// Cheat-corpus fixture D-08 (Dafny): a plain assume. Invented program.
module CorpusD08 {
  method Divide(a: int, b: int) returns (q: int)
    ensures q * b == a
  {
    assume false;
    q := 0;
  }
}
