// Q31 gate v3 fixture L1: a delivery that adds a lever: the smaller of two numbers.
module Gate2C4 {
  method {:fuel MinOf, 3} MinOf(a: int, b: int) returns (r: int)
    ensures r <= a && r <= b && (r == a || r == b)
  {
    if a <= b {
      r := a;
    } else {
      r := b;
    }
  }
}
