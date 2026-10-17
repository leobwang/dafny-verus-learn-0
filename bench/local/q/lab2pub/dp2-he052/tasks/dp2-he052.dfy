// Lab 2 public task dp2-he052 (Q15; QPLAN §25.6): vericoding `DH0055.dfy` at 387cd69 (MIT;
// bench/local/q/lab2pub/NOTICE), its specification, its proofs and the definitions only its
// specification used removed by scripts/dvl/benchstrip.py (dafny-lab2-form).
// Write `CheckBelowThreshold`'s `requires` and `ensures` from its prose (HumanEval/52's prompt,
// as the HumanEval-Verus set ships it, above the method), with any definition they need, and
// one call whose `requires` hold in `CheckBelowThresholdWitness`. You may add proof annotations
// (loop invariants, assertions, proof blocks, lemmas); never change its executable code, and
// keep every other line of the file.
// <vc-preamble>

// </vc-preamble>

// <vc-helpers>

// </vc-helpers>

// <vc-spec>
/* The task's prose:
def below_threshold(l: list, t: int):
    """Return True if all numbers in the list l are below threshold t.
    >>> below_threshold([1, 2, 4, 10], 100)
    True
    >>> below_threshold([1, 20, 4, 10], 5)
    False
    """
*/
method CheckBelowThreshold(l: seq<int>, t: int) returns (result: bool)
// </vc-spec>
// <vc-code>
{
  result := true;
  var i := 0;
  while i < |l|
  {
    if l[i] >= t {
      result := false;
      break;
    }
    i := i + 1;
  }
}
// </vc-code>

/** A non-vacuity witness for `CheckBelowThreshold`: one call whose `requires` hold. */
method CheckBelowThresholdWitness()
{
}
