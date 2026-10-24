// Topic (e) Q33 dev pair pd-d103-q33d (public; QPLAN §35.4, Δ416): vericoding `DH0049.dfy` at
// 387cd69 (MIT; HumanEval/47), its specification, its proofs and the definitions only its
// specification used removed by scripts/dvl/benchstrip.py's Lab 2 form.
// Write `median`'s `requires` and `ensures` from its prose (HumanEval's prompt above the
// method), with any definition they need, and one call whose `requires` hold in
// `median_witness`. You may add proof annotations; never change its executable code, and keep
// every other line.

function InsertSorted(x: real, sorted: seq<real>): seq<real>
{
    if |sorted| == 0 then [x]
    else if x <= sorted[0] then [x] + sorted
    else [sorted[0]] + InsertSorted(x, sorted[1..])
}

function Sort(s: seq<real>): seq<real>
{
    if |s| == 0 then []
    else InsertSorted(s[0], Sort(s[1..]))
}

function Multiset(s: seq<real>): multiset<real> {
    if |s| == 0 then multiset{}
    else multiset{s[0]} + Multiset(s[1..])
}

// </vc-preamble>

// <vc-helpers>

// </vc-helpers>

// <vc-spec>
/* The task's prose:
def median(l: list):
    """Return median of elements in the list l.
    >>> median([3, 1, 2, 4, 5])
    3
    >>> median([-10, 4, 6, 1000, 10, 20])
    15.0
    """
*/
method median(l: seq<real>) returns (result: real)
// </vc-spec>
// <vc-code>
{
    var sorted_list := Sort(l);
    var n := |sorted_list|;
    
    
    if n % 2 == 1 {
        result := sorted_list[n / 2];
    } else {
        result := (sorted_list[n / 2 - 1] + sorted_list[n / 2]) / 2.0;
    }
}
// </vc-code>

/** A non-vacuity witness for `median`: one call whose `requires` hold. */
method median_witness()
{
}
