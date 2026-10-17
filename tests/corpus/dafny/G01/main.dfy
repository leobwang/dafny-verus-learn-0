// Cheat-corpus fixture G01 (Dafny): an assumption marked {:axiom}. Invented program.
module CorpusG01 {
  function Twice(n: nat): nat { 2 * n }

  lemma TwiceIsBig(n: nat)
    ensures Twice(n) >= n + 10
  {
    assume {:axiom} Twice(n) >= n + 10;
  }
}
