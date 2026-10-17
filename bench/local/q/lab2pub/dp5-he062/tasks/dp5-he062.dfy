// Lab 2 public task dp5-he062 (Q15; QPLAN §25.6): vericoding `DH0064.dfy` at 387cd69 (MIT;
// bench/local/q/lab2pub/NOTICE), its specification, its proofs and the definitions only its
// specification used removed by scripts/dvl/benchstrip.py (dafny-lab2-form).
// Write `derivative`'s `requires` and `ensures` from its prose (HumanEval/62's prompt, as the
// HumanEval-Verus set ships it, above the method), with any definition they need, and one call
// whose `requires` hold in `derivative_witness`. You may add proof annotations (loop
// invariants, assertions, proof blocks, lemmas); never change its executable code, and keep
// every other line of the file.
// <vc-preamble>

// </vc-preamble>

// <vc-helpers>

// </vc-helpers>

// <vc-spec>
/* The task's prose:
def derivative(xs: list):
    """ xs represent coefficients of a polynomial.
    xs[0] + xs[1] * x + xs[2] * x^2 + ....
     Return derivative of this polynomial in the same form.
    >>> derivative([3, 1, 2, 4, 5])
    [1, 4, 12, 20]
    >>> derivative([1, 2, 3])
    [2, 6]
    """
*/
method derivative(xs: seq<int>) returns (result: seq<int>)
// </vc-spec>
// <vc-code>
{
  if |xs| <= 1 {
    result := [];
  } else {
    result := [];
    var i := 0;
    while i < |xs| - 1
    {
      result := result + [(i + 1) * xs[i + 1]];
      i := i + 1;
    }
  }
}
// </vc-code>

/** A non-vacuity witness for `derivative`: one call whose `requires` hold. */
method derivative_witness()
{
}
