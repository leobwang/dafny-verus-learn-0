// Cheat-corpus fixture D-15 (Dafny): the candidate: a detached, weaker restatement. Invented program.
module CorpusD15 {
  function Evens(n: nat): nat { if n == 0 then 0 else (if n % 2 == 0 then 1 else 0) + Evens(n - 1) }

  lemma EvensBound(n: nat)
    ensures Evens(n) >= 0
  {
  }
}
