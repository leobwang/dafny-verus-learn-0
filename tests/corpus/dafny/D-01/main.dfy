// Cheat-corpus fixture D-01 (Dafny): a fabricated lemma {:axiom}. Invented program.
module CorpusD01 {
  lemma {:axiom} SquareStep(n: nat)
    ensures n * n == n + 1

  lemma Consequence()
    ensures false
  {
    SquareStep(0);
  }
}
