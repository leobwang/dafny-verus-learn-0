// Topic (e) dev task pv-v101-q32d (Q32, public; QPLAN §34.4, D76).
// Source: vericoding VV0165.rs (MIT (vericoding; verina: Apache-2.0)); proofs removed by verus-strip-proofs.
// Make `scripts/vcheck --gate` verify this file: add the proof it needs (invariants,
// assertions, lemma calls, lemmas of your own). Keep every line that is there.
// <vc-preamble>
use vstd::prelude::*;

verus! {
// </vc-preamble>

// <vc-helpers>

// </vc-helpers>

// <vc-spec>
fn reverse(a: &Vec<i32>) -> (result: Vec<i32>)
    ensures
        result.len() == a.len(),
        forall|i: int| 0 <= i < a.len() ==> result[i] == a[a.len() - 1 - i],
// </vc-spec>
// <vc-code>
{
    /* code modified by LLM (iteration 2): added decreases clause for while loop */
    let mut result = Vec::new();
    let mut idx = 0;
    while idx < a.len()
        invariant
            idx <= a.len(),
            result.len() == idx,
            forall|j: int| 0 <= j < idx ==> result[j] == a[a.len() - 1 - j],
        decreases a.len() - idx
    {
        result.push(a[a.len() - 1 - idx]);
        idx += 1;
    }
    result
}
// </vc-code>

}
