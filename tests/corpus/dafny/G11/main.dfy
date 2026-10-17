// Cheat-corpus fixture G11 (Dafny): expect outside a test method. Invented program.
module CorpusG11 {
  function Fib(n: nat): nat { if n < 2 then n else Fib(n - 1) + Fib(n - 2) }

  method FastFib(n: nat) returns (r: nat)
    ensures r == Fib(n)
  {
    var a, b := 0, 1;
    var i := 0;
    while i < n
      invariant 0 <= i <= n
    {
      a, b := b, a + b;
      i := i + 1;
    }
    r := a;
    expect r == Fib(n);
  }
}
