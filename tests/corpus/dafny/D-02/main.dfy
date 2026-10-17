// Cheat-corpus fixture D-02 (Dafny): an @Axiom lemma. Invented program.
module CorpusD02 {
  function Cube(n: int): int { n * n * n }

  @Axiom
  lemma CubeMonotone(a: int, b: int)
    requires a < b
    ensures Cube(a) < Cube(b)

  lemma CubeStep(a: int)
    ensures Cube(a) < Cube(a + 1)
  {
    CubeMonotone(a, a + 1);
  }
}
