// Cheat-corpus fixture C-02 (Dafny): the conclusion swapped for false. Invented program.
module CorpusC02 {
  function Pow2(n: nat): nat { if n == 0 then 1 else 2 * Pow2(n - 1) }

  lemma Pow2Grows(n: nat)
    ensures false
  {
    if n > 0 {
      Pow2Grows(n - 1);
    }
  }
}
