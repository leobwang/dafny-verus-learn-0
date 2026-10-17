// Lab 2 public task dp3-he063 (Q15; QPLAN §25.6): vericoding `DH0065.dfy` at 387cd69 (MIT;
// bench/local/q/lab2pub/NOTICE), its specification, its proofs and the definitions only its
// specification used removed by scripts/dvl/benchstrip.py (dafny-lab2-form).
// Write `fibfib`'s `requires` and `ensures` from its prose (HumanEval/63's prompt, as the
// HumanEval-Verus set ships it, above the method), with any definition they need, and one call
// whose `requires` hold in `fibfib_witness`. You may add proof annotations (loop invariants,
// assertions, proof blocks, lemmas); never change its executable code, and keep every other
// line of the file.
// <vc-preamble>

function fibfib_spec(n: int): int
    requires n >= 0
{
    if n == 0 then 0
    else if n == 1 then 0
    else if n == 2 then 1
    else fibfib_spec(n-1) + fibfib_spec(n-2) + fibfib_spec(n-3)
}
// </vc-preamble>

// <vc-helpers>

// </vc-helpers>

// <vc-spec>
/* The task's prose:
def fibfib(n: int):
    """The FibFib number sequence is a sequence similar to the Fibbonacci sequnece that's defined as follows:
    fibfib(0) == 0
    fibfib(1) == 0
    fibfib(2) == 1
    fibfib(n) == fibfib(n-1) + fibfib(n-2) + fibfib(n-3).
    Please write a function to efficiently compute the n-th element of the fibfib number sequence.
    >>> fibfib(1)
    0
    >>> fibfib(5)
    4
    >>> fibfib(8)
    24
    """
*/
method fibfib(n: int) returns (result: int)
// </vc-spec>
// <vc-code>
{
  if n == 0 {
    result := 0;
  } else if n == 1 {
    result := 0;
  } else if n == 2 {
    result := 1;
  } else {
    var a := fibfib(n-3);
    var b := fibfib(n-2);
    var c := fibfib(n-1);
    result := a + b + c;
  }
}
// </vc-code>

/** A non-vacuity witness for `fibfib`: one call whose `requires` hold. */
method fibfib_witness()
{
}
