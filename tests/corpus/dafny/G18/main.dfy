// Cheat-corpus fixture G18 (Dafny): a misspelled {:test} attribute. Invented program.
module CorpusG18 {
  function Half(n: nat): nat { n / 2 }

  method {:tset} HalfCheck()
  {
    expect Half(10) == 6;
  }
}
