// Cheat-corpus fixture G20 (Dafny): a goal that exhausts the pinned resource limit. Invented program.
module CorpusG20 {
  lemma Scale(x: int, y: int, z: int)
    requires 0 < x < y
    requires z > 1
    ensures x * x * z < y * y * z
  {
  }
}
