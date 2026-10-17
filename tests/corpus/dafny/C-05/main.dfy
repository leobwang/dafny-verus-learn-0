// Cheat-corpus fixture C-05 (Dafny): healthy control. Invented program.
module CorpusC05 {
  function SumTo(n: nat): nat
  {
    if n == 0 then 0 else n + SumTo(n - 1)
  } by method {
    var acc := 0;
    var i := 0;
    while i < n
      invariant 0 <= i <= n
      invariant acc == SumTo(i)
    {
      i := i + 1;
      acc := acc + i;
    }
    return acc;
  }
}
