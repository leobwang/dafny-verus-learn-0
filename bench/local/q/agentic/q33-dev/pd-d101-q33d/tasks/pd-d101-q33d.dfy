// Topic (e) Q33 dev pair pd-d101-q33d (public; QPLAN §35.4, Δ416): vericoding `DH0137.dfy` at
// 387cd69 (MIT; HumanEval/135), its specification, its proofs and the definitions only its
// specification used removed by scripts/dvl/benchstrip.py's Lab 2 form.
// Write `can_arrange`'s `requires` and `ensures` from its prose (HumanEval's prompt above the
// method), with any definition they need, and one call whose `requires` hold in
// `can_arrange_witness`. You may add proof annotations; never change its executable code, and
// keep every other line.

predicate HasDecreaseAt(arr: seq<int>, i: int) {
    1 <= i < |arr| && arr[i] < arr[i-1]
}

// </vc-preamble>

// <vc-helpers>

// </vc-helpers>

// <vc-spec>
/* The task's prose:
def can_arrange(arr):
    """Create a function which returns the largest index of an element which
    is not greater than or equal to the element immediately preceding it. If
    no such element exists then return -1. The given array will not contain
    duplicate values.

    Examples:
    can_arrange([1,2,4,3,5]) = 3
    can_arrange([1,2,3]) = -1
    """
*/
method can_arrange(arr: seq<int>) returns (result: int)
// </vc-spec>
// <vc-code>
{
  if |arr| <= 1 {
    return -1;
  }
  
  var i := |arr| - 1;
  while i >= 1
  {
    if arr[i] < arr[i-1] {
      return i;
    }
    i := i - 1;
  }
  
  return -1;
}
// </vc-code>

/** A non-vacuity witness for `can_arrange`: one call whose `requires` hold. */
method can_arrange_witness()
{
}
