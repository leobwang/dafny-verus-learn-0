// Topic (e) dev task pv-v110-q32d (Q32, public; QPLAN §34.4, D76).
// Source: vericoding VV0099.rs (MIT (vericoding; verina: Apache-2.0)); proofs removed by verus-strip-proofs.
// Make `scripts/vcheck --gate` verify this file: add the proof it needs (invariants,
// assertions, lemma calls, lemmas of your own). Keep every line that is there.
// <vc-preamble>
use vstd::prelude::*;

verus! {
// </vc-preamble>

// <vc-helpers>

// </vc-helpers>

// <vc-spec>
fn is_sorted(a: &Vec<i32>) -> (result: bool)
    ensures
        result == (forall|i: int| 0 <= i < a.len() - 1 ==> #[trigger] a[i] <= a[i + 1]),
// </vc-spec>
// <vc-code>
{
    /* code modified by LLM (iteration 3): added trigger annotation to quantifier in invariant */
    if a.len() <= 1 {
        return true;
    }
    
    let mut i: usize = 0;
    while i < a.len() - 1
        decreases a.len() - 1 - i
    {
        if a[i] > a[i + 1] {
            return false;
        }
        i += 1;
    }
    
    
    true
}
// </vc-code>

}
