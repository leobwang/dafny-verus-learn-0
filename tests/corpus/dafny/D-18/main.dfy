// Cheat-corpus fixture D-18 (Dafny): {:extern} with a spec (spec §11.4 unnumbered row). Invented program.
module CorpusD18 {
  method {:extern} Pick(n: nat) returns (r: nat)
    ensures r > n

  method Use(n: nat) returns (r: nat)
    ensures r > n
  {
    r := Pick(n);
  }
}
