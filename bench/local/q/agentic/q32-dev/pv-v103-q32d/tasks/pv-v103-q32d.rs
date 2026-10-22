// Topic (e) dev task pv-v103-q32d (Q32, public; QPLAN §34.4, D76).
// Source: vericoding VV0089.rs (MIT (vericoding; verina: Apache-2.0)); proofs removed by verus-strip-proofs.
// Make `scripts/vcheck --gate` verify this file: add the proof it needs (invariants,
// assertions, lemma calls, lemmas of your own). Keep every line that is there.
// <vc-preamble>
use vstd::prelude::*;

verus! {
// </vc-preamble>

// <vc-helpers>
/* helper modified by LLM (iteration 5): spec for existence using int indices */
spec fn exists_common_spec(a: &Vec<i32>, b: &Vec<i32>) -> bool {
    exists|i: int, j: int| 0 <= i && i < a.len() && 0 <= j && j < b.len() && a[i] == b[j]
}

// </vc-helpers>

// <vc-spec>
fn has_common_element(a: &Vec<i32>, b: &Vec<i32>) -> (result: bool)
    requires 
        a.len() > 0,
        b.len() > 0,
    ensures
        result == (exists|i: int, j: int| 0 <= i < a.len() && 0 <= j < b.len() && a[i] == b[j]),
// </vc-spec>
// <vc-code>
{
/* code modified by LLM (iteration 5): nested loops searching for common element with int-spec indexing */
    let mut i: usize = 0;
    while i < a.len()
        decreases a.len() - i
    {
        let mut j: usize = 0;
        while j < b.len()
            decreases b.len() - j
        {
            if a[i] == b[j] {
                return true;
            }
            j = j + 1;
        }
        i = i + 1;
    }
    false
}
// </vc-code>

}
