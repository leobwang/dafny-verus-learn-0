// Topic (e) Q33 dev pair pd-d104-q33d (public; QPLAN §35.4, Δ416): vericoding `DH0048.dfy` at
// 387cd69 (MIT; HumanEval/46), its specification, its proofs and the definitions only its
// specification used removed by scripts/dvl/benchstrip.py's Lab 2 form.
// Write `fib4`'s `requires` and `ensures` from its prose (HumanEval's prompt above the method),
// with any definition they need, and one call whose `requires` hold in `fib4_witness`. You may
// add proof annotations; never change its executable code, and keep every other line.

function fib4_func(n: int): int
    requires n >= 0
{
    if n == 0 then 0
    else if n == 1 then 0
    else if n == 2 then 2
    else if n == 3 then 0
    else fib4_func(n-1) + fib4_func(n-2) + fib4_func(n-3) + fib4_func(n-4)
}
// </vc-preamble>

// <vc-helpers>

// </vc-helpers>

// <vc-spec>
/* The task's prose:
def fib4(n: int):
    """The Fib4 number sequence is a sequence similar to the Fibbonacci sequnece that's defined as follows:
    fib4(0) -> 0
    fib4(1) -> 0
    fib4(2) -> 2
    fib4(3) -> 0
    fib4(n) -> fib4(n-1) + fib4(n-2) + fib4(n-3) + fib4(n-4).
    Please write a function to efficiently compute the n-th element of the fib4 number sequence.  Do not use recursion.
    >>> fib4(5)
    4
    >>> fib4(6)
    8
    >>> fib4(7)
    14
    """
*/
method fib4(n: int) returns (result: int)
// </vc-spec>
// <vc-code>
{
  if n == 0 {
    result := 0;
  } else if n == 1 {
    result := 0;
  } else if n == 2 {
    result := 2;
  } else if n == 3 {
    result := 0;
  } else {
    var a := fib4(n-4);
    var b := fib4(n-3);
    var c := fib4(n-2);
    var d := fib4(n-1);
    result := a + b + c + d;
  }
}
// </vc-code>

/** A non-vacuity witness for `fib4`: one call whose `requires` hold. */
method fib4_witness()
{
}
