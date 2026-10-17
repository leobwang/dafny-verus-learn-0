// Cheat-corpus fixture G02 (Dafny): a bodyless helper lemma with an ensures. Invented program.
module CorpusG02 {
  function Sum(n: nat): nat { if n == 0 then 0 else n + Sum(n - 1) }

  lemma SumFormula(n: nat)
    ensures 2 * Sum(n) == n * (n + 1)

  lemma SumTwice(n: nat)
    ensures Sum(n) * 2 == n * n + n
  {
    SumFormula(n);
  }
}
