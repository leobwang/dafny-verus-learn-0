// Topic (e) Q33 dev pair pd-d106-q33d (public; QPLAN §35.4, Δ416): vericoding `DH0051.dfy` at
// 387cd69 (MIT; HumanEval/49), its specification, its proofs and the definitions only its
// specification used removed by scripts/dvl/benchstrip.py's Lab 2 form.
// Write `modp`'s `requires` and `ensures` from its prose (HumanEval's prompt above the method),
// with any definition they need, and one call whose `requires` hold in `modp_witness`. You may
// add proof annotations; never change its executable code, and keep every other line.

function power(base: int, exp: nat): int
{
    if exp == 0 then 1
    else base * power(base, exp - 1)
}
// </vc-preamble>

// <vc-helpers>
/* helper modified by LLM (iteration 2): PowerPred proves unfolding of power for positive exponent */

/* helper modified by LLM (iteration 2): PowerAdd by induction on y: power(a, x+y) = power(a,x)*power(a,y) */

/* helper modified by LLM (iteration 2): PowerBaseMul by induction on k: power(a*c,k) = power(a,k)*power(c,k) */

// </vc-helpers>

// <vc-spec>
/* The task's prose:
def modp(n: int, p: int):
    """Return 2^n modulo p (be aware of numerics).
    >>> modp(3, 5)
    3
    >>> modp(1101, 101)
    2
    >>> modp(0, 101)
    1
    >>> modp(3, 11)
    8
    >>> modp(100, 101)
    1
    """
*/
method modp(n: int, p: int) returns (result: int)
// </vc-spec>
// <vc-code>
{
  /* code modified by LLM (iteration 2): Implement fast exponentiation and mod reduction without axioms */
  var res: nat := 1;
  var b: nat := 2;
  var e: nat := n;
  while e > 0
    decreases e
  {
    if e % 2 == 1 {
      var olde := e;
      var oldb := b;
      var oldres := res;
      // update for odd exponent: multiply result by base and decrement exponent
      res := res * b;
      e := e - 1;
    } else {
      var olde := e;
      var oldb := b;
      b := b * b;
      e := e / 2;
    }
  }
  result := res % p;
}

// </vc-code>

/** A non-vacuity witness for `modp`: one call whose `requires` hold. */
method modp_witness()
{
}
