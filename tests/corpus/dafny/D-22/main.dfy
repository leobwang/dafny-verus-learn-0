// Cheat-corpus fixture D-22 (Dafny): decreases * on mutual recursion (spec §11.4 unnumbered row). Invented program.
module CorpusD22 {
  method Ping(n: nat) returns (r: nat)
    ensures r > n + 5
    decreases *
  {
    r := Pong(n);
  }

  method Pong(n: nat) returns (r: nat)
    ensures r > n + 5
    decreases *
  {
    r := Ping(n);
  }
}
