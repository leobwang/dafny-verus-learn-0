// Cheat-corpus fixture D-14 (Dafny): the frozen abstract statement module. Invented program.
abstract module CorpusD14Spec {
  function Half(n: nat): nat { n / 2 }

  lemma HalfLe(n: nat)
    ensures Half(n) <= n
}
