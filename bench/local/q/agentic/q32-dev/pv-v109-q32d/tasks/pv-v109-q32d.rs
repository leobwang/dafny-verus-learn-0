// Topic (e) dev task pv-v109-q32d (Q32, public; QPLAN §34.4, D76).
// Source: vericoding VV0136.rs (MIT (vericoding; verina: Apache-2.0)); proofs removed by verus-strip-proofs.
// Make `scripts/vcheck --gate` verify this file: add the proof it needs (invariants,
// assertions, lemma calls, lemmas of your own). Keep every line that is there.
// <vc-preamble>
use vstd::prelude::*;

verus! {
// </vc-preamble>

// <vc-helpers>

// </vc-helpers>

// <vc-spec>
fn copy(src: &Vec<i32>, s_start: usize, dest: &Vec<i32>, d_start: usize, len: usize) -> (result: Vec<i32>)
    requires 
        src.len() >= s_start + len,
        dest.len() >= d_start + len,
    ensures
        result.len() == dest.len(),
        forall|i: int| 0 <= i < d_start ==> #[trigger] result[i] == dest[i],
        forall|i: int| d_start + len <= i < result.len() ==> #[trigger] result[i] == dest[i],
        forall|i: int| 0 <= i < len ==> #[trigger] result[d_start + i] == #[trigger] src[s_start + i],
// </vc-spec>
// <vc-code>
{
    /* code modified by LLM (iteration 2): fixed invariant syntax and added preconditions */
    let mut result = dest.clone();
    let mut i: usize = 0;
    while i < len
        decreases len - i
    {
        let val = src[s_start + i];
        result.set(d_start + i, val);
        i = i + 1;
    }
    result
}
// </vc-code>

}
