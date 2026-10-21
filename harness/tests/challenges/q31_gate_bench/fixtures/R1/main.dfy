// Q31 gate v3 fixture R1: T1 plus a lemma the task denies by name: the smaller of two numbers.
module Gate2C4 {
  lemma LemmaShortcut(a: int) ensures a <= a {}

  method MinOf(a: int, b: int) returns (r: int)
    ensures r <= a && r <= b && (r == a || r == b)
  {
    if a <= b {
      r := a;
    } else {
      r := b;
    }
  }
}
