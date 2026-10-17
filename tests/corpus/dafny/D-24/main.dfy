// Cheat-corpus fixture D-24 (Dafny): a per-declaration resource-limit attribute. Invented program.
module CorpusD24 {
  @ResourceLimit("40e6")
  lemma Expand(x: int, y: int)
    ensures (x + y) * (x + y) == x * x + 2 * x * y + y * y
  {
  }
}
