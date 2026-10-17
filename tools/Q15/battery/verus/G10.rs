// Battery goal G10, Verus form (a whole file; it stands alone; given, Q15).
// A number is below the place value of any longer length.
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

pub proof fn lemma_weight_mono(m: nat, n: nat)
    requires
        m <= n,
    ensures
        weight(m) <= weight(n),
    decreases n - m,
{
    if m < n {
        lemma_weight_mono(m + 1, n);
        lemma_weight_succ(m);
        lemma_weight_pos(m);
    }
}

pub proof fn lemma_below_longer_place(s: Seq<u64>, n: nat)
    requires
        s.len() <= n,
    ensures
        seq_to_nat(s) < weight(n),
{
    assert forall|m: nat, k: nat| m <= k implies weight(m) <= weight(k) by {
        lemma_weight_mono(m, k);
    }
    lemma_seq_to_nat_upper(s);
}

} // verus!
