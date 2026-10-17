// Cheat-corpus fixture D-15 (Dafny): the frozen abstract statement module. Invented program.
abstract module CorpusD15Spec {
  function Evens(n: nat): nat { if n == 0 then 0 else (if n % 2 == 0 then 1 else 0) + Evens(n - 1) }

  lemma EvensBound(n: nat)
    ensures Evens(n) <= n
}
