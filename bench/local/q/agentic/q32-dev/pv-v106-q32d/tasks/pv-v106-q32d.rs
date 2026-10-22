// Topic (e) dev task pv-v106-q32d (Q32, public; QPLAN §34.4, D76).
// Source: vericoding VV0090.rs (MIT (vericoding; verina: Apache-2.0)); proofs removed by verus-strip-proofs.
// Make `scripts/vcheck --gate` verify this file: add the proof it needs (invariants,
// assertions, lemma calls, lemmas of your own). Keep every line that is there.
// <vc-preamble>
use vstd::prelude::*;

verus! {
// </vc-preamble>

// <vc-helpers>
spec fn all_gt(n: i32, a: &Vec<i32>) -> bool {
    forall|i: int| 0 <= i < a.len() ==> n > a[i]
}
// </vc-helpers>

// <vc-spec>
fn is_greater(n: i32, a: &Vec<i32>) -> (result: bool)
    requires a.len() > 0,
    ensures result == (forall|i: int| 0 <= i < a.len() ==> n > a[i]),
// </vc-spec>
// <vc-code>
{
    let mut res: bool = true;
    let mut i: usize = 0;
    while i < a.len()
        decreases (a.len() - i) as int
    {
        let ai = a[i];
        res = res && n > ai;
        i = i + 1;
    }
    res
}
// </vc-code>

}
