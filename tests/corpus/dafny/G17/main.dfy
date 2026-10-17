// Cheat-corpus fixture G17 (Dafny): Boogie pass-through attributes. Invented program.
module CorpusG17 {
  method {:selective_checking} Check(x: int)
  {
    assert x == x + 1;
    assert {:start_checking_here} true;
    assert x * 0 == 0;
  }
}
