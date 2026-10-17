// Cheat-corpus fixture C-04 (Dafny): healthy control: refines the frozen module, with a proof. Invented program.
module CorpusC04 refines CorpusC04Spec {
  lemma CountBound ...
  {
    if |s| > 0 {
      CountBound(s[1..]);
    }
  }
}
