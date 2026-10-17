// Cheat-corpus fixture C-08 (Dafny): the frozen statement as shipped (the body is the hole). Invented program.
module CorpusC08 {
  function Min3(a: int, b: int, c: int): int {
    if a <= b && a <= c then a else if b <= c then b else c
  }

  method Min3Impl(a: int, b: int, c: int) returns (m: int)
    ensures m == Min3(a, b, c)
}
