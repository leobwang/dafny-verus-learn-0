// Cheat-corpus fixture C-03 (Dafny): healthy control. Invented program.
module CorpusC03 {
  function Clamp(x: int, lo: int, hi: int): int
    requires lo <= hi
  {
    if x < lo then lo else if x > hi then hi else x
  }

  method {:test} ClampCases() {
    expect Clamp(5, 0, 3) == 3;
    expect Clamp(-2, 0, 3) == 0;
    expect Clamp(2, 0, 3) == 2;
  }
}
