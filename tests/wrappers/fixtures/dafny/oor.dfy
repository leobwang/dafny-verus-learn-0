// Wrapper fixture (tests/wrappers): nonlinear modular arithmetic that runs out of
// resource at the course pin (an inconclusive verdict, never a refutation).
module Fx_Oor {
  lemma Hard(a: int, b: int, c: int, d: int)
    requires a > 1 && b > 1 && c > 1 && d > 1
    ensures (a * b * c * d) % 7 == ((a % 7) * (b % 7) * (c % 7) * (d % 7)) % 7
  {
  }
}
