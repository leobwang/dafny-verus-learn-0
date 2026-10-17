// Cheat-corpus fixture D-19 (Dafny): {:extern} {:axiom} with a spec (spec §11.4 unnumbered row). Invented program.
module CorpusD19 {
  method {:extern} {:axiom} Next(n: nat) returns (r: nat)
    ensures r == n + 1 && r == n + 2

  method Use(n: nat) returns (r: nat)
    ensures r == n + 1
  {
    r := Next(n);
  }
}
