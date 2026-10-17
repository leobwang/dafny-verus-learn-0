// Battery goal G12, Verus form (a whole file; it stands alone; given, Q15).
// Limbs under a bound stay under it in a concatenation (the step on the parts).
// The goal is the last proof fn; everything above it is given. Its statement
// (signature and clauses) is frozen; its quantified step's trigger is the choice.
use vstd::prelude::*;

verus! {

pub spec const BASE: nat = 0x1_0000_0000_0000_0000;

/// The value of a limb sequence, least significant limb first.
pub open spec fn seq_to_nat(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        s[0] as nat + BASE * seq_to_nat(s.drop_first())
    }
}

/// The place value of limb n, BASE to the power n. Opaque: its facts are the lemmas
/// below.
#[verifier::opaque]
pub open spec fn weight(n: nat) -> nat
    decreases n,
{
    if n == 0 {
        1
    } else {
        BASE * weight((n - 1) as nat)
    }
}

pub proof fn lemma_weight_succ(k: nat)
    ensures
        weight(k + 1) == BASE * weight(k),
{
    reveal(weight);
}

pub proof fn lemma_weight_pos(k: nat)
    ensures
        weight(k) > 0,
    decreases k,
{
    reveal(weight);
    if k > 0 {
        lemma_weight_pos((k - 1) as nat);
    }
}

/// Every limb is at most m.
pub open spec fn below(s: Seq<u64>, m: u64) -> bool {
    forall|i: int| 0 <= i < s.len() ==> #[trigger] s[i] <= m
}

pub proof fn lemma_below_concat(s: Seq<u64>, t: Seq<u64>, m: u64)
    requires
        below(s, m),
        below(t, m),
    ensures
        below(s + t, m),
{
    assert forall|i: int| 0 <= i < (s + t).len() implies (s + t)[i] <= m by {
        if i >= s.len() {
            assert((s + t)[i] == t[i - s.len()]);
        }
    }
}

} // verus!
