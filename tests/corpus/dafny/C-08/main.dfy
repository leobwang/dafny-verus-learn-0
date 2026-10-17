// Cheat-corpus fixture C-08 (Dafny): healthy control. Invented program.
module CorpusC08 {
  function Min3(a: int, b: int, c: int): int {
    if a <= b && a <= c then a else if b <= c then b else c
  }

  // the statement is the frozen one; only the body is new
  method Min3Impl(a: int, b: int, c: int) returns (m: int)
    ensures m == Min3(a, b, c)
  {
    m := a;
    if b < m {
      m := b;
    }
    if c < m {
      m := c;
    }
  }
}
