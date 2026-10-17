// Battery goal G04, Verus form (a whole file; it stands alone; given, Q15).
// Two numbers of one length are below twice its place value.
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

pub proof fn lemma_seq_to_nat_upper(s: Seq<u64>)
    ensures
        seq_to_nat(s) < weight(s.len()),
    decreases s.len(),
{
    reveal(weight);
    if s.len() > 0 {
        lemma_seq_to_nat_upper(s.drop_first());
        lemma_weight_succ((s.len() - 1) as nat);
    }
}

pub proof fn lemma_two_below_twice(s: Seq<u64>, t: Seq<u64>)
    requires
        s.len() == t.len(),
    ensures
        seq_to_nat(s) + seq_to_nat(t) < 2 * weight(s.len()),
{
    assert forall|u: Seq<u64>| seq_to_nat(u) < #[trigger] weight(u.len()) by {
        lemma_seq_to_nat_upper(u);
    }
}

} // verus!
