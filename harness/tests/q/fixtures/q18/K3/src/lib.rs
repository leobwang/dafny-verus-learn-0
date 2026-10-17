//! Gate v2 fixture K3: a value modulo BASE - 1, from the top limb down.
use vstd::prelude::*;
use vstd::arithmetic::div_mod::*;

verus! {

pub open spec fn seq_to_nat(s: Seq<u64>) -> nat
    decreases s.len(),
{
    if s.len() == 0 {
        0
    } else {
        s[0] as nat + 0x1_0000_0000_0000_0000 * seq_to_nat(s.drop_first())
    }
}

pub fn mod_word(v: &Vec<u64>) -> (r: u64)
    ensures
        r as nat == seq_to_nat(v@) % 18446744073709551615,
{
    let n = v.len();
    let mut r: u64 = 0;
    let mut i: usize = n;
    while i > 0
        invariant
            i <= n,
            n == v@.len(),
            r < 18446744073709551615,
            r as nat == seq_to_nat(v@.subrange(i as int, n as int)) % 18446744073709551615,
        decreases i,
    {
        i = i - 1;
        let x = v[i];
        let s: u128 = x as u128 + r as u128;
        let r2: u64 = (s % 18446744073709551615u128) as u64;
        proof {
        let t = seq_to_nat(v@.subrange(i as int + 1, n as int));
        assert(v@.subrange(i as int, n as int).drop_first() =~= v@.subrange(i as int + 1, n as int));
        broadcast use lemma_mod_multiples_vanish, lemma_mod_twice;
        }
        r = r2;
    }
    proof {
        assert(v@.subrange(0, n as int) =~= v@);
    }
    r
}

} // verus!
