// Cheat-corpus fixture G09 (Dafny): an include of a non-root file. Invented program.
include "helper.dfy"

module CorpusG09 {
  import CorpusG09Helper

  lemma Uses(n: nat)
    ensures n + 1 == n
  {
    CorpusG09Helper.Shift(n);
  }
}
