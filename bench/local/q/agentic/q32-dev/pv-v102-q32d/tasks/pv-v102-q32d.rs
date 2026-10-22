// Topic (e) dev task pv-v102-q32d (Q32, public; QPLAN §34.4, D76).
// Source: vericoding VA0665.rs (MIT (vericoding; APPS: MIT)); proofs removed by verus-strip-proofs.
// Make `scripts/vcheck --gate` verify this file: add the proof it needs (invariants,
// assertions, lemma calls, lemmas of your own). Keep every line that is there.
// <vc-preamble>
use vstd::prelude::*;

verus! {
spec fn valid_input(lines: Seq<Seq<char>>) -> bool {
    lines.len() == 3 && forall|i: int| 0 <= i < 3 ==> lines[i].len() == 3
}

spec fn extract_diagonal(lines: Seq<Seq<char>>) -> Seq<char>
    recommends valid_input(lines)
{
    seq![lines[0][0], lines[1][1], lines[2][2]]
}
// </vc-preamble>

// <vc-helpers>
/* helper modified by LLM (iteration 4): added bounds checking lemmas */

// </vc-helpers>

// <vc-spec>
fn solve(lines: Vec<Vec<char>>) -> (result: Vec<char>)
    requires valid_input(lines@.map(|i: int, v: Vec<char>| v@))
    ensures 
        result@.len() == 4 &&
        result@[0] == lines@[0]@[0] &&
        result@[1] == lines@[1]@[1] &&
        result@[2] == lines@[2]@[2] &&
        result@[3] == '\n' &&
        result@ == extract_diagonal(lines@.map(|i: int, v: Vec<char>| v@)).push('\n')
// </vc-spec>
// <vc-code>
{
    /* code modified by LLM (iteration 4): added bounds checking proof */
    
    let mut result = Vec::new();
    
    result.push(lines[0][0]);
    result.push(lines[1][1]);
    result.push(lines[2][2]);
    result.push('\n');
    
    
    result
}
// </vc-code>


}

