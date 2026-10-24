// Topic (e) Q33 dev pair pd-d108-q33d (public; QPLAN §35.4, Δ416): vericoding `DH0060.dfy` at
// 387cd69 (MIT; HumanEval/57), its specification, its proofs and the definitions only its
// specification used removed by scripts/dvl/benchstrip.py's Lab 2 form.
// Write `IsMonotonic`'s `requires` and `ensures` from its prose (HumanEval's prompt above the
// method), with any definition they need, and one call whose `requires` hold in
// `IsMonotonicWitness`. You may add proof annotations; never change its executable code, and
// keep every other line.

function monotonic(l: seq<int>): bool
    ensures |l| <= 1 ==> monotonic(l) == true
    ensures |l| > 1 ==> (monotonic(l) == (
        (forall i :: 0 <= i < |l| - 1 ==> l[i] <= l[i + 1]) ||
        (forall i :: 0 <= i < |l| - 1 ==> l[i] >= l[i + 1])
    ))
{
    if |l| <= 1 then true
    else
        var increasing := forall i :: 0 <= i < |l| - 1 ==> l[i] <= l[i + 1];
        var decreasing := forall i :: 0 <= i < |l| - 1 ==> l[i] >= l[i + 1];
        increasing || decreasing
}
// </vc-preamble>

// <vc-helpers>

// </vc-helpers>

// <vc-spec>
/* The task's prose:
def monotonic(l: list):
    """Return True is list elements are monotonically increasing or decreasing.
    >>> monotonic([1, 2, 4, 20])
    True
    >>> monotonic([1, 20, 4, 10])
    False
    >>> monotonic([4, 1, 0, -10])
    True
    """
*/
method IsMonotonic(l: seq<int>) returns (result: bool)
// </vc-spec>
// <vc-code>
{
    if |l| <= 1 {
        result := true;
    } else {
        var increasing := true;
        var decreasing := true;
        var i := 0;
        while i < |l| - 1
        {
            if l[i] > l[i + 1] {
                increasing := false;
            }
            if l[i] < l[i + 1] {
                decreasing := false;
            }
            i := i + 1;
        }
        result := increasing || decreasing;
    }
}
// </vc-code>

/** A non-vacuity witness for `IsMonotonic`: one call whose `requires` hold. */
method IsMonotonicWitness()
{
}
