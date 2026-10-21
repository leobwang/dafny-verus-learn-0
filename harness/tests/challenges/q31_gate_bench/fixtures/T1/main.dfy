// Q31 gate v3 fixture T1 (a copy of Q18 C4): the smaller of two numbers.
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
