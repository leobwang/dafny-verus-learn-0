// Gate v2 fixture C4: the frozen statement of `MinOf` (the specfreeze reference).
module Gate2C4 {
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
