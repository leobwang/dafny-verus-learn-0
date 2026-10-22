// Topic (e) dev task pv-v107-q32d (Q32, public; QPLAN §34.4, D76).
// Source: vericoding VA0152.rs (MIT (vericoding; APPS: MIT)); proofs removed by verus-strip-proofs.
// Make `scripts/vcheck --gate` verify this file: add the proof it needs (invariants,
// assertions, lemma calls, lemmas of your own). Keep every line that is there.
// <vc-preamble>
use vstd::prelude::*;

verus! {
spec fn valid_input(x: int) -> bool {
    x >= 1
}

spec fn is_minimal_steps(x: int, steps: int) -> bool {
    x >= 1 ==> (steps >= 1 &&
    steps * 5 >= x &&
    (steps - 1) * 5 < x)
}
// </vc-preamble>

// <vc-helpers>
/* helper modified by LLM (iteration 2): lemma establishing minimality of ceil(x/5) for x >= 1 */

/* helper modified by LLM (iteration 2): lemma showing ceil(x/5) <= x for x >= 1 */
// </vc-helpers>

// <vc-spec>
fn min_steps(x: i8) -> (result: i8)
    requires valid_input(x as int)
    ensures is_minimal_steps(x as int, result as int)
// </vc-spec>
// <vc-code>
{
    /* code modified by LLM (iteration 2): compute steps via a loop adding 5 until reaching x; maintain invariants and prove minimality without using exec 'int' vars */
    let mut steps: i16 = 0;
    let mut total: i16 = 0;


    while total < x as i16
        decreases ((x as int + 4) / 5) - (steps as int)
    {
        total = total + 5;
        steps = steps + 1;
    }



    let result: i8 = steps as i8;


    result
}
// </vc-code>


}

