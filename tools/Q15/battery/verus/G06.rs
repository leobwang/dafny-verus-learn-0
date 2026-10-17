// Battery goal G06, Verus form (a whole file; it stands alone; given, Q15).
// Two zero limbs on top change no value.
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

pub proof fn lemma_zero_top(u: Seq<u64>)
    ensures
        seq_to_nat(u.push(0)) == seq_to_nat(u),
    decreases u.len(),
{
    if u.len() > 0 {
        assert(u.push(0).drop_first() =~= u.drop_first().push(0));
        lemma_zero_top(u.drop_first());
    } else {
        reveal_with_fuel(seq_to_nat, 2);
        assert(u.push(0).drop_first() =~= u);
    }
}

pub proof fn lemma_top_zeros_free(s: Seq<u64>)
    ensures
        seq_to_nat(s.push(0).push(0)) == seq_to_nat(s),
{
    assert forall|u: Seq<u64>| seq_to_nat(u.push(0)) == #[trigger] seq_to_nat(u) by {
        lemma_zero_top(u);
    }
}

} // verus!
